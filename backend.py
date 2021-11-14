import print_fleet
import print_queue
import json
from cryptography.fernet import Fernet

class Backend:
    def __init__(self):
        self.secrets = {}
        self.load_secrets()

        self.printer_status_dict = {}
        self.prusa_queue = print_queue.PrintQueue(self.secrets["google_secrets"], "Prusa")
        self.fleet = print_fleet.PrintFleet(self.secrets["printers"])
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

    def update(self):
        self.prusa_queue.update()
        self.fleet.update_status(self.prusa_queue.get_running_printers())
        self.printer_status_dict = self.fleet.get_status()

    def do_print(self, printer_name):
        filename = self.prusa_queue.download_selected()
        self.fleet.select_printer(printer_name)
        self.fleet.add_print(filename)
        self.fleet.run_print(filename)

        self.prusa_queue.mark_running(printer_name)

    def end_print(self, printer_name, result, comment=""):
        # TODO: any other handling of finished prints?
        # TODO: extract completed filename from printer for mark complete? (more robust?)
        #   - currently only works by printer
        self.prusa_queue.mark_result(printer_name, result, comment)
        self.fleet.select_printer(printer_name)
        self.fleet.clear_files()
