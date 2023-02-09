import print_fleet_v2 as print_fleet
import print_sheet
import json
import time
from cryptography.fernet import Fernet
import os
import logging
import getpass

logging.basicConfig()
logging.getLogger().setLevel(logging.ERROR)

class Backend:
    def __init__(self, printer_group):
        logging.info(f"Starting backend, {printer_group}")
        self.secrets = {}
        self.load_secrets()

        valid_groups = list(self.secrets["printers"].keys())
        if not printer_group in valid_groups:
            logging.critical("Invalid printer group provided")
            exit(-1)

        self.printers = self.secrets["printers"][printer_group]
        self.printer_type = list(set([val["type"] for i, val in self.printers.items()]))[0]
        self.queue = print_sheet.PrintQueue(google_secrets=self.secrets["google_secrets"], printer_type=self.printer_type)
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
    def connect(self):
        self.fleet.connect("all")

    def connect_printer(self, printer_name):
        self.fleet.connect_printer(printer_name)
        self.update()

    def disconnect_printer(self, printer_name):
        self.fleet.disconnect_printer(printer_name)
        self.update()

    def update(self):
        self.queue.update()
        running_printers = self.queue.get_running_printers()
        self.fleet.update(printer_name='all', queue_running=running_printers)

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

    def auth_admin(self):
        pwd = getpass.getpass("Enter Admin Password:\n>> ")
        if pwd == self.secrets["admin"]["password"]:
            return True
        else:
            return False
