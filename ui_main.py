import PySimpleGUI as sg
from main_backend import Backend
import ui_passcode
import ui_start_print
import ui_finish_print
import datetime
import time

MASTER_PASSCODE = "69420"  # TODO: actually set something in secrets xD
# TODO: match safe code: 436743

TIMEOUT = 300

PRINTER_COLS = 2


def main():
    sg.theme("Dark Blue 12")
    sg.DEFAULT_FONT = ("Helvetica", 18)

    temp_layout = [
        [sg.VStretch()],
        [sg.Stretch(), sg.Text('iForge 3D Print Automation System', justification='center', font=(24)), sg.Stretch()],
        [sg.Stretch(), sg.Text('Loading...'), sg.Stretch()],
        [sg.VStretch()]]

    temp_window = sg.Window("Loading",
                            temp_layout,
                            resizable=False)
    temp_window.finalize()
    temp_window.maximize()
    temp_window.read(timeout=20)
    temp_window.read(timeout=20)

    backend = Backend("Ultimaker")

    printer_layout = [[]]
    col_counter = 0
    frame_dict = {}
    for printer in backend.printers.keys():
        # states = ["available", "printing", "finished", "offline", "unknown"]
        # for state in states:
        available_layout = [[sg.T(f"{printer} | available")],
                            [sg.B(f"print", key=f"{printer}_print")]
                            ]

        filename = "allthegecks.gcode"
        progress = 69.420  # used in element updates
        temp = {"ex": 420.420, "bed": 69.69}
        eta = "4:20:69"

        printing_layout = [[sg.T(f"{printer} | printing")],
                           [sg.Text(f"{filename}")],
                           [sg.Text("t_ex: "), sg.Text(f"{temp['ex']}", key=f"{printer}_t_ex"), sg.Text("t_bed: "),
                            sg.Text(f"{temp['bed']}", key=f"{printer}_t_bed")],
                           [sg.Text("eta: "), sg.Text(f"{eta}", key=f"{printer}_eta"),
                            sg.Button("cancel", key=f"{printer}_cancel")],
                           [sg.ProgressBar(max_value=100, orientation='h', key=f"{printer}_progbar")],
                           ]

        finished_layout = [[sg.T(f"{printer} | finished")],
                           [sg.Text(f"finished: {filename}")],
                           [sg.Text(f"Was this print successful?")],
                           [sg.Button("success", key=f"{printer.lower()}_success"),
                            sg.Button("fail", key=f"{printer.lower()}_fail")]
                           ]

        offline_layout = [[sg.T(f"{printer} | offline")],
                          [sg.Button("reconnect", key=f"{printer.lower()}_reconnect")]]

        unknown_layout = [[sg.T(f"{printer} | unknown")],
                          [sg.Text('status unknown, please notify system administrator')]]

        frame_dict[printer] = {
            "available": sg.Frame(f"{printer.capitalize()}", available_layout, visible=False,
                                  key=f"{printer}_frame_available"),
            "printing": sg.Frame(f"{printer.capitalize()}", printing_layout, visible=False,
                                 key=f"{printer}_frame_printing"),
            "finished": sg.Frame(f"{printer.capitalize()}", finished_layout, visible=False,
                                 key=f"{printer}_frame_finished"),
            "offline": sg.Frame(f"{printer.capitalize()}", offline_layout, visible=False,
                                key=f"{printer}_frame_offline"),
            "unknown": sg.Frame(f"{printer.capitalize()}", unknown_layout, visible=False,
                                key=f"{printer}_frame_unknown")
        }

    layout = [
        [sg.Text('iForge 3D Print Automation System', justification='center', expand_x=True)],
        [sg.pin(frame_dict["keith"]["available"]),
         sg.pin(frame_dict["keith"]["printing"]),
         sg.pin(frame_dict["keith"]["finished"]),
         sg.pin(frame_dict["keith"]["offline"]),
         sg.pin(frame_dict["keith"]["unknown"]),
         sg.pin(frame_dict["pam"]["available"]),
         sg.pin(frame_dict["pam"]["printing"]),
         sg.pin(frame_dict["pam"]["finished"]),
         sg.pin(frame_dict["pam"]["offline"]),
         sg.pin(frame_dict["pam"]["unknown"])],
        [sg.pin(frame_dict["rob"]["available"]),
         sg.pin(frame_dict["rob"]["printing"]),
         sg.pin(frame_dict["rob"]["finished"]),
         sg.pin(frame_dict["rob"]["offline"]),
         sg.pin(frame_dict["rob"]["unknown"]),
         sg.pin(frame_dict["sarah"]["available"]),
         sg.pin(frame_dict["sarah"]["printing"]),
         sg.pin(frame_dict["sarah"]["finished"]),
         sg.pin(frame_dict["sarah"]["offline"]),
         sg.pin(frame_dict["sarah"]["unknown"])],
    ]

    temp_window.close()

    window = sg.Window('iForge Printer Control',
                       layout,
                       element_justification="center",
                       resizable=True
                       )
    window.finalize()
    window.maximize()

    logout_timer = time.time()

    # This is an Event Loop
    while True:
        window.bring_to_front()
        event, values = window.read(timeout=1000)

        if event in (None, 'Exit'):
            print("[LOG] Clicked Exit!")
            break

        # No-event update
        backend.update()
        joblist = backend.queue.get_jobs()
        for printer in backend.printers.keys():
            if not window[f"{printer}_frame_{backend.printers[printer]['details']['state']}"].visible:
                for state in ["available", "printing", "finished", "offline", "unknown"]:
                    window[f"{printer}_frame_{state}"].update(visible=False)
                try:
                    window[f"{printer}_frame_{backend.printers[printer]['details']['state']}"].update(visible=True)
                except KeyError:
                    window[f"{printer}_frame_unknown"].update(visible=True)

            # if backend.fleet.printers[printer]['status'] != "offline":
            #     # print(backend.fleet.printers[printer])
            #     window[f"{printer} temps"].update(
            #         f"Bed: {backend.fleet.printers[printer]['details']['status']['temperature']['bed']['actual']}/{backend.fleet.printers[printer]['details']['status']['temperature']['bed']['target']}, Tool: {backend.fleet.printers[printer]['details']['status']['temperature']['tool0']['actual']}/{backend.fleet.printers[printer]['details']['status']['temperature']['tool0']['target']}")
            #     window[f"{printer} job"].update(
            #         f"{backend.fleet.printers[printer]['details']['job_info']['job']['file']['printer_name']}")
            #     window[f"{printer} progress"].update(
            #         f"{backend.fleet.printers[printer]['details']['job_info']['progress']['completion'] or 0:.1f}% complete, {str(datetime.timedelta(seconds=backend.fleet.printers[printer]['details']['job_info']['progress']['printTimeLeft'] or 0))} remaining")
            # else:
            #     window[f"{printer} temps"].update("N/A")
            #     window[f"{printer} job"].update("N/A")
            #     window[f"{printer} progress"].update("N/A")

            if joblist.shape[0] > 0:
                window[f"{printer}_print"].update(disabled=False)
            else:
                window[f"{printer}_print"].update(disabled=True)

        # Event handling
        if event.split("_")[-1] == "print":
            print(f"printing on {event.split('_')[0]}")

        # Event handling
        if event.split("_")[-1] == "finish":
            print(f"finishing on {event.split('_')[0]}")

        if event not in (sg.TIMEOUT_EVENT, sg.WIN_CLOSED):
            print('Event = ', event)
            print('Values Dictionary (key = value):')
            for key in values:
                print(key, ' = ', values[key])

        if event not in (sg.TIMEOUT_EVENT,):
            logout_timer = time.time()
        else:
            if time.time() - logout_timer > TIMEOUT:
                print("[LOG] Timed out! Eggo.")
                break

    window.close()


if __name__ == '__main__':
    while True:
        if ui_passcode.main(MASTER_PASSCODE):
            main()
        else:
            break
