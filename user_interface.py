import PySimpleGUI as sg
from main import Backend
import interface_passcode
import datetime

MASTER_PASSCODE = "69420"


def make_window(theme):
    sg.theme(theme)

    # Table Data
    data = [["John", 10], ["Jen", 5]]
    headings = ["Name", "Score"]

    printer_layout = [[]]

    main_layout = [[sg.Text('Header')],
                   [sg.Frame("Printers", key="printer_frame", layout=printer_layout)],
                   # [sg.Input(key='-INPUT-')],
                   # [sg.Slider(orientation='h', key='-SKIDER-'),
                   #  sg.Image(data=sg.DEFAULT_BASE64_LOADING_GIF, enable_events=True, key='-GIF-IMAGE-'),],
                   # [sg.Checkbox('Checkbox', default=True, k='-CB-')],
                   # [sg.Radio('Radio1', "RadioDemo", default=True, size=(10, 1), k='-R1-'),
                   #  sg.Radio('Radio2', "RadioDemo", default=True, size=(10, 1), k='-R2-')],
                   # [sg.Combo(values=('Combo 1', 'Combo 2', 'Combo 3'), default_value='Combo 1', readonly=True,
                   #           k='-COMBO-'),
                   #  sg.OptionMenu(values=('Option 1', 'Option 2', 'Option 3'), k='-OPTION MENU-'), ],
                   # [sg.Spin([i for i in range(1, 11)], initial_value=10, k='-SPIN-'), sg.Text('Spin')],
                   # [sg.Multiline(
                   #     'Demo of a Multi-Line Text Element!\nLine 2\nLine 3\nLine 4\nLine 5\nLine 6\nLine 7\nYou get the point.',
                   #     size=(45, 5), k='-MLINE-')],
                   # [sg.Button('Button'), sg.Button('Popup'),
                   #  sg.Button(image_data=sg.DEFAULT_BASE64_ICON, key='-LOGO-')]
                   ]

    finish_layout = [[sg.T('Anything that you would use for asthetics is in this tab!')],
                     [sg.Image(data=sg.DEFAULT_BASE64_ICON, k='-IMAGE-')],
                     [sg.ProgressBar(1000, orientation='h', size=(20, 20), key='-PROGRESS BAR-'),
                      sg.Button('Test Progress bar')]]

    start_layout = [[sg.Text("Start print from queue")],
                    [sg.Table(values=data, headings=headings, max_col_width=25,
                              auto_size_columns=True,
                              display_row_numbers=True,
                              justification='right',
                              # num_rows=2,
                              key='-TABLE-',
                              row_height=25)]]

    maintenance_layout = [[sg.T('Printer Maintenance Options')],
                          [sg.OptionMenu(values=("1", "2"), k='maintenance_printer_choice')],
                          [sg.Image(data=sg.DEFAULT_BASE64_ICON, k='-IMAGE-')],
                          [sg.ProgressBar(1000, orientation='h', size=(20, 20), key='-PROGRESS BAR-'),
                           sg.Button('Test Progress bar')]]

    layout = [[sg.Text('iForge 3D Print Automation System', size=(38, 1),
                       justification='center', font=("Helvetica", 16),
                       key='-TEXT HEADING-', enable_events=True)]]
    layout += [[sg.TabGroup([[sg.Tab('Main', main_layout),
                              sg.Tab('Finished Prints', finish_layout),
                              sg.Tab('Start Print', start_layout),
                              sg.Tab('Maintenance', maintenance_layout)]],
                            key='-TAB GROUP-')]]

    return sg.Window('iForge Printer Control', layout)


def main():
    sg.theme("Dark Blue 12")

    temp_layout = [[sg.Text('iForge 3D Print Automation System', justification='center', font=("Helvetica", 16))],
                   [sg.Text('Loading...')]]

    temp_window = sg.Window("Loading", temp_layout)
    temp_window.finalize()

    backend = Backend()

    printer_layout = []
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
                        [sg.B("Start Print", key=f"{printer} start", disabled=True, size=(16, 1)),
                         sg.B("Finish Print", key=f"{printer} finish", disabled=True, size=(16, 1)),
                         sg.B("Settings", key=f"{printer} settings", disabled=True, size=(16, 1))
                         ]
                        ]
        printer_layout.append([sg.Frame(printer, frame_layout, expand_x=True, key=f"{printer} frame")])

    layout = [[sg.Text('iForge 3D Print Automation System', justification='center', font=("Helvetica", 16))],
              [sg.B('Exit')],
              [sg.Frame("Printers", key="printer_frame", layout=printer_layout, expand_x=True)],
              ]

    temp_window.close()

    window = sg.Window('iForge Printer Control', layout)
    window.finalize()

    # This is an Event Loop
    while True:
        event, values = window.read(timeout=1000)
        backend.update()
        # print(event)

        for printer in backend.fleet.printer_access.keys():
            window[f"{printer} status"].update(backend.fleet.printers[printer]['status'])
            if backend.fleet.printers[printer]['status'] != "offline":
                print(backend.fleet.printers[printer])
                window[f"{printer} temps"].update(
                    f"Bed: {backend.fleet.printers[printer]['details']['status']['temperature']['bed']['actual']}/{backend.fleet.printers[printer]['details']['status']['temperature']['bed']['target']}, Tool: {backend.fleet.printers[printer]['details']['status']['temperature']['tool0']['actual']}/{backend.fleet.printers[printer]['details']['status']['temperature']['tool0']['target']}")
                window[f"{printer} job"].update(
                    f"{backend.fleet.printers[printer]['details']['job_info']['job']['file']['name']}")
                window[f"{printer} progress"].update(
                    f"{backend.fleet.printers[printer]['details']['job_info']['progress']['completion'] or 0:.1f}% complete, {str(datetime.timedelta(seconds=backend.fleet.printers[printer]['details']['job_info']['progress']['printTimeLeft'] or 0))} remaining")
            else:
                window[f"{printer} temps"].update("N/A")
                window[f"{printer} job"].update("N/A")

        # if event not in (sg.TIMEOUT_EVENT, sg.WIN_CLOSED):
        #     print('Event = ', event)
        #     print('Values Dictionary (key = value):')
        #     for key in values:
        #         print(key, ' = ', values[key])
        if event in (None, 'Exit'):
            print("[LOG] Clicked Exit!")
            break

    window.close()


if __name__ == '__main__':
    while True:
        if interface_passcode.main(MASTER_PASSCODE):
            main()
        else:
            break
