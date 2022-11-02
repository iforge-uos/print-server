import PySimpleGUI as sg
import time
import datetime
import logging

TIMEOUT = 60
WINDOW_SIZE = (800, 480)


def main(backend, printer, suppress_fullscreen=False):
    logging.info("Starting")
    backend.update()
    joblist = backend.queue.get_jobs()
    if joblist.shape[0] <= 0:
        return -1
    logging.debug(joblist)
    column_headings = ["Gcode Filename", "Print Time", "Name", "Rep Check", "Filament (g)"]
    layout = [
        [sg.T("Start Print", justification='center', expand_x=True, key="title")],
        [sg.Table([column_headings],
                  select_mode=sg.TABLE_SELECT_MODE_BROWSE,  # noqa
                  enable_events=True,
                  key="print_table",
                  headings=column_headings,
                  num_rows=24,
                  # col_widths=[36, 8, 16, 10, 10],  # Full width
                  col_widths=[10, 10, 10, 10, 10],  # With details pane
                  auto_size_columns=False,
                  display_row_numbers=True,
                  justification='center'),
         sg.Multiline("Click a print job to see details.", expand_x=True, expand_y=True, disabled=True, key="details")],
        [sg.B("Cancel"), sg.B("Refresh"), sg.B("Print")]
    ]

    window = sg.Window('Start Print',
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
    window["title"].update(f"Start Print: {printer}")
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
            try:
                backend.queue.select_by_id(joblist.loc[:, "Unique ID"].values[values['print_table'][0]])
            except ValueError:
                sg.popup_quick_message("ERROR: Queue spreadsheet malformed", background_color="red")
                window.close()
                return -1
            backend.do_print(printer)
            window.close()
            logging.info("Done")
            return 1

        if event == "print_table":
            job = joblist.iloc[values['print_table'][0]]
            window["details"].update(
                f"Print Details:\n"
                f"User:\n\t{job['Name']}\n"
                f"Rep Check:\n\t{job['Rep Check']}\n"
                f"Filename:\n\t{job['Gcode Filename']}\n"
                f"Print Time:\n\t{job['Print Time']}\n"
                f"Filament:\n\t{job['Filament (g)']}g\n"
                f"Project:\n\t{job['Project type']}\n"
                f"Date added:\n\t{job['Date Added']}\n"
                f"Notes:\n\t{job['Notes']}\n")

        if event not in (sg.TIMEOUT_EVENT,):
            logging.debug("Timeout reset")
            logout_timer = time.time()
        else:
            if time.time() - logout_timer > TIMEOUT:
                logging.info("Timed out")
                break

    window.close()
    return -1
