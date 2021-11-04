import octorest


class PrintHub:
    def __init__(self):
        self.selected_printer = []

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def connect(self):
        print(f"Connected to print hub")

    def disconnect(self):
        print(f"Disconnected from print hub")

    def list_printers(self):
        return ['test1', 'test2', 'test3']

    def select_printer(self, printer):
        self.selected_printer = printer
        print(f"Selected printer: {printer}")

    def deselect_printer(self):
        print(f"Deselected {self.selected_printer}")
        self.selected_printer = []

    def clear_files(self, printer=[]):
        if not printer:
            printer = self.selected_printer
        print(f"Cleared files on {printer}")

    def upload_gcode(self, filename, printer=[]):
        if not printer:
            printer = self.selected_printer
        print(f"Writing to {printer}", end="")
        with open(filename) as file:
            print(f", complete")

    def get_printer_status(self, printer=[]):
        if not printer:
            printer = self.selected_printer
        status = "Waiting"
        # print(f"{printer} status = {status}")
        return status

    def get_printer_progress(self, printer=[]):
        if not printer:
            printer = self.selected_printer
        progress = 0
        # eta?
        print(f"{printer} progress = {progress}")

    def start_print(self, printer=[]):
        if not printer:
            printer = self.selected_printer
        print(f"Starting print on {printer}")

    def pause_print(self, printer=[]):
        if not printer:
            printer = self.selected_printer
        print(f"Pausing print on {printer}")

    def cancel_print(self, printer=[]):
        if not printer:
            printer = self.selected_printer
        print(f"Cancelling print on {printer}")
