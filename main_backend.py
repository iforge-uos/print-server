import print_fleet_v2 as print_fleet
import print_queue
import json
import time
from cryptography.fernet import Fernet
import os


class Backend:
    def __init__(self, printer_list):
        self.secrets = {}
        self.load_secrets()

        self.printers = self.secrets["printers"][printer_list]
        self.printer_type = list(set([val["type"] for i, val in self.printers.items()]))[0].capitalize()
        self.queue = print_queue.PrintQueue(google_secrets=self.secrets["google_secrets"], printer_type=self.printer_type)
        print("Performing initial printer connection, this may take some time")
        self.fleet = print_fleet.PrintFleet(self.printers)
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

    def connect(self):
        self.fleet.connect("all")

    def connect_printer(self, printer_name):
        self.fleet.attach_printer(printer_name)
        self.update()

    def disconnect_printer(self, printer_name):
        self.fleet.detach_printer(printer_name)
        self.update()

    def update(self):
        self.queue.update()
        running_printers = self.queue.get_running_printers()
        self.fleet.update("all", queue_running=running_printers)

    def do_print(self, printer_name):
        filename = self.queue.download_selected()

        self.fleet.upload(printer_name, filename)
        self.fleet.run_print(printer_name, filename)

        self.queue.mark_running(printer_name)

        os.remove(filename)

    def end_print(self, printer_name, result, requeue, comment=""):
        # TODO: any other handling of finished prints?
        # TODO: extract completed filename from printer for mark complete? (more robust?)
        #   - currently only works by printer
        self.queue.mark_result(printer_name, result, requeue, comment)

        self.fleet.clear_files(printer_name)

    def cancel_print(self, printer_name, requeue, comment):
        print(f"Cancelling: {printer_name}, Re-Queue: {requeue}")
        self.fleet.cancel_print(printer_name)
        self.fleet.clear_files(printer_name)

        self.queue.mark_result(printer_name, "Failed", requeue, comment)
