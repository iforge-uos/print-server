import time

import octorest
from requests.exceptions import ConnectionError
import json


class PrintFleet:
    def __init__(self, printers_filename):
        self.printer_access = {}
        with open(printers_filename) as file:
            self.printer_access = json.load(file)
        # print(self.printers)

        self.printers = {}
        self.connect_clients()
        self.update_printing_status()
        # print(self.printers)


    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        del self.printers


    def connect_clients(self):
        for printer, accessDict in self.printer_access.items():
            try:
                self.printers[printer] = {"client": octorest.OctoRest(url="http://" + accessDict["ip"] + ":" + accessDict["port"], apikey=accessDict["apikey"])}
            except ConnectionError as e:
                print("Connection Error")
            except RuntimeError as e:
                print("Runtime Error")
            except TypeError:
                print("Type Error")

    def update_printing_status(self):
        for printer_name, printer in self.printers.items():
            try:
                printer['printing'] = printer['client'].printer()['state']['flags']['printing']
            except(ConnectionError) as e:
                print(f"Connection error: {e}")

    def get_available_printers(self):
        self.update_printing_status()
        available_printers = {}
        for printer_name, printer in self.printers.items():
            if not printer["printing"]:
                available_printers[printer_name] = printer
        return available_printers

    def add_print(self, filename, path=""):
        for printer_name, printer in self.printers.items():
            printer["client"].upload(filename, path=path)

    def run_print(self, filename):
        for printer_name, printer in self.printers.items():
            printer["client"].select(filename, print=True)

    def clear_files(self):
        for printer_name, printer in self.printers.items():
            for file in printer["client"].files()["files"]:
                printer["client"].delete(file["display"])

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


if __name__ == '__main__':
    with PrintFleet("printers.json") as fleet:
        # fleet.add_print("testSquare.gcode")
        # fleet.run_print("testSquare.gcode")
        # error = True
        # while(error):
        #     try:
        #         fleet.clear_files()
        #         error = False
        #         print("File deleted")
        #     except:
        #         pass
        pass

# with PrintFleet("TestBench", vars["printer"]["ip"], vars["printer"]["apikey"]) as printer:
#     print(printer.connect())
#     printer.file_names()
#     print(printer.get_printer_info())