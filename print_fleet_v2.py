import copy
import random

import octorest
from requests.exceptions import ConnectionError
import json
import time
from cryptography.fernet import Fernet
import multiprocessing
import threading
import logging

OCTOREST_TIMEOUT = 5.00  # Timeout for Octoprint connection, seconds

PRINTER_UPDATE_INTERVAL = 5.00  # Time between printer updates


def thread_connect(param_dict):
    client = octorest.OctoRest(
        url=f"http://{param_dict['ip']}:{param_dict['port']}",
        apikey=param_dict['apikey'])
    param_dict['client'] = client


class PrintFleet:
    def __init__(self, printer_access_dict):
        self.queue_running = []
        self.printers_lock = threading.Lock()
        with self.printers_lock:
            self.printers = printer_access_dict
            for printer in self.printers:
                self.printers[printer]['client'] = None
                self.printers[printer]['details'] = None
                self.printers[printer]['poll_time'] = 0

        self.connect("all")

        for printer in self.printers:
            update_daemon = threading.Thread(target=self._update_printer_daemon, args=(printer,), daemon=True)
            update_daemon.start()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        del self.printers

    def get_printer_dict(self, printer):
        with self.printers_lock:
            printer_dict = self.printers[printer]
        return printer_dict

    def reconnect_offline(self):
        for printer in self.printers:
            if not self.printers[printer]['client']:
                self.connect(printer)

    def connect(self, printer_name):
        if printer_name == "all":
            for printer in self.printers:
                with self.printers_lock:
                    self.printers[printer]['client'] = None
                self.connect(printer)

            # TODO: implement something like this for offline printers only - needs to also handle printers going offline?

        else:
            with self.printers_lock:
                print(f"Connecting to {printer_name:10s}...\t", end="")
                logging.info(f"Attempting connection, {printer_name} at {self.printers[printer_name]['ip']}")

                arg_return_dict = multiprocessing.Manager().dict()
                arg_return_dict['ip'] = self.printers[printer_name]['ip']
                arg_return_dict['port'] = self.printers[printer_name]['port']
                arg_return_dict['apikey'] = self.printers[printer_name]['apikey']
                arg_return_dict['client'] = self.printers[printer_name]['client']

                # Multiprocessing used so the process can be killed if the printer doesn't connect within a set time
                p = multiprocessing.Process(target=thread_connect, args=(arg_return_dict,))
                p.start()
                p.join(OCTOREST_TIMEOUT)

                if p.is_alive():
                    logging.info(f"Forced timeout, {printer_name} at {arg_return_dict['ip']}")
                    p.terminate()
                    p.join()

                self.printers[printer_name]['client'] = arg_return_dict['client']

                if not self.printers[printer_name]['client']:
                    self.printers[printer_name]['details'] = {'state': "offline"}
                    logging.info(f"Connection failed, {printer_name} at {self.printers[printer_name]['ip']}")

                try:
                    # attempt to get job_info - will except if octopi is disconnected from printer?
                    self.printers[printer_name]['client'].job_info()
                    self.printers[printer_name]['details'] = {'state': "operational"}
                    print("Success")
                    logging.info(f"Connection success, {printer_name} at {self.printers[printer_name]['ip']}")
                except AttributeError or ConnectionError or RuntimeError or TypeError as e:
                    # print(f"Connection error: {e}")
                    self.printers[printer_name]['details'] = {'state': "offline"}
                    print("Failed")
                    logging.info(f"Connection success but printer disconnected, {printer_name} at {self.printers[printer_name]['ip']}")

    def update(self, printer_name, queue_running=None):
        # Used to update whole printer but that was too slow, now just updates list of running printers
        with self.printers_lock:
            if queue_running is None:
                self.queue_running = self.queue_running or []
            else:
                self.queue_running = queue_running

    def _update_printer_daemon(self, printer_name):
        time.sleep(random.random())  # Spread out updates to improve overall responsiveness
        while True:
            with self.printers_lock:
                printer_dict = copy.deepcopy(self.printers[printer_name])
                queue_running = copy.deepcopy(self.queue_running)
            if printer_dict['details']['state'] != "offline":
                try:
                    printer_dict['details'] = printer_dict['client'].job_info()

                    # fix bad standards from octorest
                    printer_dict['details']['state'] = printer_dict['details']['state'].lower()

                    # Can't be bothered dealing with this state, just wait until it has cleared
                    while printer_dict['details']['state'] == "connecting":
                        time.sleep(0.5)
                        printer_dict['details'] = printer_dict['client'].job_info()
                    try:
                        if "error" in printer_dict['details']:
                            printer_dict['details']['state'] = "error"
                        elif printer_dict['details']['state'] == "offline":
                            printer_dict['details']['state'] = "error"
                            printer_dict['details']['error'] = "Printer disconnected"
                        else:
                            printer_dict['details']['status'] = printer_dict['client'].printer()
                    except RuntimeError as e:
                        logging.error(f"Last printer state: {printer_dict['details']}")
                        raise e

                    printer_dict['poll_time'] = time.time()

                    if printer_dict['details']['state'] == "operational":
                        if printer_name in queue_running:
                            printer_dict['details']['state'] = "finished"
                        else:
                            printer_dict['details']['state'] = "available"

                    if printer_dict['details']['state'] == "printing" and printer_name not in queue_running:
                        printer_dict['details']['state'] = "queue_error"

                except ConnectionError:
                    printer_dict['details'] = {"state": "offline"}
                    logging.warning(f"Connection error, {printer_name} at {printer_dict['ip']}")

            with self.printers_lock:
                self.printers[printer_name] = printer_dict

            time.sleep(PRINTER_UPDATE_INTERVAL)

    def upload(self, printer_name, filename, path=""):
        with self.printers_lock:
            print(f"Uploading {filename} to {printer_name}...\t", end="")
            val = self.printers[printer_name]['client'].upload(filename, path=path)
            print("Complete")
        return val

    def run_print(self, printer_name, filename):
        with self.printers_lock:
            self.printers[printer_name]['client'].select(filename, print=True)

    def cancel_print(self, printer_name):
        with self.printers_lock:
            self.printers[printer_name]['client'].cancel()
            t0 = time.time()
            while self.printers[printer_name]['client'].printer()['state']['flags']['cancelling']:
                time.sleep(0.5)
            time.sleep(0.5)
        return time.time() - t0

    def clear_files(self, printer_name):
        with self.printers_lock:
            for file in self.printers[printer_name]['client'].files()['files']:
                try:
                    self.printers[printer_name]['client'].delete(file['display'])
                except RuntimeError as e:
                    print(f"Error, usually from non-existent path? - {e}")


if __name__ == "__main__":
    with open('secrets.key', 'rb') as file:
        key = file.read()

    # load plain secrets
    with open('secrets.json.enc', 'rb') as f:
        data = f.read()

    # encrypt
    fernet = Fernet(key)
    decrypted = fernet.decrypt(data)

    printer_secrets = json.loads(decrypted)['printers']

    fleet = PrintFleet(printer_secrets)

    for name, data in fleet.printers.items():
        print(f"{name}:\n{data}")
    fleet.update("all", [])
    fleet.upload("rob", "testPrint_no_extrude.gcode")
    print("upload complete")
