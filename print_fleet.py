import octorest
from requests.exceptions import ConnectionError
import time


class PrintFleet:
    def __init__(self, printer_access):
        self.printer_access = printer_access

        self.selected_printer = {}

        self.printers = {}
        self.connect_clients()

        self.prev_reconnect_time = time.time()
        self.offline_timeout = 300

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        del self.printers

    def connect_clients(self):
        for printer, accessDict in self.printer_access.items():
            self.printers[printer] = {"name": printer, "client": None, "print_job": None, 'status': 'unreachable',
                                      'printing': False, 'details': {}}
            try:
                print(f"Connecting to {printer.capitalize()}... ", end='')
                self.printers[printer]["client"] = \
                    octorest.OctoRest(url="http://" + accessDict["ip"] + ":" + accessDict["port"],
                                      apikey=accessDict["apikey"])
                print("Success")
            except ConnectionError as e:
                print("Failed")
                # print("Connection Error")
                pass
            except RuntimeError as e:
                print("Failed")
                # print("Runtime Error")
                pass
            except TypeError:
                print("Failed")
                # print("Type Error")
                pass

    def update_status(self, queue_running):
        for printer in self.printers.values():
            i = 0
            while True:
                i += 1
                printer['status'] = "offline"
                printer['printing'] = False
                printer['details'] = {}
                try:
                    if not printer['client']:
                        tnow = time.time()
                        if tnow - self.prev_reconnect_time > self.offline_timeout:
                            print("Refreshing available printers, please wait")
                            self.connect_clients()
                            self.prev_reconnect_time = tnow

                    if printer['client']:
                        status = printer['client'].printer()
                        job_info = printer['client'].job_info()

                        # print(f"Octoprint Status for {printer['name']}:\n{status}\nend")  # TODO make debug

                        printer['details'] = {'status': status,
                                              'job_info': job_info
                                              }

                        printer['printing'] = status['state']['flags']['printing']
                        if printer['printing']:
                            printer['status'] = "printing"
                        else:
                            printer['status'] = "available"
                        break

                except ConnectionError as e:
                    # print(e)  # TODO: logging
                    break
                except RuntimeError as e:
                    # print(e)  # TODO: logging
                    break

                if i >= 3:
                    break

        for name in queue_running:
            try:
                if not self.printers[name]['printing'] and self.printers[name]['status'] != "offline":
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
        print(f"Uploading {filename}... ", end="")
        self.selected_printer["client"].upload(filename, path=path)
        print("Complete")

    def select_print(self, filename):
        self.selected_printer["client"].select(filename, print=False)

    def run_print(self):
        self.selected_printer["client"].start()

    def cancel_print(self):
        # print(self.selected_printer["client"].printer()['state'])
        self.selected_printer["client"].cancel()
        t0 = time.time()
        while self.selected_printer["client"].printer()['state']['flags']['cancelling']:
            time.sleep(0.5)
        print(f"Cancel of {self.selected_printer['name']} complete, time taken: {time.time() - t0:.1f}s")
        time.sleep(0.5)

    def clear_files(self):
        for file in self.selected_printer["client"].files()["files"]:
            try:
                self.selected_printer["client"].delete(file["display"])
            except RuntimeError as e:
                print(f"Error, usually from non-existent path? - {e}")

    def select_printer(self, name):
        self.selected_printer = self.printers[name]

    # # TODO: Ad-hoc handling
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
