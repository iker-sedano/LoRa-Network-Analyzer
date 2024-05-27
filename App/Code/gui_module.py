from datetime import datetime
import os
import sys
from tkinter import END, filedialog
from tkcalendar import Calendar
import tkinter as tk
import threading
import copy
from pathlib import Path
from tkinter import BOTH, LEFT, RIGHT, Y, Frame, Listbox, Scrollbar, Tk, Canvas, Entry, Text, Button, PhotoImage, messagebox, ttk

class MainApplication:
    def __init__(self, window, api, data):
        self.OUTPUT_PATH = Path(__file__).parent
        self.ASSETS_PATH = self.OUTPUT_PATH / Path(r".\assets")

        self.window = window
        self.api = api
        self.data = data

        self.setup_gui()

    def relative_to_assets(self, relative_path):
        try:
            base_path = sys._MEIPASS2
        except Exception:
            base_path = os.path.abspath(r".\assets")
        return os.path.join(base_path, relative_path)

    #def relative_to_assets(self, path: str) -> Path:
        #return self.ASSETS_PATH / Path(path)

    def clear_widgets(self):
        # Destruir todos los widgets en la ventana principal
        for widget in self.window.winfo_children():
            widget.destroy()

    def center_text(self, text):
        # Obtenemos las coordenadas de la bounding box del texto
        self.bbox = self.canvas.bbox(text)

        # Calculamos el ajuste necesario para centrar el texto
        text_center = (self.bbox[0] + self.bbox[2]) / 2
        offset_x = self.canvas_center[0] - text_center

        # Movemos el texto al centro del canvas
        self.canvas.move(text, offset_x, 0)

    def setup_gui(self):
        self.window.title("LoRa Network Analyzer (Itelazpi)")
        self.window.geometry("800x600")
        self.window.resizable(False, False)
        self.window.configure(bg = "#E8F0EE")
        self.window.iconbitmap(self.relative_to_assets("icon.ico"))

        self.clear_widgets()

        self.canvas = Canvas(
            self.window,
            bg = "#E8F0EE",
            height = 600,
            width = 800,
            bd = 0,
            highlightthickness = 0,
            relief = "ridge"
        )

        # Calculamos el centro del canvas
        self.canvas_center = (800 / 2, 0)

        self.canvas.place(x = 0, y = 0)

        self.canvas.create_rectangle(
            0.0,
            0.0,
            800.0,
            100.0,
            fill="#96D525",
            outline="")
        
        self.text_1 = self.canvas.create_text(
            0.0,
            10.0,
            anchor="nw",
            text="LoRa Network Analyzer",
            fill="#004957",
            font=("UbuntuCondensed Regular", 64 * -1)
        )
        self.center_text(self.text_1)

        self.text_2 = self.canvas.create_text(
            150.0,
            125.0,
            anchor="nw",
            text="Inicia sesión para realizar un análisis",
            fill="#000000",
            font=("UbuntuCondensed Regular", 32 * -1)
        )
        self.center_text(self.text_2)

        self.text_3 = self.canvas.create_text(
            250.0,
            200.0,
            anchor="nw",
            text="Usuario",
            fill="#000000",
            font=("UbuntuCondensed Regular", 24 * -1)
        )
        self.center_text(self.text_3)

        self.entry_image_1 = PhotoImage(
            file=self.relative_to_assets("entry_1.png"))
        self.entry_bg_1 = self.canvas.create_image(
            400.0,
            250.5,
            image=self.entry_image_1
        )
        self.entry_1 = Entry(
            bd=0,
            bg="#D9D9D9",
            fg="#000716",
            highlightthickness=0,
            justify='center'
        )
        self.entry_1.place(
            x=212.5,
            y=238.0,
            width=375.0,
            height=23.0
        )

        self.text_4 = self.canvas.create_text(
            250.0,
            300.0,
            anchor="nw",
            text="Contraseña",
            fill="#000000",
            font=("UbuntuCondensed Regular", 24 * -1)
        )
        self.center_text(self.text_4)

        self.entry_image_2 = PhotoImage(
            file=self.relative_to_assets("entry_1.png"))
        self.entry_bg_2 = self.canvas.create_image(
            400.0,
            350.5,
            image=self.entry_image_2
        )
        self.entry_2 = Entry(
            bd=0,
            bg="#D9D9D9",
            fg="#000716",
            highlightthickness=0,
            justify='center',
            show="*"
        )
        self.entry_2.place(
            x=212.5,
            y=338.0,
            width=375.0,
            height=23.0
        )

        self.button_image_1 = PhotoImage(
            file=self.relative_to_assets("button_1.png"))
        self.button_1 = Button(
            image=self.button_image_1,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.login_api(),
            relief="flat"
        )
        self.button_1.place(
            x=350.0,
            y=400.0,
            width=100.0,
            height=25.0
        )

        self.button_image_2 = PhotoImage(
            file=self.relative_to_assets("button_2.png"))
        self.button_2 = Button(
            image=self.button_image_2,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.select_number_of_paths(),
            relief="flat"
        )
        self.button_2.place(
            x=300.0,
            y=538.0,
            width=200.0,
            height=25.0
        )

        self.text_5 = self.canvas.create_text(
            25.0,
            475.0,
            anchor="nw",
            text="O inicia una comparativa entre análisis ya realizados",
            fill="#000000",
            font=("UbuntuCondensed Regular", 24 * -1)
        )
        self.center_text(self.text_5)

    def login_api(self):
        # Esta función se ejecutará en un hilo separado
        def api_login_thread():
            self.button_1.config(state="disabled")
            login_conf = self.api.validate_user_and_get_token(self.entry_1.get(), self.entry_2.get())
            if login_conf:
                self.groupids = self.api.get_groups_from_user()
                # Una vez que las llamadas a la API hayan terminado, llama a group_selection en el hilo principal
                self.window.after(0, self.group_selection)
            else:
                messagebox.showinfo(message="Credenciales no validas. Intentalo de nuevo.")
                self.entry_1.delete(0, END)
                self.entry_2.delete(0, END)
                self.button_1.config(state="active")

        # Crea un hilo para ejecutar las llamadas a la API
        api_thread = threading.Thread(target=api_login_thread)
        api_thread.start()

    def group_selection(self):
        self.clear_widgets()
        
        def filter_elements():
            filtro = self.entry_1.get().lower()
            filtered_names = [entry for entry in self.groupids if filtro in entry.lower()]
            self.listbox.delete(0, tk.END)  # Limpiar la lista
            for name in filtered_names:
                self.listbox.insert(tk.END, name)
        
        def select_group():
            selected_index = self.listbox.curselection()
            if selected_index:
                self.selected_group = self.listbox.get(selected_index[0])  # Obtener el texto del índice seleccionado
                self.group_api()
            else:
                messagebox.showinfo(message="Selecciona un grupo")
                print("Ningún elemento seleccionado.")
        
        self.canvas = Canvas(
            self.window,
            bg = "#E8F0EE",
            height = 600,
            width = 800,
            bd = 0,
            highlightthickness = 0,
            relief = "ridge"
        )

        self.canvas.place(x = 0, y = 0)
        self.canvas.create_text(
            150.0,
            13.0,
            anchor="nw",
            text="      Selecciona el grupo deseado",
            fill="#000000",
            font=("UbuntuCondensed Regular", 32 * -1)
        )

        self.entry_image_1 = PhotoImage(
            file=self.relative_to_assets("entry_1.png"))
        self.entry_bg_1 = self.canvas.create_image(
            400.0,
            87.5,
            image=self.entry_image_1
        )
        self.entry_1 = Entry(
            bd=0,
            bg="#D9D9D9",
            fg="#000716",
            highlightthickness=0,
            justify='center'
        )
        self.entry_1.place(
            x=212.5,
            y=75.0,
            width=375.0,
            height=23.0
        )
        self.entry_1.bind(
            "<KeyRelease>",
            lambda event: filter_elements()
        )

        self.button_image_1 = PhotoImage(
            file=self.relative_to_assets("button_3.png"))
        self.button_1 = Button(
            image=self.button_image_1,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: select_group(),
            relief="flat"
        )
        self.button_1.place(
            x=300.0,
            y=538.0,
            width=200.0,
            height=25.0
        )

        self.list_frame = Frame(self.canvas, bg="#D9D9D9")  # Frame para la Listbox y Scrollbar
        self.list_frame.place(x=200.0, y=125.0, width=400.0, height=400.0)

        self.scrollbar = Scrollbar(self.list_frame, bg="#D9D9D9")
        self.scrollbar.pack(side=RIGHT, fill=Y)

        self.listbox = Listbox(self.list_frame, yscrollcommand=self.scrollbar.set, bg="#D9D9D9")
        self.listbox.pack(side=LEFT, fill=BOTH, expand=True)

        self.scrollbar.config(command=self.listbox.yview)

        # Insertar los nombres en la Listbox
        for entry in self.groupids:
            self.listbox.insert(tk.END, entry)

    def group_api(self):
        def group_api_thread():
            self.button_1.config(state="disabled")
            self.deveui_set, self.devices_all = self.api.get_devices_from_group(self.selected_group)
            self.window.after(0, self.time_range_selection_for_payloads)
        
        group_thread = threading.Thread(target=group_api_thread)
        group_thread.start()

    def time_range_selection_for_payloads(self):
        def check_positive_time():
            self.total_payloads_days = (datetime.strptime(self.cal_end.get_date(), "%Y-%m-%d") - datetime.strptime(self.cal_start.get_date(), "%Y-%m-%d")).days + 1
            if self.total_payloads_days > 0:
                self.payloads_progress_bar()
            else:
                messagebox.showinfo(message="El tiempo de inicio tiene que ser menos al tiempo de final")
            
        self.clear_widgets()

        self.canvas = Canvas(
            self.window,
            bg = "#E8F0EE",
            height = 600,
            width = 800,
            bd = 0,
            highlightthickness = 0,
            relief = "ridge"
        )

        self.canvas.place(x = 0, y = 0)
        self.text_1 = self.canvas.create_text(
            0.0,
            13.0,
            anchor="nw",
            text="Selecciona un rango de fechas para realizar el análisis",
            fill="#000000",
            font=("UbuntuCondensed Regular", 32 * -1)
        )
        self.center_text(self.text_1)

        self.canvas.create_text(
            0.0,
            200.0,
            anchor="nw",
            text="         Fecha de inicio (00:00:00)",
            fill="#000000",
            font=("UbuntuCondensed Regular", 24 * -1)
        )

        self.canvas.create_text(
            400.0,
            200.0,
            anchor="nw",
            text="           Fecha de fin (23:59:59)",
            fill="#000000",
            font=("UbuntuCondensed Regular", 24 * -1)
        )

        self.button_image_1 = PhotoImage(
            file=self.relative_to_assets("button_4.png"))
        self.button_1 = Button(
            image=self.button_image_1,
            borderwidth=0,
            highlightthickness=0,
            command= check_positive_time,
            relief="flat"
        )
        self.button_1.place(
            x=300.0,
            y=538.0,
            width=200.0,
            height=25.0
        )

        self.text_2 = self.canvas.create_text(
            25.0,
            88.0,
            anchor="nw",
            text=f"Dispositivos en el grupo “{self.selected_group}”: {len(self.deveui_set)} ",
            fill="#000000",
            font=("UbuntuCondensed Regular", 24 * -1)
        )
        self.center_text(self.text_2)

        # Widget Calendar para la fecha de inicio
        self.cal_start = Calendar(
            self.canvas,
            selectmode='day',
            locale='es_ES',
            date_pattern='y-mm-dd'
        )
        self.canvas.create_window(
            70,
            250,
            anchor="nw",
            window=self.cal_start
        )

        # Widget Calendar para la fecha de fin
        self.cal_end = Calendar(
            self.canvas,
            selectmode='day',
            locale='es_ES',
            date_pattern='y-mm-dd'
        )
        self.canvas.create_window(
            470,
            250,
            anchor="nw",
            window=self.cal_end
    )
        
    def payloads_progress_bar(self):
        self.clear_widgets()

        self.canvas = Canvas(
            self.window,
            bg = "#E8F0EE",
            height = 600,
            width = 800,
            bd = 0,
            highlightthickness = 0,
            relief = "ridge"
        )

        self.canvas.place(x = 0, y = 0)
        self.text_1 = self.canvas.create_text(
            0.0,
            13.0,
            anchor="nw",
            text=f"Vas a obtener {self.total_payloads_days} dias de payloads de {len(self.deveui_set)} dispositivos",
            fill="#000000",
            font=("UbuntuCondensed Regular", 32 * -1)
        )
        self.center_text(self.text_1)

        self.text_2 = self.canvas.create_text(
            200.0,
            350.0,
            anchor="nw",
            text="0.00%",
            fill="#000000",
            font=("UbuntuCondensed Regular", 24 * -1)
        )
        self.center_text(self.text_2)

        self.button_image_1 = PhotoImage(
            file=self.relative_to_assets("button_5.png"))
        self.button_1 = Button(
            image=self.button_image_1,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.payloads_api(),
            relief="flat"
        )
        self.button_1.place(
            x=337.0,
            y=539.0,
            width=126.0,
            height=25.0
        )

        self.text_3 = self.canvas.create_text(
            25.0,
            88.0,
            anchor="nw",
            text="* El tiempo de carga variara en funcion del número",
            fill="#000000",
            font=("UbuntuCondensed Regular", 24 * -1)
        )
        self.center_text(self.text_3)

        self.text_4 = self.canvas.create_text(
            25.0,
            113.0,
            anchor="nw",
            text="de dispositivos y rango de tiempo",
            fill="#000000",
            font=("UbuntuCondensed Regular", 24 * -1)
        )
        self.center_text(self.text_4)

        self.progress_bar = ttk.Progressbar(self.window, orient="horizontal", length=600, mode="determinate")
        self.progress_bar["maximum"] = len(self.deveui_set)
        self.progress_bar.place(x=100, y=287)

    def payloads_api(self):
        def payloads_api_thread():
            self.button_1.config(state="disabled")
            self.payloads_all = self.api.get_payloads_from_each_device(self.cal_start.get_date(), self.cal_end.get_date(), self.update_payloads_progress_bar)
            self.window.after(0, self.save_payloads_screen())
        
        payloads_thread = threading.Thread(target=payloads_api_thread)
        payloads_thread.start() 

    def update_payloads_progress_bar(self, valor_actual):
        self.progress_bar["value"] = valor_actual
        porcentaje = (valor_actual / len(self.deveui_set)) * 100
        self.canvas.itemconfig(self.text_2, text=f"{porcentaje:.2f}%")
        self.window.update_idletasks()  # Actualizar la interfaz gráfica

    def save_payloads_screen(self):
        self.clear_widgets()

        self.canvas = Canvas(
            self.window,
            bg = "#E8F0EE",
            height = 600,
            width = 800,
            bd = 0,
            highlightthickness = 0,
            relief = "ridge"
        )

        self.canvas.place(x = 0, y = 0)
        self.text_1 = self.canvas.create_text(
            0.0,
            13.0,
            anchor="nw",
            text="Los datos se han obtenido correctamente",
            fill="#000000",
            font=("UbuntuCondensed Regular", 32 * -1)
        )
        self.center_text(self.text_1)

        self.text_2 = self.canvas.create_text(
            0.0,
            63.0,
            anchor="nw",
            text="Selecciona un directorio para guardar los datos",
            fill="#000000",
            font=("UbuntuCondensed Regular", 32 * -1)
        )
        self.center_text(self.text_2)

        self.button_image_1 = PhotoImage(
            file=self.relative_to_assets("button_6.png"))
        self.button_1 = Button(
            image=self.button_image_1,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.save_data(),
            relief="flat"
        )
        self.button_1.place(
            x=337.0,
            y=539.0,
            width=126.0,
            height=25.0
        )

        self.text_3 = self.canvas.create_text(
            25.0,
            150.0,
            anchor="nw",
            text="* Selecciona el directorio raiz, el programa se encargara de",
            fill="#000000",
            font=("UbuntuCondensed Regular", 24 * -1)
        )
        self.center_text(self.text_3)

        self.text_4 = self.canvas.create_text(
            25.0,
            175.0,
            anchor="nw",
            text="crear los subdirectorios correspondientes",
            fill="#000000",
            font=("UbuntuCondensed Regular", 24 * -1)
        )
        self.center_text(self.text_4)

        self.image_image_1 = PhotoImage(
            file=self.relative_to_assets("image_1.png"))
        self.image_1 = self.canvas.create_image(
            400.0,
            376.0,
            image=self.image_image_1
        )

    def save_data(self):
        # Convertir las fechas de tipo str a objetos datetime
        start_date_dt = datetime.strptime(self.cal_start.get_date(), '%Y-%m-%d')
        end_date_dt = datetime.strptime(self.cal_end.get_date(), '%Y-%m-%d')

        # Convertir el objeto datetime a un string con el formato para generar el nombre del archivo
        start_date = start_date_dt.strftime("%d%m%Y")
        end_date = end_date_dt.strftime("%d%m%Y")

        self.working_directory = self.data.create_directory_hierarchy(self.selected_group, start_date, end_date)
        self.data.save_devices_and_payloads(self.devices_all, self.payloads_all)

        self.after_save_data_screen()

    def after_save_data_screen(self):
        self.clear_widgets()

        self.canvas = Canvas(
            self.window,
            bg = "#E8F0EE",
            height = 600,
            width = 800,
            bd = 0,
            highlightthickness = 0,
            relief = "ridge"
        )

        self.canvas.place(x = 0, y = 0)
        self.text_1 = self.canvas.create_text(
            0.0,
            13.0,
            anchor="nw",
            text="Los datos se han guardado correctamente",
            fill="#000000",
            font=("UbuntuCondensed Regular", 32 * -1)
        )
        self.center_text(self.text_1)

        self.text_2 = self.canvas.create_text(
            0.0,
            63.0,
            anchor="nw",
            text="Los puedes encontrar en el siguiente directorio:",
            fill="#000000",
            font=("UbuntuCondensed Regular", 32 * -1)
        )
        self.center_text(self.text_2)

        self.button_image_1 = PhotoImage(
            file=self.relative_to_assets("button_7.png"))
        self.button_1 = Button(
            image=self.button_image_1,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.login_gateways_gui(),
            relief="flat"
        )
        self.button_1.place(
            x=337.0,
            y=539.0,
            width=126.0,
            height=25.0
        )

        self.text_3 = self.canvas.create_text(
            25.0,
            200.0,
            anchor="nw",
            text=f"{self.working_directory}",
            fill="#000000",
            font=("UbuntuCondensed Regular", 20 * -1)
        )
        self.center_text(self.text_1)

    def login_gateways_gui(self):
        self.clear_widgets()

        self.canvas = Canvas(
            self.window,
            bg = "#E8F0EE",
            height = 600,
            width = 800,
            bd = 0,
            highlightthickness = 0,
            relief = "ridge"
        )

        self.canvas.place(x = 0, y = 0)
        self.text_1 = self.canvas.create_text(
            0.0,
            25.0,
            anchor="nw",
            text="Introduce las credenciales del",
            fill="#000000",
            font=("UbuntuCondensed Regular", 32 * -1)
        )
        self.center_text(self.text_1)

        self.text_4 = self.canvas.create_text(
            0.0,
            50.0,
            anchor="nw",
            text="usuario de control de gateways",
            fill="#000000",
            font=("UbuntuCondensed Regular", 32 * -1)
        )
        self.center_text(self.text_4)

        self.text_2 = self.canvas.create_text(
            250.0,
            125.0,
            anchor="nw",
            text="Usuario",
            fill="#000000",
            font=("UbuntuCondensed Regular", 24 * -1)
        )
        self.center_text(self.text_2)

        self.entry_image_1 = PhotoImage(
            file=self.relative_to_assets("entry_1.png"))
        self.entry_bg_1 = self.canvas.create_image(
            400.0,
            175.5,
            image=self.entry_image_1
        )
        self.entry_1 = Entry(
            bd=0,
            bg="#D9D9D9",
            fg="#000716",
            highlightthickness=0,
            justify='center'
        )
        self.entry_1.place(
            x=212.5,
            y=163.0,
            width=375.0,
            height=23.0
        )

        self.text_3 = self.canvas.create_text(
            250.0,
            225.0,
            anchor="nw",
            text="Contraseña",
            fill="#000000",
            font=("UbuntuCondensed Regular", 24 * -1)
        )
        self.center_text(self.text_3)

        self.entry_image_2 = PhotoImage(
            file=self.relative_to_assets("entry_1.png"))
        self.entry_bg_2 = self.canvas.create_image(
            400.0,
            275.5,
            image=self.entry_image_2
        )
        self.entry_2 = Entry(
            bd=0,
            bg="#D9D9D9",
            fg="#000716",
            highlightthickness=0,
            justify='center',
            show="*"
        )
        self.entry_2.place(
            x=212.5,
            y=263.0,
            width=375.0,
            height=23.0
        )

        self.button_image_1 = PhotoImage(
            file=self.relative_to_assets("button_1.png"))
        self.button_1 = Button(
            image=self.button_image_1,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.gateways_api(),
            relief="flat"
        )
        self.button_1.place(
            x=350.0,
            y=325.0,
            width=100.0,
            height=25.0
        )
    
    def gateways_api(self):
        def gateways_api_thread():
            self.button_1.config(state="disabled")
            login_conf = self.api.validate_user_and_get_token(self.entry_1.get(), self.entry_2.get())
            if login_conf:
                self.filtered_gateways = self.api.get_gateways_from_user()
                self.data.save_gateways(self.filtered_gateways)
                self.window.after(0, self.gateways_selection())
            else:
                messagebox.showinfo(message="Credenciales no validas. Intentalo de nuevo.")
                self.entry_1.delete(0, END)
                self.entry_2.delete(0, END)
                self.button_1.config(state="active")
        
        gateways_thread = threading.Thread(target=gateways_api_thread)
        gateways_thread.start()

    def gateways_selection(self):
        def filter_elements(event=None):
            filter = self.entry_1.get().lower()
            filtered_names = [entry['name'] for entry in data if filter in entry['name'].lower()]
            self.listbox1.delete(0, tk.END)  # Limpiar la lista
            for name in filtered_names:
                self.listbox1.insert(tk.END, name)

        def add_selected():
            selected_text = self.listbox1.get(tk.ACTIVE)  # Obtener el texto del elemento activo seleccionado
            if selected_text:
                selected_index = next((index for index, entry in enumerate(data) if entry['name'] == selected_text), None)
                if selected_index is not None:
                    selected_entry = data[selected_index]
                    self.listbox2.insert(tk.END, selected_entry['name'])
                    self.listbox1.delete(selected_index)
                    data.pop(selected_index)
                    filter_elements()

        def save_all_selected():
            if not self.listbox2.size() > 0:
                messagebox.showinfo(message="No se han seleccionado gateways. Por favor, selecciona al menos uno.")
                print("No se han seleccionado elementos. Por favor, selecciona al menos uno.")
                return
            
            self.selected_entries = []
            for index in range(self.listbox2.size()):
                selected_text = self.listbox2.get(index)
                selected_entry = next((entry for entry in original_data if entry['name'] == selected_text), None)

                if selected_entry:
                    self.selected_entries.append(selected_entry)

            if not self.selected_entries:
                print("No se han encontrado elementos seleccionados en los datos originales.")
                return

            # Crear un nuevo JSON con los parámetros seleccionados
            self.data.save_selected_gateways(self.selected_entries)
            print(f"Se han guardado {len(self.selected_entries)} elementos en 'selectedGateways.json'.")

            self.gateways_info_progress_bar()

        self.clear_widgets()

        original_data = self.filtered_gateways

        # Realizar una copia profunda de los datos originales
        data = copy.deepcopy(original_data)

        self.canvas = Canvas(
            self.window,
            bg = "#E8F0EE",
            height = 600,
            width = 800,
            bd = 0,
            highlightthickness = 0,
            relief = "ridge"
        )

        self.canvas.place(x = 0, y = 0)
        self.text_1 = self.canvas.create_text(
            150.0,
            13.0,
            anchor="nw",
            text="Selecciona los gateways deseados",
            fill="#000000",
            font=("UbuntuCondensed Regular", 32 * -1)
        )
        self.center_text(self.text_1)

        self.entry_image_1 = PhotoImage(
            file=self.relative_to_assets("entry_2.png"))
        self.entry_bg_1 = self.canvas.create_image(
            400.0,
            87.5,
            image=self.entry_image_1
        )
        self.entry_1 = Entry(
            bd=0,
            bg="#D9D9D9",
            fg="#000716",
            highlightthickness=0,
            justify='center'
        )
        self.entry_1.place(
            x=337.5,
            y=75.0,
            width=125.0,
            height=23.0
        )
        self.entry_1.bind("<KeyRelease>", filter_elements)

        self.button_image_1 = PhotoImage(
            file=self.relative_to_assets("button_9.png"))
        self.button_1 = Button(
            image=self.button_image_1,
            borderwidth=0,
            highlightthickness=0,
            command=save_all_selected,
            relief="flat"
        )
        self.button_1.place(
            x=300.0,
            y=538.0,
            width=200.0,
            height=25.0
        )

        self.button_image_2 = PhotoImage(
            file=self.relative_to_assets("button_8.png"))
        self.button_2 = Button(
            image=self.button_image_2,
            borderwidth=0,
            highlightthickness=0,
            command=add_selected,
            relief="flat"
        )
        self.button_2.place(
            x=337.0,
            y=125.0,
            width=125.0,
            height=25.0
        )

        # Listbox 1 para mostrar todos los elementos
        self.scrollbar1 = Scrollbar(self.window, bg="#D9D9D9")
        self.listbox1 = Listbox(self.window, yscrollcommand=self.scrollbar1.set, bg="#D9D9D9")
        self.scrollbar1.config(command=self.listbox1.yview)
        self.listbox1.place(x=20, y=75, width=280, height=450)
        self.scrollbar1.place(x=300, y=75, height=450, width=20)

        for entry in data:
            self.listbox1.insert(tk.END, entry['name'])

        # Listbox 2 para los elementos seleccionados
        self.scrollbar2 = Scrollbar(self.window, bg="#D9D9D9")
        self.listbox2 = Listbox(self.window, yscrollcommand=self.scrollbar2.set, bg="#D9D9D9")
        self.scrollbar2.config(command=self.listbox2.yview)
        self.listbox2.place(x=480, y=75, width=280, height=450)
        self.scrollbar2.place(x=760, y=75, height=450, width=20)

    def gateways_info_progress_bar(self):
        self.clear_widgets()

        self.canvas = Canvas(
            self.window,
            bg = "#E8F0EE",
            height = 600,
            width = 800,
            bd = 0,
            highlightthickness = 0,
            relief = "ridge"
        )

        self.canvas.place(x = 0, y = 0)
        self.text_1 = self.canvas.create_text(
            0.0,
            13.0,
            anchor="nw",
            text=f"Vas a obtener los datos de {len(self.selected_entries)} gateways",
            fill="#000000",
            font=("UbuntuCondensed Regular", 32 * -1)
        )
        self.center_text(self.text_1)

        self.text_2 = self.canvas.create_text(
            200.0,
            350.0,
            anchor="nw",
            text="0.00%",
            fill="#000000",
            font=("UbuntuCondensed Regular", 24 * -1)
        )
        self.center_text(self.text_2)

        self.button_image_1 = PhotoImage(
            file=self.relative_to_assets("button_5.png"))
        self.button_1 = Button(
            image=self.button_image_1,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.gateways_info_api(),
            relief="flat"
        )
        self.button_1.place(
            x=337.0,
            y=539.0,
            width=126.0,
            height=25.0
        )

        self.text_3 = self.canvas.create_text(
            25.0,
            88.0,
            anchor="nw",
            text="* El tiempo de carga variara en funcion del número",
            fill="#000000",
            font=("UbuntuCondensed Regular", 24 * -1)
        )
        self.center_text(self.text_3)

        self.text_4 = self.canvas.create_text(
            25.0,
            113.0,
            anchor="nw",
            text="de gateways seleccionados",
            fill="#000000",
            font=("UbuntuCondensed Regular", 24 * -1)
        )
        self.center_text(self.text_4)

        self.progress_bar = ttk.Progressbar(self.window, orient="horizontal", length=600, mode="determinate")
        self.progress_bar["maximum"] = len(self.selected_entries)
        self.progress_bar.place(x=100, y=287)

    def gateways_info_api(self):
        def gateways_info_api_thread():
            self.button_1.config(state="disabled")
            self.api.get_gateways_info_web_scraping(self.selected_entries, self.update_gateways_info_progress_bar)
            self.window.after(0, self.graphics_creation_progress_bar())
        
        gateways_info_thread = threading.Thread(target=gateways_info_api_thread)
        gateways_info_thread.start()

    def update_gateways_info_progress_bar(self, valor_actual):
        self.progress_bar["value"] = valor_actual
        porcentaje = (valor_actual / len(self.selected_entries)) * 100
        self.canvas.itemconfig(self.text_2, text=f"{porcentaje:.2f}%")
        self.window.update_idletasks()  # Actualizar la interfaz gráfica

    def graphics_creation_progress_bar(self):
        self.clear_widgets()

        self.functions_to_call = 11

        self.canvas = Canvas(
            self.window,
            bg = "#E8F0EE",
            height = 600,
            width = 800,
            bd = 0,
            highlightthickness = 0,
            relief = "ridge"
        )

        self.canvas.place(x = 0, y = 0)
        self.text_1 = self.canvas.create_text(
            0.0,
            13.0,
            anchor="nw",
            text=f"Vas a generar gráficos con {len(self.selected_entries)} gateways y {len(self.deveui_set)} dispositivos",
            fill="#000000",
            font=("UbuntuCondensed Regular", 32 * -1)
        )
        self.center_text(self.text_1)

        self.text_2 = self.canvas.create_text(
            200.0,
            350.0,
            anchor="nw",
            text="0.00%",
            fill="#000000",
            font=("UbuntuCondensed Regular", 24 * -1)
        )
        self.center_text(self.text_2)

        self.button_image_1 = PhotoImage(
            file=self.relative_to_assets("button_5.png"))
        self.button_1 = Button(
            image=self.button_image_1,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.graphics_data(),
            relief="flat"
        )
        self.button_1.place(
            x=337.0,
            y=539.0,
            width=126.0,
            height=25.0
        )

        self.text_3 = self.canvas.create_text(
            25.0,
            88.0,
            anchor="nw",
            text="* La creación de los gráficos durará unos segundos",
            fill="#000000",
            font=("UbuntuCondensed Regular", 24 * -1)
        )
        self.center_text(self.text_3)

        self.progress_bar = ttk.Progressbar(self.window, orient="horizontal", length=600, mode="determinate")
        self.progress_bar["maximum"] = self.functions_to_call
        self.progress_bar.place(x=100, y=287)

    def update_graphics_creation_progress_bar(self, valor_actual):
        self.progress_bar["value"] = valor_actual
        porcentaje = (valor_actual / self.functions_to_call) * 100
        self.canvas.itemconfig(self.text_2, text=f"{porcentaje:.2f}%")
        self.window.update_idletasks()  # Actualizar la interfaz gráfica

    def graphics_data(self):
        def graphics_data_thread():
            self.button_1.config(state="disabled")
            self.data.generate_data_for_graphics(self.update_graphics_creation_progress_bar)
            self.data.generate_graphics(self.update_graphics_creation_progress_bar)
            self.window.after(0, self.finish_screen())
        
        gateways_data_thread = threading.Thread(target=graphics_data_thread)
        gateways_data_thread.start()

    def finish_screen(self):
        self.clear_widgets()

        self.canvas = Canvas(
            self.window,
            bg = "#E8F0EE",
            height = 600,
            width = 800,
            bd = 0,
            highlightthickness = 0,
            relief = "ridge"
        )

        self.canvas.place(x = 0, y = 0)
        self.text_1 = self.canvas.create_text(
            0.0,
            25.0,
            anchor="nw",
            text="Generación de gráficos finalizada",
            fill="#000000",
            font=("UbuntuCondensed Regular", 32 * -1)
        )
        self.center_text(self.text_1)

        self.text_2 = self.canvas.create_text(
            0.0,
            75.0,
            anchor="nw",
            text="¿Que desesas hacer ahora?",
            fill="#000000",
            font=("UbuntuCondensed Regular", 24 * -1)
        )
        self.center_text(self.text_2)

        self.text_3 = self.canvas.create_text(
            0.0,
            225.0,
            anchor="nw",
            text="Puedes volver al inicio y realizar otro análisis o",
            fill="#000000",
            font=("UbuntuCondensed Regular", 24 * -1)
        )
        self.center_text(self.text_3)

        self.text_4 = self.canvas.create_text(
            0.0,
            275.0,
            anchor="nw",
            text="realizar una comparativa entre diferentes análisis",
            fill="#000000",
            font=("UbuntuCondensed Regular", 24 * -1)
        )
        self.center_text(self.text_4)

        self.button_image_1 = PhotoImage(
            file=self.relative_to_assets("button_11.png"))
        self.button_1 = Button(
            image=self.button_image_1,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.setup_gui(),
            relief="flat"
        )
        self.button_1.place(
            x=350.0,
            y=350.0,
            width=100.0,
            height=25.0
        )

        self.button_image_2 = PhotoImage(
            file=self.relative_to_assets("button_12.png"))
        self.button_2 = Button(
            image=self.button_image_2,
            borderwidth=0,
            highlightthickness=0,
            command=self.window.destroy,
            relief="flat"
        )
        self.button_2.place(
            x=350.0,
            y=539.0,
            width=100.0,
            height=25.0
        )

        self.text_5 = self.canvas.create_text(
            25.0,
            464.0,
            anchor="nw",
            text="O puedes salir de la aplicación",
            fill="#000000",
            font=("UbuntuCondensed Regular", 24 * -1)
        )
        self.center_text(self.text_5)

    def select_number_of_paths(self):
        self.clear_widgets()

        def select_screen():
            # Obtener la opción seleccionada por el usuario
            self.options = self.var_opcion.get()
            
            # Dependiendo de la opción seleccionada, abrir la ventana correspondiente
            if self.options == 2:
                self.select_data_to_compare_screen_2()
            elif self.options == 3:
                self.select_data_to_compare_screen_3()

        self.canvas = Canvas(
            self.window,
            bg = "#E8F0EE",
            height = 600,
            width = 800,
            bd = 0,
            highlightthickness = 0,
            relief = "ridge"
        )

        self.canvas.place(x = 0, y = 0)
        self.text_1 = self.canvas.create_text(
            0.0,
            13.0,
            anchor="nw",
            text="Selecciona el número de análisis a comparar",
            fill="#000000",
            font=("UbuntuCondensed Regular", 32 * -1)
        )
        self.center_text(self.text_1)

        self.button_image_1 = PhotoImage(
            file=self.relative_to_assets("button_7.png"))
        self.button_1 = Button(
            image=self.button_image_1,
            borderwidth=0,
            highlightthickness=0,
            command=select_screen,
            relief="flat"
        )
        self.button_1.place(
            x=337.0,
            y=539.0,
            width=126.0,
            height=25.0
        )

        # Radiobuttons
        self.var_opcion = tk.IntVar(value=2)  # Variable para almacenar la opción seleccionada (Por defecto --> 2)
        self.opcion_2 = tk.Radiobutton(
            self.canvas,
            text="2 Variables",
            variable=self.var_opcion,
            value=2,
            background="#E8F0EE",
            font=("UbuntuCondensed Regular", 24 * -1)
        )
        self.opcion_2.place(
            x=300,
            y=200,
            width=200.0,
            height=25.0
        )

        self.opcion_3 = tk.Radiobutton(
            self.canvas,
            text="3 Variables",
            variable=self.var_opcion,
            value=3,
            background="#E8F0EE",
            font=("UbuntuCondensed Regular", 24 * -1)
        )
        self.opcion_3.place(
            x=300,
            y=250,
            width=200.0,
            height=25.0
        )

    def select_data_to_compare_screen_2(self):
        self. clear_widgets()

        def select_folder1():
            folder_path = filedialog.askdirectory()
            if folder_path:
                self.folder1_path.set(folder_path)
                self.folder1_path_str = folder_path
                print(self.folder1_path_str)

        def select_folder2():
            folder_path = filedialog.askdirectory()
            if folder_path:
                self.folder2_path.set(folder_path)
                self.folder2_path_str = folder_path
                print(self.folder2_path_str)

        # Variables para almacenar los paths de las carpetas seleccionadas
        self.folder1_path = tk.StringVar()
        self.folder2_path = tk.StringVar()

        self.canvas = Canvas(
            self.window,
            bg = "#E8F0EE",
            height = 600,
            width = 800,
            bd = 0,
            highlightthickness = 0,
            relief = "ridge"
        )

        self.canvas.place(x = 0, y = 0)
        self.text_1 = self.canvas.create_text(
            0.0,
            25.0,
            anchor="nw",
            text="Selecciona las carpetas a comparar (FromXX_ToYY)",
            fill="#000000",
            font=("UbuntuCondensed Regular", 32 * -1)
        )
        self.center_text(self.text_1)

        self.canvas.create_text(
            250.0,
            150.0,
            anchor="nw",
            text="Carpeta 1",
            fill="#000000",
            font=("UbuntuCondensed Regular", 24 * -1)
        )

        self.entry_image_1 = PhotoImage(
            file=self.relative_to_assets("entry_3.png"))
        self.entry_bg_1 = self.canvas.create_image(
            312.5,
            200.5,
            image=self.entry_image_1
        )
        self.entry_1 = Entry(
            bd=0,
            bg="#D9D9D9",
            fg="#000716",
            highlightthickness=0,
            textvariable=self.folder1_path
        )
        self.entry_1.place(
            x=62.5,
            y=188.0,
            width=500.0,
            height=23.0
        )

        self.button_image_1 = PhotoImage(
            file=self.relative_to_assets("button_10.png"))
        self.button_1 = Button(
            image=self.button_image_1,
            borderwidth=0,
            highlightthickness=0,
            command=select_folder1,
            relief="flat"
        )
        self.button_1.place(
            x=625.0,
            y=188.0,
            width=125.0,
            height=25.0
        )

        self.canvas.create_text(
            250.0,
            250.0,
            anchor="nw",
            text="Carpeta 2",
            fill="#000000",
            font=("UbuntuCondensed Regular", 24 * -1)
        )

        self.entry_image_2 = PhotoImage(
            file=self.relative_to_assets("entry_3.png"))
        self.entry_bg_2 = self.canvas.create_image(
            312.5,
            300.5,
            image=self.entry_image_2
        )
        self.entry_2 = Entry(
            bd=0,
            bg="#D9D9D9",
            fg="#000716",
            highlightthickness=0,
            textvariable=self.folder2_path
        )
        self.entry_2.place(
            x=62.5,
            y=288.0,
            width=500.0,
            height=23.0
        )

        self.button_image_2 = PhotoImage(
            file=self.relative_to_assets("button_10.png"))
        self.button_2 = Button(
            image=self.button_image_2,
            borderwidth=0,
            highlightthickness=0,
            command=select_folder2,
            relief="flat"
        )
        self.button_2.place(
            x=625.0,
            y=288.0,
            width=125.0,
            height=25.0
        )

        self.button_image_3 = PhotoImage(
            file=self.relative_to_assets("button_7.png"))
        self.button_3 = Button(
            image=self.button_image_3,
            borderwidth=0,
            highlightthickness=0,
            command=self.compare_graphics_progress_bar,
            relief="flat"
        )
        self.button_3.place(
            x=337.0,
            y=538.0,
            width=125.0,
            height=25.0
        )

    def compare_graphics_progress_bar(self):
        self.clear_widgets()

        self.functions_to_call = 4

        self.canvas = Canvas(
            self.window,
            bg = "#E8F0EE",
            height = 600,
            width = 800,
            bd = 0,
            highlightthickness = 0,
            relief = "ridge"
        )

        self.canvas.place(x = 0, y = 0)
        self.text_1 = self.canvas.create_text(
            0.0,
            13.0,
            anchor="nw",
            text=f"La creación de los gráficos durará unos segundos",
            fill="#000000",
            font=("UbuntuCondensed Regular", 32 * -1)
        )
        self.center_text(self.text_1)

        self.text_2 = self.canvas.create_text(
            200.0,
            350.0,
            anchor="nw",
            text="0.00%",
            fill="#000000",
            font=("UbuntuCondensed Regular", 24 * -1)
        )
        self.center_text(self.text_2)

        self.button_image_1 = PhotoImage(
            file=self.relative_to_assets("button_5.png"))
        self.button_1 = Button(
            image=self.button_image_1,
            borderwidth=0,
            highlightthickness=0,
            command=lambda: self.compare_graphics_data(),
            relief="flat"
        )
        self.button_1.place(
            x=337.0,
            y=539.0,
            width=126.0,
            height=25.0
        )

        self.progress_bar = ttk.Progressbar(self.window, orient="horizontal", length=600, mode="determinate")
        self.progress_bar["maximum"] = self.functions_to_call
        self.progress_bar.place(x=100, y=287)

    def compare_graphics_data(self):
        def compare_graphics_data_2_thread():
            self.button_1.config(state="disabled")
            self.data.create_comparison_directory_hierarchy_2(self.folder1_path_str, self.folder2_path_str)
            self.data.compare_graphics_2(self.update_compare_graphics_progress_bar)
            self.window.after(0, self.finish_screen())

        def compare_graphics_data_3_thread():
            self.button_1.config(state="disabled")
            self.data.create_comparison_directory_hierarchy_3(self.folder1_path_str, self.folder2_path_str, self.folder3_path_str)
            self.data.compare_graphics_3(self.update_compare_graphics_progress_bar)
            self.window.after(0, self.finish_screen())
        
        if self.options == 2:
            compare_gateways_data_thread = threading.Thread(target=compare_graphics_data_2_thread)
        elif self.options == 3:
            compare_gateways_data_thread = threading.Thread(target=compare_graphics_data_3_thread)

        compare_gateways_data_thread.start()

    def update_compare_graphics_progress_bar(self, valor_actual):
        self.progress_bar["value"] = valor_actual
        porcentaje = (valor_actual / self.functions_to_call) * 100
        self.canvas.itemconfig(self.text_2, text=f"{porcentaje:.2f}%")
        self.window.update_idletasks()  # Actualizar la interfaz gráfica

    def select_data_to_compare_screen_3(self):
        self. clear_widgets()

        def select_folder1():
            folder_path = filedialog.askdirectory()
            if folder_path:
                self.folder1_path.set(folder_path)
                self.folder1_path_str = folder_path

        def select_folder2():
            folder_path = filedialog.askdirectory()
            if folder_path:
                self.folder2_path.set(folder_path)
                self.folder2_path_str = folder_path

        def select_folder3():
            folder_path = filedialog.askdirectory()
            if folder_path:
                self.folder3_path.set(folder_path)
                self.folder3_path_str = folder_path

        # Variables para almacenar los paths de las carpetas seleccionadas
        self.folder1_path = tk.StringVar()
        self.folder2_path = tk.StringVar()
        self.folder3_path = tk.StringVar()

        self.canvas = Canvas(
            self.window,
            bg = "#E8F0EE",
            height = 600,
            width = 800,
            bd = 0,
            highlightthickness = 0,
            relief = "ridge"
        )

        self.canvas.place(x = 0, y = 0)
        self.text_1 = self.canvas.create_text(
            0.0,
            25.0,
            anchor="nw",
            text="Selecciona las carpetas a comparar (FromXX_ToYY)",
            fill="#000000",
            font=("UbuntuCondensed Regular", 32 * -1)
        )
        self.center_text(self.text_1)

        self.canvas.create_text(
            250.0,
            150.0,
            anchor="nw",
            text="Carpeta 1",
            fill="#000000",
            font=("UbuntuCondensed Regular", 24 * -1)
        )

        self.entry_image_1 = PhotoImage(
            file=self.relative_to_assets("entry_3.png"))
        self.entry_bg_1 = self.canvas.create_image(
            312.5,
            200.5,
            image=self.entry_image_1
        )
        self.entry_1 = Entry(
            bd=0,
            bg="#D9D9D9",
            fg="#000716",
            highlightthickness=0,
            textvariable=self.folder1_path
        )
        self.entry_1.place(
            x=62.5,
            y=188.0,
            width=500.0,
            height=23.0
        )

        self.button_image_1 = PhotoImage(
            file=self.relative_to_assets("button_10.png"))
        self.button_1 = Button(
            image=self.button_image_1,
            borderwidth=0,
            highlightthickness=0,
            command=select_folder1,
            relief="flat"
        )
        self.button_1.place(
            x=625.0,
            y=188.0,
            width=125.0,
            height=25.0
        )

        self.canvas.create_text(
            250.0,
            250.0,
            anchor="nw",
            text="Carpeta 2",
            fill="#000000",
            font=("UbuntuCondensed Regular", 24 * -1)
        )

        self.entry_image_2 = PhotoImage(
            file=self.relative_to_assets("entry_3.png"))
        self.entry_bg_2 = self.canvas.create_image(
            312.5,
            300.5,
            image=self.entry_image_2
        )
        self.entry_2 = Entry(
            bd=0,
            bg="#D9D9D9",
            fg="#000716",
            highlightthickness=0,
            textvariable=self.folder2_path
        )
        self.entry_2.place(
            x=62.5,
            y=288.0,
            width=500.0,
            height=23.0
        )

        self.button_image_2 = PhotoImage(
            file=self.relative_to_assets("button_10.png"))
        self.button_2 = Button(
            image=self.button_image_2,
            borderwidth=0,
            highlightthickness=0,
            command=select_folder2,
            relief="flat"
        )
        self.button_2.place(
            x=625.0,
            y=288.0,
            width=125.0,
            height=25.0
        )

        self.canvas.create_text(
            250.0,
            350.0,
            anchor="nw",
            text="Carpeta 3",
            fill="#000000",
            font=("UbuntuCondensed Regular", 24 * -1)
        )

        self.entry_image_3 = PhotoImage(
            file=self.relative_to_assets("entry_3.png"))
        self.entry_bg_3 = self.canvas.create_image(
            312.5,
            400.5,
            image=self.entry_image_3
        )
        self.entry_3 = Entry(
            bd=0,
            bg="#D9D9D9",
            fg="#000716",
            highlightthickness=0,
            textvariable=self.folder3_path
        )
        self.entry_3.place(
            x=62.5,
            y=388.0,
            width=500.0,
            height=23.0
        )

        self.button_image_3 = PhotoImage(
            file=self.relative_to_assets("button_10.png"))
        self.button_3 = Button(
            image=self.button_image_3,
            borderwidth=0,
            highlightthickness=0,
            command=select_folder3,
            relief="flat"
        )
        self.button_3.place(
            x=625.0,
            y=388.0,
            width=125.0,
            height=25.0
        )

        self.button_image_4 = PhotoImage(
            file=self.relative_to_assets("button_7.png"))
        self.button_4 = Button(
            image=self.button_image_4,
            borderwidth=0,
            highlightthickness=0,
            command=self.compare_graphics_progress_bar,
            relief="flat"
        )
        self.button_4.place(
            x=337.0,
            y=538.0,
            width=125.0,
            height=25.0
        )

    
