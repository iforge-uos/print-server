import print_fleet
import print_queue
import json
import time
from cryptography.fernet import Fernet


class Backend:
    def __init__(self):
        self.secrets = {}
        self.load_secrets()

        self.printer_status_dict = {}
        self.printer_dict = {}
        self.prusa_queue = print_queue.PrintQueue(self.secrets["google_secrets"], "Prusa")
        print("Performing initial printer connection, this may take some time")
        self.fleet = print_fleet.PrintFleet(self.secrets["printers"])
        print("Complete")
        self.update()

    def load_secrets(self):
        with open('secrets.key', 'rb') as file:
            key = file.read()

        # load plain secrets
        with open('secrets.json.enc', 'rb') as f:
            data = f.read()

        # encrypt
        fernet = Fernet(key)
        decrypted = fernet.decrypt(data)

        self.secrets = json.loads(decrypted)

        # TODO: For testing only
        with open("secrets.json", "wb") as out_file:
            out_file.write(decrypted)

    def update(self):
        self.prusa_queue.update()
        self.fleet.update_status(self.prusa_queue.get_running_printers())
        self.printer_status_dict = self.fleet.get_status()
        for key in self.printer_status_dict.keys():
            for value in self.printer_status_dict[key]:
                self.printer_dict[value] = key

    def do_print(self, printer_name):
        filename = self.prusa_queue.download_selected()
        self.fleet.select_printer(printer_name)
        self.fleet.add_print(filename)
        self.fleet.select_print(filename)
        self.fleet.run_print()

        self.prusa_queue.mark_running(printer_name)

    def end_print(self, printer_name, result, comment=""):
        # TODO: any other handling of finished prints?
        # TODO: extract completed filename from printer for mark complete? (more robust?)
        #   - currently only works by printer
        self.prusa_queue.mark_result(printer_name, result, comment)
        self.fleet.select_printer(printer_name)
        self.fleet.clear_files()

    def cancel_print(self, printer_name, requeue, comment):
        print(f"Cancelling: {printer_name}, Re-Queue: {requeue}")
        self.fleet.select_printer(printer_name)
        self.fleet.cancel_print()
        self.fleet.clear_files()
        self.prusa_queue.mark_cancel(printer_name, requeue, comment)
