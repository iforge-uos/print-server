import PySimpleGUI as sg
import time

TIMEOUT = 60


def main(backend):
    layout = [
            [sg.T("Start Print", justification='center', font=("Helvetica", 16), expand_x=True)],
            [sg.T("Printer:"),
             sg.Combo(list(backend.fleet.printer_access.keys()),
                      disabled=True,
                      key="printer_dropdown",
                      enable_events=True)],
            [sg.Table([["Test1", "Test2", "Test3"], ["Test4", "Test5", "Test6"], ["Test7", "Test8", "Test9"]],
                      select_mode=sg.TABLE_SELECT_MODE_BROWSE,
                      enable_events=True,
                      key="print_table")],
            [sg.B("Submit"), sg.B("Refresh"), sg.B("Exit")]
        ]

    window = sg.Window('iForge Printer Control',
                       layout,
                       element_justification="center",
                       modal=True,
                       no_titlebar=True,
                       )
    window.finalize()
    window.maximize()

    available_printers = [printer['name'] for printer in backend.fleet.printers.values() if printer['status'] == "available"]
    window["printer_dropdown"].update(values=available_printers)
    if len(available_printers) > 0:
        window["printer_dropdown"].update(disabled=False)
    else:
        window["printer_dropdown"].update(disabled=True)

    logout_timer = time.time()

    while True:
        event, values = window.read(timeout=30000)

        # try:
        #     print(f"{time.time() - logout_timer}, {event}, {values[event]}")
        # except KeyError:
        #     print(f"{time.time() - logout_timer}, {event}")

        if event in (None, 'Exit'):
            print("[LOG] Clicked Exit!")
            break

        if event in ("Refresh", sg.TIMEOUT_EVENT):
            backend.update()

        if event == "Submit":
            print(f"Submitted {values['print_table']} on {values['printer_dropdown']}")
            break

        available_printers = [printer['name'] for printer in backend.fleet.printers.values() if printer['status'] == "available"]
        window["printer_dropdown"].update(value=values["printer_dropdown"], values=available_printers)
        if len(available_printers) > 0:
            window["printer_dropdown"].update(disabled=False)
        else:
            window["printer_dropdown"].update(disabled=True)

        if event not in (sg.TIMEOUT_EVENT,):
            logout_timer = time.time()
        else:
            if time.time() - logout_timer > TIMEOUT:
                print("[LOG] Timed out! Eggo.")
                break

    window.close()
