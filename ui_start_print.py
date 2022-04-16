import PySimpleGUI as sg
import time
import datetime

TIMEOUT = 60


def convert_times(raw_time):
    td = datetime.timedelta(days=raw_time)
    return str(datetime.timedelta(days=raw_time)).split(".")[0]


def main(backend, printer):
    column_headings = ["Gcode Filename", "Print Time", "Name", "iRep Check", "Filament (g)"]
    layout = [
        [sg.T("Start Print", justification='center', expand_x=True)],
        [sg.T("Printer:")],
        [sg.Table([["Filename", "Print Time", "User", "Rep", "Filament (g)"]],
                  select_mode=sg.TABLE_SELECT_MODE_BROWSE,  # noqa
                  enable_events=True,
                  key="print_table",
                  headings=column_headings)],
        [sg.B("Cancel"), sg.B("Refresh"), sg.B("Print")]
    ]

    window = sg.Window('iForge Printer Control',
                       layout,
                       element_justification="center",
                       modal=True,
                       resizable=True)
    window.finalize()
    window.maximize()

    logout_timer = time.time()

    joblist = backend.queue.get_jobs()

    joblist.loc[:, "Print Time"] = joblist.apply(lambda x: str(datetime.timedelta(days=x["Print Time"])).split(".")[0],
                                                 axis=1)
    joblist.loc[:, "Gcode Filename"] = joblist.apply(lambda x: x["Gcode Filename"].split(',')[-1][1:-2], axis=1)

    window["print_table"].update(joblist[column_headings].values.tolist())
    window["print_table"].update(select_rows=[0])

    while True:
        window.bring_to_front()
        event, values = window.read(timeout=30000)

        if event in (None, 'Exit', "Cancel"):
            print("[LOG] Clicked Exit!")
            break

        if event in ("Refresh", sg.TIMEOUT_EVENT):
            backend.update()
            joblist = backend.queue.get_jobs()
            joblist.loc[:, "Print Time"] = joblist.apply(
                lambda x: str(datetime.timedelta(days=x["Print Time"])).split(".")[0], axis=1)
            joblist.loc[:, "Gcode Filename"] = joblist.apply(lambda x: x["Gcode Filename"].split(',')[-1][1:-2], axis=1)
            window["print_table"].update(joblist[column_headings].values.tolist())
            window["print_table"].update(select_rows=[0])

        if event == "Print":
            print(f"Printing {values['print_table']} on {printer}")
            backend.queue.select_by_id(joblist.loc[:, "Unique ID"].values[values['print_table'][0]])
            backend.do_print(printer)
            break

        if event not in (sg.TIMEOUT_EVENT,):
            logout_timer = time.time()
        else:
            if time.time() - logout_timer > TIMEOUT:
                print("[LOG] Print menu timed out")
                break

    window.close()
    return -1
