import os
import json
import folium
import plotly.graph_objs as go
import numpy as np
from tkinter import filedialog
from collections import Counter, OrderedDict
from math import radians, sin, cos, sqrt, atan2
from geopy.geocoders import Nominatim

class DataAnalysis:
    def __init__(self):
        print("DataAnalysis init")
        #self.create_directory_hierarchy()

    def create_directory_hierarchy(self, group, start_date, end_date):
        self.group = group
        self.start_date = start_date
        self.end_date = end_date

        print(start_date, end_date)

        # Mostrar el diálogo para seleccionar el directorio de guardado
        directory = filedialog.askdirectory()

        # Verificar si se seleccionó un directorio
        if directory:
            group_directory = f"{directory}/{self.group}"
            os.makedirs(group_directory, exist_ok=True)  # Crear directorio si no existe
            self.working_directory = f"{group_directory}/From{self.start_date}_To{self.end_date}"
            self.data_dir = f"{self.working_directory}/data"
            self.graphics_dir = f"{self.working_directory}/graphics"
            os.makedirs(self.working_directory, exist_ok=True)  # Crear subdirectorio si no existe
            os.makedirs(f'{self.working_directory}/data', exist_ok=True)  # Crear subdirectorio si no existe
            os.makedirs(f'{self.working_directory}/data/NST', exist_ok=True)  # Crear subdirectorio si no existe
            os.makedirs(f'{self.working_directory}/graphics', exist_ok=True)  # Crear subdirectorio si no existe
            os.makedirs(f'{self.working_directory}/graphics/maps', exist_ok=True)  # Crear subdirectorio si no existe
            os.makedirs(f'{self.working_directory}/graphics/gateways', exist_ok=True)  # Crear subdirectorio si no existe
            os.makedirs(f'{self.working_directory}/graphics/distributions', exist_ok=True)  # Crear subdirectorio si no existe
            os.makedirs(f'{self.working_directory}/graphics/distancesToMainGateways', exist_ok=True)  # Crear subdirectorio si no existe
            os.makedirs(f'{self.working_directory}/graphics/lastSFused', exist_ok=True)  # Crear subdirectorio si no existe

        return self.working_directory
    
    def save_devices_and_payloads(self, devices, payloads):
        payloads_file = f"{self.working_directory}/data/{self.group}_devicesPayloads.json"
        devices_file = f"{self.working_directory}/data/{self.group}_allDevices.json"

        with open(payloads_file, 'w') as f:
            json.dump(payloads, f, indent=4)
        with open(devices_file, 'w') as f:
            json.dump(devices, f, indent=4)

    def save_gateways(self, gateways):
        gateways_file = f"{self.working_directory}/data/allGateways.json"
        with open(gateways_file, 'w') as outfile:
            json.dump(gateways, outfile, indent=4)

    def save_selected_gateways(self, gateways):
        self.gateways_file = f"{self.working_directory}/data/selectedGateways.json"
        with open(self.gateways_file, 'w') as outfile:
            json.dump(gateways, outfile, indent=4)

    def save_selected_gateway_info(self, gw_id, content):
        data = json.loads(content)
        self.gateways_file = f"{self.working_directory}/data/NST/gateway_{gw_id}.json"
        with open(self.gateways_file, 'w') as outfile:
            json.dump(data, outfile, indent=4)

    def generate_data_for_graphics(self, update_graphics_creation_progress_bar):
        self.get_average_results()
        update_graphics_creation_progress_bar(1)
        self.merge_allDevices_averageResults()
        update_graphics_creation_progress_bar(2)
        self.calculate_devices_distances_to_gateways()
        update_graphics_creation_progress_bar(3)
        self.merge_devicesAndGWsDistances_devicesSemiCombinedData()
        update_graphics_creation_progress_bar(4)
        self.merge_all_selected_gateways_data()
        update_graphics_creation_progress_bar(5)
        self.merge_selectedGateways_allGWsNSTInfo()
        update_graphics_creation_progress_bar(6)

    def get_average_results(self):
        # Cargar el JSON
        with open(f'{self.data_dir}/{self.group}_devicesPayloads.json') as payloads_json:
            devices_payloads = json.load(payloads_json)

        # Diccionario para mantener las sumas, los recuentos y los mensajes perdidos
        sums = {}
        counts = {}
        lost_frames = {}
        gw_reached_sum = {}
        main_gw_counts = {}
        received_frames = {}
        last_dr_used = {}

        max_received_frames = max(len(dev.get('data', [])) for dev in devices_payloads)

        # Recorrer los datos
        for dev in devices_payloads:
            deveui = dev['deveui']
            fcnt_list = [data['fcnt'] for data in dev.get('data', [])]  # Usamos dev.get() para manejar casos donde no hay 'data'
            fcnt_list.sort()

            if len(fcnt_list) >= 2:
                lost_frames[deveui] = max_received_frames - len(fcnt_list)
            else:
                lost_frames[deveui] = max_received_frames
            
            gw_reached_sum[deveui] = sum(data['gws_reached'] for data in dev.get('data', []))  # Usamos dev.get() para manejar casos donde no hay 'data'
            
            received_frames[deveui] = len(dev.get('data', []))  # Usamos dev.get() para manejar casos donde no hay 'data'

            main_gw_counter = Counter(data['main_gw'] for data in dev.get('data', []))  # Usamos dev.get() para manejar casos donde no hay 'data'
            main_gw_counts[deveui] = main_gw_counter.most_common(1)[0][0] if main_gw_counter else None
            
            if dev.get('data'):  # Verificar si hay datos antes de intentar acceder al último elemento
                last_dr_used[deveui] = dev['data'][-1]['dr_used'].split('BW')[0]  # Obtiene la parte del string antes de 'BW'
            else:
                last_dr_used[deveui] = "Unknown"

            
            for data in dev.get('data', []):  # Usamos dev.get() para manejar casos donde no hay 'data'
                rssi = data['rssi']
                snr = data['snr']
                time_on_air_ms = data['time_on_air_ms']

                if deveui not in sums:
                    sums[deveui] = {'rssi': 0, 'snr': 0, 'time_on_air_ms': 0}
                    counts[deveui] = 0

                sums[deveui]['rssi'] += rssi
                sums[deveui]['snr'] += snr
                sums[deveui]['time_on_air_ms'] += time_on_air_ms
                counts[deveui] += 1

        # Calcular las medias
        averages = []
        for deveui in sums:
            averages.append({
                'deveui': deveui,
                'average_rssi': sums[deveui]['rssi'] / counts[deveui],
                'average_snr': sums[deveui]['snr'] / counts[deveui],
                'average_time_on_air_ms': sums[deveui]['time_on_air_ms'] / counts[deveui],
                'average_gws_reached': gw_reached_sum[deveui] / counts[deveui],
                'main_gw': main_gw_counts[deveui],
                'lost_frames': lost_frames[deveui],
                'received_frames': received_frames[deveui],
                'last_SF_used': last_dr_used[deveui]  # Agrega el valor de 'dr_used' del último objeto dentro de 'data'
            })

        # Guardar los resultados en un nuevo JSON
        with open(f'{self.data_dir}/averageResults.json', 'w') as outfile:
            json.dump(averages, outfile, indent=4)

    def merge_allDevices_averageResults(self):
        # Cargar los datos desde los archivos JSON
        with open(f'{self.data_dir}/{self.group}_allDevices.json', 'r') as f:
            all_devices_data = json.load(f)

        with open(f'{self.data_dir}/averageResults.json', 'r') as f:
            average_results_data = json.load(f)

        # Crear un diccionario para mapear los datos por deveui
        device_mapping = {device['deveui']: {'latitude': device['latitude'], 'longitude': device['longitude']} for device in all_devices_data}

        # Iterar sobre los datos de average_results.json y combinarlos con los datos de all_devices.json
        combined_data = []
        for result in average_results_data:
            deveui = result['deveui']
            if deveui in device_mapping:
                combined_data.append({**device_mapping[deveui], **result})

        # Escribir los datos combinados en un nuevo archivo JSON
        with open(f'{self.data_dir}/devicesSemiCombinedData.json', 'w') as f:
            json.dump(combined_data, f, indent=4)

    def calculate_devices_distances_to_gateways(self):
        def calcular_distancia(lat1, lon1, lat2, lon2):
            if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
                return float('inf')
            
            # Radio de la Tierra en kilómetros
            R = 6371.0

            # Convertir las latitudes y longitudes de grados a radianes
            lat1_rad = radians(lat1)
            lon1_rad = radians(lon1)
            lat2_rad = radians(lat2)
            lon2_rad = radians(lon2)

            # Diferencias entre las latitudes y longitudes
            dlat = lat2_rad - lat1_rad
            dlon = lon2_rad - lon1_rad

            # Fórmula de Haversine
            a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
            c = 2 * atan2(sqrt(a), sqrt(1 - a))

            # Distancia entre los dos puntos
            distancia = R * c
            return distancia
        
        # Cargar los datos de los gateways y dispositivos desde los archivos JSON
        with open(f'{self.data_dir}/selectedGateways.json', 'r') as file:
            gateways = json.load(file)

        with open(f'{self.data_dir}/devicesSemiCombinedData.json', 'r') as file:
            dispositivos = json.load(file)

        # Crear una lista para almacenar la información de salida
        output_data = []

        # Iterar sobre cada dispositivo
        for dispositivo in dispositivos:
            dispositivo_lat = dispositivo['latitude']
            dispositivo_lon = dispositivo['longitude']
            distancia_minima = float('inf')
            gateway_mas_cercano = None
            distancia_main_gw = None

            # Iterar sobre cada gateway para encontrar el más cercano al dispositivo actual
            for gateway in gateways:
                gateway_lat = gateway['latitude']
                gateway_lon = gateway['longitude']
                distancia = calcular_distancia(dispositivo_lat, dispositivo_lon, gateway_lat, gateway_lon) * 1000 # Multiplicamos x1000 para ponerlo en metros
                if distancia < distancia_minima:
                    distancia_minima = distancia
                    gateway_mas_cercano = gateway
                if dispositivo['main_gw'] == gateway['id']:
                    distancia_main_gw = distancia

            # Si el main_gw no se encuentra en la lista de gateways, establecer la distancia y el ID como "unknown"
            if distancia_main_gw is None or distancia_main_gw == "out of range":
                distancia_main_gw = "unknown"
                main_gw_id = "unknown"
            else:
                main_gw_id = dispositivo['main_gw']

            # Guardar la información en la lista de salida solo si se encontró un gateway cercano
            if gateway_mas_cercano is not None:
                output_data.append({
                    'deveui': dispositivo['deveui'],
                    'gateway_id_mas_cercano': gateway_mas_cercano['id'],
                    'distancia_entre_dispositivo_y_gateway_mas_cercano': distancia_minima,
                    'main_gw_id': main_gw_id,
                    'distancia_entre_dispositivo_y_main_gw': distancia_main_gw
                })
            else:
                output_data.append({
                    'deveui': dispositivo['deveui'],
                    'gateway_id_mas_cercano': "unknown",
                    'distancia_entre_dispositivo_y_gateway_mas_cercano': "unknown",
                    'main_gw_id': main_gw_id,
                    'distancia_entre_dispositivo_y_main_gw': "unknown"
                })

        # Guardar la información en un nuevo archivo JSON
        with open(f'{self.data_dir}/devicesAndGWsDistances.json', 'w') as file:
            json.dump(output_data, file, indent=4)

    def merge_devicesAndGWsDistances_devicesSemiCombinedData(self):
        # Cargar datos desde los archivos JSON
        with open(f'{self.data_dir}/devicesAndGWsDistances.json', 'r') as file:
            devices_and_gws_distances = json.load(file)

        with open(f'{self.data_dir}/devicesSemiCombinedData.json', 'r') as file:
            combined_data_devices = json.load(file)

        # Crear un diccionario para mapear deveui a los datos combinados
        combined_data_map = {device['deveui']: device for device in combined_data_devices}

        # Unir los datos en un solo JSON
        combined_json = []
        for device_distance in devices_and_gws_distances:
            deveui = device_distance['deveui']
            if deveui in combined_data_map:
                combined_data = combined_data_map[deveui]
                # Mover 'deveui' al principio del objeto
                combined_data = {'deveui': combined_data['deveui'], **combined_data}
                combined_data.update(device_distance)  # Actualizar los datos combinados con la información de distancias
                combined_json.append(combined_data)

        # Guardar los datos combinados en un nuevo archivo JSON
        with open(f'{self.data_dir}/devicesCombinedData.json', 'w') as file:
            json.dump(combined_json, file, indent=4)

    def merge_all_selected_gateways_data(self):
        # Directorio que contiene los archivos JSON
        directory = f"{self.data_dir}/NST"

        # Lista para almacenar los datos combinados
        combined_data = []

        # Iterar sobre cada archivo en el directorio
        for filename in os.listdir(directory):
            if filename.endswith('.json'):
                with open(os.path.join(directory, filename)) as file:
                    data = json.load(file)
                    for gateway_id, values in data.items():
                        # Procesar los datos según el formato requerido
                        combined_data.append({
                            "Gateway_ID": gateway_id,
                            "UL_Frame_Cnt": values['ulToa'],
                            "Lost_Frame_Cnt": 0,  # Por defecto 0, ya que no se proporciona en los datos originales
                            "Avr_RSSI_[dBm]": float(values['aRSSI']),
                            "Avr_SNR_[dB]": float(values['aSNR'])
                        })

        # Escribir los datos combinados en un archivo JSON
        with open(f'{self.data_dir}/allGWsNSTInfo.json', 'w') as file:
            json.dump(combined_data, file, indent=4)

    def merge_selectedGateways_allGWsNSTInfo(self):
        # Cargar datos desde los archivos JSON
        with open(f'{self.data_dir}/selectedGateways.json', 'r') as file:
            all_gateways = json.load(file)

        with open(f'{self.data_dir}/allGWsNSTInfo.json', 'r') as file:
            all_gws_nst_info = json.load(file)
        
        # Convertir Gateway_ID a minúsculas en all_gws_nst_info para que coincida con 'id' en all_gateways
        for item in all_gws_nst_info:
            item['Gateway_ID'] = item['Gateway_ID'].lower()

        # Crear un diccionario para mapear id/Gateway_ID a los datos de all_gws_nst_info
        gws_nst_info_map = {gateway['Gateway_ID'].lower(): gateway for gateway in all_gws_nst_info}

        # Unir los datos en un solo JSON
        combined_json = []
        for gateway in all_gateways:
            gateway_id = gateway['id'].lower()
            if gateway_id in gws_nst_info_map:
                nst_info = gws_nst_info_map[gateway_id]
                combined_data = OrderedDict([('Gateway_ID', gateway_id), ('name', gateway['name']), ('status', gateway['status']), ('altitude', gateway['altitude']), ('latitude', gateway['latitude']), ('longitude', gateway['longitude']), ('UL_Frame_Cnt', nst_info['UL_Frame_Cnt']), ('Lost_Frame_Cnt', nst_info['Lost_Frame_Cnt']), ('Avr_RSSI_[dBm]', nst_info['Avr_RSSI_[dBm]']), ('Avr_SNR_[dB]', nst_info['Avr_SNR_[dB]'])])
                combined_json.append(combined_data)

        # Guardar los datos combinados en un nuevo archivo JSON
        with open(f'{self.data_dir}/gatewaysCombinedData.json', 'w') as file:
            json.dump(combined_json, file, indent=4)

    ### GRAPHICS (FIXED TIME) ###

    def generate_graphics(self, update_graphics_creation_progress_bar):
        self.create_map()
        update_graphics_creation_progress_bar(7)
        self.gateways_graphics()
        update_graphics_creation_progress_bar(8)
        self.devices_graphics_1()
        update_graphics_creation_progress_bar(9)
        self.devices_graphics_2()
        update_graphics_creation_progress_bar(10)
        self.devices_graphics_3()
        update_graphics_creation_progress_bar(11)

    def create_map(self):
        def obtener_coordenadas(barrio):
            geolocalizador = Nominatim(user_agent="aplicacion_geopy")
            ubicacion = geolocalizador.geocode(barrio)
            if ubicacion:
                return ubicacion.latitude, ubicacion.longitude
            else:
                return None

        with open(f'{self.data_dir}/gatewaysCombinedData.json') as gw_json:
            gateways = json.load(gw_json)

        with open(f'{self.data_dir}/devicesCombinedData.json') as devices_json:
            devices = json.load(devices_json)

        coordenadas = obtener_coordenadas(self.group)
        startZoom = 14
        if coordenadas == None:
            coordenadas = [43.031211, -2.606495]
            startZoom = 10

        mapa = folium.Map(location=[coordenadas[0], coordenadas[1]], zoom_start=startZoom)

        iconos = {
            "gateway": "cloud",
            "device": "mobile"
        }

        for gw in gateways:
            ubicacion = (gw["latitude"], gw["longitude"])
            folium.Marker(location=ubicacion, popup=gw["name"], icon=folium.Icon(icon=iconos["gateway"])).add_to(mapa)
            #folium.Circle(location=ubicacion, radius=500, color='green').add_to(mapa)
            #folium.Circle(location=ubicacion, radius=1000, color='blue').add_to(mapa)
            #folium.Circle(location=ubicacion, radius=1500, color='blue').add_to(mapa)

        for dev in devices:
            ubicacion = (dev["latitude"], dev["longitude"])
            if ubicacion != (None, None):
                #folium.Marker(location=ubicacion, icon=folium.Icon(icon=iconos["device"])).add_to(mapa)
                folium.CircleMarker(location=ubicacion, radius=2, color='red', fill=True, fill_color='red').add_to(mapa)

        mapa.save(f'{self.graphics_dir}/maps/mapGWsAndDevices.html')

    def gateways_graphics(self):
        def generar_grafico(data, x_variable, y_variable, titulo, nombre_archivo, titulo_y, titulo_x):
            data_sorted = sorted(data, key=lambda x: x[y_variable], reverse=True)  # Ordenar por variable Y
            data_plot = go.Bar(x=[d[x_variable] for d in data_sorted], y=[d[y_variable] for d in data_sorted],
                            hovertext=[f'{y_variable}: {d[y_variable]}, name: {d["name"]}' for d in data_sorted])
            layout_plot = go.Layout(title=titulo, xaxis=dict(title=titulo_x), yaxis=dict(title=titulo_y), bargap=0.1)
            fig_plot = go.Figure(data=[data_plot], layout=layout_plot)
            fig_plot.write_html(f'{self.graphics_dir}/gateways/{nombre_archivo}')

        with open(f'{self.data_dir}/gatewaysCombinedData.json') as gw_json:
            datos_gateways = json.load(gw_json)

        # Convertir "UL_Frame_Cnt" de cadena de texto a número
        for gateway in datos_gateways:
            gateway["UL_Frame_Cnt"] = float(gateway["UL_Frame_Cnt"])
        
        # Generar y guardar el gráficos
        generar_grafico(datos_gateways, 'Gateway_ID', 'UL_Frame_Cnt', 'Número de frames de Uplink por gateway', 'uplinkFrameCounter_x_gateways.html', 'Uplink Frame Counter', 'Gateway ID')
        generar_grafico(datos_gateways, 'Gateway_ID', 'Lost_Frame_Cnt', 'Número de frames perdidos por gateway', 'lostFrameCounter_x_gateways.html', 'Lost Frame Counter', 'Gateway ID')
        # generar_grafico(datos_gateways, 'Gateway_ID', 'FER_[%]', 'Porcentaje de FER (Frame Error Rate) por gateway', 'FER[%]_x_gateways.html', 'FER (%)', 'Gateway ID')
        generar_grafico(datos_gateways, 'Gateway_ID', 'Avr_RSSI_[dBm]', 'Media de RSSI (dBm) por gateway', 'averageRSSI_x_gateways.html', 'Average RSSI (dBm)', 'Gateway ID')
        generar_grafico(datos_gateways, 'Gateway_ID', 'Avr_SNR_[dB]', 'Media de SNR (dB) por gateway', 'averageSNR_x_gateways.html', 'Average SNR (dB)', 'Gateway ID')

    def devices_graphics_1(self):
        # Función para agrupar los valores en números enteros o de 10 en 10
        def agrupar_valores(datos, nombre_variable):
            valores = [dato[nombre_variable] for dato in datos]
            min_valor = min(valores)
            max_valor = max(valores)
            agrupados = {}
            
            if nombre_variable == "average_time_on_air_ms":  # Para "time on air"
                for valor in range(0, int(max_valor) + 1, 10):
                    agrupados[valor] = sum(1 for v in valores if int(v) // 10 == valor // 10)
            elif nombre_variable == "average_gws_reached":  # Para "average_gws_reached"
                for valor in valores:
                    grupo = round(valor * 10) / 10  # Redondea al décimo más cercano
                    agrupados[grupo] = agrupados.get(grupo, 0) + 1
            else:
                for valor in range(int(min_valor), int(max_valor) + 1):
                    agrupados[valor] = sum(1 for v in valores if int(v) == valor)
            return agrupados
        
        # Función para contar las ocurrencias de cada valor único de la variable
        def contar_ocurrencias(datos, nombre_variable, valores_incluidos):
            ocurrencias = {}
            for dato in datos:
                valor = dato[nombre_variable]
                if valor in valores_incluidos:
                    if valor in ocurrencias:
                        ocurrencias[valor] += 1
                    else:
                        ocurrencias[valor] = 1
                else:
                    if "others" in ocurrencias:
                        ocurrencias["others"] += 1
                    else:
                        ocurrencias["others"] = 1
            return ocurrencias

        # Funcion para generar los graficos
        def generar_grafico(datos, atributo, nombre_archivo, x_titulo):
            datos_agrupados = agrupar_valores(datos, atributo)
            data = go.Bar(x=list(datos_agrupados.keys()), y=list(datos_agrupados.values()))
            layout = go.Layout(title=f'Distribución de {x_titulo}', xaxis=dict(title=x_titulo), yaxis=dict(title='Número de ocurrencias'), bargap=0.1)
            fig = go.Figure(data=[data], layout=layout)
            fig.write_html(f'{self.graphics_dir}/distributions/{nombre_archivo}')
        
        with open(f'{self.data_dir}/devicesCombinedData.json') as dev_json:
            datos_devices = json.load(dev_json)

        generar_grafico(datos_devices, "average_rssi", 'RSSI_distribution.html', 'Average RSSI')
        generar_grafico(datos_devices, "average_snr", 'SNR_distribution.html', 'Average SNR')
        generar_grafico(datos_devices, "average_time_on_air_ms", 'timeOnAir_distribution.html', 'Average Time on Air')
        generar_grafico(datos_devices, "lost_frames", 'lostFrames_distribution.html', 'Lost Frames')
        generar_grafico(datos_devices, "received_frames", 'receivedFrames_distribution.html', 'Received Frames')
        generar_grafico(datos_devices, "average_gws_reached", 'averageGatewaysReached_distribution.html', 'Average Gateways reached')

        with open(f'{self.data_dir}/gatewaysCombinedData.json') as gw_json:
            datos_gateways = json.load(gw_json)

        # Obtener datos de main_gw de gateways específicos y ordenarlos
        gateways_ids = [gateway["Gateway_ID"] for gateway in datos_gateways]
        gateways_names = {gateway["Gateway_ID"]: gateway["name"] for gateway in datos_gateways}
        ocurrencias_main_gw = contar_ocurrencias(datos_devices, "main_gw", gateways_ids)
        ocurrencias_main_gw_sorted = dict(sorted(ocurrencias_main_gw.items(), key=lambda x: x[1], reverse=True))
        ocurrencias_main_gw_sorted["others"] = ocurrencias_main_gw_sorted.pop("others", 0)

        # Generar y guardar el gráfico para main_gw
        data_main_gw = go.Bar(x=list(ocurrencias_main_gw_sorted.keys()), y=list(ocurrencias_main_gw_sorted.values()), hovertext=[gateways_names[id] if id in gateways_names else id for id in ocurrencias_main_gw_sorted.keys()])
        layout_main_gw = go.Layout(title='Distribución de Main Gateways', xaxis=dict(title='Main gateways'), yaxis=dict(title='Número de ocurrencias'), bargap=0.1)
        fig_main_gw = go.Figure(data=[data_main_gw], layout=layout_main_gw)
        fig_main_gw.write_html(f'{self.graphics_dir}/distributions/mainGateways_distribution.html')

        # Obtener todos los valores únicos de "last_SF_used"
        valores_unicos_last_SF_used = set(dato["last_SF_used"] for dato in datos_devices)
        datos_ocurrencias_last_SF_used = contar_ocurrencias(datos_devices, "last_SF_used", valores_incluidos=valores_unicos_last_SF_used)

        # Ordenar las keys del diccionario
        keys_ordenadas = sorted(datos_ocurrencias_last_SF_used.keys(), key=lambda x: int(x[2:]))

        # Generar y guardar el gráfico para last_SF_used
        data_last_SF_used = go.Bar(x=keys_ordenadas, y=[datos_ocurrencias_last_SF_used[key] for key in keys_ordenadas])
        layout_last_SF_used = go.Layout(title='Distribución de last Spreading factor (SF) used', xaxis=dict(title='Last SF used'), yaxis=dict(title='Número de ocurrencias'), bargap=0.1)
        fig_last_SF_used = go.Figure(data=[data_last_SF_used], layout=layout_last_SF_used)
        fig_last_SF_used.write_html(f'{self.graphics_dir}/distributions/lastSFUsed_distribution.html')

    def devices_graphics_2(self):
        def group_by_interval(distances, values, distance_intervals):
            data_by_distance_interval = {interval: [] for interval in distance_intervals}
            for distance, value in zip(distances, values):
                interval = next(interval for interval in distance_intervals if interval >= distance)
                data_by_distance_interval[interval].append(value)
            return data_by_distance_interval
        
        def get_lost_by_interval(received, max):
            lost_by_distance_interval = {}
            for distance, values in received.items():
                if values:
                    lost_values = [max - value for value in values]
                    lost_by_distance_interval[distance] = lost_values
                else:
                    lost_by_distance_interval[distance] = []
            return lost_by_distance_interval

        def calculate_mean_by_interval(data_by_distance_interval):
            mean_by_distance_interval = {}
            for interval, values in data_by_distance_interval.items():
                if len(values) > 1:
                    mean_by_distance_interval[interval] = np.mean(values)
            return mean_by_distance_interval
        
        def calculate_cumulative_mean(mean_by_distance_interval, data_by_distance_interval):
            cumulative_mean = []
            cumulative_mean_value = 0
            total_count = 0
            for interval, values in data_by_distance_interval.items():
                if interval in mean_by_distance_interval:
                    mean_value = mean_by_distance_interval[interval]
                    count = len(values)
                    cumulative_mean_value += mean_value * count
                    total_count += count
                cumulative_mean.append(cumulative_mean_value / total_count if total_count > 0 else np.nan)
            cumulative_mean.pop(0)  # Remove first element which is NaN
            return cumulative_mean
        
        def calculate_cumulative_mean_percentage(mean_by_distance_interval, data_by_distance_interval, max_received_frames):
            cumulative_mean_percentage = []
            cumulative_mean_value = 0
            total_count = 0
            for interval, values in data_by_distance_interval.items():
                if interval in mean_by_distance_interval:
                    mean_value = mean_by_distance_interval[interval]
                    count = len(values)
                    cumulative_mean_value += mean_value * count
                    total_count += count
                    cumulative_mean_percentage.append((cumulative_mean_value / total_count) / max_received_frames * 100)
            return cumulative_mean_percentage

        def calculate_percentage_of_max(received_by_distance_interval, max_received_frames):
            percentage_of_max = {}
            for interval, values in received_by_distance_interval.items():
                if len(values) > 1:
                    mean_value = np.mean(values)
                    percentage_of_max[interval] = (mean_value / max_received_frames) * 100
            return percentage_of_max

        def generate_plotly_bar_and_line_graph(data_dict, bar_labels, cumulative_values, title, x_axis_title, y_axis_title, file_name):
            fig = go.Figure()

            # Add bar chart
            fig.add_trace(go.Bar(
                x=list(data_dict.keys()),
                y=list(data_dict.values()),
                text=bar_labels,
                name='Media por Intervalo'
                #marker_color='rgb(55, 83, 109)',
            ))

            # Add cumulative line
            fig.add_trace(go.Scatter(
                x=list(data_dict.keys()),
                y=cumulative_values,
                mode='lines',
                name='Media Acumulada',
                line=dict(color='red', width=2)
            ))

            # Configure layout
            fig.update_layout(
                title=title,
                xaxis_title=x_axis_title,
                yaxis_title=y_axis_title,
                xaxis=dict(
                    tickmode='linear',
                    dtick=100
                )
            )

            # Write to HTML file
            fig.write_html(f'{self.graphics_dir}/distancesToMainGateways/{file_name}')

        def generate_plotly_bar_and_line_graph_with_threshold(data_dict, bar_labels, cumulative_values, title, x_axis_title, y_axis_title, file_name, y_threshold):
            fig = go.Figure()

            # Add bar chart
            fig.add_trace(go.Bar(
                x=list(data_dict.keys()),
                y=list(data_dict.values()),
                text=bar_labels,
                name='Media por Intervalo'
                #marker_color='rgb(55, 83, 109)',
            ))

            # Add cumulative line
            fig.add_trace(go.Scatter(
                x=list(data_dict.keys()),
                y=cumulative_values,
                mode='lines',
                name='Media Acumulada',
                line=dict(color='red', width=2)
            ))

            # Add horizontal line at y = y_threshold
            fig.add_shape(type="line",
                x0=min(data_dict.keys()), y0=y_threshold,
                x1=max(data_dict.keys()), y1=y_threshold,
                line=dict(color="green", width=2, dash="dash"),
            )

            # Configure layout
            fig.update_layout(
                title=title,
                xaxis_title=x_axis_title,
                yaxis_title=y_axis_title,
                xaxis=dict(
                    tickmode='linear',
                    dtick=100
                )
            )

            # Write to HTML file
            fig.write_html(f'{self.graphics_dir}/distancesToMainGateways/{file_name}')

        def process_data_and_generate_graphs(attribute_averages, distance_intervals, filename_prefix, y_axis_label):
            data_by_distance_interval = group_by_interval(distances, attribute_averages, distance_intervals)
            mean_by_distance_interval = calculate_mean_by_interval(data_by_distance_interval)
            cumulative_mean = calculate_cumulative_mean(mean_by_distance_interval, data_by_distance_interval)
            bar_labels = [f'Dispositivos: {len(data_by_distance_interval[interval])}' for interval in mean_by_distance_interval.keys()]
            generate_plotly_bar_and_line_graph(mean_by_distance_interval, bar_labels, cumulative_mean,
                                                f'Media de {y_axis_label} y Media Acumulada por Intervalo de Distancia',
                                                'Distancia (m)', f'Media de {y_axis_label}', f'{filename_prefix}.html')

        # Cargar los datos desde el archivo JSON
        with open(f'{self.data_dir}/devicesCombinedData.json') as dev_json:
            data = json.load(dev_json)

        # Crear listas para almacenar las distancias y los promedios
        distances = []
        rssi_averages = []
        snr_averages = []
        toa_averages = []
        lost_averages = []
        received_averages = []

        # Extraer distancias y promedios
        for device in data:
            distance_str = device['distancia_entre_dispositivo_y_main_gw']
            # Verificar si la distancia es conocida
            if distance_str != 'unknown':
                distance = float(distance_str)
                rssi = device['average_rssi']
                snr = device['average_snr']
                toa = device['average_time_on_air_ms']
                lost = device['lost_frames']
                received = device['received_frames']
                distances.append(distance)
                rssi_averages.append(rssi)
                snr_averages.append(snr)
                toa_averages.append(toa)
                lost_averages.append(lost)
                received_averages.append(received)

        # Definir los intervalos de distancia
        distance_intervals = list(range(0, int(max(distances)) + 100, 100))

        # Generar graficos
        process_data_and_generate_graphs(rssi_averages, distance_intervals, 'averageRSSI_x_distanceToMainGateway', 'RSSI (dBm)')
        process_data_and_generate_graphs(snr_averages, distance_intervals, 'averageSNR_x_distanceToMainGateway', 'SNR (dB)')
        process_data_and_generate_graphs(toa_averages, distance_intervals, 'averageTimeOnAir_x_distanceToMainGateway', 'Time on Air (ms)')
        process_data_and_generate_graphs(lost_averages, distance_intervals, 'averageLostFrames_x_distanceToMainGateway', 'Lost Frames (paquetes)')
        process_data_and_generate_graphs(received_averages, distance_intervals, 'averageReceivedFrames_x_distanceToMainGateway', 'Received Frames (paquetes)')

        # Group data by distance interval
        received_by_distance_interval = group_by_interval(distances, received_averages, distance_intervals)
        lost_by_distance_interval = get_lost_by_interval(received_by_distance_interval, max(received_averages))

        # Calculate mean by distance interval
        mean_lost_by_distance_interval = calculate_mean_by_interval(lost_by_distance_interval)
        mean_received_by_distance_interval = calculate_mean_by_interval(received_by_distance_interval)

        # Calculate cumulative mean
        cumulative_mean_lost = calculate_cumulative_mean_percentage(mean_lost_by_distance_interval, lost_by_distance_interval, max(received_averages))
        cumulative_mean_received = calculate_cumulative_mean_percentage(mean_received_by_distance_interval, received_by_distance_interval, max(received_averages))

        # Calculate percentage of max
        percentage_of_max_lost = calculate_percentage_of_max(lost_by_distance_interval, max(received_averages))
        percentage_of_max_received = calculate_percentage_of_max(received_by_distance_interval, max(received_averages))

        # Create bar labels
        bar_labels_lost = [f'Dispositivos: {len(lost_by_distance_interval[interval])}' for interval in mean_lost_by_distance_interval.keys()]
        bar_labels_received = [f'Dispositivos: {len(received_by_distance_interval[interval])}' for interval in mean_received_by_distance_interval.keys()]

        # Generate and save graphs
        generate_plotly_bar_and_line_graph_with_threshold(percentage_of_max_lost, bar_labels_lost, cumulative_mean_lost, 'Media de Lost Frames y Media Acumulada por Intervalo de Distancia', 'Distancia (m)', 'Media de Lost Frames (%)', 'averageLostFramesPercentage_x_distanceToMainGateway.html', 10)
        generate_plotly_bar_and_line_graph_with_threshold(percentage_of_max_received, bar_labels_received, cumulative_mean_received, 'Media de Received Frames y Media Acumulada por Intervalo de Distancia', 'Distancia (m)', 'Media de Received Frames (%)', 'averageReceivedFramesPercentage_x_distanceToMainGateway.html', 90)

    def devices_graphics_3(self):
        # Cargar los datos desde el archivo JSON
        with open(f'{self.data_dir}/devicesCombinedData.json') as dev_json:
            data = json.load(dev_json)

        # Crear diccionario para almacenar los datos agrupados
        grouped_received_data = {}
        max_sf_received = 0
        grouped_lost_data = {}
        grouped_rssi_data = {}
        grouped_snr_data = {}

        # Agrupar los datos según el campo "last_SF_used"
        for entry in data:
            sf_used = entry['last_SF_used']
            received_frames = entry['received_frames']
            lost_frames = entry['lost_frames']
            rssi = entry['average_rssi']
            snr = entry['average_snr']
            
            # Para received_frames
            if received_frames > max_sf_received:
                max_sf_received = received_frames

            if sf_used not in grouped_received_data:
                grouped_received_data[sf_used] = {'received_frames_list': [], 'device_count': 0}
                
            grouped_received_data[sf_used]['received_frames_list'].append(received_frames)
            grouped_received_data[sf_used]['device_count'] += 1
            
            # Para lost_frames
            if sf_used not in grouped_lost_data:
                grouped_lost_data[sf_used] = {'lost_frames_list': [], 'device_count': 0}
                
            grouped_lost_data[sf_used]['lost_frames_list'].append(lost_frames)
            grouped_lost_data[sf_used]['device_count'] += 1

            # Para average_rssi
            if sf_used not in grouped_rssi_data:
                grouped_rssi_data[sf_used] = {'rssi_list': [], 'device_count': 0}
                
            grouped_rssi_data[sf_used]['rssi_list'].append(rssi)
            grouped_rssi_data[sf_used]['device_count'] += 1

            # Para average_snr
            if sf_used not in grouped_snr_data:
                grouped_snr_data[sf_used] = {'snr_list': [], 'device_count': 0}
                
            grouped_snr_data[sf_used]['snr_list'].append(snr)
            grouped_snr_data[sf_used]['device_count'] += 1

        # Calcular la media de "received_frames", "lost_frames", "average_rssi" y "average_snr" y contar el número de dispositivos para cada grupo
        sf_received_info = {}
        for sf_used, data in grouped_received_data.items():
            mean_received_frames = sum(data['received_frames_list']) / len(data['received_frames_list'])
            sf_received_info[sf_used] = {'mean_received_frames_percentage': mean_received_frames / max_sf_received * 100, 'device_count': data['device_count']}

        sf_lost_info = {}
        for sf_used, data in grouped_lost_data.items():
            mean_lost_frames = sum(data['lost_frames_list']) / len(data['lost_frames_list'])
            sf_lost_info[sf_used] = {'mean_lost_frames_percentage': mean_lost_frames / max_sf_received * 100, 'device_count': data['device_count']}

        sf_rssi_info = {}
        for sf_used, data in grouped_rssi_data.items():
            mean_rssi = sum(data['rssi_list']) / len(data['rssi_list'])
            sf_rssi_info[sf_used] = {'mean_rssi': mean_rssi, 'device_count': data['device_count']}

        sf_snr_info = {}
        for sf_used, data in grouped_snr_data.items():
            mean_snr = sum(data['snr_list']) / len(data['snr_list'])
            sf_snr_info[sf_used] = {'mean_snr': mean_snr, 'device_count': data['device_count']}

        # Ordenar las claves de SF7 a SF12
        sorted_sf_received_info = {sf: sf_received_info.get(sf, {'mean_received_frames_percentage': 0, 'device_count': 0}) for sf in ['SF7', 'SF8', 'SF9', 'SF10', 'SF11', 'SF12']}
        sorted_sf_lost_info = {sf: sf_lost_info.get(sf, {'mean_lost_frames_percentage': 0, 'device_count': 0}) for sf in ['SF7', 'SF8', 'SF9', 'SF10', 'SF11', 'SF12']}
        sorted_sf_rssi_info = {sf: sf_rssi_info.get(sf, {'mean_rssi': 0, 'device_count': 0}) for sf in ['SF7', 'SF8', 'SF9', 'SF10', 'SF11', 'SF12']}
        sorted_sf_snr_info = {sf: sf_snr_info.get(sf, {'mean_snr': 0, 'device_count': 0}) for sf in ['SF7', 'SF8', 'SF9', 'SF10', 'SF11', 'SF12']}

        # Crear gráfico de barras interactivo para received_frames
        bar_trace_received = go.Bar(
            x=[sf for sf in sorted_sf_received_info.keys()],
            y=[info['mean_received_frames_percentage'] for info in sorted_sf_received_info.values()],
            text=[f'Dispositivos: {info["device_count"]}' for info in sorted_sf_received_info.values()],
            textposition='auto'
        )

        layout_received = go.Layout(
            title="Media de Received Frames (%) por Last SF used",
            xaxis=dict(title="Last SF used"),
            yaxis=dict(title="Average Received Frames (%)")
        )

        fig_received = go.Figure(data=[bar_trace_received], layout=layout_received)

        # Write received_frames to HTML file
        fig_received.write_html(f'{self.graphics_dir}/lastSFused/averageReceivedFramesPercentage_x_lastSFUsed.html')

        # Crear gráfico de barras interactivo para lost_frames
        bar_trace_lost = go.Bar(
            x=[sf for sf in sorted_sf_lost_info.keys()],
            y=[info['mean_lost_frames_percentage'] for info in sorted_sf_lost_info.values()],
            text=[f'Dispositivos: {info["device_count"]}' for info in sorted_sf_lost_info.values()],
            textposition='auto'
        )

        layout_lost = go.Layout(
            title="Media de Lost Frames (%) por Last SF used",
            xaxis=dict(title="Last SF used"),
            yaxis=dict(title="Average Lost Frames (%)")
        )

        fig_lost = go.Figure(data=[bar_trace_lost], layout=layout_lost)

        # Write lost_frames to HTML file
        fig_lost.write_html(f'{self.graphics_dir}/lastSFused/averageLostFramesPercentage_x_lastSFUsed.html')

        # Crear gráficos de barras interactivos para average_rssi
        bar_trace_rssi = go.Bar(
            x=[sf for sf in sorted_sf_rssi_info.keys()],
            y=[info['mean_rssi'] for info in sorted_sf_rssi_info.values()],
            text=[f'Dispositivos: {info["device_count"]}' for info in sorted_sf_rssi_info.values()],
            textposition='auto'
        )

        layout_rssi = go.Layout(
            title="Media de RSSI por Last SF used",
            xaxis=dict(title="Last SF used"),
            yaxis=dict(title="Average RSSI")
        )

        fig_rssi = go.Figure(data=[bar_trace_rssi], layout=layout_rssi)

        # Write average_rssi to HTML file
        fig_rssi.write_html(f'{self.graphics_dir}/lastSFused/averageRSSI_x_lastSFUsed.html')

        # Crear gráficos de barras interactivos para average_snr
        bar_trace_snr = go.Bar(
            x=[sf for sf in sorted_sf_snr_info.keys()],
            y=[info['mean_snr'] for info in sorted_sf_snr_info.values()],
            text=[f'Dispositivos: {info["device_count"]}' for info in sorted_sf_snr_info.values()],
            textposition='auto'
        )

        layout_snr = go.Layout(
            title="Media de SNR por Last SF used",
            xaxis=dict(title="Last SF used"),
            yaxis=dict(title="Average SNR")
        )

        fig_snr = go.Figure(data=[bar_trace_snr], layout=layout_snr)

        # Write average_snr to HTML file
        fig_snr.write_html(f'{self.graphics_dir}/lastSFused/averageSNR_x_lastSFUsed.html')

    ### GRAPHICS (COMPARISON OF 2) ###
        
    def create_comparison_directory_hierarchy_2(self, compare_dir_1, compare_dir_2):
        self.compare_dir_1 = compare_dir_1
        self.compare_dir_2 = compare_dir_2

        father_dir_1 = os.path.dirname(self.compare_dir_1)
        folder_dir_1 = os.path.basename(self.compare_dir_1)
        dates_dir_1 = folder_dir_1.split('_')
        from_dir_1 = dates_dir_1[0][4:8]  # Tomar los 2 siguientes caracteres después de "From"
        to_dir_1 = dates_dir_1[1][2:6]  # Tomar los 2 siguientes caracteres después de "To"

        folder_dir_2 = os.path.basename(self.compare_dir_2)
        dates_dir_2 = folder_dir_2.split('_')
        from_dir_2 = dates_dir_2[0][4:8]  # Tomar los 2 siguientes caracteres después de "From"
        to_dir_2 = dates_dir_2[1][2:6]  # Tomar los 2 siguientes caracteres después de "To"

        self.output_dir = os.path.join(father_dir_1, f"Compare_{from_dir_1}{to_dir_1}_to_{from_dir_2}{to_dir_2}")
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(f"{self.output_dir}/distancesToMainGateways", exist_ok=True)
        os.makedirs(f"{self.output_dir}/distributions", exist_ok=True)
        os.makedirs(f"{self.output_dir}/gateways", exist_ok=True)
        os.makedirs(f"{self.output_dir}/lastSFused", exist_ok=True)
        
    def compare_graphics_2(self, update_compare_graphics_progress_bar):
        #self.compare_dir_1 = compare_dir_1
        #self.compare_dir_2 = compare_dir_2
        #self.output_dir = "D:/Clase/Master/2 MAILA/TFM/LoRa Analisis/galdakao/output"

        self.compare_2_gateways_graphics()
        update_compare_graphics_progress_bar(1)
        self.compare_2_devices_graphics_1()
        update_compare_graphics_progress_bar(2)
        self.compare_2_devices_graphics_2()
        update_compare_graphics_progress_bar(3)
        self.compare_2_devices_graphics_3()
        update_compare_graphics_progress_bar(4)

    def compare_2_gateways_graphics(self):
        def generar_grafico(data1, data2, x_variable, y_variable, titulo, nombre_archivo, titulo_y, titulo_x):
            data1_sorted = sorted(data1, key=lambda x: x[y_variable], reverse=True)  # Ordenar por variable Y
            data2_sorted = sorted(data2, key=lambda x: x[y_variable], reverse=True)  # Ordenar por variable Y

            data1_plot = go.Bar(x=[d[x_variable] for d in data1_sorted], y=[d[y_variable] for d in data1_sorted],
                            hovertext=[f'{y_variable}: {d[y_variable]}, name: {d["name"]}' for d in data1_sorted],
                            name='Data 1', marker=dict(color='blue'))

            data2_plot = go.Bar(x=[d[x_variable] for d in data2_sorted], y=[d[y_variable] for d in data2_sorted],
                            hovertext=[f'{y_variable}: {d[y_variable]}, name: {d["name"]}' for d in data2_sorted],
                            name='Data 2', marker=dict(color='red'))

            layout_plot = go.Layout(title=titulo, xaxis=dict(title=titulo_x), yaxis=dict(title=titulo_y), bargap=0.1)
            fig_plot = go.Figure(data=[data1_plot, data2_plot], layout=layout_plot)
            fig_plot.write_html(f'{self.output_dir}/gateways/{nombre_archivo}')

        with open(f'{self.compare_dir_1}/data/gatewaysCombinedData.json') as gw_json:
            data1 = json.load(gw_json)

        with open(f'{self.compare_dir_2}/data/gatewaysCombinedData.json') as gw_json:
            data2 = json.load(gw_json)

        # Convertir "UL_Frame_Cnt" de cadena de texto a número
        for gateway in data1:
            gateway["UL_Frame_Cnt"] = float(gateway["UL_Frame_Cnt"])

        for gateway in data2:
            gateway["UL_Frame_Cnt"] = float(gateway["UL_Frame_Cnt"])

        # Generar y guardar los gráficos
        generar_grafico(data1, data2, 'Gateway_ID', 'UL_Frame_Cnt', 'Número de frames de Uplink por gateway', 'uplinkFrameCounter_x_gateways.html', 'Uplink Frame Counter', 'Gateway ID')
        generar_grafico(data1, data2, 'Gateway_ID', 'Lost_Frame_Cnt', 'Número de frames perdidos por gateway', 'lostFrameCounter_x_gateways.html', 'Lost Frame Counter', 'Gateway ID')
        # generar_grafico(data1, data2, 'Gateway_ID', 'FER_[%]', 'Porcentaje de FER (Frame Error Rate) por gateway', 'FER[%]_x_gateways.html', 'FER (%)', 'Gateway ID')
        generar_grafico(data1, data2, 'Gateway_ID', 'Avr_RSSI_[dBm]', 'Media de RSSI (dBm) por gateway', 'averageRSSI_x_gateways.html', 'Average RSSI (dBm)', 'Gateway ID')
        generar_grafico(data1, data2, 'Gateway_ID', 'Avr_SNR_[dB]', 'Media de SNR (dB) por gateway', 'averageSNR_x_gateways.html', 'Average SNR (dB)', 'Gateway ID')

    def compare_2_devices_graphics_1(self):
        # Función para agrupar los valores en números enteros o de 10 en 10
        def agrupar_valores(datos, nombre_variable):
            valores = [dato[nombre_variable] for dato in datos]
            min_valor = min(valores)
            max_valor = max(valores)
            agrupados = {}
            
            if nombre_variable == "average_time_on_air_ms":  # Para "time on air"
                for valor in range(0, int(max_valor) + 1, 10):
                    agrupados[valor] = sum(1 for v in valores if int(v) // 10 == valor // 10)
            elif nombre_variable == "average_gws_reached":  # Para "average_gws_reached"
                for valor in valores:
                    grupo = round(valor * 10) / 10  # Redondea al décimo más cercano
                    agrupados[grupo] = agrupados.get(grupo, 0) + 1
            else:
                for valor in range(int(min_valor), int(max_valor) + 1):
                    agrupados[valor] = sum(1 for v in valores if int(v) == valor)
            return agrupados

        def generar_grafico(datos_1, datos_2, atributo, nombre_archivo, x_titulo):
            datos_agrupados_1 = agrupar_valores(datos_1, atributo)
            datos_agrupados_2 = agrupar_valores(datos_2, atributo)
            
            data_1 = go.Bar(x=[x - 0.2 for x in datos_agrupados_1.keys()], y=list(datos_agrupados_1.values()), name='Datos 1', marker=dict(color='blue'))
            data_2 = go.Bar(x=[x + 0.2 for x in datos_agrupados_2.keys()], y=list(datos_agrupados_2.values()), name='Datos 2', marker=dict(color='red'))
            data = [data_1, data_2]
            
            layout = go.Layout(title=f'Distribución de {x_titulo}', xaxis=dict(title=x_titulo), yaxis=dict(title='Número de ocurrencias'), bargap=0.1)
            fig = go.Figure(data=data, layout=layout)
            fig.write_html(f'{self.output_dir}/distributions/{nombre_archivo}')
             
        def contar_ocurrencias(datos, nombre_variable, valores_incluidos):
            ocurrencias = {}
            for dato in datos:
                valor = dato[nombre_variable]
                if valor in valores_incluidos:
                    if valor in ocurrencias:
                        ocurrencias[valor] += 1
                    else:
                        ocurrencias[valor] = 1
                else:
                    if "others" in ocurrencias:
                        ocurrencias["others"] += 1
                    else:
                        ocurrencias["others"] = 1
            return ocurrencias
        
        def generar_grafico_SF(datos1, datos2, titulo):
            keys_ordenadas = sorted(set(datos1.keys()) | set(datos2.keys()), key=lambda x: int(x[2:]))
            data1 = go.Bar(x=keys_ordenadas, y=[datos1.get(key, 0) for key in keys_ordenadas], name='Archivo 1', marker=dict(color='blue'))
            data2 = go.Bar(x=keys_ordenadas, y=[datos2.get(key, 0) for key in keys_ordenadas], name='Archivo 2', marker=dict(color='red'))
            layout = go.Layout(title=titulo, xaxis=dict(title='Last SF used'), yaxis=dict(title='Número de ocurrencias'), bargap=0.1)
            return go.Figure(data=[data1, data2], layout=layout)

        def generar_grafico_GW(datos1, datos2, titulo):
            keys_ordenadas = sorted(set(datos1.keys()) | set(datos2.keys()))
            data1 = go.Bar(x=list(datos1.keys()), y=list(datos1.values()), hovertext=[gateways_names[id] if id in gateways_names else id for id in datos1.keys()], name='Archivo 1', marker=dict(color='blue'))
            data2 = go.Bar(x=list(datos2.keys()), y=list(datos2.values()), hovertext=[gateways_names[id] if id in gateways_names else id for id in datos2.keys()], name='Archivo 2', marker=dict(color='red'))
            layout = go.Layout(title=titulo, xaxis=dict(title='Main gateways'), yaxis=dict(title='Número de ocurrencias'), bargap=0.1)
            return go.Figure(data=[data1, data2], layout=layout)
        
        with open(f'{self.compare_dir_1}/data/devicesCombinedData.json') as dev_json:
            datos_1 = json.load(dev_json)

        with open(f'{self.compare_dir_2}/data/devicesCombinedData.json') as dev_json:
            datos_2 = json.load(dev_json)

        generar_grafico(datos_1, datos_2, "average_rssi", 'RSSI_distribution.html', 'Average RSSI')
        generar_grafico(datos_1, datos_2, "average_snr", 'SNR_distribution.html', 'Average SNR')
        generar_grafico(datos_1, datos_2, "average_time_on_air_ms", 'timeOnAir_distribution.html', 'Average Time on Air')
        generar_grafico(datos_1, datos_2, "lost_frames", 'lostFrames_distribution.html', 'Lost Frames')
        generar_grafico(datos_1, datos_2, "received_frames", 'receivedFrames_distribution.html', 'Received Frames')
        generar_grafico(datos_1, datos_2, "average_gws_reached", 'averageGatewaysReached_distribution.html', 'Average Gateways reached')

        # Contar ocurrencias para cada conjunto de datos
        ocurrencias1 = contar_ocurrencias(datos_1, "last_SF_used", set(dato["last_SF_used"] for dato in datos_1))
        ocurrencias2 = contar_ocurrencias(datos_2, "last_SF_used", set(dato["last_SF_used"] for dato in datos_2))

        # Generar el gráfico combinado
        figura_combinada = generar_grafico_SF(ocurrencias1, ocurrencias2, 'Comparación de last Spreading factor (SF) used')

        # Generar el archivo HTML del gráfico combinado
        figura_combinada.write_html(f'{self.output_dir}/distributions/lastSFUsed_distribution.html')

        with open(f'{self.compare_dir_1}/data/gatewaysCombinedData.json') as gw_json:
            datos_gateways1 = json.load(gw_json)

        with open(f'{self.compare_dir_2}/data/gatewaysCombinedData.json') as gw_json:
            datos_gateways2 = json.load(gw_json)

        # Obtener datos de main_gw de gateways específicos y ordenarlos
        gateways_ids1 = [gateway["Gateway_ID"] for gateway in datos_gateways1]
        gateways_names = {gateway["Gateway_ID"]: gateway["name"] for gateway in datos_gateways1}
        ocurrencias_main_gw1 = contar_ocurrencias(datos_1, "main_gw", gateways_ids1)
        ocurrencias_main_gw_sorted1 = dict(sorted(ocurrencias_main_gw1.items(), key=lambda x: x[1], reverse=True))
        ocurrencias_main_gw_sorted1["others"] = ocurrencias_main_gw_sorted1.pop("others", 0)

        gateways_ids2 = [gateway["Gateway_ID"] for gateway in datos_gateways2]
        gateways_names = {gateway["Gateway_ID"]: gateway["name"] for gateway in datos_gateways2}
        ocurrencias_main_gw2 = contar_ocurrencias(datos_2, "main_gw", gateways_ids2)
        ocurrencias_main_gw_sorted2 = dict(sorted(ocurrencias_main_gw2.items(), key=lambda x: x[1], reverse=True))
        ocurrencias_main_gw_sorted2["others"] = ocurrencias_main_gw_sorted2.pop("others", 0)

        # Generar y guardar el gráfico combinado para main_gw
        figura_main_gw = generar_grafico_GW(ocurrencias_main_gw_sorted1, ocurrencias_main_gw_sorted2, 'Comparación de Main Gateways')
        figura_main_gw.write_html(f'{self.output_dir}/distributions/mainGateways_comparison.html')
        
    def compare_2_devices_graphics_2(self):
        def group_by_interval(distances, values, distance_intervals):
            data_by_distance_interval = {interval: [] for interval in distance_intervals}
            for distance, value in zip(distances, values):
                interval = next(interval for interval in distance_intervals if interval >= distance)
                data_by_distance_interval[interval].append(value)
            return data_by_distance_interval
        
        def get_lost_by_interval(received, max):
            lost_by_distance_interval = {}
            for distance, values in received.items():
                if values:
                    lost_values = [max - value for value in values]
                    lost_by_distance_interval[distance] = lost_values
                else:
                    lost_by_distance_interval[distance] = []
            return lost_by_distance_interval
        
        def calculate_mean_by_interval(data_by_distance_interval):
            mean_by_distance_interval = {}
            for interval, values in data_by_distance_interval.items():
                if len(values) > 1:
                    mean_by_distance_interval[interval] = np.mean(values)
            return mean_by_distance_interval
        
        def calculate_cumulative_mean(mean_by_distance_interval, data_by_distance_interval):
            cumulative_mean = []
            cumulative_mean_value = 0
            total_count = 0
            for interval, values in data_by_distance_interval.items():
                if interval in mean_by_distance_interval:
                    mean_value = mean_by_distance_interval[interval]
                    count = len(values)
                    cumulative_mean_value += mean_value * count
                    total_count += count
                cumulative_mean.append(cumulative_mean_value / total_count if total_count > 0 else np.nan)
            cumulative_mean.pop(0)  # Remove first element which is NaN
            return cumulative_mean
        
        def calculate_cumulative_mean_percentage(mean_by_distance_interval, data_by_distance_interval, max_received_frames):
            cumulative_mean_percentage = []
            cumulative_mean_value = 0
            total_count = 0
            for interval, values in data_by_distance_interval.items():
                if interval in mean_by_distance_interval:
                    mean_value = mean_by_distance_interval[interval]
                    count = len(values)
                    cumulative_mean_value += mean_value * count
                    total_count += count
                    cumulative_mean_percentage.append((cumulative_mean_value / total_count) / max_received_frames * 100)
            return cumulative_mean_percentage
        
        def calculate_percentage_of_max(received_by_distance_interval, max_received_frames):
            percentage_of_max = {}
            for interval, values in received_by_distance_interval.items():
                if len(values) > 1:
                    mean_value = np.mean(values)
                    percentage_of_max[interval] = (mean_value / max_received_frames) * 100
            return percentage_of_max

        def generate_plotly_comparison_graphs(data_dict1, data_dict2, bar_labels1, bar_labels2, cumulative_values1, cumulative_values2, title, x_axis_title, y_axis_title, file_name):
            fig = go.Figure()

            # Add bar charts for data1 and data2
            fig.add_trace(go.Bar(
                x=list(data_dict1.keys()),
                y=list(data_dict1.values()),
                text=bar_labels1,
                name='Media por Intervalo (Data 1)',
                marker=dict(color='blue')
            ))

            fig.add_trace(go.Bar(
                x=list(data_dict2.keys()),
                y=list(data_dict2.values()),
                text=bar_labels2,
                name='Media por Intervalo (Data 2)',
                marker=dict(color='red')
            ))

            # Add cumulative lines for data1 and data2
            fig.add_trace(go.Scatter(
                x=list(data_dict1.keys()),
                y=cumulative_values1,
                mode='lines',
                name='Media Acumulada (Data 1)',
                line=dict(color='blue', width=2)
            ))

            fig.add_trace(go.Scatter(
                x=list(data_dict2.keys()),
                y=cumulative_values2,
                mode='lines',
                name='Media Acumulada (Data 2)',
                line=dict(color='red', width=2)
            ))

            # Configure layout
            fig.update_layout(
                title=title,
                xaxis_title=x_axis_title,
                yaxis_title=y_axis_title,
                xaxis=dict(
                    tickmode='linear',
                    dtick=100
                )
            )

            # Write to HTML file
            fig.write_html(f'{self.output_dir}/distancesToMainGateways/{file_name}')

        def generate_plotly_bar_and_line_graph_with_threshold_comparison(data_dict1, bar_labels1, cumulative_values1, data_dict2, bar_labels2, cumulative_values2, title, x_axis_title, y_axis_title, file_name, y_threshold):
            fig = go.Figure()

            # Add bar chart
            fig.add_trace(go.Bar(
                x=list(data_dict1.keys()),
                y=list(data_dict1.values()),
                text=bar_labels1,
                name='Media por Intervalo (Data 1)',
                marker=dict(color='blue')
            ))

            # Add cumulative line
            fig.add_trace(go.Scatter(
                x=list(data_dict1.keys()),
                y=cumulative_values1,
                mode='lines',
                name='Media Acumulada (Data 1)',
                line=dict(color='blue', width=2)
            ))

            # Add bar chart
            fig.add_trace(go.Bar(
                x=list(data_dict2.keys()),
                y=list(data_dict2.values()),
                text=bar_labels2,
                name='Media por Intervalo (Data 2)',
                marker=dict(color='red')
            ))

            # Add cumulative line
            fig.add_trace(go.Scatter(
                x=list(data_dict2.keys()),
                y=cumulative_values2,
                mode='lines',
                name='Media Acumulada (Data 2)',
                line=dict(color='red', width=2)
            ))

            # Add horizontal line at y = y_threshold
            fig.add_shape(type="line",
                x0=min(data_dict1.keys()), y0=y_threshold,
                x1=max(data_dict1.keys()), y1=y_threshold,
                line=dict(color="purple", width=2, dash="dash"),
            )

            # Configure layout
            fig.update_layout(
                title=title,
                xaxis_title=x_axis_title,
                yaxis_title=y_axis_title,
                xaxis=dict(
                    tickmode='linear',
                    dtick=100
                )
            )

            # Write to HTML file
            fig.write_html(f'{self.output_dir}/distancesToMainGateways/{file_name}')

        # Cargar los datos desde el archivo JSON
        with open(f'{self.compare_dir_1}/data/devicesCombinedData.json') as dev_json:
            data1 = json.load(dev_json)

        with open(f'{self.compare_dir_2}/data/devicesCombinedData.json') as dev_json:
            data2 = json.load(dev_json)

        # Crear listas para almacenar las distancias y los promedios de ambos conjuntos de datos
        distances = []
        rssi_averages1 = []
        snr_averages1 = []
        toa_averages1 = []
        lost_averages1 = []
        received_averages1 = []

        rssi_averages2 = []
        snr_averages2 = []
        toa_averages2 = []
        lost_averages2 = []
        received_averages2 = []

        # Extraer distancias y promedios del primer conjunto de datos
        for device in data1:
            distance_str = device['distancia_entre_dispositivo_y_main_gw']
            # Verificar si la distancia es conocida
            if distance_str != 'unknown':
                distance = float(distance_str)
                rssi = device['average_rssi']
                snr = device['average_snr']
                toa = device['average_time_on_air_ms']
                lost = device['lost_frames']
                received = device['received_frames']
                distances.append(distance)
                rssi_averages1.append(rssi)
                snr_averages1.append(snr)
                toa_averages1.append(toa)
                lost_averages1.append(lost)
                received_averages1.append(received)

        # Extraer distancias y promedios del segundo conjunto de datos
        for device in data2:
            distance_str = device['distancia_entre_dispositivo_y_main_gw']
            # Verificar si la distancia es conocida
            if distance_str != 'unknown':
                distance = float(distance_str)
                rssi = device['average_rssi']
                snr = device['average_snr']
                toa = device['average_time_on_air_ms']
                lost = device['lost_frames']
                received = device['received_frames']
                rssi_averages2.append(rssi)
                snr_averages2.append(snr)
                toa_averages2.append(toa)
                lost_averages2.append(lost)
                received_averages2.append(received)

        # Definir los intervalos de distancia
        distance_intervals = list(range(0, int(max(distances)) + 100, 100))

        def process_data_and_generate_comparison_graphs(attribute_averages1, attribute_averages2, distance_intervals, filename_prefix, y_axis_label):
            data_by_distance_interval1 = group_by_interval(distances, attribute_averages1, distance_intervals)
            data_by_distance_interval2 = group_by_interval(distances, attribute_averages2, distance_intervals)
            mean_by_distance_interval1 = calculate_mean_by_interval(data_by_distance_interval1)
            mean_by_distance_interval2 = calculate_mean_by_interval(data_by_distance_interval2)
            cumulative_mean1 = calculate_cumulative_mean(mean_by_distance_interval1, data_by_distance_interval1)
            cumulative_mean2 = calculate_cumulative_mean(mean_by_distance_interval2, data_by_distance_interval2)
            bar_labels1 = [f'Dispositivos: {len(data_by_distance_interval1[interval])}' for interval in mean_by_distance_interval1.keys()]
            bar_labels2 = [f'Dispositivos: {len(data_by_distance_interval2[interval])}' for interval in mean_by_distance_interval2.keys()]

            # Generate and save graphs
            generate_plotly_comparison_graphs(mean_by_distance_interval1, mean_by_distance_interval2, bar_labels1, bar_labels2, cumulative_mean1, cumulative_mean2,
                                            f'Media de {y_axis_label} y Media Acumulada por Intervalo de Distancia',
                                            'Distancia (m)', f'Media de {y_axis_label}', f'{filename_prefix}.html')

        # Generar graficos comparativos
        process_data_and_generate_comparison_graphs(rssi_averages1, rssi_averages2, distance_intervals, 'averageRSSI_x_distanceToMainGateway', 'RSSI (dBm)')
        process_data_and_generate_comparison_graphs(snr_averages1, snr_averages2, distance_intervals, 'averageSNR_x_distanceToMainGateway', 'SNR (dB)')
        process_data_and_generate_comparison_graphs(toa_averages1, toa_averages2, distance_intervals, 'averageTimeOnAir_x_distanceToMainGateway', 'Time on Air (ms)')
        process_data_and_generate_comparison_graphs(lost_averages1, lost_averages2, distance_intervals, 'averageLostFrames_x_distanceToMainGateway', 'Lost Frames (paquetes)')
        process_data_and_generate_comparison_graphs(received_averages1, received_averages2, distance_intervals, 'averageReceivedFrames_x_distanceToMainGateway', 'Received Frames (paquetes)')

        # Group data by distance interval
        received_by_distance_interval1 = group_by_interval(distances, received_averages1, distance_intervals)
        lost_by_distance_interval1 = get_lost_by_interval(received_by_distance_interval1, max(received_averages1))
        received_by_distance_interval2 = group_by_interval(distances, received_averages2, distance_intervals)
        lost_by_distance_interval2 = get_lost_by_interval(received_by_distance_interval2, max(received_averages2))

        # Calculate mean by distance interval
        mean_lost_by_distance_interval1 = calculate_mean_by_interval(lost_by_distance_interval1)
        mean_received_by_distance_interval1 = calculate_mean_by_interval(received_by_distance_interval1)
        mean_lost_by_distance_interval2 = calculate_mean_by_interval(lost_by_distance_interval2)
        mean_received_by_distance_interval2 = calculate_mean_by_interval(received_by_distance_interval2)

        # Calculate cumulative mean
        cumulative_mean_lost1 = calculate_cumulative_mean_percentage(mean_lost_by_distance_interval1, lost_by_distance_interval1, max(received_averages1))
        cumulative_mean_received1 = calculate_cumulative_mean_percentage(mean_received_by_distance_interval1, received_by_distance_interval1, max(received_averages1))
        cumulative_mean_lost2 = calculate_cumulative_mean_percentage(mean_lost_by_distance_interval2, lost_by_distance_interval2, max(received_averages2))
        cumulative_mean_received2 = calculate_cumulative_mean_percentage(mean_received_by_distance_interval2, received_by_distance_interval2, max(received_averages2))

        # Calculate percentage of max
        percentage_of_max_lost1 = calculate_percentage_of_max(lost_by_distance_interval1, max(received_averages1))
        percentage_of_max_received1 = calculate_percentage_of_max(received_by_distance_interval1, max(received_averages1))
        percentage_of_max_lost2 = calculate_percentage_of_max(lost_by_distance_interval2, max(received_averages2))
        percentage_of_max_received2 = calculate_percentage_of_max(received_by_distance_interval2, max(received_averages2))

        # Create bar labels
        bar_labels_lost1 = [f'Dispositivos: {len(lost_by_distance_interval1[interval])}' for interval in mean_lost_by_distance_interval1.keys()]
        bar_labels_received1 = [f'Dispositivos: {len(received_by_distance_interval1[interval])}' for interval in mean_received_by_distance_interval1.keys()]
        bar_labels_lost2 = [f'Dispositivos: {len(lost_by_distance_interval2[interval])}' for interval in mean_lost_by_distance_interval2.keys()]
        bar_labels_received2 = [f'Dispositivos: {len(received_by_distance_interval2[interval])}' for interval in mean_received_by_distance_interval2.keys()]

        # Generate and save graphs
        generate_plotly_bar_and_line_graph_with_threshold_comparison(percentage_of_max_lost1, bar_labels_lost1, cumulative_mean_lost1, percentage_of_max_lost2, bar_labels_lost2, cumulative_mean_lost2, 'Media de Lost Frames y Media Acumulada por Intervalo de Distancia', 'Distancia (m)', 'Media de Lost Frames (%)', 'averageLostFramesPercentage_x_distanceToMainGateway.html', 10)
        generate_plotly_bar_and_line_graph_with_threshold_comparison(percentage_of_max_received1, bar_labels_received1, cumulative_mean_received1, percentage_of_max_received2, bar_labels_received2, cumulative_mean_received2, 'Media de Received Frames y Media Acumulada por Intervalo de Distancia', 'Distancia (m)', 'Media de Received Frames (%)', 'averageReceivedFramesPercentage_x_distanceToMainGateway.html', 90)

    def compare_2_devices_graphics_3(self):
        # Cargar los datos desde el primer archivo JSON
        with open(f'{self.compare_dir_1}/data/devicesCombinedData.json') as dev_json_1:
            data_1 = json.load(dev_json_1)

        # Cargar los datos desde el segundo archivo JSON
        with open(f'{self.compare_dir_2}/data/devicesCombinedData.json') as dev_json_2:
            data_2 = json.load(dev_json_2)

        # Crear diccionario para almacenar los datos agrupados de received_frames para el primer conjunto de datos
        grouped_received_data_1 = {}
        max_sf_received_1 = 0

        # Crear diccionario para almacenar los datos agrupados de lost_frames para el primer conjunto de datos
        grouped_lost_data_1 = {}
        grouped_rssi_data_1 = {}
        grouped_snr_data_1 = {}

        # Agrupar los datos del primer conjunto según el campo "last_SF_used"
        for entry in data_1:
            sf_used = entry['last_SF_used']
            received_frames = entry['received_frames']
            lost_frames = entry['lost_frames']
            rssi = entry['average_rssi']
            snr = entry['average_snr']

            # Para received_frames
            if received_frames > max_sf_received_1:
                max_sf_received_1 = received_frames

            if sf_used not in grouped_received_data_1:
                grouped_received_data_1[sf_used] = {'received_frames_list': [], 'device_count': 0}

            grouped_received_data_1[sf_used]['received_frames_list'].append(received_frames)
            grouped_received_data_1[sf_used]['device_count'] += 1

            # Para lost_frames
            if sf_used not in grouped_lost_data_1:
                grouped_lost_data_1[sf_used] = {'lost_frames_list': [], 'device_count': 0}

            grouped_lost_data_1[sf_used]['lost_frames_list'].append(lost_frames)
            grouped_lost_data_1[sf_used]['device_count'] += 1

            # Para average_rssi
            if sf_used not in grouped_rssi_data_1:
                grouped_rssi_data_1[sf_used] = {'rssi_list': [], 'device_count': 0}
                
            grouped_rssi_data_1[sf_used]['rssi_list'].append(rssi)
            grouped_rssi_data_1[sf_used]['device_count'] += 1

            # Para average_snr
            if sf_used not in grouped_snr_data_1:
                grouped_snr_data_1[sf_used] = {'snr_list': [], 'device_count': 0}
                
            grouped_snr_data_1[sf_used]['snr_list'].append(snr)
            grouped_snr_data_1[sf_used]['device_count'] += 1


        # Crear diccionario para almacenar los datos agrupados de received_frames para el segundo conjunto de datos
        grouped_received_data_2 = {}
        max_sf_received_2 = 0

        # Crear diccionario para almacenar los datos agrupados de lost_frames para el segundo conjunto de datos
        grouped_lost_data_2 = {}
        grouped_rssi_data_2 = {}
        grouped_snr_data_2 = {}

        # Agrupar los datos del segundo conjunto según el campo "last_SF_used"
        for entry in data_2:
            sf_used = entry['last_SF_used']
            received_frames = entry['received_frames']
            lost_frames = entry['lost_frames']
            rssi = entry['average_rssi']
            snr = entry['average_snr']

            # Para received_frames
            if received_frames > max_sf_received_2:
                max_sf_received_2 = received_frames

            if sf_used not in grouped_received_data_2:
                grouped_received_data_2[sf_used] = {'received_frames_list': [], 'device_count': 0}

            grouped_received_data_2[sf_used]['received_frames_list'].append(received_frames)
            grouped_received_data_2[sf_used]['device_count'] += 1

            # Para lost_frames
            if sf_used not in grouped_lost_data_2:
                grouped_lost_data_2[sf_used] = {'lost_frames_list': [], 'device_count': 0}

            grouped_lost_data_2[sf_used]['lost_frames_list'].append(lost_frames)
            grouped_lost_data_2[sf_used]['device_count'] += 1

            # Para average_rssi
            if sf_used not in grouped_rssi_data_2:
                grouped_rssi_data_2[sf_used] = {'rssi_list': [], 'device_count': 0}
                
            grouped_rssi_data_2[sf_used]['rssi_list'].append(rssi)
            grouped_rssi_data_2[sf_used]['device_count'] += 1

            # Para average_snr
            if sf_used not in grouped_snr_data_2:
                grouped_snr_data_2[sf_used] = {'snr_list': [], 'device_count': 0}
                
            grouped_snr_data_2[sf_used]['snr_list'].append(snr)
            grouped_snr_data_2[sf_used]['device_count'] += 1

        # Calcular la media de "received_frames" y "lost_frames" y contar el número de dispositivos para cada grupo para el primer conjunto de datos
        sf_received_info_1 = {}
        for sf_used, data in grouped_received_data_1.items():
            mean_received_frames = sum(data['received_frames_list']) / len(data['received_frames_list'])
            sf_received_info_1[sf_used] = {'mean_received_frames_percentage': mean_received_frames / max_sf_received_1 * 100, 'device_count': data['device_count']}

        sf_lost_info_1 = {}
        for sf_used, data in grouped_lost_data_1.items():
            mean_lost_frames = sum(data['lost_frames_list']) / len(data['lost_frames_list'])
            sf_lost_info_1[sf_used] = {'mean_lost_frames_percentage': mean_lost_frames / max_sf_received_1 * 100, 'device_count': data['device_count']}

        sf_rssi_info_1 = {}
        for sf_used, data in grouped_rssi_data_1.items():
            mean_rssi = sum(data['rssi_list']) / len(data['rssi_list'])
            sf_rssi_info_1[sf_used] = {'mean_rssi': mean_rssi, 'device_count': data['device_count']}

        sf_snr_info_1 = {}
        for sf_used, data in grouped_snr_data_1.items():
            mean_snr = sum(data['snr_list']) / len(data['snr_list'])
            sf_snr_info_1[sf_used] = {'mean_snr': mean_snr, 'device_count': data['device_count']}

        # Calcular la media de "received_frames" y "lost_frames" y contar el número de dispositivos para cada grupo para el segundo conjunto de datos
        sf_received_info_2 = {}
        for sf_used, data in grouped_received_data_2.items():
            mean_received_frames = sum(data['received_frames_list']) / len(data['received_frames_list'])
            sf_received_info_2[sf_used] = {'mean_received_frames_percentage': mean_received_frames / max_sf_received_2 * 100, 'device_count': data['device_count']}

        sf_lost_info_2 = {}
        for sf_used, data in grouped_lost_data_2.items():
            mean_lost_frames = sum(data['lost_frames_list']) / len(data['lost_frames_list'])
            sf_lost_info_2[sf_used] = {'mean_lost_frames_percentage': mean_lost_frames / max_sf_received_2 * 100, 'device_count': data['device_count']}

        sf_rssi_info_2 = {}
        for sf_used, data in grouped_rssi_data_2.items():
            mean_rssi = sum(data['rssi_list']) / len(data['rssi_list'])
            sf_rssi_info_2[sf_used] = {'mean_rssi': mean_rssi, 'device_count': data['device_count']}

        sf_snr_info_2 = {}
        for sf_used, data in grouped_snr_data_2.items():
            mean_snr = sum(data['snr_list']) / len(data['snr_list'])
            sf_snr_info_2[sf_used] = {'mean_snr': mean_snr, 'device_count': data['device_count']}

        # Ordenar las claves de SF7 a SF12
        sorted_sf_received_info_1 = {sf: sf_received_info_1.get(sf, {'mean_received_frames_percentage': 0, 'device_count': 0}) for sf in ['SF7', 'SF8', 'SF9', 'SF10', 'SF11', 'SF12']}
        sorted_sf_lost_info_1 = {sf: sf_lost_info_1.get(sf, {'mean_lost_frames_percentage': 0, 'device_count': 0}) for sf in ['SF7', 'SF8', 'SF9', 'SF10', 'SF11', 'SF12']}
        sorted_sf_rssi_info_1 = {sf: sf_rssi_info_1.get(sf, {'mean_rssi': 0, 'device_count': 0}) for sf in ['SF7', 'SF8', 'SF9', 'SF10', 'SF11', 'SF12']}
        sorted_sf_snr_info_1 = {sf: sf_snr_info_1.get(sf, {'mean_snr': 0, 'device_count': 0}) for sf in ['SF7', 'SF8', 'SF9', 'SF10', 'SF11', 'SF12']}

        sorted_sf_received_info_2 = {sf: sf_received_info_2.get(sf, {'mean_received_frames_percentage': 0, 'device_count': 0}) for sf in ['SF7', 'SF8', 'SF9', 'SF10', 'SF11', 'SF12']}
        sorted_sf_lost_info_2 = {sf: sf_lost_info_2.get(sf, {'mean_lost_frames_percentage': 0, 'device_count': 0}) for sf in ['SF7', 'SF8', 'SF9', 'SF10', 'SF11', 'SF12']}
        sorted_sf_rssi_info_2 = {sf: sf_rssi_info_2.get(sf, {'mean_rssi': 0, 'device_count': 0}) for sf in ['SF7', 'SF8', 'SF9', 'SF10', 'SF11', 'SF12']}
        sorted_sf_snr_info_2 = {sf: sf_snr_info_2.get(sf, {'mean_snr': 0, 'device_count': 0}) for sf in ['SF7', 'SF8', 'SF9', 'SF10', 'SF11', 'SF12']}

        # Crear gráfico de barras interactivo para received_frames comparando los dos conjuntos de datos
        bar_trace_received_1 = go.Bar(
            x=[sf for sf in sorted_sf_received_info_1.keys()],
            y=[info['mean_received_frames_percentage'] for info in sorted_sf_received_info_1.values()],
            text=[f'Dispositivos: {info["device_count"]}' for info in sorted_sf_received_info_1.values()],
            textposition='auto',
            name="data_1",
            marker=dict(color='blue')
        )

        bar_trace_received_2 = go.Bar(
            x=[sf for sf in sorted_sf_received_info_2.keys()],
            y=[info['mean_received_frames_percentage'] for info in sorted_sf_received_info_2.values()],
            text=[f'Dispositivos: {info["device_count"]}' for info in sorted_sf_received_info_2.values()],
            textposition='auto',
            name="data_2",
            marker=dict(color='red')
        )

        layout_received = go.Layout(
            title="Media de Received Frames (%) por Last SF used",
            xaxis=dict(title="Last SF used"),
            yaxis=dict(title="Average Received Frames (%)")
        )

        fig_received = go.Figure(data=[bar_trace_received_1, bar_trace_received_2], layout=layout_received)

        # Write received_frames comparison to HTML file
        fig_received.write_html(f'{self.output_dir}/lastSFused/averageReceivedFramesComparison_x_lastSFUsed.html')

        # Crear gráfico de barras interactivo para lost_frames comparando los dos conjuntos de datos
        bar_trace_lost_1 = go.Bar(
            x=[sf for sf in sorted_sf_lost_info_1.keys()],
            y=[info['mean_lost_frames_percentage'] for info in sorted_sf_lost_info_1.values()],
            text=[f'Dispositivos: {info["device_count"]}' for info in sorted_sf_lost_info_1.values()],
            textposition='auto',
            name="data_1",
            marker=dict(color='blue')
        )

        bar_trace_lost_2 = go.Bar(
            x=[sf for sf in sorted_sf_lost_info_2.keys()],
            y=[info['mean_lost_frames_percentage'] for info in sorted_sf_lost_info_2.values()],
            text=[f'Dispositivos: {info["device_count"]}' for info in sorted_sf_lost_info_2.values()],
            textposition='auto',
            name="data_2",
            marker=dict(color='red')
        )

        layout_lost = go.Layout(
            title="Media de Lost Frames (%) por Last SF used",
            xaxis=dict(title="Last SF used"),
            yaxis=dict(title="Average Lost Frames (%)")
        )

        fig_lost = go.Figure(data=[bar_trace_lost_1, bar_trace_lost_2], layout=layout_lost)

        # Write lost_frames comparison to HTML file
        fig_lost.write_html(f'{self.output_dir}/lastSFused/averageLostFramesComparison_x_lastSFUsed.html')

        # Crear gráficos de barras interactivos para average_rssi
        bar_trace_rssi_1 = go.Bar(
            x=[sf for sf in sorted_sf_rssi_info_1.keys()],
            y=[info['mean_rssi'] for info in sorted_sf_rssi_info_1.values()],
            text=[f'Dispositivos: {info["device_count"]}' for info in sorted_sf_rssi_info_1.values()],
            textposition='auto',
            name="data_1",
            marker=dict(color='blue')
        )

        bar_trace_rssi_2 = go.Bar(
            x=[sf for sf in sorted_sf_rssi_info_2.keys()],
            y=[info['mean_rssi'] for info in sorted_sf_rssi_info_2.values()],
            text=[f'Dispositivos: {info["device_count"]}' for info in sorted_sf_rssi_info_2.values()],
            textposition='auto',
            name="data_2",
            marker=dict(color='red')
        )

        layout_rssi = go.Layout(
            title="Media de RSSI por Last SF used",
            xaxis=dict(title="Last SF used"),
            yaxis=dict(title="Average RSSI")
        )

        fig_rssi = go.Figure(data=[bar_trace_rssi_1, bar_trace_rssi_2], layout=layout_rssi)

        # Write average_rssi to HTML file
        fig_rssi.write_html(f'{self.output_dir}/lastSFused/averageRSSI_x_lastSFUsed.html')

        # Crear gráficos de barras interactivos para average_snr
        bar_trace_snr_1 = go.Bar(
            x=[sf for sf in sorted_sf_snr_info_1.keys()],
            y=[info['mean_snr'] for info in sorted_sf_snr_info_1.values()],
            text=[f'Dispositivos: {info["device_count"]}' for info in sorted_sf_snr_info_1.values()],
            textposition='auto',
            name="data_1",
            marker=dict(color='blue')
        )

        bar_trace_snr_2 = go.Bar(
            x=[sf for sf in sorted_sf_snr_info_2.keys()],
            y=[info['mean_snr'] for info in sorted_sf_snr_info_2.values()],
            text=[f'Dispositivos: {info["device_count"]}' for info in sorted_sf_snr_info_2.values()],
            textposition='auto',
            name="data_2",
            marker=dict(color='red')
        )

        layout_snr = go.Layout(
            title="Media de SNR por Last SF used",
            xaxis=dict(title="Last SF used"),
            yaxis=dict(title="Average SNR")
        )

        fig_snr = go.Figure(data=[bar_trace_snr_1, bar_trace_snr_2], layout=layout_snr)

        # Write average_snr to HTML file
        fig_snr.write_html(f'{self.output_dir}/lastSFused/averageSNR_x_lastSFUsed.html')

    ### GRAPHICS (COMPARISON OF 3) ###
    
    def create_comparison_directory_hierarchy_3(self, compare_dir_1, compare_dir_2, compare_dir_3):
        self.compare_dir_1 = compare_dir_1
        self.compare_dir_2 = compare_dir_2
        self.compare_dir_3 = compare_dir_3

        father_dir_1 = os.path.dirname(self.compare_dir_1)
        folder_dir_1 = os.path.basename(self.compare_dir_1)
        dates_dir_1 = folder_dir_1.split('_')
        from_dir_1 = dates_dir_1[0][4:8]  # Tomar los 2 siguientes caracteres después de "From"
        to_dir_1 = dates_dir_1[1][2:6]  # Tomar los 2 siguientes caracteres después de "To"

        folder_dir_2 = os.path.basename(self.compare_dir_2)
        dates_dir_2 = folder_dir_2.split('_')
        from_dir_2 = dates_dir_2[0][4:8]  # Tomar los 2 siguientes caracteres después de "From"
        to_dir_2 = dates_dir_2[1][2:6]  # Tomar los 2 siguientes caracteres después de "To"

        folder_dir_3 = os.path.basename(self.compare_dir_3)
        dates_dir_3 = folder_dir_3.split('_')
        from_dir_3 = dates_dir_3[0][4:8]  # Tomar los 2 siguientes caracteres después de "From"
        to_dir_3 = dates_dir_3[1][2:6]  # Tomar los 2 siguientes caracteres después de "To"

        self.output_dir = os.path.join(father_dir_1, f"Compare_{from_dir_1}{to_dir_1}_to_{from_dir_2}{to_dir_2}_to_{from_dir_3}{to_dir_3}")
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(f"{self.output_dir}/distancesToMainGateways", exist_ok=True)
        os.makedirs(f"{self.output_dir}/distributions", exist_ok=True)
        os.makedirs(f"{self.output_dir}/gateways", exist_ok=True)
        os.makedirs(f"{self.output_dir}/lastSFused", exist_ok=True)

    def compare_graphics_3(self, update_compare_graphics_progress_bar):
        #self.compare_dir_1 = compare_dir_1
        #self.compare_dir_2 = compare_dir_2
        #self.compare_dir_3 = compare_dir_3
        #self.output_dir = "D:/Clase/Master/2 MAILA/TFM/LoRa Analisis/galdakao/output"

        self.compare_3_gateways_graphics()
        update_compare_graphics_progress_bar(1)
        self.compare_3_devices_graphics_1()
        update_compare_graphics_progress_bar(2)
        self.compare_3_devices_graphics_2()
        update_compare_graphics_progress_bar(3)
        self.compare_3_devices_graphics_3()
        update_compare_graphics_progress_bar(4)

    def compare_3_gateways_graphics(self):
        def generar_grafico(data1, data2, data3, x_variable, y_variable, titulo, nombre_archivo, titulo_y, titulo_x):
            data1_sorted = sorted(data1, key=lambda x: x[y_variable], reverse=True)  # Ordenar por variable Y
            data2_sorted = sorted(data2, key=lambda x: x[y_variable], reverse=True)  # Ordenar por variable Y
            data3_sorted = sorted(data3, key=lambda x: x[y_variable], reverse=True)  # Ordenar por variable Y

            data1_plot = go.Bar(x=[d[x_variable] for d in data1_sorted], y=[d[y_variable] for d in data1_sorted],
                            hovertext=[f'{y_variable}: {d[y_variable]}, name: {d["name"]}' for d in data1_sorted],
                            name='Data 1', marker=dict(color='blue'))

            data2_plot = go.Bar(x=[d[x_variable] for d in data2_sorted], y=[d[y_variable] for d in data2_sorted],
                            hovertext=[f'{y_variable}: {d[y_variable]}, name: {d["name"]}' for d in data2_sorted],
                            name='Data 2', marker=dict(color='red'))
            
            data3_plot = go.Bar(x=[d[x_variable] for d in data3_sorted], y=[d[y_variable] for d in data3_sorted],
                            hovertext=[f'{y_variable}: {d[y_variable]}, name: {d["name"]}' for d in data3_sorted],
                            name='Data 3', marker=dict(color='green'))

            layout_plot = go.Layout(title=titulo, xaxis=dict(title=titulo_x), yaxis=dict(title=titulo_y), bargap=0.1)
            fig_plot = go.Figure(data=[data1_plot, data2_plot, data3_plot], layout=layout_plot)
            fig_plot.write_html(f'{self.output_dir}/gateways/{nombre_archivo}')

        with open(f'{self.compare_dir_1}/data/gatewaysCombinedData.json') as gw_json:
            data1 = json.load(gw_json)

        with open(f'{self.compare_dir_2}/data/gatewaysCombinedData.json') as gw_json:
            data2 = json.load(gw_json)

        with open(f'{self.compare_dir_3}/data/gatewaysCombinedData.json') as gw_json:
            data3 = json.load(gw_json)

        # Convertir "UL_Frame_Cnt" de cadena de texto a número
        for gateway in data1:
            gateway["UL_Frame_Cnt"] = float(gateway["UL_Frame_Cnt"])

        for gateway in data2:
            gateway["UL_Frame_Cnt"] = float(gateway["UL_Frame_Cnt"])

        for gateway in data3:
            gateway["UL_Frame_Cnt"] = float(gateway["UL_Frame_Cnt"])

        # Generar y guardar los gráficos
        generar_grafico(data1, data2, data3, 'Gateway_ID', 'UL_Frame_Cnt', 'Número de frames de Uplink por gateway', 'uplinkFrameCounter_x_gateways.html', 'Uplink Frame Counter', 'Gateway ID')
        generar_grafico(data1, data2, data3, 'Gateway_ID', 'Lost_Frame_Cnt', 'Número de frames perdidos por gateway', 'lostFrameCounter_x_gateways.html', 'Lost Frame Counter', 'Gateway ID')
        # generar_grafico(data1, data2, 'Gateway_ID', 'FER_[%]', 'Porcentaje de FER (Frame Error Rate) por gateway', 'FER[%]_x_gateways.html', 'FER (%)', 'Gateway ID')
        generar_grafico(data1, data2, data3, 'Gateway_ID', 'Avr_RSSI_[dBm]', 'Media de RSSI (dBm) por gateway', 'averageRSSI_x_gateways.html', 'Average RSSI (dBm)', 'Gateway ID')
        generar_grafico(data1, data2, data3, 'Gateway_ID', 'Avr_SNR_[dB]', 'Media de SNR (dB) por gateway', 'averageSNR_x_gateways.html', 'Average SNR (dB)', 'Gateway ID')

    def compare_3_devices_graphics_1(self):
        # Función para agrupar los valores en números enteros o de 10 en 10
        def agrupar_valores(datos, nombre_variable):
            valores = [dato[nombre_variable] for dato in datos]
            min_valor = min(valores)
            max_valor = max(valores)
            agrupados = {}
            
            if nombre_variable == "average_time_on_air_ms":  # Para "time on air"
                for valor in range(0, int(max_valor) + 1, 10):
                    agrupados[valor] = sum(1 for v in valores if int(v) // 10 == valor // 10)
            elif nombre_variable == "average_gws_reached":  # Para "average_gws_reached"
                for valor in valores:
                    grupo = round(valor * 10) / 10  # Redondea al décimo más cercano
                    agrupados[grupo] = agrupados.get(grupo, 0) + 1
            else:
                for valor in range(int(min_valor), int(max_valor) + 1):
                    agrupados[valor] = sum(1 for v in valores if int(v) == valor)
            return agrupados

        def generar_grafico(datos_1, datos_2, datos_3, atributo, nombre_archivo, x_titulo):
            datos_agrupados_1 = agrupar_valores(datos_1, atributo)
            datos_agrupados_2 = agrupar_valores(datos_2, atributo)
            datos_agrupados_3 = agrupar_valores(datos_3, atributo)
            
            data_1 = go.Bar(x=[x - 0.2 for x in datos_agrupados_1.keys()], y=list(datos_agrupados_1.values()), name='Datos 1', marker=dict(color='blue'))
            data_2 = go.Bar(x=[x + 0.2 for x in datos_agrupados_2.keys()], y=list(datos_agrupados_2.values()), name='Datos 2', marker=dict(color='red'))
            data_3 = go.Bar(x=[x + 0.2 for x in datos_agrupados_3.keys()], y=list(datos_agrupados_3.values()), name='Datos 3', marker=dict(color='green'))
            data = [data_1, data_2, data_3]
            
            layout = go.Layout(title=f'Distribución de {x_titulo}', xaxis=dict(title=x_titulo), yaxis=dict(title='Número de ocurrencias'), bargap=0.1)
            fig = go.Figure(data=data, layout=layout)
            fig.write_html(f'{self.output_dir}/distributions/{nombre_archivo}')
             
        def contar_ocurrencias(datos, nombre_variable, valores_incluidos):
            ocurrencias = {}
            for dato in datos:
                valor = dato[nombre_variable]
                if valor in valores_incluidos:
                    if valor in ocurrencias:
                        ocurrencias[valor] += 1
                    else:
                        ocurrencias[valor] = 1
                else:
                    if "others" in ocurrencias:
                        ocurrencias["others"] += 1
                    else:
                        ocurrencias["others"] = 1
            return ocurrencias
        
        def generar_grafico_SF(datos1, datos2, datos3, titulo):
            keys_ordenadas = sorted(set(datos1.keys()) | set(datos2.keys()) | set(datos3.keys()), key=lambda x: int(x[2:]))
            data1 = go.Bar(x=keys_ordenadas, y=[datos1.get(key, 0) for key in keys_ordenadas], name='Archivo 1', marker=dict(color='blue'))
            data2 = go.Bar(x=keys_ordenadas, y=[datos2.get(key, 0) for key in keys_ordenadas], name='Archivo 2', marker=dict(color='red'))
            data3 = go.Bar(x=keys_ordenadas, y=[datos3.get(key, 0) for key in keys_ordenadas], name='Archivo 3', marker=dict(color='green'))
            layout = go.Layout(title=titulo, xaxis=dict(title='Last SF used'), yaxis=dict(title='Número de ocurrencias'), bargap=0.1)
            return go.Figure(data=[data1, data2, data3], layout=layout)

        def generar_grafico_GW(datos1, datos2, datos3, titulo):
            keys_ordenadas = sorted(set(datos1.keys()) | set(datos2.keys()) | set(datos3.keys()))
            data1 = go.Bar(x=list(datos1.keys()), y=list(datos1.values()), hovertext=[gateways_names[id] if id in gateways_names else id for id in datos1.keys()], name='Archivo 1', marker=dict(color='blue'))
            data2 = go.Bar(x=list(datos2.keys()), y=list(datos2.values()), hovertext=[gateways_names[id] if id in gateways_names else id for id in datos2.keys()], name='Archivo 2', marker=dict(color='red'))
            data3 = go.Bar(x=list(datos3.keys()), y=list(datos3.values()), hovertext=[gateways_names[id] if id in gateways_names else id for id in datos3.keys()], name='Archivo 3', marker=dict(color='green'))
            layout = go.Layout(title=titulo, xaxis=dict(title='Main gateways'), yaxis=dict(title='Número de ocurrencias'), bargap=0.1)
            return go.Figure(data=[data1, data2, data3], layout=layout)
        
        with open(f'{self.compare_dir_1}/data/devicesCombinedData.json') as dev_json:
            datos_1 = json.load(dev_json)

        with open(f'{self.compare_dir_2}/data/devicesCombinedData.json') as dev_json:
            datos_2 = json.load(dev_json)

        with open(f'{self.compare_dir_3}/data/devicesCombinedData.json') as dev_json:
            datos_3 = json.load(dev_json)

        generar_grafico(datos_1, datos_2, datos_3, "average_rssi", 'RSSI_distribution.html', 'Average RSSI')
        generar_grafico(datos_1, datos_2, datos_3, "average_snr", 'SNR_distribution.html', 'Average SNR')
        generar_grafico(datos_1, datos_2, datos_3, "average_time_on_air_ms", 'timeOnAir_distribution.html', 'Average Time on Air')
        generar_grafico(datos_1, datos_2, datos_3, "lost_frames", 'lostFrames_distribution.html', 'Lost Frames')
        generar_grafico(datos_1, datos_2, datos_3, "received_frames", 'receivedFrames_distribution.html', 'Received Frames')
        generar_grafico(datos_1, datos_2, datos_3, "average_gws_reached", 'averageGatewaysReached_distribution.html', 'Average Gateways reached')

        # Contar ocurrencias para cada conjunto de datos
        ocurrencias1 = contar_ocurrencias(datos_1, "last_SF_used", set(dato["last_SF_used"] for dato in datos_1))
        ocurrencias2 = contar_ocurrencias(datos_2, "last_SF_used", set(dato["last_SF_used"] for dato in datos_2))
        ocurrencias3 = contar_ocurrencias(datos_3, "last_SF_used", set(dato["last_SF_used"] for dato in datos_3))

        # Generar el gráfico combinado
        figura_combinada = generar_grafico_SF(ocurrencias1, ocurrencias2, ocurrencias3, 'Comparación de last Spreading factor (SF) used')

        # Generar el archivo HTML del gráfico combinado
        figura_combinada.write_html(f'{self.output_dir}/distributions/lastSFUsed_distribution.html')

        with open(f'{self.compare_dir_1}/data/gatewaysCombinedData.json') as gw_json:
            datos_gateways1 = json.load(gw_json)

        with open(f'{self.compare_dir_2}/data/gatewaysCombinedData.json') as gw_json:
            datos_gateways2 = json.load(gw_json)

        with open(f'{self.compare_dir_3}/data/gatewaysCombinedData.json') as gw_json:
            datos_gateways3 = json.load(gw_json)

        # Obtener datos de main_gw de gateways específicos y ordenarlos
        gateways_ids1 = [gateway["Gateway_ID"] for gateway in datos_gateways1]
        gateways_names = {gateway["Gateway_ID"]: gateway["name"] for gateway in datos_gateways1}
        ocurrencias_main_gw1 = contar_ocurrencias(datos_1, "main_gw", gateways_ids1)
        ocurrencias_main_gw_sorted1 = dict(sorted(ocurrencias_main_gw1.items(), key=lambda x: x[1], reverse=True))
        ocurrencias_main_gw_sorted1["others"] = ocurrencias_main_gw_sorted1.pop("others", 0)

        gateways_ids2 = [gateway["Gateway_ID"] for gateway in datos_gateways2]
        gateways_names = {gateway["Gateway_ID"]: gateway["name"] for gateway in datos_gateways2}
        ocurrencias_main_gw2 = contar_ocurrencias(datos_2, "main_gw", gateways_ids2)
        ocurrencias_main_gw_sorted2 = dict(sorted(ocurrencias_main_gw2.items(), key=lambda x: x[1], reverse=True))
        ocurrencias_main_gw_sorted2["others"] = ocurrencias_main_gw_sorted2.pop("others", 0)

        gateways_ids3 = [gateway["Gateway_ID"] for gateway in datos_gateways3]
        gateways_names = {gateway["Gateway_ID"]: gateway["name"] for gateway in datos_gateways3}
        ocurrencias_main_gw3 = contar_ocurrencias(datos_3, "main_gw", gateways_ids3)
        ocurrencias_main_gw_sorted3 = dict(sorted(ocurrencias_main_gw3.items(), key=lambda x: x[1], reverse=True))
        ocurrencias_main_gw_sorted3["others"] = ocurrencias_main_gw_sorted3.pop("others", 0)

        # Generar y guardar el gráfico combinado para main_gw
        figura_main_gw = generar_grafico_GW(ocurrencias_main_gw_sorted1, ocurrencias_main_gw_sorted2, ocurrencias_main_gw_sorted3, 'Comparación de Main Gateways')
        figura_main_gw.write_html(f'{self.output_dir}/distributions/mainGateways_comparison.html')

    def compare_3_devices_graphics_2(self):
        def group_by_interval(distances, values, distance_intervals):
            data_by_distance_interval = {interval: [] for interval in distance_intervals}
            for distance, value in zip(distances, values):
                interval = next(interval for interval in distance_intervals if interval >= distance)
                data_by_distance_interval[interval].append(value)
            return data_by_distance_interval
        
        def get_lost_by_interval(received, max):
            lost_by_distance_interval = {}
            for distance, values in received.items():
                if values:
                    lost_values = [max - value for value in values]
                    lost_by_distance_interval[distance] = lost_values
                else:
                    lost_by_distance_interval[distance] = []
            return lost_by_distance_interval
        
        def calculate_mean_by_interval(data_by_distance_interval):
            mean_by_distance_interval = {}
            for interval, values in data_by_distance_interval.items():
                if len(values) > 1:
                    mean_by_distance_interval[interval] = np.mean(values)
            return mean_by_distance_interval
        
        def calculate_cumulative_mean(mean_by_distance_interval, data_by_distance_interval):
            cumulative_mean = []
            cumulative_mean_value = 0
            total_count = 0
            for interval, values in data_by_distance_interval.items():
                if interval in mean_by_distance_interval:
                    mean_value = mean_by_distance_interval[interval]
                    count = len(values)
                    cumulative_mean_value += mean_value * count
                    total_count += count
                cumulative_mean.append(cumulative_mean_value / total_count if total_count > 0 else np.nan)
            cumulative_mean.pop(0)  # Remove first element which is NaN
            return cumulative_mean
        
        def calculate_cumulative_mean_percentage(mean_by_distance_interval, data_by_distance_interval, max_received_frames):
            cumulative_mean_percentage = []
            cumulative_mean_value = 0
            total_count = 0
            for interval, values in data_by_distance_interval.items():
                if interval in mean_by_distance_interval:
                    mean_value = mean_by_distance_interval[interval]
                    count = len(values)
                    cumulative_mean_value += mean_value * count
                    total_count += count
                    cumulative_mean_percentage.append((cumulative_mean_value / total_count) / max_received_frames * 100)
            return cumulative_mean_percentage
        
        def calculate_percentage_of_max(received_by_distance_interval, max_received_frames):
            percentage_of_max = {}
            for interval, values in received_by_distance_interval.items():
                if len(values) > 1:
                    mean_value = np.mean(values)
                    percentage_of_max[interval] = (mean_value / max_received_frames) * 100
            return percentage_of_max

        def generate_plotly_comparison_graphs(data_dict1, data_dict2, data_dict3, bar_labels1, bar_labels2, bar_labels3, cumulative_values1, cumulative_values2, cumulative_values3, title, x_axis_title, y_axis_title, file_name):
            fig = go.Figure()

            # Add bar charts for data1, data2 and data3
            fig.add_trace(go.Bar(
                x=list(data_dict1.keys()),
                y=list(data_dict1.values()),
                text=bar_labels1,
                name='Media por Intervalo (Data 1)',
                marker=dict(color='blue')
            ))

            fig.add_trace(go.Bar(
                x=list(data_dict2.keys()),
                y=list(data_dict2.values()),
                text=bar_labels2,
                name='Media por Intervalo (Data 2)',
                marker=dict(color='red')
            ))

            fig.add_trace(go.Bar(
                x=list(data_dict3.keys()),
                y=list(data_dict3.values()),
                text=bar_labels3,
                name='Media por Intervalo (Data 3)',
                marker=dict(color='green')
            ))

            # Add cumulative lines for data1 and data2
            fig.add_trace(go.Scatter(
                x=list(data_dict1.keys()),
                y=cumulative_values1,
                mode='lines',
                name='Media Acumulada (Data 1)',
                line=dict(color='blue', width=2)
            ))

            fig.add_trace(go.Scatter(
                x=list(data_dict2.keys()),
                y=cumulative_values2,
                mode='lines',
                name='Media Acumulada (Data 2)',
                line=dict(color='red', width=2)
            ))

            fig.add_trace(go.Scatter(
                x=list(data_dict3.keys()),
                y=cumulative_values3,
                mode='lines',
                name='Media Acumulada (Data 3)',
                line=dict(color='green', width=2)
            ))

            # Configure layout
            fig.update_layout(
                title=title,
                xaxis_title=x_axis_title,
                yaxis_title=y_axis_title,
                xaxis=dict(
                    tickmode='linear',
                    dtick=100
                )
            )

            # Write to HTML file
            fig.write_html(f'{self.output_dir}/distancesToMainGateways/{file_name}')

        def generate_plotly_bar_and_line_graph_with_threshold_comparison(data_dict1, bar_labels1, cumulative_values1, data_dict2, bar_labels2, cumulative_values2, data_dict3, bar_labels3, cumulative_values3, title, x_axis_title, y_axis_title, file_name, y_threshold):
            fig = go.Figure()

            # Add bar chart
            fig.add_trace(go.Bar(
                x=list(data_dict1.keys()),
                y=list(data_dict1.values()),
                text=bar_labels1,
                name='Media por Intervalo (Data 1)',
                marker=dict(color='blue')
            ))

            # Add cumulative line
            fig.add_trace(go.Scatter(
                x=list(data_dict1.keys()),
                y=cumulative_values1,
                mode='lines',
                name='Media Acumulada (Data 1)',
                line=dict(color='blue', width=2)
            ))

            # Add bar chart
            fig.add_trace(go.Bar(
                x=list(data_dict2.keys()),
                y=list(data_dict2.values()),
                text=bar_labels2,
                name='Media por Intervalo (Data 2)',
                marker=dict(color='red')
            ))

            # Add cumulative line
            fig.add_trace(go.Scatter(
                x=list(data_dict2.keys()),
                y=cumulative_values2,
                mode='lines',
                name='Media Acumulada (Data 2)',
                line=dict(color='red', width=2)
            ))

            # Add bar chart
            fig.add_trace(go.Bar(
                x=list(data_dict3.keys()),
                y=list(data_dict3.values()),
                text=bar_labels3,
                name='Media por Intervalo (Data 3)',
                marker=dict(color='green')
            ))

            # Add cumulative line
            fig.add_trace(go.Scatter(
                x=list(data_dict3.keys()),
                y=cumulative_values3,
                mode='lines',
                name='Media Acumulada (Data 3)',
                line=dict(color='green', width=2)
            ))

            # Add horizontal line at y = y_threshold
            fig.add_shape(type="line",
                x0=min(data_dict1.keys()), y0=y_threshold,
                x1=max(data_dict1.keys()), y1=y_threshold,
                line=dict(color="purple", width=2, dash="dash"),
            )

            # Configure layout
            fig.update_layout(
                title=title,
                xaxis_title=x_axis_title,
                yaxis_title=y_axis_title,
                xaxis=dict(
                    tickmode='linear',
                    dtick=100
                )
            )

            # Write to HTML file
            fig.write_html(f'{self.output_dir}/distancesToMainGateways/{file_name}')

        # Cargar los datos desde el archivo JSON
        with open(f'{self.compare_dir_1}/data/devicesCombinedData.json') as dev_json:
            data1 = json.load(dev_json)

        with open(f'{self.compare_dir_2}/data/devicesCombinedData.json') as dev_json:
            data2 = json.load(dev_json)

        with open(f'{self.compare_dir_3}/data/devicesCombinedData.json') as dev_json:
            data3 = json.load(dev_json)

        # Crear listas para almacenar las distancias y los promedios de ambos conjuntos de datos
        distances = []
        rssi_averages1 = []
        snr_averages1 = []
        toa_averages1 = []
        lost_averages1 = []
        received_averages1 = []

        rssi_averages2 = []
        snr_averages2 = []
        toa_averages2 = []
        lost_averages2 = []
        received_averages2 = []

        rssi_averages3 = []
        snr_averages3 = []
        toa_averages3 = []
        lost_averages3 = []
        received_averages3 = []

        # Extraer distancias y promedios del primer conjunto de datos
        for device in data1:
            distance_str = device['distancia_entre_dispositivo_y_main_gw']
            # Verificar si la distancia es conocida
            if distance_str != 'unknown':
                distance = float(distance_str)
                rssi = device['average_rssi']
                snr = device['average_snr']
                toa = device['average_time_on_air_ms']
                lost = device['lost_frames']
                received = device['received_frames']
                distances.append(distance)
                rssi_averages1.append(rssi)
                snr_averages1.append(snr)
                toa_averages1.append(toa)
                lost_averages1.append(lost)
                received_averages1.append(received)

        # Extraer distancias y promedios del segundo conjunto de datos
        for device in data2:
            distance_str = device['distancia_entre_dispositivo_y_main_gw']
            # Verificar si la distancia es conocida
            if distance_str != 'unknown':
                distance = float(distance_str)
                rssi = device['average_rssi']
                snr = device['average_snr']
                toa = device['average_time_on_air_ms']
                lost = device['lost_frames']
                received = device['received_frames']
                rssi_averages2.append(rssi)
                snr_averages2.append(snr)
                toa_averages2.append(toa)
                lost_averages2.append(lost)
                received_averages2.append(received)

        # Extraer distancias y promedios del tercer conjunto de datos
        for device in data3:
            distance_str = device['distancia_entre_dispositivo_y_main_gw']
            # Verificar si la distancia es conocida
            if distance_str != 'unknown':
                distance = float(distance_str)
                rssi = device['average_rssi']
                snr = device['average_snr']
                toa = device['average_time_on_air_ms']
                lost = device['lost_frames']
                received = device['received_frames']
                rssi_averages3.append(rssi)
                snr_averages3.append(snr)
                toa_averages3.append(toa)
                lost_averages3.append(lost)
                received_averages3.append(received)

        # Definir los intervalos de distancia
        distance_intervals = list(range(0, int(max(distances)) + 100, 100))

        def process_data_and_generate_comparison_graphs(attribute_averages1, attribute_averages2, attribute_averages3, distance_intervals, filename_prefix, y_axis_label):
            data_by_distance_interval1 = group_by_interval(distances, attribute_averages1, distance_intervals)
            data_by_distance_interval2 = group_by_interval(distances, attribute_averages2, distance_intervals)
            data_by_distance_interval3 = group_by_interval(distances, attribute_averages3, distance_intervals)
            mean_by_distance_interval1 = calculate_mean_by_interval(data_by_distance_interval1)
            mean_by_distance_interval2 = calculate_mean_by_interval(data_by_distance_interval2)
            mean_by_distance_interval3 = calculate_mean_by_interval(data_by_distance_interval3)
            cumulative_mean1 = calculate_cumulative_mean(mean_by_distance_interval1, data_by_distance_interval1)
            cumulative_mean2 = calculate_cumulative_mean(mean_by_distance_interval2, data_by_distance_interval2)
            cumulative_mean3 = calculate_cumulative_mean(mean_by_distance_interval3, data_by_distance_interval3)
            bar_labels1 = [f'Dispositivos: {len(data_by_distance_interval1[interval])}' for interval in mean_by_distance_interval1.keys()]
            bar_labels2 = [f'Dispositivos: {len(data_by_distance_interval2[interval])}' for interval in mean_by_distance_interval2.keys()]
            bar_labels3 = [f'Dispositivos: {len(data_by_distance_interval3[interval])}' for interval in mean_by_distance_interval3.keys()]

            # Generate and save graphs
            generate_plotly_comparison_graphs(mean_by_distance_interval1, mean_by_distance_interval2, mean_by_distance_interval3, bar_labels1, bar_labels2, bar_labels3, cumulative_mean1, cumulative_mean2, cumulative_mean3,
                                            f'Media de {y_axis_label} y Media Acumulada por Intervalo de Distancia',
                                            'Distancia (m)', f'Media de {y_axis_label}', f'{filename_prefix}.html')

        # Generar graficos comparativos
        process_data_and_generate_comparison_graphs(rssi_averages1, rssi_averages2, rssi_averages3, distance_intervals, 'averageRSSI_x_distanceToMainGateway', 'RSSI (dBm)')
        process_data_and_generate_comparison_graphs(snr_averages1, snr_averages2, snr_averages3, distance_intervals, 'averageSNR_x_distanceToMainGateway', 'SNR (dB)')
        process_data_and_generate_comparison_graphs(toa_averages1, toa_averages2, toa_averages3, distance_intervals, 'averageTimeOnAir_x_distanceToMainGateway', 'Time on Air (ms)')
        process_data_and_generate_comparison_graphs(lost_averages1, lost_averages2, lost_averages3, distance_intervals, 'averageLostFrames_x_distanceToMainGateway', 'Lost Frames (paquetes)')
        process_data_and_generate_comparison_graphs(received_averages1, received_averages2, received_averages3, distance_intervals, 'averageReceivedFrames_x_distanceToMainGateway', 'Received Frames (paquetes)')

        # Group data by distance interval
        received_by_distance_interval1 = group_by_interval(distances, received_averages1, distance_intervals)
        lost_by_distance_interval1 = get_lost_by_interval(received_by_distance_interval1, max(received_averages1))
        received_by_distance_interval2 = group_by_interval(distances, received_averages2, distance_intervals)
        lost_by_distance_interval2 = get_lost_by_interval(received_by_distance_interval2, max(received_averages2))
        received_by_distance_interval3 = group_by_interval(distances, received_averages3, distance_intervals)
        lost_by_distance_interval3 = get_lost_by_interval(received_by_distance_interval3, max(received_averages3))

        # Calculate mean by distance interval
        mean_lost_by_distance_interval1 = calculate_mean_by_interval(lost_by_distance_interval1)
        mean_received_by_distance_interval1 = calculate_mean_by_interval(received_by_distance_interval1)
        mean_lost_by_distance_interval2 = calculate_mean_by_interval(lost_by_distance_interval2)
        mean_received_by_distance_interval2 = calculate_mean_by_interval(received_by_distance_interval2)
        mean_lost_by_distance_interval3 = calculate_mean_by_interval(lost_by_distance_interval3)
        mean_received_by_distance_interval3 = calculate_mean_by_interval(received_by_distance_interval3)

        # Calculate cumulative mean
        cumulative_mean_lost1 = calculate_cumulative_mean_percentage(mean_lost_by_distance_interval1, lost_by_distance_interval1, max(received_averages1))
        cumulative_mean_received1 = calculate_cumulative_mean_percentage(mean_received_by_distance_interval1, received_by_distance_interval1, max(received_averages1))
        cumulative_mean_lost2 = calculate_cumulative_mean_percentage(mean_lost_by_distance_interval2, lost_by_distance_interval2, max(received_averages2))
        cumulative_mean_received2 = calculate_cumulative_mean_percentage(mean_received_by_distance_interval2, received_by_distance_interval2, max(received_averages2))
        cumulative_mean_lost3 = calculate_cumulative_mean_percentage(mean_lost_by_distance_interval3, lost_by_distance_interval3, max(received_averages3))
        cumulative_mean_received3 = calculate_cumulative_mean_percentage(mean_received_by_distance_interval3, received_by_distance_interval3, max(received_averages3))

        # Calculate percentage of max
        percentage_of_max_lost1 = calculate_percentage_of_max(lost_by_distance_interval1, max(received_averages1))
        percentage_of_max_received1 = calculate_percentage_of_max(received_by_distance_interval1, max(received_averages1))
        percentage_of_max_lost2 = calculate_percentage_of_max(lost_by_distance_interval2, max(received_averages2))
        percentage_of_max_received2 = calculate_percentage_of_max(received_by_distance_interval2, max(received_averages2))
        percentage_of_max_lost3 = calculate_percentage_of_max(lost_by_distance_interval3, max(received_averages3))
        percentage_of_max_received3 = calculate_percentage_of_max(received_by_distance_interval3, max(received_averages3))

        # Create bar labels
        bar_labels_lost1 = [f'Dispositivos: {len(lost_by_distance_interval1[interval])}' for interval in mean_lost_by_distance_interval1.keys()]
        bar_labels_received1 = [f'Dispositivos: {len(received_by_distance_interval1[interval])}' for interval in mean_received_by_distance_interval1.keys()]
        bar_labels_lost2 = [f'Dispositivos: {len(lost_by_distance_interval2[interval])}' for interval in mean_lost_by_distance_interval2.keys()]
        bar_labels_received2 = [f'Dispositivos: {len(received_by_distance_interval2[interval])}' for interval in mean_received_by_distance_interval2.keys()]
        bar_labels_lost3 = [f'Dispositivos: {len(lost_by_distance_interval3[interval])}' for interval in mean_lost_by_distance_interval3.keys()]
        bar_labels_received3 = [f'Dispositivos: {len(received_by_distance_interval3[interval])}' for interval in mean_received_by_distance_interval3.keys()]

        # Generate and save graphs
        generate_plotly_bar_and_line_graph_with_threshold_comparison(percentage_of_max_lost1, bar_labels_lost1, cumulative_mean_lost1, percentage_of_max_lost2, bar_labels_lost2, cumulative_mean_lost2, percentage_of_max_lost3, bar_labels_lost3, cumulative_mean_lost3, 'Media de Lost Frames y Media Acumulada por Intervalo de Distancia', 'Distancia (m)', 'Media de Lost Frames (%)', 'averageLostFramesPercentage_x_distanceToMainGateway.html', 10)
        generate_plotly_bar_and_line_graph_with_threshold_comparison(percentage_of_max_received1, bar_labels_received1, cumulative_mean_received1, percentage_of_max_received2, bar_labels_received2, cumulative_mean_received2, percentage_of_max_received3, bar_labels_received3, cumulative_mean_received3, 'Media de Received Frames y Media Acumulada por Intervalo de Distancia', 'Distancia (m)', 'Media de Received Frames (%)', 'averageReceivedFramesPercentage_x_distanceToMainGateway.html', 90)

    def compare_3_devices_graphics_3(self):
        # Cargar los datos desde el primer archivo JSON
        with open(f'{self.compare_dir_1}/data/devicesCombinedData.json') as dev_json_1:
            data_1 = json.load(dev_json_1)

        # Cargar los datos desde el segundo archivo JSON
        with open(f'{self.compare_dir_2}/data/devicesCombinedData.json') as dev_json_2:
            data_2 = json.load(dev_json_2)

        # Cargar los datos desde el tercer archivo JSON
        with open(f'{self.compare_dir_3}/data/devicesCombinedData.json') as dev_json_3:
            data_3 = json.load(dev_json_3)

        # Crear diccionario para almacenar los datos agrupados de received_frames para el primer conjunto de datos
        grouped_received_data_1 = {}
        max_sf_received_1 = 0

        # Crear diccionario para almacenar los datos agrupados de lost_frames para el primer conjunto de datos
        grouped_lost_data_1 = {}
        grouped_rssi_data_1 = {}
        grouped_snr_data_1 = {}

        # Agrupar los datos del primer conjunto según el campo "last_SF_used"
        for entry in data_1:
            sf_used = entry['last_SF_used']
            received_frames = entry['received_frames']
            lost_frames = entry['lost_frames']
            rssi = entry['average_rssi']
            snr = entry['average_snr']

            # Para received_frames
            if received_frames > max_sf_received_1:
                max_sf_received_1 = received_frames

            if sf_used not in grouped_received_data_1:
                grouped_received_data_1[sf_used] = {'received_frames_list': [], 'device_count': 0}

            grouped_received_data_1[sf_used]['received_frames_list'].append(received_frames)
            grouped_received_data_1[sf_used]['device_count'] += 1

            # Para lost_frames
            if sf_used not in grouped_lost_data_1:
                grouped_lost_data_1[sf_used] = {'lost_frames_list': [], 'device_count': 0}

            grouped_lost_data_1[sf_used]['lost_frames_list'].append(lost_frames)
            grouped_lost_data_1[sf_used]['device_count'] += 1

            # Para average_rssi
            if sf_used not in grouped_rssi_data_1:
                grouped_rssi_data_1[sf_used] = {'rssi_list': [], 'device_count': 0}
                
            grouped_rssi_data_1[sf_used]['rssi_list'].append(rssi)
            grouped_rssi_data_1[sf_used]['device_count'] += 1

            # Para average_snr
            if sf_used not in grouped_snr_data_1:
                grouped_snr_data_1[sf_used] = {'snr_list': [], 'device_count': 0}
                
            grouped_snr_data_1[sf_used]['snr_list'].append(snr)
            grouped_snr_data_1[sf_used]['device_count'] += 1


        # Crear diccionario para almacenar los datos agrupados de received_frames para el segundo conjunto de datos
        grouped_received_data_2 = {}
        max_sf_received_2 = 0

        # Crear diccionario para almacenar los datos agrupados de lost_frames para el segundo conjunto de datos
        grouped_lost_data_2 = {}
        grouped_rssi_data_2 = {}
        grouped_snr_data_2 = {}

        # Agrupar los datos del segundo conjunto según el campo "last_SF_used"
        for entry in data_2:
            sf_used = entry['last_SF_used']
            received_frames = entry['received_frames']
            lost_frames = entry['lost_frames']
            rssi = entry['average_rssi']
            snr = entry['average_snr']

            # Para received_frames
            if received_frames > max_sf_received_2:
                max_sf_received_2 = received_frames

            if sf_used not in grouped_received_data_2:
                grouped_received_data_2[sf_used] = {'received_frames_list': [], 'device_count': 0}

            grouped_received_data_2[sf_used]['received_frames_list'].append(received_frames)
            grouped_received_data_2[sf_used]['device_count'] += 1

            # Para lost_frames
            if sf_used not in grouped_lost_data_2:
                grouped_lost_data_2[sf_used] = {'lost_frames_list': [], 'device_count': 0}

            grouped_lost_data_2[sf_used]['lost_frames_list'].append(lost_frames)
            grouped_lost_data_2[sf_used]['device_count'] += 1

            # Para average_rssi
            if sf_used not in grouped_rssi_data_2:
                grouped_rssi_data_2[sf_used] = {'rssi_list': [], 'device_count': 0}
                
            grouped_rssi_data_2[sf_used]['rssi_list'].append(rssi)
            grouped_rssi_data_2[sf_used]['device_count'] += 1

            # Para average_snr
            if sf_used not in grouped_snr_data_2:
                grouped_snr_data_2[sf_used] = {'snr_list': [], 'device_count': 0}
                
            grouped_snr_data_2[sf_used]['snr_list'].append(snr)
            grouped_snr_data_2[sf_used]['device_count'] += 1


        # Crear diccionario para almacenar los datos agrupados de received_frames para el tercer conjunto de datos
        grouped_received_data_3 = {}
        max_sf_received_3 = 0

        # Crear diccionario para almacenar los datos agrupados de lost_frames para el segundo conjunto de datos
        grouped_lost_data_3 = {}
        grouped_rssi_data_3 = {}
        grouped_snr_data_3 = {}

        # Agrupar los datos del tercer conjunto según el campo "last_SF_used"
        for entry in data_3:
            sf_used = entry['last_SF_used']
            received_frames = entry['received_frames']
            lost_frames = entry['lost_frames']
            rssi = entry['average_rssi']
            snr = entry['average_snr']

            # Para received_frames
            if received_frames > max_sf_received_3:
                max_sf_received_3 = received_frames

            if sf_used not in grouped_received_data_3:
                grouped_received_data_3[sf_used] = {'received_frames_list': [], 'device_count': 0}

            grouped_received_data_3[sf_used]['received_frames_list'].append(received_frames)
            grouped_received_data_3[sf_used]['device_count'] += 1

            # Para lost_frames
            if sf_used not in grouped_lost_data_3:
                grouped_lost_data_3[sf_used] = {'lost_frames_list': [], 'device_count': 0}

            grouped_lost_data_3[sf_used]['lost_frames_list'].append(lost_frames)
            grouped_lost_data_3[sf_used]['device_count'] += 1

            # Para average_rssi
            if sf_used not in grouped_rssi_data_3:
                grouped_rssi_data_3[sf_used] = {'rssi_list': [], 'device_count': 0}
                
            grouped_rssi_data_3[sf_used]['rssi_list'].append(rssi)
            grouped_rssi_data_3[sf_used]['device_count'] += 1

            # Para average_snr
            if sf_used not in grouped_snr_data_3:
                grouped_snr_data_3[sf_used] = {'snr_list': [], 'device_count': 0}
                
            grouped_snr_data_3[sf_used]['snr_list'].append(snr)
            grouped_snr_data_3[sf_used]['device_count'] += 1

        # Calcular la media de "received_frames" y "lost_frames" y contar el número de dispositivos para cada grupo para el primer conjunto de datos
        sf_received_info_1 = {}
        for sf_used, data in grouped_received_data_1.items():
            mean_received_frames = sum(data['received_frames_list']) / len(data['received_frames_list'])
            sf_received_info_1[sf_used] = {'mean_received_frames_percentage': mean_received_frames / max_sf_received_1 * 100, 'device_count': data['device_count']}

        sf_lost_info_1 = {}
        for sf_used, data in grouped_lost_data_1.items():
            mean_lost_frames = sum(data['lost_frames_list']) / len(data['lost_frames_list'])
            sf_lost_info_1[sf_used] = {'mean_lost_frames_percentage': mean_lost_frames / max_sf_received_1 * 100, 'device_count': data['device_count']}

        sf_rssi_info_1 = {}
        for sf_used, data in grouped_rssi_data_1.items():
            mean_rssi = sum(data['rssi_list']) / len(data['rssi_list'])
            sf_rssi_info_1[sf_used] = {'mean_rssi': mean_rssi, 'device_count': data['device_count']}

        sf_snr_info_1 = {}
        for sf_used, data in grouped_snr_data_1.items():
            mean_snr = sum(data['snr_list']) / len(data['snr_list'])
            sf_snr_info_1[sf_used] = {'mean_snr': mean_snr, 'device_count': data['device_count']}

        # Calcular la media de "received_frames" y "lost_frames" y contar el número de dispositivos para cada grupo para el segundo conjunto de datos
        sf_received_info_2 = {}
        for sf_used, data in grouped_received_data_2.items():
            mean_received_frames = sum(data['received_frames_list']) / len(data['received_frames_list'])
            sf_received_info_2[sf_used] = {'mean_received_frames_percentage': mean_received_frames / max_sf_received_2 * 100, 'device_count': data['device_count']}

        sf_lost_info_2 = {}
        for sf_used, data in grouped_lost_data_2.items():
            mean_lost_frames = sum(data['lost_frames_list']) / len(data['lost_frames_list'])
            sf_lost_info_2[sf_used] = {'mean_lost_frames_percentage': mean_lost_frames / max_sf_received_2 * 100, 'device_count': data['device_count']}

        sf_rssi_info_2 = {}
        for sf_used, data in grouped_rssi_data_2.items():
            mean_rssi = sum(data['rssi_list']) / len(data['rssi_list'])
            sf_rssi_info_2[sf_used] = {'mean_rssi': mean_rssi, 'device_count': data['device_count']}

        sf_snr_info_2 = {}
        for sf_used, data in grouped_snr_data_2.items():
            mean_snr = sum(data['snr_list']) / len(data['snr_list'])
            sf_snr_info_2[sf_used] = {'mean_snr': mean_snr, 'device_count': data['device_count']}

        # Calcular la media de "received_frames" y "lost_frames" y contar el número de dispositivos para cada grupo para el tercer conjunto de datos
        sf_received_info_3 = {}
        for sf_used, data in grouped_received_data_3.items():
            mean_received_frames = sum(data['received_frames_list']) / len(data['received_frames_list'])
            sf_received_info_3[sf_used] = {'mean_received_frames_percentage': mean_received_frames / max_sf_received_3 * 100, 'device_count': data['device_count']}

        sf_lost_info_3 = {}
        for sf_used, data in grouped_lost_data_3.items():
            mean_lost_frames = sum(data['lost_frames_list']) / len(data['lost_frames_list'])
            sf_lost_info_3[sf_used] = {'mean_lost_frames_percentage': mean_lost_frames / max_sf_received_3 * 100, 'device_count': data['device_count']}

        sf_rssi_info_3 = {}
        for sf_used, data in grouped_rssi_data_3.items():
            mean_rssi = sum(data['rssi_list']) / len(data['rssi_list'])
            sf_rssi_info_3[sf_used] = {'mean_rssi': mean_rssi, 'device_count': data['device_count']}

        sf_snr_info_3 = {}
        for sf_used, data in grouped_snr_data_3.items():
            mean_snr = sum(data['snr_list']) / len(data['snr_list'])
            sf_snr_info_3[sf_used] = {'mean_snr': mean_snr, 'device_count': data['device_count']}

        # Ordenar las claves de SF7 a SF12
        sorted_sf_received_info_1 = {sf: sf_received_info_1.get(sf, {'mean_received_frames_percentage': 0, 'device_count': 0}) for sf in ['SF7', 'SF8', 'SF9', 'SF10', 'SF11', 'SF12']}
        sorted_sf_lost_info_1 = {sf: sf_lost_info_1.get(sf, {'mean_lost_frames_percentage': 0, 'device_count': 0}) for sf in ['SF7', 'SF8', 'SF9', 'SF10', 'SF11', 'SF12']}
        sorted_sf_rssi_info_1 = {sf: sf_rssi_info_1.get(sf, {'mean_rssi': 0, 'device_count': 0}) for sf in ['SF7', 'SF8', 'SF9', 'SF10', 'SF11', 'SF12']}
        sorted_sf_snr_info_1 = {sf: sf_snr_info_1.get(sf, {'mean_snr': 0, 'device_count': 0}) for sf in ['SF7', 'SF8', 'SF9', 'SF10', 'SF11', 'SF12']}

        sorted_sf_received_info_2 = {sf: sf_received_info_2.get(sf, {'mean_received_frames_percentage': 0, 'device_count': 0}) for sf in ['SF7', 'SF8', 'SF9', 'SF10', 'SF11', 'SF12']}
        sorted_sf_lost_info_2 = {sf: sf_lost_info_2.get(sf, {'mean_lost_frames_percentage': 0, 'device_count': 0}) for sf in ['SF7', 'SF8', 'SF9', 'SF10', 'SF11', 'SF12']}
        sorted_sf_rssi_info_2 = {sf: sf_rssi_info_2.get(sf, {'mean_rssi': 0, 'device_count': 0}) for sf in ['SF7', 'SF8', 'SF9', 'SF10', 'SF11', 'SF12']}
        sorted_sf_snr_info_2 = {sf: sf_snr_info_2.get(sf, {'mean_snr': 0, 'device_count': 0}) for sf in ['SF7', 'SF8', 'SF9', 'SF10', 'SF11', 'SF12']}

        sorted_sf_received_info_3 = {sf: sf_received_info_3.get(sf, {'mean_received_frames_percentage': 0, 'device_count': 0}) for sf in ['SF7', 'SF8', 'SF9', 'SF10', 'SF11', 'SF12']}
        sorted_sf_lost_info_3 = {sf: sf_lost_info_3.get(sf, {'mean_lost_frames_percentage': 0, 'device_count': 0}) for sf in ['SF7', 'SF8', 'SF9', 'SF10', 'SF11', 'SF12']}
        sorted_sf_rssi_info_3 = {sf: sf_rssi_info_3.get(sf, {'mean_rssi': 0, 'device_count': 0}) for sf in ['SF7', 'SF8', 'SF9', 'SF10', 'SF11', 'SF12']}
        sorted_sf_snr_info_3 = {sf: sf_snr_info_3.get(sf, {'mean_snr': 0, 'device_count': 0}) for sf in ['SF7', 'SF8', 'SF9', 'SF10', 'SF11', 'SF12']}

        # Crear gráfico de barras interactivo para received_frames comparando los dos conjuntos de datos
        bar_trace_received_1 = go.Bar(
            x=[sf for sf in sorted_sf_received_info_1.keys()],
            y=[info['mean_received_frames_percentage'] for info in sorted_sf_received_info_1.values()],
            text=[f'Dispositivos: {info["device_count"]}' for info in sorted_sf_received_info_1.values()],
            textposition='auto',
            name="data_1",
            marker=dict(color='blue')
        )

        bar_trace_received_2 = go.Bar(
            x=[sf for sf in sorted_sf_received_info_2.keys()],
            y=[info['mean_received_frames_percentage'] for info in sorted_sf_received_info_2.values()],
            text=[f'Dispositivos: {info["device_count"]}' for info in sorted_sf_received_info_2.values()],
            textposition='auto',
            name="data_2",
            marker=dict(color='red')
        )

        bar_trace_received_3 = go.Bar(
            x=[sf for sf in sorted_sf_received_info_3.keys()],
            y=[info['mean_received_frames_percentage'] for info in sorted_sf_received_info_3.values()],
            text=[f'Dispositivos: {info["device_count"]}' for info in sorted_sf_received_info_3.values()],
            textposition='auto',
            name="data_3",
            marker=dict(color='green')
        )

        layout_received = go.Layout(
            title="Media de Received Frames (%) por Last SF used",
            xaxis=dict(title="Last SF used"),
            yaxis=dict(title="Average Received Frames (%)")
        )

        fig_received = go.Figure(data=[bar_trace_received_1, bar_trace_received_2, bar_trace_received_3], layout=layout_received)

        # Write received_frames comparison to HTML file
        fig_received.write_html(f'{self.output_dir}/lastSFused/averageReceivedFramesComparison_x_lastSFUsed.html')

        # Crear gráfico de barras interactivo para lost_frames comparando los dos conjuntos de datos
        bar_trace_lost_1 = go.Bar(
            x=[sf for sf in sorted_sf_lost_info_1.keys()],
            y=[info['mean_lost_frames_percentage'] for info in sorted_sf_lost_info_1.values()],
            text=[f'Dispositivos: {info["device_count"]}' for info in sorted_sf_lost_info_1.values()],
            textposition='auto',
            name="data_1",
            marker=dict(color='blue')
        )

        bar_trace_lost_2 = go.Bar(
            x=[sf for sf in sorted_sf_lost_info_2.keys()],
            y=[info['mean_lost_frames_percentage'] for info in sorted_sf_lost_info_2.values()],
            text=[f'Dispositivos: {info["device_count"]}' for info in sorted_sf_lost_info_2.values()],
            textposition='auto',
            name="data_2",
            marker=dict(color='red')
        )

        bar_trace_lost_3 = go.Bar(
            x=[sf for sf in sorted_sf_lost_info_3.keys()],
            y=[info['mean_lost_frames_percentage'] for info in sorted_sf_lost_info_3.values()],
            text=[f'Dispositivos: {info["device_count"]}' for info in sorted_sf_lost_info_3.values()],
            textposition='auto',
            name="data_3",
            marker=dict(color='green')
        )

        layout_lost = go.Layout(
            title="Media de Lost Frames (%) por Last SF used",
            xaxis=dict(title="Last SF used"),
            yaxis=dict(title="Average Lost Frames (%)")
        )

        fig_lost = go.Figure(data=[bar_trace_lost_1, bar_trace_lost_2, bar_trace_lost_3], layout=layout_lost)

        # Write lost_frames comparison to HTML file
        fig_lost.write_html(f'{self.output_dir}/lastSFused/averageLostFramesComparison_x_lastSFUsed.html')

        # Crear gráficos de barras interactivos para average_rssi
        bar_trace_rssi_1 = go.Bar(
            x=[sf for sf in sorted_sf_rssi_info_1.keys()],
            y=[info['mean_rssi'] for info in sorted_sf_rssi_info_1.values()],
            text=[f'Dispositivos: {info["device_count"]}' for info in sorted_sf_rssi_info_1.values()],
            textposition='auto',
            name="data_1",
            marker=dict(color='blue')
        )

        bar_trace_rssi_2 = go.Bar(
            x=[sf for sf in sorted_sf_rssi_info_2.keys()],
            y=[info['mean_rssi'] for info in sorted_sf_rssi_info_2.values()],
            text=[f'Dispositivos: {info["device_count"]}' for info in sorted_sf_rssi_info_2.values()],
            textposition='auto',
            name="data_2",
            marker=dict(color='red')
        )

        bar_trace_rssi_3 = go.Bar(
            x=[sf for sf in sorted_sf_rssi_info_3.keys()],
            y=[info['mean_rssi'] for info in sorted_sf_rssi_info_3.values()],
            text=[f'Dispositivos: {info["device_count"]}' for info in sorted_sf_rssi_info_3.values()],
            textposition='auto',
            name="data_3",
            marker=dict(color='green')
        )

        layout_rssi = go.Layout(
            title="Media de RSSI por Last SF used",
            xaxis=dict(title="Last SF used"),
            yaxis=dict(title="Average RSSI")
        )

        fig_rssi = go.Figure(data=[bar_trace_rssi_1, bar_trace_rssi_2, bar_trace_rssi_3], layout=layout_rssi)

        # Write average_rssi to HTML file
        fig_rssi.write_html(f'{self.output_dir}/lastSFused/averageRSSI_x_lastSFUsed.html')

        # Crear gráficos de barras interactivos para average_snr
        bar_trace_snr_1 = go.Bar(
            x=[sf for sf in sorted_sf_snr_info_1.keys()],
            y=[info['mean_snr'] for info in sorted_sf_snr_info_1.values()],
            text=[f'Dispositivos: {info["device_count"]}' for info in sorted_sf_snr_info_1.values()],
            textposition='auto',
            name="data_1",
            marker=dict(color='blue')
        )

        bar_trace_snr_2 = go.Bar(
            x=[sf for sf in sorted_sf_snr_info_2.keys()],
            y=[info['mean_snr'] for info in sorted_sf_snr_info_2.values()],
            text=[f'Dispositivos: {info["device_count"]}' for info in sorted_sf_snr_info_2.values()],
            textposition='auto',
            name="data_2",
            marker=dict(color='red')
        )

        bar_trace_snr_3 = go.Bar(
            x=[sf for sf in sorted_sf_snr_info_3.keys()],
            y=[info['mean_snr'] for info in sorted_sf_snr_info_3.values()],
            text=[f'Dispositivos: {info["device_count"]}' for info in sorted_sf_snr_info_3.values()],
            textposition='auto',
            name="data_3",
            marker=dict(color='green')
        )

        layout_snr = go.Layout(
            title="Media de SNR por Last SF used",
            xaxis=dict(title="Last SF used"),
            yaxis=dict(title="Average SNR")
        )

        fig_snr = go.Figure(data=[bar_trace_snr_1, bar_trace_snr_2, bar_trace_snr_3], layout=layout_snr)

        # Write average_snr to HTML file
        fig_snr.write_html(f'{self.output_dir}/lastSFused/averageSNR_x_lastSFUsed.html')

