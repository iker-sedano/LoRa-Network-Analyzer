import urllib3
import socket
import requests
import os
from datetime import datetime, timedelta
from playwright.sync_api import sync_playwright

class OrbiwiseAPI:
    def __init__(self, data):
        urllib3.disable_warnings()
        self.data = data
        self.get_api_endpoint()

    def get_api_endpoint(self):
        ip_address = socket.gethostbyname(socket.gethostname())
        if ip_address.startswith('10.101.') or ip_address.startswith('10.144.') or ip_address.startswith('172.29.'):
            # Estamos dentro de la red local
            self.base_url = "https://172.29.8.20/rest"
            self.url_signin = "https://172.29.8.20/app/signin"
        else:
            # Estamos fuera de la red local
            #self.base_url = "https://itelorbiwise.itelazpi.eus/rest"
            self.base_url = "https://194.30.1.140/rest"
            self.url_signin = "https://itelorbiwise.itelazpi.eus/app/signin"

    def validate_user_and_get_token(self, username, password):
        self.username = username
        self.password = password
        auth_url = f"{self.base_url}/oauth2/token"
        auth_data = {"grant_type": "password", "username": username, "password": password}
        auth_response = requests.post(auth_url, data=auth_data, verify=False)

        if auth_response.status_code == 200:
            self.access_token = auth_response.json()["access_token"]
            print(f"Token obtenido correctamente")
            return True
        else:
            print(f"No se pudo obtener el token de autenticacion por el siguiente error: {auth_response.status_code}")
            return False
            #exit()

    def get_groups_from_user(self):
        group_url = f"{self.base_url}/groups"
        group_headers = {"Authorization": f"Bearer {self.access_token}"}
        group_response = requests.get(group_url, headers=group_headers, verify=False)

        if group_response.status_code == 200:
            all_groups = group_response.json()
            print(f"Grupos obtenidos correctamente")
            groupids_unsorted = [item['groupid'] for item in all_groups]
            groupids = sorted(groupids_unsorted)
            return groupids
        else:
            print(f"No se han podido obtener los grupos por el siguiente error: {group_response.status_code}")
            exit()

    def get_devices_from_group(self, group):
        self.devices_all = []

        devices_url = f"{self.base_url}/nodes"
        devices_headers = {"Authorization": f"Bearer {self.access_token}"}
        devices_params = {"group": group, "limit": 2000}
        pages_params = {"group": group, "limit": 2000, "get_pages": "true"}
        pages_response = requests.get(devices_url, params=pages_params, headers=devices_headers, verify=False)

        if pages_response.status_code == 200:
            pages_list = pages_response.json()
            print(f"Hay un total de {pages_list['total']} dispositivos y se van a ir obteniendo en grupos de {pages_list['per_page']}")
            for p in pages_list["pages"]:
                devices_params["page_state"] = p["page_state"]
                devices_response = requests.get(devices_url, params=devices_params, headers=devices_headers, verify=False)
                if devices_response.status_code == 200:
                    devices_list = devices_response.json()
                    print(f"Se han obtenido los datos de {len(devices_list)} dispositivos")
                    self.devices_all.extend(devices_list)
                else:
                    print(f"No se pudo obtener la siguiente lista de dispositivos por el siguiente error: {devices_response.status_code}")
                    exit()
            deveui_list = [item['deveui'] for item in self.devices_all]
            self.deveui_set = set(deveui_list)
            return self.deveui_set, self.devices_all

        else:
            print(f"No se pudo obtener la lista de dispositivos por el siguiente error: {pages_response.status_code}")
            exit()

    def get_payloads_from_each_device(self, start_date, end_date, update_payloads_progress_bar):
        self.payloads_all = []
        self.start_date = start_date
        self.end_date = end_date
        valor_actual = 0

        # Convertir las fechas de tipo str a objetos datetime
        start_date_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_dt = datetime.strptime(end_date, '%Y-%m-%d')

        # Formatear las fechas en el formato deseado
        from_date_iso = start_date_dt.strftime('%Y-%m-%dT00:00:00')
        to_date_iso = end_date_dt.strftime('%Y-%m-%dT23:59:59')

        device_header = {"Authorization": f"Bearer {self.access_token}"}
        device_param = {"data_format": "hex", "from_date": from_date_iso, "to_date": to_date_iso}

        for deveui in self.deveui_set:
            each_device_url = f"{self.base_url}/nodes/{deveui}/payloads/ul"
            each_device_response = requests.get(each_device_url, params=device_param, headers=device_header, verify=False)
            if each_device_response.status_code == 200:
                device_response = each_device_response.json()
                filtered_data = []
                for obj in device_response:
                    # Obtener el primer objeto de gtw_info
                    first_gtw_info = obj.get("gtw_info", [{}])[0]
                    main_gw = first_gtw_info.get("gtw_id", "")
                    
                    # Obtener el número de objetos en gtw_info
                    gws_reached = len(obj.get("gtw_info", []))
                    
                    filtered_obj = {
                        "dr_used": obj["dr_used"],
                        "fcnt": obj["fcnt"],
                        "rssi": obj["rssi"],
                        "snr": obj["snr"],
                        "time_on_air_ms": obj["time_on_air_ms"],
                        "main_gw": main_gw,
                        "gws_reached": gws_reached
                    }
                    filtered_data.append(filtered_obj)
                formatted_json = {"deveui": deveui, "data": filtered_data}
                self.payloads_all.append(formatted_json)
            else:
                print(f"No se pudo obtener la info de los payloads de uplink del dispositivo {deveui} por la siguiente razon: {each_device_response.status_code}")
                exit()

            valor_actual += 1
            update_payloads_progress_bar(valor_actual)

        return self.payloads_all
    
    def get_gateways_from_user(self):
        gateways_url = f"{self.base_url}/gateways"
        gateways_headers = {"Authorization": f"Bearer {self.access_token}"}
        gateways_response = requests.get(gateways_url, headers=gateways_headers, verify=False)

        if gateways_response.status_code == 200:
            all_gateways = gateways_response.json()
            self.filtered_gateways = [
                {
                    "altitude": gw["altitude"],
                    #"backhaul_cell_rssi": gw["backhaul_cell_rssi"],
                    "id": gw["id"],
                    "latitude": gw["latitude"],
                    "longitude": gw["longitude"],
                    "name": gw["name"],
                    "status": gw["status"],
                }
                for gw in all_gateways
                if "altitude" in gw
            ]

            # Ordenar la lista de gateways por el nombre
            self.filtered_gateways = sorted(self.filtered_gateways, key=lambda x: x['name'])

            print(f"Gateways obtenidos correctamente")

            return self.filtered_gateways
        else:
            print(f"No se pudieron obtener los gateways por el siguiente error: {gateways_response.status_code}")
            exit()

    def get_gateways_info_web_scraping(self, selected_gateways, update_gateways_info_progress_bar):
        valor_actual = 0

        # Obtén la ruta al directorio del script
        #dir_path = os.path.dirname(os.path.realpath(__file__))

        # Ruta al ejecutable de Chromium (relativa)
        #chromium_executable_path = os.path.join(dir_path, 'chromium-1097\\chrome-win', 'chrome.exe')

        # Absolute path de chromium
        # 'C:\\Users\\Iker Sedano\\AppData\\Local\\ms-playwright\\chromium-1097\\chrome-win\\chrome.exe'

        with sync_playwright() as p:
            #browser = p.chromium.launch(headless=False, executable_path=chromium_executable_path) # headless=False para ejecutar en primer plano
            browser = p.chromium.launch(headless=True) # headless=False para ejecutar en primer plano
            context = browser.new_context()
            page_one = context.new_page()

            # Abrir la URL en una pestaña
            page_one.goto(self.url_signin)

            # Escribir el user
            username_input_selector = '.form-control[type="text"]'
            page_one.type(username_input_selector, self.username)

            # Escribir en el segundo campo de entrada de contraseña
            password_input_selector = '.form-control[type="password"]'
            page_one.type(password_input_selector, self.password)

            # Hacer clic en el botón de inicio de sesión
            sign_in_button_selector = '.btn.btn-dark'
            page_one.click(sign_in_button_selector)
            
            # Convertir las fechas a objetos datetime
            start_date_obj = datetime.strptime(self.start_date, "%Y-%m-%d")
            end_date_obj = datetime.strptime(self.end_date, "%Y-%m-%d")

            # Formatear las fechas según el formato deseado
            from_date = start_date_obj.strftime("%d%%2F%m%%2F%Y%%2000%%3A00%%3A00")
            to_date = (end_date_obj + timedelta(days=1) - timedelta(seconds=1)).strftime("%d%%2F%m%%2F%Y%%20%H%%3A%M%%3A%S")

            page_one.wait_for_timeout(1000)

            for gateways in selected_gateways:
                gw_id = gateways['id']
                url = f"https://itelorbiwise.itelazpi.eus/tfw1/rest?getGWStatsAggregated=1&from={from_date}&to={to_date}&gw={gw_id}&tz=-60"
                new_tab = context.new_page()
                new_tab.goto(url)
                json_content = new_tab.inner_html("body")
                self.data.save_selected_gateway_info(gw_id, json_content)
                new_tab.close()

                valor_actual += 1
                update_gateways_info_progress_bar(valor_actual)

            # Cerrar el navegador al finalizar
            browser.close()
            