import octorest
from requests.exceptions import ConnectionError
import json
import time


class PrintFleet:
    def __init__(self, printer_access):
        self.printer_access = printer_access

        self.selected_printer = {}

        self.printers = {}
        self.connect_clients()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        del self.printers

    def connect_clients(self):
        for printer, accessDict in self.printer_access.items():
            try:
                self.printers[printer] = {"name": printer, "client": octorest.OctoRest(
                    url="http://" + accessDict["ip"] + ":" + accessDict["port"], apikey=accessDict["apikey"])}
            except ConnectionError as e:
                # print("Connection Error")
                pass
            except RuntimeError as e:
                # print("Runtime Error")
                pass
            except TypeError:
                # print("Type Error")
                pass

    def update_status(self, queue_running):
        for printer in self.printers.values():
            i = 0
            while True:
                i += 1
                printer['status'] = "offline"
                printer['printing'] = False
                try:

                    printer['printing'] = printer['client'].printer()['state']['flags']['printing']
                    if printer['printing']:
                        printer['status'] = "printing"
                    else:
                        printer['status'] = "available"
                    break
                except ConnectionError as e:
                    # print(e)
                    if i >= 1:
                        break
                    continue
                except RuntimeError as e:
                    # print(e)  # TODO: logging
                    break

        for name in queue_running:
            try:
                if not self.printers[name]['printing']:
                    self.printers[name]['status'] = "finished"
            except KeyError:
                # not in printer list
                continue

        for printer in self.printers.values():
            if printer['name'] not in queue_running and printer['printing']:
                printer['status'] = "invalid"

    def get_status(self):
        status_dict = {"available": [], "printing": [], "finished": [], "invalid": [], "offline": []}
        for printer in self.printers.values():
            status_dict[printer["status"]].append(printer["name"])
        return status_dict

    def add_print(self, filename, path=""):
        self.selected_printer["client"].upload(filename, path=path)

    def select_print(self, filename):
        self.selected_printer["client"].select(filename, print=False)

    def run_print(self):
        self.selected_printer["client"].start()

    def cancel_print(self):
        print(self.selected_printer["client"].printer()['state'])
        self.selected_printer["client"].cancel()
        while self.selected_printer["client"].printer()['state']['flags']['cancelling']:
            time.sleep(0.5)
        time.sleep(0.5)

    def clear_files(self):
        for file in self.selected_printer["client"].files()["files"]:
            try:
                self.selected_printer["client"].delete(file["display"])
            except RuntimeError as e:
                print(f"Error, usually from non-existent path? - {e}")

    def select_printer(self, name):
        self.selected_printer = self.printers[name]

    # def file_names(self):
    #     """Retrieves the G-code file names from the
    #     OctoPrint server and returns a string message listing the
    #     file names.
    #
    #     Args:
    #         client - the OctoRest client
    #     """
    #     message = "\nCurrent GCODE Files:\n"
    #     for i, k in enumerate(self.client.files()['files']):
    #         message += f"{i}.\t{k['name']}\n"
    #     print(message)
    #
    # def get_printer_info(self):
    #     try:
    #         message = ""
    #         message += str(self.client.version) + "\n"
    #         message += str(self.client.job_info()) + "\n"
    #         printing = self.client.printer()['state']['flags']['printing']
    #         if printing:
    #             message += "Currently printing!\n"
    #         else:
    #             message += "Not currently printing...\n"
    #         return message
    #     except Exception as e:
    #         print(e)
    #
    # def home(self):
    #     self.client.home()
    #
    # def toggle(self):
    #     self.client.pause()

