from main_backend import Backend
import PySimpleGUI as sg


class WindozeManager:
    def __init__(self):
        init_layout = [[sg.VStretch()], [sg.Stretch(), sg.Text("Loading, please wait"), sg.Stretch()], [sg.VStretch()]]

        loading_window = sg.Window("Loading Window", init_layout, resizable=False)
        loading_window.finalize()
        loading_window.maximize()
        loading_window.read(timeout=10)
        loading_window.read(timeout=10)  # ensure fully updated (some oddities in testing)

        self.backend = Backend()
        # TODO: loading things

