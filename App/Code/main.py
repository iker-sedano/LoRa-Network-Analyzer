import tkinter as tk
from gui_module import MainApplication
from api_module import OrbiwiseAPI
from data_module import DataAnalysis

def main():
    root = tk.Tk()
    data = DataAnalysis()
    api = OrbiwiseAPI(data)
    app = MainApplication(root, api, data)
    root.mainloop()

if __name__ == "__main__":
    main()
