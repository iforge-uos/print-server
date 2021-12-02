import PySimpleGUI as sg
from main_backend import Backend
import ui_passcode
import ui_start_print
import datetime
import time

MASTER_PASSCODE = "69420"  # TODO: actually set something in secrets xD

TIMEOUT = 300

PRINTER_COLS = 2


def main():
    sg.theme("Dark Blue 12")

    temp_layout = [[sg.Text('iForge 3D Print Automation System', justification='center', font=("Helvetica", 16))],
                   [sg.Text('Loading...')]]

    temp_window = sg.Window("Loading",
                            temp_layout,
                            no_titlebar=True)
    temp_window.finalize()
    temp_window.maximize()

    backend = Backend()

    printer_layout = [[]]
    col_counter = 0
    for printer in backend.fleet.printer_access.keys():
        frame_layout = [[sg.T("Status:", size=(10, 1), justification="right"),
                         sg.T("Loading...", key=f"{printer} status", size=(38, 1))
                         ],
                        [sg.T("Temperature:", size=(10, 1), justification="right"),
                         sg.T("Loading...", key=f"{printer} temps", size=(38, 1))
                         ],
                        [sg.T("Job:", size=(10, 1), justification="right"),
                         sg.T("Loading...", key=f"{printer} job", size=(38, 1))
                         ],
                        [sg.T("Progress:", size=(10, 1), justification="right"),
                         sg.T("Loading...", key=f"{printer} progress", size=(38, 1))
                         ],
                        # [sg.B("Start Print", key=f"{printer} start", disabled=True, size=(16, 1)),
                        #  sg.B("Finish Print", key=f"{printer} finish", disabled=True, size=(16, 1)),
                        #  sg.B("Settings", key=f"{printer} settings", disabled=True, size=(16, 1))
                        #  ],
                        ]
        if col_counter < PRINTER_COLS:
            col_counter += 1
            printer_layout[-1].append(sg.Frame(printer, frame_layout, key=f"{printer} frame"))
        else:
            printer_layout.append([sg.Frame(printer, frame_layout, key=f"{printer} frame")])
            col_counter = 1

    layout = [
        [sg.Text('iForge 3D Print Automation System', justification='center', font=("Helvetica", 16), expand_x=True)],
        [sg.Frame("Printers", key="printer_frame", layout=printer_layout, expand_x=True)],
        [sg.B("Start Print", key=f"start", disabled=True, size=(16, 1)),
         sg.B("Finish Print", key=f"finish", disabled=True, size=(16, 1)),
         sg.B("Settings", key=f"settings", disabled=True, size=(16, 1)),
         sg.B('Exit', size=(16, 1)),
         ],
    ]

    temp_window.close()

    window = sg.Window('iForge Printer Control',
                       layout,
                       element_justification="center",
                       no_titlebar=True)
    window.finalize()
    window.maximize()

    logout_timer = time.time()

    # This is an Event Loop
    while True:
        window.bring_to_front()
        event, values = window.read(timeout=1000)
        backend.update()
        # print(event)

        if event in (None, 'Exit'):
            print("[LOG] Clicked Exit!")
            break

        # No-event update
        for printer in backend.fleet.printer_access.keys():
            window[f"{printer} status"].update(backend.fleet.printers[printer]['status'])
            if backend.fleet.printers[printer]['status'] != "offline":
                # print(backend.fleet.printers[printer])
                window[f"{printer} temps"].update(
                    f"Bed: {backend.fleet.printers[printer]['details']['status']['temperature']['bed']['actual']}/{backend.fleet.printers[printer]['details']['status']['temperature']['bed']['target']}, Tool: {backend.fleet.printers[printer]['details']['status']['temperature']['tool0']['actual']}/{backend.fleet.printers[printer]['details']['status']['temperature']['tool0']['target']}")
                window[f"{printer} job"].update(
                    f"{backend.fleet.printers[printer]['details']['job_info']['job']['file']['name']}")
                window[f"{printer} progress"].update(
                    f"{backend.fleet.printers[printer]['details']['job_info']['progress']['completion'] or 0:.1f}% complete, {str(datetime.timedelta(seconds=backend.fleet.printers[printer]['details']['job_info']['progress']['printTimeLeft'] or 0))} remaining")
            else:
                window[f"{printer} temps"].update("N/A")
                window[f"{printer} job"].update("N/A")

        joblist = backend.queue.get_jobs()
        if joblist.shape[0] > 0 and len(backend.printer_status_dict["available"]) > 0:
            window["start"].update(disabled=False)
        else:
            window["start"].update(disabled=True)

        # Event handling
        if event == "start":
            ui_start_print.main(backend)

        # if event not in (sg.TIMEOUT_EVENT, sg.WIN_CLOSED):
        #     print('Event = ', event)
        #     print('Values Dictionary (key = value):')
        #     for key in values:
        #         print(key, ' = ', values[key])

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
