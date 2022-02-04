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

    def setup(self, WINDOW_FRAME_X_Y=(2, 2)):

        """ Make loading screen """
        self.FRAME_TILING_X_Y = WINDOW_FRAME_X_Y

        init_layout = [[sg.VStretch()], [sg.Stretch(), sg.Text("Loading, please wait"), sg.Stretch()], [sg.VStretch()]]

        wm.redraw(init_layout)

        """ Get screen size and compute dimensions """
        x, y = self.window.size

        WINDOW_BORDER = (8 + 5 * self.FRAME_TILING_X_Y[0],
                         8 + int(3.5 * self.FRAME_TILING_X_Y[1]))  # forumlas by trial and error - 1080p & 1440p (16:9)
        self.FRAME_SIZE = [(x - 2 * WINDOW_BORDER[0]) / self.FRAME_TILING_X_Y[0],
                           (y - 2 * WINDOW_BORDER[1]) / self.FRAME_TILING_X_Y[1]]

        """ Setup dictionary for dynamically managing the layout """
        self.layout_dict["order"] = []
        for row_number in range(self.FRAME_TILING_X_Y[1]):
            self.layout_dict["order"].append([])
            for col_number in range(self.FRAME_TILING_X_Y[0]):
                self.layout_dict[f"{col_number},{row_number}"] = None
                self.layout_dict["order"][-1].append(f"{col_number},{row_number}")

        self.backend = Backend()
        self.printers_update()

    def printers_update(self):
        # TODO: load printer data to `printer_data`
        # for printer in self.backend.fleet.printer_access.keys():
        #     window[f"{printer} status"].update(backend.fleet.printers[printer]['status'])
        #     if self.backend.fleet.printers[printer]['status'] != "offline":
        #         self.printer_data[f"{printer.upper()}"] = {}
        #
        #
        #         # print(backend.fleet.printers[printer])
        #         self.window[f"{printer} temps"].update(
        #             f"Bed: {self.backend.fleet.printers[printer]['details']['status']['temperature']['bed']['actual']}/{backend.fleet.printers[printer]['details']['status']['temperature']['bed']['target']}, Tool: {backend.fleet.printers[printer]['details']['status']['temperature']['tool0']['actual']}/{backend.fleet.printers[printer]['details']['status']['temperature']['tool0']['target']}")
        #         window[f"{printer} job"].update(
        #             f"{self.backend.fleet.printers[printer]['details']['job_info']['job']['file']['printer_name']}")
        #         window[f"{printer} progress"].update(
        #             f"{self.backend.fleet.printers[printer]['details']['job_info']['progress']['completion'] or 0:.1f}% complete, {str(datetime.timedelta(seconds=backend.fleet.printers[printer]['details']['job_info']['progress']['printTimeLeft'] or 0))} remaining")
        #     else:
        #         window[f"{printer} temps"].update("N/A")
        #         window[f"{printer} job"].update("N/A")
        #         window[f"{printer} progress"].update("N/A")

        # placeholders:
        self.printer_data["KEITH"] = {"STATUS": "IDLE", "OTHER_DEETS": None}
        self.printer_data["PAM"] = {"STATUS": "RUNNING", "OTHER_DEETS": None}
        self.printer_data["ROB"] = {"STATUS": "FINISHED", "OTHER_DEETS": None}
        self.printer_data["SARAH"] = {"STATUS": "OFFLINE", "OTHER_DEETS": None}

        for name in self.printer_data.keys():
            self.printer_frames[name] = self.printer_frame(name,
                                                           self.printer_data[name]["STATUS"],
                                                           self.printer_data[name]["OTHER_DEETS"])

        # TODO: update displayed printer details

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

    def printer_frame(self, printer_name, status, other_deets=None):  # TODO: other_deets
        printer_name = printer_name.upper()
        status = status.upper()

        assert self.FRAME_SIZE is not None

        frame_layout = [
            [sg.Stretch(), sg.Text(f"{printer_name.capitalize()} | {status.capitalize()}"), sg.Stretch()]]

        if status == "IDLE":
            # add big print button
            button_size = [0, 0]
            button_size[0] = int(self.FRAME_SIZE[0] * 0.08)  # x scaling
            button_size[1] = int(self.FRAME_SIZE[1] * 0.04)  # y scaling
            print(button_size)
            layout_addition = [
                [sg.VStretch()],
                [sg.Stretch(), sg.Button("Print", key=f"{printer_name.upper()}_PRINT", size=tuple(button_size)), sg.Stretch()],
                [sg.VStretch()]]
        elif status == "RUNNING":
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
