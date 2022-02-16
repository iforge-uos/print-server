import PySimpleGUI as sg
import time
import datetime

TIMEOUT = 60

def main(backend):
    column_headings = ["Gcode Filename", "Print Time", "Name", "iRep Check", "Filament (g)"]
    layout = [
        [sg.T("Finish Print", justification='center', expand_x=True)],
        [sg.T("Printer:"),
         sg.Combo(list(backend.fleet.printer_access.keys()),
                  disabled=True,
                  key="printer_dropdown",
                  enable_events=True)],
        [sg.Table([["Filename", "Print Time", "User", "Rep", "Filament (g)"]],
                  select_mode=sg.TABLE_SELECT_MODE_BROWSE,
                  enable_events=True,
                  key="print_table",
                  headings=column_headings)],
        [sg.B("Submit", disabled=True), sg.B("Refresh"), sg.B("Exit")]
    ]

    window = sg.Window('iForge Printer Control',
                       layout,
                       element_justification="center",
                       modal=True,
                       resizable=True)
    window.finalize()
    window.maximize()

    available_printers = [printer['name'] for printer in backend.fleet.printers.values() if
                          printer['status'] == "available"]
    window["printer_dropdown"].update(values=available_printers)
    if len(available_printers) > 0:
        window["printer_dropdown"].update(disabled=False)
    else:
        window["printer_dropdown"].update(disabled=True)

    logout_timer = time.time()

    joblist = backend.queue.get_jobs()

    # ignore these warnings, there is no fix... we tried :'(
    joblist.loc[:, "Print Time"] = joblist.apply(lambda x: str(datetime.timedelta(days=x["Print Time"])).split(".")[0],
                                                 axis=1)
    joblist.loc[:, "Gcode Filename"] = joblist.apply(lambda x: x["Gcode Filename"].split(',')[-1][1:-2], axis=1)

    window["print_table"].update(joblist[column_headings].values.tolist())

    while True:
        window.bring_to_front()
        event, values = window.read(timeout=30000)

        # print(event)

        # try:
        #     print(f"{time.time() - logout_timer}, {event}, {values[event]}")
        # except KeyError:
        #     print(f"{time.time() - logout_timer}, {event}")

        if event in (None, 'Exit'):
            print("[LOG] Clicked Exit!")
            break

        if event in ["printer_dropdown", "print_table"]:
            if values["print_table"] and values["printer_dropdown"]:
                window["Submit"].update(disabled=False)
            else:
                window["Submit"].update(disabled=True)

        if event in ("Refresh", sg.TIMEOUT_EVENT):
            backend.update()
            joblist = backend.queue.get_jobs()
            # ignore these warnings, there is no fix... we tried :'(
            joblist.loc[:, "Print Time"] = joblist.apply(
                lambda x: str(datetime.timedelta(days=x["Print Time"])).split(".")[0], axis=1)
            joblist.loc[:, "Gcode Filename"] = joblist.apply(lambda x: x["Gcode Filename"].split(',')[-1][1:-2], axis=1)
            window["print_table"].update(joblist[column_headings].values.tolist())

        if event == "Submit":
            print(f"Submitted {values['print_table']} on {values['printer_dropdown']}")
            sg.popup_no_wait(f"Print starting on {values['printer_dropdown']}!", title="Starting",
                             auto_close=True, auto_close_duration=10, modal=False, keep_on_top=True)
            backend.queue.select_by_id(joblist.loc[:, "Unique ID"].values[values['print_table'][0]])
            backend.do_print(values['printer_dropdown'])
            break

        available_printers = [printer['name'] for printer in backend.fleet.printers.values() if
                              printer['status'] == "available"]
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
