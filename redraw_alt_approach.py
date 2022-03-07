import time
from main_backend import Backend
import PySimpleGUI
import PySimpleGUI as sg
import copy


class WindozeManager:
    def __init__(self):
        self.FRAME_SIZE = None
        self.window = None

        self.layout_dict = {}  # keys are frame coords, values are the frames (with appropriate content)
        # this will be 'listified' to create the layout for each iteration

        self.printer_data = {}
        self.printer_frames = {}

        self.backend = None

    def __del__(self):
        if self.window:
            self.window.close()

    def setup(self):

        loading_layout = [[sg.VStretch()], [sg.Stretch(), sg.Text("Loading, please wait"), sg.Stretch()], [sg.VStretch()]]
        loading_window = sg.Window("Loading Print Server", loading_layout, resizable=False)
        loading_window.finalize()
        loading_window.maximize()
        loading_window.read(timeout=10)
        loading_window.read(timeout=10)

        """ Get screen size and compute dimensions """
        screen_size = loading_window.size

        self.backend = Backend("Ultimaker")
        self.printers_update()

    def printers_update(self):
        # placeholders:
        self.printer_data["KEITH"] = {"STATUS": "AVAILABLE", "OTHER_DEETS": None}
        self.printer_data["PAM"] = {"STATUS": "PRINTING", "OTHER_DEETS": None}
        self.printer_data["ROB"] = {"STATUS": "FINISHED", "OTHER_DEETS": None}
        self.printer_data["SARAH"] = {"STATUS": "OFFLINE", "OTHER_DEETS": None}

        for name in self.printer_data.keys():
            self.printers[name] = self.printer_frames(name)

        # TODO: update displayed printer details

    def printer_frames(self, name):
        status_list = ["PRINTING", "AVAILABLE", "FINISHED", "OFFLINE", "UNKNOWN"]
        frames = {}
        for status in status_list:
            frames[status] = self.state_frame(name, status)
        return frames

    def state_frame(self, printer_name, status):
        printer_name = printer_name.upper()
        status = status.upper()

        frame_layout = [
            [sg.Stretch(), sg.Text(f"{printer_name.capitalize()} | {status.capitalize()}"), sg.Stretch()]]

        if status == "AVAILABLE":
            # # add big print button
            # button_size = [0, 0]
            # button_size[0] = int(self.FRAME_SIZE[0] * 0.08)  # x scaling
            # button_size[1] = int(self.FRAME_SIZE[1] * 0.04)  # y scaling
            # print(button_size)
            layout_addition = [
                [sg.VStretch()],
                [sg.Stretch(), sg.Button("Print", key=f"{printer_name.upper()}_PRINT"), sg.Stretch()],
                [sg.VStretch()]]
        elif status == "PRINTING":
            # add running status, filename, temps, progress, cancel
            bar_size = [0, 0]
            bar_size[0] = int(self.FRAME_SIZE[0] * 0.75)  # x scaling
            bar_size[1] = int(self.FRAME_SIZE[1] * 0.05)  # y scaling

            # TODO: get filename and progress from `other_deets`
            filename = "allthegecks.gcode"
            progress = 69.420  # used in element updates
            temp = {"EX": 420.420, "BED": 69.69}
            eta = "4:20:69"  # ;)

            layout_addition = [
                [sg.VStretch()],
                [sg.Stretch(), sg.Text(f"{filename}"), sg.Stretch()],
                [sg.VStretch()],
                [sg.Stretch(), sg.Text("T_ex: "), sg.Text(f"{temp['EX']}", key=f"{printer_name}_T_EX"), sg.Stretch(), sg.Text("T_BED: "), sg.Text(f"{temp['BED']}", key=f"{printer_name}_T_BED"), sg.Stretch()],
                [sg.VStretch()],
                [sg.Stretch(), sg.Text("ETA: "), sg.Text(f"{eta}", key=f"{printer_name}_ETA"), sg.Stretch(), sg.Button("Cancel", key=f"{printer_name}_CANCEL"), sg.Stretch()],
                [sg.VStretch()],
                [sg.Stretch(), sg.ProgressBar(max_value=100, orientation='h', size_px=bar_size, key=f"{printer_name}_PROGBAR"), sg.Stretch()],
                [sg.VStretch()]
            ]
        elif status == "FINISHED":
            # add filename, success dialogue
            button_size = [0, 0]
            button_size[0] = int(self.FRAME_SIZE[0] * 0.03)  # x scaling
            button_size[1] = int(self.FRAME_SIZE[1] * 0.015)  # y scaling

            # TODO: get filename and progress from `other_deets`
            filename = "allthegecks.gcode"
            progress = 69.420  # used in element updates
            temp = {"EX": 420.420, "BED": 69.69}
            eta = "4:20:69"  # ;)

            layout_addition = [
                [sg.VStretch()],
                [sg.Stretch(), sg.Text(f"Finished: {filename}"), sg.Stretch()],
                [sg.VStretch()],
                [sg.Stretch(), sg.Text(f"Was this print successful?"), sg.Stretch()],
                [sg.VStretch()],
                [sg.Stretch(), sg.Button("SUCCESS", key=f"{printer_name.upper()}_SUCCESS", size=tuple(button_size)), sg.Stretch(), sg.Button("FAIL", key=f"{printer_name.upper()}_FAIL", size=tuple(button_size)), sg.Stretch()],
                [sg.VStretch()]]
        elif status == "OFFLINE":
            # add big reconnect button
            button_size = [0,0]
            button_size[0] = int(self.FRAME_SIZE[0] * 0.08)  # x scaling
            button_size[1] = int(self.FRAME_SIZE[1] * 0.04)  # y scaling
            print(button_size)
            layout_addition = [
                [sg.VStretch()],
                [sg.Stretch(), sg.Button("Reconnect", key=f"{printer_name.upper()}_RECONNECT", size=tuple(button_size)), sg.Stretch()],
                [sg.VStretch()]]
        else:
            layout_addition = [sg.Stretch(), sg.Text('Layout Error, please notify system administrator'), sg.Stretch()]

        for elem in layout_addition:
            frame_layout.append(elem)

        return sg.Frame(printer_name.capitalize(), frame_layout, size=self.FRAME_SIZE)

    def layout_update(self):
        available_slot_coords = [coord for row in self.layout_dict["order"] for coord in row]
        available_slot_coords.reverse()
        for printer in self.printer_frames.keys():
            self.layout_dict[available_slot_coords.pop()] = self.printer_frames[printer]

    def layout_make(self):
        new_layout = []

        for row in self.layout_dict["order"]:
            new_layout.append([])
            for key in row:
                new_layout[-1].append(self.layout_dict[key])

        return new_layout

    def redraw(self, new_layout=None):
        print("make")
        if not new_layout:
            new_layout = self.layout_make()

        new_window = sg.Window("Test window2", copy.deepcopy(new_layout), resizable=False)
        new_window.finalize()
        new_window.maximize()
        new_window.read(timeout=10)
        new_window.read(timeout=10)  # ensure fully updated (some oddities in testing)

        if self.window:
            print("bin")
            self.window.close()

        self.window = new_window  # transfer to class variable
        del new_window  # force tidy, just in case

        self.window_update()

    def window_update(self):
        """ update progress bars and text etc without needing to refresh layour """
        pam_progress = 69.420
        if type(self.window.find_element("PAM_PROGBAR", silent_on_error=True)) is PySimpleGUI.ProgressBar:
            self.window["PAM_PROGBAR"].update(current_count=int(pam_progress))

    def read(self, time_out=None):
        return self.window.read(timeout=time_out)

    # def


if __name__ == "__main__":
    """
    colours:
        background: #565656
    """
    sg.theme("Dark")

    wm = WindozeManager()

    wm.setup()
    time.sleep(1)
    wm.layout_update()
    wm.redraw()

    while True:
        event, values = wm.read()

        print(event, values)

        if event == sg.WIN_CLOSED:
            break

        if event.split('_')[-1] == "CANCEL":
            wm.redraw()

    # layout = []
    # for j in range(WINDOW_TILES[1]):
    #     row = []
    #     for i in range(WINDOW_TILES[0]):
    #         row.append(sg.Frame(f"Printer:{i}.{j}", layout=wm.gen_printer_frame(f"Printer:{i},{j}", "idle"), size=FRAME_SIZE,
    #                             key=f"printer_{i}_{j}"))
    #     layout.append(row)
    #
    # window = wm.redraw(copy.deepcopy(layout), temp_window)
    #
    # while True:  # event loop
    #     event, values = window.read()
    #     print(event, values)
    #     print(window.size)
    #
    #     if event == sg.WIN_CLOSED:
    #         break
    #
    #     if event[:4] == "butt":
    #         window = wm.redraw(copy.deepcopy(layout), window)
    #
    # window.close()
