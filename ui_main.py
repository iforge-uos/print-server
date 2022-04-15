import PySimpleGUI as sg
from main_backend import Backend
import ui_passcode
import ui_start_print
import ui_finish_print
import datetime
import time

MASTER_PASSCODE = "69420"  # TODO: actually set something in secrets xD
# TODO: match safe code: 436743

TIMEOUT = 300  # Seconds to automatically log out
REFRESH_INTERVAL = 5000  # Milliseconds between each refresh (remember: plus time it takes backend to refresh)

PRINTER_ROWS = 2
PRINTER_COLS = 2
WINDOW_SIZE = (800, 480)
X_BUFFER = 20
Y_BUFFER = 25
FRAME_SIZE = (WINDOW_SIZE[0]//PRINTER_COLS - X_BUFFER*PRINTER_COLS,
              WINDOW_SIZE[1]//PRINTER_ROWS - Y_BUFFER*PRINTER_ROWS)

colours = {
    "available": None,
    "printing": None,
    "finished": None,
    "offline": None,
    "unknown": None,
    "blank": None
}

TEST_MODE = True


def main():
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
                            resizable=False)
    temp_window.finalize()
    temp_window.maximize()
    # Two reads to make sure it actually goes fullscreen, sometimes dodgy...
    temp_window.read(timeout=20)
    temp_window.read(timeout=20)

    # Start backend, slow and blocking procedure!
    backend = Backend("Prusa")
    printers = list(backend.printers)

    states = ["available", "printing", "finished", "offline", "unknown", "blank"]

    # Set up printer grid
    frame_dict = {}

    layout = [[sg.Text('iForge 3D Print Automation System', justification='center', expand_x=True)]]

    for y in range(PRINTER_ROWS):
        layout.append([])
        for x in range(PRINTER_COLS):
            # State 'available', printer idle and waiting for new print
            available_layout = [[sg.Text("Hotend: "),
                                 sg.Text(f"-0.00°C", key=f"{x}_{y}_available_hotend")],
                                [sg.Text("Bed: "),
                                 sg.Text(f"-0.00°C", key=f"{x}_{y}_available_bed")],
                                [sg.B(f"print", key=f"{x}_{y}_print")]
                                ]

            printing_layout = [[sg.Text(f"LOADING", key=f"{x}_{y}_printing_filename")],
                               [sg.Text("Hotend:\t"),
                                sg.Text(f"-0.00°C / 0.00°C", key=f"{x}_{y}_printing_hotend")],
                               [sg.Text("Bed:\t"),
                                sg.Text(f"-0.00°C / 0.00°C", key=f"{x}_{y}_printing_bed")],
                               [sg.Text(f"Print time: 0:00:00 elapsed, approx 0:00:00 remaining", key=f"{x}_{y}_printing_time")],
                               [sg.Button("cancel", key=f"{x}_{y}_cancel")],
                               [sg.ProgressBar(max_value=100, orientation='h', key=f"{x}_{y}_printing_progbar", size=(100,20), expand_x=True)],
                               ]

            finished_layout = [[sg.Text(f"Finished: N/A", key=f"{x}_{y}_finished_filename")],
                               [sg.Text(f"Was this print successful?")],
                               [sg.Button("success", key=f"{x}_{y}_success"),
                                sg.Button("fail", key=f"{x}_{y}_fail")]
                               ]

            offline_layout = [[sg.Text("Printer Offline")],
                              [sg.Text("Cause: Unknown", key=f"{x}_{y}_offline_cause")],
                              [sg.Button("Reconnect", key=f"{x}_{y}_reconnect")]]

            unknown_layout = [[sg.Text('ERROR: printer status unknown!')],
                              [sg.Text('Please notify system administrator')],
                              [sg.Multiline('Details: ', key=f"{x}_{y}_unknown_details", disabled=True, expand_x=True, expand_y=True)]
                              ]

            blank_layout = []

            frame_dict[f"{x}_{y}"] = {
                "available":
                    sg.Frame(f"{x}_{y}", available_layout, size=FRAME_SIZE, visible=False, key=f"{x}_{y}_frame_available", background_color=colours["available"]),  # noqa
                "printing":
                    sg.Frame(f"{x}_{y}", printing_layout, size=FRAME_SIZE, visible=False, key=f"{x}_{y}_frame_printing", background_color=colours["printing"]),  # noqa
                "finished":
                    sg.Frame(f"{x}_{y}", finished_layout, size=FRAME_SIZE, visible=False, key=f"{x}_{y}_frame_finished", background_color=colours["finished"]),  # noqa
                "offline":
                    sg.Frame(f"{x}_{y}", offline_layout, size=FRAME_SIZE, visible=False, key=f"{x}_{y}_frame_offline", background_color=colours["offline"]),  # noqa
                "unknown":
                    sg.Frame(f"{x}_{y}", unknown_layout, size=FRAME_SIZE, visible=False, key=f"{x}_{y}_frame_unknown", background_color=colours["unknown"]),  # noqa
                "blank":
                    sg.Frame(f"{x}_{y}", blank_layout, size=FRAME_SIZE, visible=False, key=f"{x}_{y}_frame_blank", background_color=colours["blank"])  # noqa
            }
            for key in frame_dict[f"{x}_{y}"]:
                # Comment after following line disables inspection because PyCharm is too dumb in some cases
                layout[y+1].append(sg.pin(frame_dict[f"{x}_{y}"][key]))  # noqa
    # Page buttons
    layout.append([sg.Button("<<<", key="prev_page"), sg.Text("Page 0", key="page"), sg.Button(">>>", key="next_page")])

    temp_window.close()

    window = sg.Window('iForge Printer Control',
                       layout,
                       element_justification="center",
                       size=WINDOW_SIZE
                       )
    window.finalize()
    if TEST_MODE:
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

    # This is an Event Loop
    while True:
        if TEST_MODE:
            print(f"T: {time.time()}")
        # Ensure window at front
        if not TEST_MODE:
            window.bring_to_front()
        # Timeout for refreshing stats
        event, values = window.read(timeout=REFRESH_INTERVAL)

        # Exit events
        if event in (None, 'Exit'):
            print("[LOG] Clicked Exit!")
            break

        if event == "next_page":
            print("[LOG] Next page")
            page += 1

        if event == "prev_page":
            print("[LOG] Previous page")
            page -= 1

        # Update page buttons and counter
        if event in ("next_page", "prev_page"):
            window["page"].update(value=f"Page {page+1}/{pages}")
            window["prev_page"].update(disabled=True if page == 0 else False)
            window["next_page"].update(disabled=True if page == pages - 1 else False)

        # Events that trigger main display updates
        if event in (sg.TIMEOUT_EVENT, "next_page", "prev_page"):
            backend.update()
            joblist = backend.queue.get_jobs()
            print(f"[INFO] joblist: {joblist}")
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
                        for state in states:
                            window[f"{loc}_frame_{state}"].update(visible=False)
                        window[f"{loc}_frame_{printer_state}"].update(visible=True)

                    # Update frame title to match printer and state
                    window[f"{loc}_frame_{printer_state}"].update(
                        value=f"{printer if printer else 'N/A'} | {backend.printers[printer]['details']['state'].title() if printer else 'None'}")

                    if printer_state == "available":
                        window[f"{loc}_{printer_state}_hotend"].update(f"{backend.fleet.printers[printer]['details']['status']['temperature']['tool0']['actual']}°C")
                        window[f"{loc}_{printer_state}_bed"].update(f"{backend.fleet.printers[printer]['details']['status']['temperature']['bed']['actual']}°C")

                        if joblist.shape[0] > 0:
                            window[f"{loc}_print"].update(disabled=False)
                        else:
                            window[f"{loc}_print"].update(disabled=True)

                    if printer_state == "printing":
                        print(f"[INFO] Details: {backend.fleet.printers[printer]['details']}")
                        window[f"{loc}_{printer_state}_filename"].update(f"{backend.fleet.printers[printer]['details']['job']['file']['display']}")
                        window[f"{loc}_{printer_state}_hotend"].update(f"{backend.fleet.printers[printer]['details']['status']['temperature']['tool0']['actual']}°C / {backend.fleet.printers[printer]['details']['status']['temperature']['tool0']['target']}°C")
                        window[f"{loc}_{printer_state}_bed"].update(f"{backend.fleet.printers[printer]['details']['status']['temperature']['bed']['actual']}°C / {backend.fleet.printers[printer]['details']['status']['temperature']['bed']['target']}°C")
                        window[f"{loc}_{printer_state}_time"].update(f"Print time: {str(datetime.timedelta(seconds=backend.fleet.printers[printer]['details']['progress']['printTime'] or 0))} elapsed, approx {str(datetime.timedelta(seconds=backend.fleet.printers[printer]['details']['progress']['printTimeLeft'] or 0))} remaining")
                        window[f"{loc}_{printer_state}_progbar"].update(int(backend.fleet.printers[printer]['details']['progress']['completion'] or 0))

                    if printer_state == "finished":
                        pass

                    if printer_state == "offline":
                        if backend.printers[printer]['details']['state'] == "offline_after_error":
                            window[f"{loc}_{printer_state}_cause"].update(f"Cause: {backend.printers[printer]['details']['error']}")
                        else:
                            window[f"{loc}_{printer_state}_cause"].update(f"Cause: Lost connection, try reconnecting later")

                    if printer_state == "unknown":
                        window[f"{loc}_{printer_state}_details"].update(f"Details:\n"
                                                                        f"State: {backend.printers[printer]['details']['state']}\n"
                                                                        f"File: {backend.fleet.printers[printer]['details']['job']['file']['display']}\n"
                                                                        f"{backend.fleet.printers[printer]}")
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
            if event_components == "print":
                print(f"Printing: {loc} -> {printer}")

            # Event handling
            if event_components == "finish":
                print(f"Printing: {loc} -> {printer}")

        # Auto-logout timer
        if event not in (sg.TIMEOUT_EVENT, sg.WIN_CLOSED):
            logout_timer = time.time()
            if TEST_MODE:
                print('Event = ', event)
                print('Values Dictionary (key = value):')
                for key in values:
                    print(key, ' = ', values[key])
        else:
            if time.time() - logout_timer > TIMEOUT:
                print("[LOG] Timed out!")
                break

    print("Eggo.")
    window.close()


if __name__ == '__main__':
    while True:
        if ui_passcode.main(MASTER_PASSCODE):
            main()
        else:
            break
