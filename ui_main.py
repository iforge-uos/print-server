import PySimpleGUI as sg
from main_backend import Backend
import ui_passcode
import ui_start_print
import ui_finish_print
import datetime
import time
import logging
import json

MASTER_PASSCODE = "69420"  # TODO: actually set something in secrets xD
# TODO: match safe code: 436743

TIMEOUT = 300  # Seconds to automatically log out
REFRESH_INTERVAL = 1000  # Milliseconds between each refresh (remember: plus time it takes backend to refresh)

PRINTER_ROWS = 2
PRINTER_COLS = 2
WINDOW_SIZE = (800, 480)
X_BUFFER = 20
Y_BUFFER = 25
FRAME_SIZE = (WINDOW_SIZE[0]//PRINTER_COLS - X_BUFFER*PRINTER_COLS,
              WINDOW_SIZE[1]//PRINTER_ROWS - Y_BUFFER*PRINTER_ROWS)

frame_background_colours = {
    "available": None,
    "printing": None,
    "finished": None,
    "offline": None,
    "unknown": None,
    "blank": None
}


def main():
    with open("ui_config.json", "r") as config_file:
        config = json.load(config_file)
        logging.info(f"Config loaded, {config}")
        printer_type = config["printer_type"]
        test_mode = config["test_mode"]

    logging.info("UI Starting")
    sg.theme("Dark Blue 12")
    sg.DEFAULT_FONT = ("Helvetica", 18)

    # Temporary loading window while everything connects
    temp_layout = [
        [sg.VStretch()],
        [sg.Stretch(), sg.Text('iForge 3D Print Automation System', justification='center', font=(24)), sg.Stretch()],
        [sg.Stretch(), sg.Text('Loading...'), sg.Stretch()],
        [sg.VStretch()]]

    temp_window = sg.Window("Loading",
                            temp_layout,
                            resizable=True,
                            size=WINDOW_SIZE)
    temp_window.finalize()
    if not test_mode:
        temp_window.maximize()
    # Two reads to make sure it actually goes fullscreen, sometimes dodgy...
    temp_window.read(timeout=20)
    temp_window.read(timeout=20)

    # Start backend, slow and blocking procedure!
    backend = Backend(printer_type)
    logging.info("Backend started")
    printers = list(backend.printers)
    logging.debug(printers)

    states = ["available", "printing", "finished", "offline", "unknown", "blank"]

    # Set up printer grid
    frame_dict = {}

    layout = [
        [sg.VStretch()],
        [sg.Text('iForge 3D Print Automation System', justification='center', expand_x=True)],
    ]

    for y in range(PRINTER_ROWS):
        layout.append([])
        for x in range(PRINTER_COLS):
            # State 'available', printer idle and waiting for new print
            available_layout = [[sg.B(f"print", key=f"{x}_{y}_print")]]

            printing_layout = [[sg.Text(f"LOADING", key=f"{x}_{y}_printing_filename")],
                               [sg.Text(f"Print time: 0:00:00 elapsed, approx 0:00:00 remaining", key=f"{x}_{y}_printing_time")],
                               [sg.Button("cancel", key=f"{x}_{y}_cancel")],
                               [sg.ProgressBar(max_value=100, orientation='h', key=f"{x}_{y}_printing_progbar", size=(100,20), expand_x=True)],
                               ]

            finished_layout = [[sg.Text("Print Finished:")],
                               [sg.Text(f"N/A", key=f"{x}_{y}_finished_filename")],
                               [sg.Text(f"Was the print successful?")],
                               [sg.Button("Complete", key=f"{x}_{y}_complete"),
                                sg.Button("Failed", key=f"{x}_{y}_fail")]
                               ]

            offline_layout = [[sg.Text("Printer Offline")],
                              [sg.Text("Cause: Unknown", key=f"{x}_{y}_offline_cause")],
                              [sg.Button("Reconnect", key=f"{x}_{y}_reconnect")]]

            unknown_layout = [[sg.Text('ERROR: printer status unknown!')],
                              [sg.Text('Please notify system administrator')],
                              [sg.Multiline('Details: ', key=f"{x}_{y}_unknown_details", disabled=True, expand_x=True, expand_y=True)]
                              ]

            blank_layout = []  # Intentionally left empty

            frame_dict[f"{x}_{y}"] = {
                "available":
                    sg.Frame(f"{x}_{y}", available_layout, size=FRAME_SIZE, visible=False, key=f"{x}_{y}_frame_available", background_color=frame_background_colours["available"], element_justification="center", title_location=sg.TITLE_LOCATION_TOP, title_color="light blue"),  # noqa
                "printing":
                    sg.Frame(f"{x}_{y}", printing_layout, size=FRAME_SIZE, visible=False, key=f"{x}_{y}_frame_printing", background_color=frame_background_colours["printing"], element_justification="center", title_location=sg.TITLE_LOCATION_TOP, title_color="light coral"),  # noqa
                "finished":
                    sg.Frame(f"{x}_{y}", finished_layout, size=FRAME_SIZE, visible=False, key=f"{x}_{y}_frame_finished", background_color=frame_background_colours["finished"], element_justification="center", title_location=sg.TITLE_LOCATION_TOP, title_color="light green"),  # noqa
                "offline":
                    sg.Frame(f"{x}_{y}", offline_layout, size=FRAME_SIZE, visible=False, key=f"{x}_{y}_frame_offline", background_color=frame_background_colours["offline"], element_justification="center", title_location=sg.TITLE_LOCATION_TOP, title_color="hot pink"),  # noqa
                "unknown":
                    sg.Frame(f"{x}_{y}", unknown_layout, size=FRAME_SIZE, visible=False, key=f"{x}_{y}_frame_unknown", background_color=frame_background_colours["unknown"], element_justification="center", title_location=sg.TITLE_LOCATION_TOP, title_color="orange red"),  # noqa
                "blank":
                    sg.Frame(f"{x}_{y}", blank_layout, size=FRAME_SIZE, visible=True, key=f"{x}_{y}_frame_blank", background_color=frame_background_colours["blank"], element_justification="center", title_location=sg.TITLE_LOCATION_TOP, title_color="grey")  # noqa
            }
            for key in frame_dict[f"{x}_{y}"]:
                # Comment after following line disables inspection because PyCharm is too dumb in some cases
                layout[-1].append(sg.pin(frame_dict[f"{x}_{y}"][key]))  # noqa
    # Page buttons
    layout.append([sg.Button("<<<", key="prev_page"), sg.Text("Page 0", key="page"), sg.Button(">>>", key="next_page")])
    layout.append([sg.VStretch()])

    temp_window.close()

    window = sg.Window('iForge Printer Control',
                       layout,
                       element_justification="center",
                       size=WINDOW_SIZE
                       )
    window.finalize()
    if test_mode:
        window.set_title("iForge Printer Control TEST MODE")
        window.disable_debugger()
    else:
        window.maximize()

    # Initialise logout timer
    logout_timer = time.time()

    page = 0  # Start on page 0
    pages = -(-len(printers) // (PRINTER_ROWS*PRINTER_COLS))  # Integer divide rounded up
    window["page"].update(value=f"Page {page+1}/{pages}")
    window["prev_page"].update(disabled=True if page == 0 else False)
    window["next_page"].update(disabled=True if page == pages - 1 else False)
    logging.info("UI initialised")

    # Main event loop
    while True:
        # Ensure window at front
        if not test_mode:
            window.bring_to_front()
        # Timeout for refreshing stats
        event, values = window.read(timeout=REFRESH_INTERVAL)
        logging.debug(event)

        # Exit events
        if event in (None, 'Exit'):
            break

        if event == "next_page":
            logging.info("Next page")
            page += 1

        if event == "prev_page":
            logging.info("Previous page")
            page -= 1

        # Update page buttons and counter
        if event in ("next_page", "prev_page"):
            window["page"].update(value=f"Page {page+1}/{pages}")
            window["prev_page"].update(disabled=True if page == 0 else False)
            window["next_page"].update(disabled=True if page == pages - 1 else False)

        # Events that trigger main display updates
        if event in (sg.TIMEOUT_EVENT, "next_page", "prev_page"):
            t0 = time.time()
            backend.update()
            if test_mode:
                logging.debug(f"Update took {time.time()-t0:.2f}s")
            joblist = backend.queue.get_jobs()
            logging.debug(joblist)
            # print(f"[INFO] joblist: {joblist}")
            for y in range(PRINTER_ROWS):
                for x in range(PRINTER_COLS):
                    loc = f"{x}_{y}"
                    idx = page*PRINTER_ROWS*PRINTER_COLS + y*PRINTER_COLS + x
                    printer = printers[idx] if idx < len(printers) else None

                    if printer:
                        printer_state = backend.printers[printer]['details']['state']
                        if printer_state in ("paused", "finishing", "cancelling"):  # Transient non-dangerous states
                            printer_state = "printing"
                        elif printer_state == "error":  # For offline_after_error
                            printer_state = "offline"
                        elif printer_state not in states:  # Unknown states - should be very rare
                            printer_state = "unknown"
                    else:
                        printer_state = "blank"

                    # Ensure correct frames are visible
                    if not window[f"{loc}_frame_{printer_state}"].visible:
                        logging.debug(f"changing {loc} to {printer_state}")
                        for state in states:
                            window[f"{loc}_frame_{state}"].update(visible=False)
                        window[f"{loc}_frame_{printer_state}"].update(visible=True)

                    # Update frame title to match printer and state
                    if printer:
                        if 'status' in backend.fleet.printers[printer]['details'] and 'bed' in backend.fleet.printers[printer]['details']['status']['temperature']:
                            window[f"{loc}_frame_{printer_state}"].update(
                                value=f"  {printer}  |  "
                                      f"B: {int(backend.fleet.printers[printer]['details']['status']['temperature']['bed']['actual'])}°C  "
                                      f"H: {int(backend.fleet.printers[printer]['details']['status']['temperature']['tool0']['actual'])}°C  |  "
                                      f"{backend.printers[printer]['details']['state'].title()}  ")
                        else:
                            window[f"{loc}_frame_{printer_state}"].update(
                                value=f"  {printer}  |  "
                                      f"{backend.printers[printer]['details']['state'].title()}  ")
                    else:
                        window[f"{loc}_frame_{printer_state}"].update(value=f"N/A | None")

                    if printer_state == "available":
                        if joblist.shape[0] > 0:
                            window[f"{loc}_print"].update(disabled=False)
                        else:
                            window[f"{loc}_print"].update(disabled=True)

                    if printer_state == "printing":
                        # logging.debug(f"Printer details: {backend.fleet.printers[printer]['details']}")
                        window[f"{loc}_{printer_state}_filename"].update(
                            f"{backend.fleet.printers[printer]['details']['job']['file']['display']}")
                        window[f"{loc}_{printer_state}_time"].update(
                            f"Print time: "
                            f"{str(datetime.timedelta(seconds=backend.fleet.printers[printer]['details']['progress']['printTime'] or 0))}"
                            f" elapsed, approx "
                            f"{str(datetime.timedelta(seconds=backend.fleet.printers[printer]['details']['progress']['printTimeLeft'] or 0))}" 
                            f" remaining")
                        window[f"{loc}_{printer_state}_progbar"].update(
                            int(backend.fleet.printers[printer]['details']['progress']['completion'] or 0))
                        window[f"{loc}_cancel"].update(disabled=False)

                    if printer_state == "finished":
                        window[f"{loc}_{printer_state}_filename"].update(
                            f"{backend.fleet.printers[printer]['details']['job']['file']['display']}")
                        window[f"{loc}_complete"].update(disabled=False)
                        window[f"{loc}_fail"].update(disabled=False)

                    if printer_state == "offline":
                        if "error" in backend.printers[printer]['details']:
                            logging.warning(f"Octoprint error, {backend.printers[printer]['details']['error']}")
                            logging.debug(backend.fleet.printers[printer]['details'])
                            window[f"{loc}_{printer_state}_cause"].update(
                                f"Cause: {backend.printers[printer]['details']['error']}\n"
                                f"Please contact an administrator")
                        else:
                            window[f"{loc}_{printer_state}_cause"].update(
                                f"Cause: Lost connection, try reconnecting later")

                    if printer_state == "unknown":
                        logging.warning(f"Unknown state: {backend.printers[printer]['details']['state']}")
                        logging.debug(backend.fleet.printers[printer]['details'])
                        window[f"{loc}_{printer_state}_details"].update(
                            f"Details:\n"
                            f"State: {backend.printers[printer]['details']['state']}\n"
                            f"File: {backend.fleet.printers[printer]['details']['job']['file']['display']}\n"
                            f"{backend.fleet.printers[printer]['details']}")
                        pass

                    if printer_state == "blank":
                        pass

        # Event handling
        event_components = event.split('_')
        loc = None
        printer = None

        # Check valid event, then get printer and location
        if len(event_components) >= 3 and event_components[0] != '':
            print(event_components)
            x = int(event_components[0])
            y = int(event_components[1])
            loc = f"{x}_{y}"

            try:
                printer = printers[page*PRINTER_ROWS*PRINTER_COLS + y*PRINTER_ROWS + x]
            except IndexError:
                printer = None

        if printer:
            if event_components[-1] == "print":
                logging.info(f"Print {loc}, {printer}")
                start_choice = ui_start_print.main(backend, printer, test_mode)
                print(start_choice)
                if start_choice == "Print":
                    logging.info("Print started")
                    sg.popup_quick_message("Starting print, please wait", background_color="dark green")

            # Event handling
            if event_components[-1] == "complete":
                logging.info(f"Complete {loc}, {printer}")
                window[f"{loc}_complete"].update(disabled=True)
                window[f"{loc}_fail"].update(disabled=True)
                sg.popup_quick_message("Marking print successful, please wait", background_color="dark violet")
                backend.end_print(printer, "Complete", False, "")

            if event_components[-1] == "fail":
                logging.info(f"Fail {loc}, {printer}")
                window[f"{loc}_complete"].update(disabled=True)
                window[f"{loc}_fail"].update(disabled=True)
                requeue = sg.popup_yes_no("Should this print be re-queued?", title="Requeue?")
                requeue = True if requeue == "Yes" else False  # Convert to boolean
                if not requeue:
                    comment = sg.popup_get_text("Comment", default_text="Please talk to a 3DP team member") or ""
                    sg.popup_quick_message("Marking print failed, please wait", background_color="dark turquoise")
                else:
                    comment = ""
                    sg.popup_quick_message("Requeueing print, please wait", background_color="dark turquoise")
                logging.info(f"Fail confirmed {loc}, {printer}, requeue={requeue}, comment={comment}")
                backend.end_print(printer, "Failed", requeue, comment)

            if event_components[-1] == "cancel":
                logging.info(f"Cancel {loc}, {printer}")
                window[f"{loc}_cancel"].update(disabled=True)
                backend.update()
                if backend.printers[printer]['details']['state'] != "printing":
                    sg.popup_quick_message(f"Cannot cancel, {printer} not printing!")
                    logging.warning("Cancel failed")
                else:
                    confirm = sg.popup_yes_no("Are you sure you want to cancel this print?", title="Confirm cancel?")
                    if confirm == "Yes":
                        requeue = sg.popup_yes_no("Should this print be re-queued?", title="Requeue?")
                        requeue = True if requeue == "Yes" else False  # Convert to boolean
                        if not requeue:
                            comment = sg.popup_get_text("Comment", default_text="Please talk to a 3DP team member") or ""
                        else:
                            comment = ""
                        sg.popup_quick_message("Cancelling print, please wait", background_color="maroon")
                        logging.info(f"Cancel confirmed {loc}, {printer}, requeue={requeue}, comment={comment}")
                        backend.cancel_print(printer, requeue, comment)
                        time.sleep(0.5)

            if event_components[-1] == "reconnect":
                logging.info(f"Reconnect {loc}, {printer}")
                sg.popup_quick_message("Reconnecting, please wait", background_color="dark cyan")
                backend.connect()

        # Auto-logout timer
        if event not in (sg.TIMEOUT_EVENT, sg.WIN_CLOSED):
            logging.debug("Timeout reset")
            logout_timer = time.time()
            # if test_mode:
            #     print('Event = ', event)
            #     print('Values Dictionary (key = value):')
            #     for key in values:
            #         print(key, ' = ', values[key])
        else:
            if time.time() - logout_timer > TIMEOUT:
                logging.info("Timed out")
                break

    window.close()


if __name__ == '__main__':
    # Enable logging to file
    logging.basicConfig(filename="ui_main.log", encoding="utf-8",
                        format="%(asctime)s %(levelname)s:%(name)s:%(module)s:%(message)s",
                        level=logging.INFO)

    logging.info("ui_main.py started")

    with open("ui_config.json", "r") as config_file:
        config = json.load(config_file)
        logging.info(f"Config loaded, {config}")
        test_mode = config["test_mode"]

    while True:
        if ui_passcode.main(MASTER_PASSCODE, suppress_fullscreen=test_mode):
            logging.info("Password success")
            main()
            logging.info("Eggo")
        else:
            logging.info("Exit")
            break
