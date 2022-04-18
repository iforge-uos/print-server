import PySimpleGUI as sg
import time
import datetime
import logging

TIMEOUT = 60
WINDOW_SIZE = (800, 480)


def convert_times(raw_time):
    td = datetime.timedelta(days=raw_time)
    return str(datetime.timedelta(days=raw_time)).split(".")[0]


def main(backend, printer, suppress_fullscreen=False):
    logging.info("Starting")
    backend.update()
    joblist = backend.queue.get_jobs()
    if joblist.shape[0] <= 0:
        return -1
    print(joblist)
    column_headings = ["Gcode Filename", "Print Time", "Name", "iRep Check", "Filament (g)"]
    layout = [
        [sg.T("Start Print", justification='center', expand_x=True)],
        [sg.Table([column_headings],
                  select_mode=sg.TABLE_SELECT_MODE_BROWSE,  # noqa
                  enable_events=True,
                  key="print_table",
                  headings=column_headings,
                  num_rows=25,
                  col_widths=[36, 8, 16, 10, 10],
                  auto_size_columns=False,
                  display_row_numbers=True,
                  justification='center')],
        [sg.B("Cancel"), sg.B("Refresh"), sg.B("Print")]
    ]

    window = sg.Window('iForge Printer Control',
                       layout,
                       element_justification="center",
                       modal=True,
                       size=WINDOW_SIZE,
                       resizable=True)
    window.finalize()
    if not suppress_fullscreen:
        window.maximize()

    logout_timer = time.time()

    joblist.loc[:, "Print Time"] = joblist.apply(
        lambda x: str(datetime.timedelta(days=int(x["Print Time"]))).split(".")[0], axis=1)
    joblist.loc[:, "Gcode Filename"] = joblist.apply(lambda x: x["Gcode Filename"].split(',')[-1][1:-2], axis=1)

    window["print_table"].update(joblist[column_headings].values.tolist())
    window["print_table"].update(select_rows=[0])
    logging.info("Started")
    window.finalize()

    while True:
        window.bring_to_front()
        event, values = window.read(timeout=30000)

        if event in (None, 'Exit', "Cancel"):
            logging.info("Exit")
            break

        if event in ("Refresh", sg.TIMEOUT_EVENT):
            logging.info("Refresh")
            backend.update()
            joblist = backend.queue.get_jobs()
            if joblist.shape[0] <= 0:
                break
            joblist.loc[:, "Print Time"] = joblist.apply(
                lambda x: str(datetime.timedelta(days=x["Print Time"])).split(".")[0], axis=1)
            joblist.loc[:, "Gcode Filename"] = joblist.apply(lambda x: x["Gcode Filename"].split(',')[-1][1:-2], axis=1)
            window["print_table"].update(joblist[column_headings].values.tolist())
            window["print_table"].update(select_rows=[0])

        if event == "Print":
            logging.info(f"Print confirmed {values['print_table']} on {printer}")
            sg.popup_quick_message("Starting print, please wait", background_color="dark green")
            backend.queue.select_by_id(joblist.loc[:, "Unique ID"].values[values['print_table'][0]])
            backend.do_print(printer)
            window.close()
            logging.info("Done")
            return 1

        if event not in (sg.TIMEOUT_EVENT,):
            logging.debug("Timeout reset")
            logout_timer = time.time()
        else:
            if time.time() - logout_timer > TIMEOUT:
                logging.info("Timed out")
                break

    window.close()
    return -1
