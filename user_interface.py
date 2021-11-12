import PySimpleGUI as sg
from main import Backend
import interface_passcode

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

    layout = [[sg.Text('iForge 3D Print Automation System', size=(38, 1), justification='center', font=("Helvetica", 16),
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
        frame_layout = [[sg.T("Status:"), sg.T("Loading...", key=f"{printer} status")],
                        [sg.T("Temperature:"), sg.T("Loading...", key=f"{printer} temps")]]
        printer_layout.append([sg.Frame(printer, frame_layout, expand_x=True, key=f"{printer} frame")])

    layout = [[sg.Text('iForge 3D Print Automation System', justification='center', font=("Helvetica", 16))],
              [sg.Frame("Printers", key="printer_frame", layout=printer_layout, expand_x=True)],
              ]

    temp_window.close()

    window = sg.Window('iForge Printer Control', layout)
    window.finalize()

    # This is an Event Loop
    while True:
        event, values = window.read(timeout=1000)
        backend.update()
        print(event)

        for printer in backend.fleet.printer_access.keys():
            window[f"{printer} status"].update(backend.fleet.printers[printer]['status'])
            if backend.fleet.printers[printer]['status'] != "offline":
                window[f"{printer} temps"].update(f"Bed: {backend.fleet.printers[printer]['details']['status']['temperature']['bed']['actual']}/{backend.fleet.printers[printer]['details']['status']['temperature']['bed']['target']}, Tool: {backend.fleet.printers[printer]['details']['status']['temperature']['tool0']['actual']}/{backend.fleet.printers[printer]['details']['status']['temperature']['tool0']['target']}")
            else:
                window[f"{printer} temps"].update("N/A")

        # keep an animation running so show things are happening
        # window['-GIF-IMAGE-'].update_animation(sg.DEFAULT_BASE64_LOADING_GIF, time_between_frames=100)
        if event not in (sg.TIMEOUT_EVENT, sg.WIN_CLOSED):
            print('Event = ', event)
            print('Values Dictionary (key = value):')
            for key in values:
                print(key, ' = ', values[key])
        if event in (None, 'Exit'):
            print("[LOG] Clicked Exit!")
            break
        elif event == 'About':
            print("[LOG] Clicked About!")
            sg.popup('PySimpleGUI Demo All Elements',
                     'Right click anywhere to see right click menu',
                     'Visit each of the tabs to see available elements',
                     'Output of event and values can be see in Output tab',
                     'The event and values dictionary is printed after every event')
        elif event == 'Popup':
            print("[LOG] Clicked Popup Button!")
            sg.popup("You pressed a button!")
            print("[LOG] Dismissing Popup!")
        elif event == 'Test Progress bar':
            print("[LOG] Clicked Test Progress Bar!")
            progress_bar = window['-PROGRESS BAR-']
            for i in range(1000):
                print("[LOG] Updating progress bar by 1 step (" + str(i) + ")")
                progress_bar.UpdateBar(i + 1)
            print("[LOG] Progress bar complete!")
        elif event == "Open Folder":
            print("[LOG] Clicked Open Folder!")
            folder_or_file = sg.popup_get_folder('Choose your folder')
            sg.popup("You chose: " + str(folder_or_file))
            print("[LOG] User chose folder: " + str(folder_or_file))
        elif event == "Open File":
            print("[LOG] Clicked Open File!")
            folder_or_file = sg.popup_get_file('Choose your file')
            sg.popup("You chose: " + str(folder_or_file))
            print("[LOG] User chose file: " + str(folder_or_file))
        elif event == "Set Theme":
            print("[LOG] Clicked Set Theme!")
            theme_chosen = values['-THEME LISTBOX-'][0]
            print("[LOG] User Chose Theme: " + str(theme_chosen))
            window.close()
            window = make_window(theme_chosen)

    window.close()


if __name__ == '__main__':
    while True:
        if interface_passcode.main(MASTER_PASSCODE):
            main()
        else:
            break
