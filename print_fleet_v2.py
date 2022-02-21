import octorest
from requests.exceptions import ConnectionError
import json
import time
from cryptography.fernet import Fernet


class PrintFleet:
    def __init__(self, printer_access_dict):
        self.printers = printer_access_dict
        for i_printer in self.printers.keys():
            self.printers[i_printer]["client"] = None
            self.printers[i_printer]["details"] = None
            self.printers[i_printer]["poll_time"] = 0

        self.connect("all")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        del self.printers
        pass

    def connect(self, printer_name):
        if printer_name == "all":
            for i_printer in self.printers.keys():
                self.printers[i_printer]["client"] = None
                self.connect(i_printer)

        # TODO: implement something like this for offline printers only - needs to also handle printers going offline?

        else:
            try:
                print(f"Connecting to {printer_name}... ", end="")
                self.printers[printer_name]["client"] = octorest.OctoRest(
                    url="http://" + self.printers[printer_name]["ip"]
                        + ":" + self.printers[printer_name]["port"],
                    apikey=self.printers[printer_name]["apikey"])
                print("Success")
            except ConnectionError as e:
                # print(f"Connection error: {e}")
                print("Failed")
            except RuntimeError as e:
                # print(f"Runtime error: {e}")
                print("Failed")
            except TypeError as e:
                # print(f"Type error: {e}")
                print("Failed")

            self.update(printer_name)

    def update(self, printer_name, queue_running=[]):
        if printer_name == "all":
            for i_printer in self.printers.keys():
                self.update(i_printer)
        else:
            if self.printers[printer_name]["client"]:
                self.printers[printer_name]["details"] = self.printers[printer_name]["client"].job_info()
                self.printers[printer_name]["poll_time"] = int(time.time())

                if self.printers[printer_name]["details"]['state'].lower() == "operational" and printer_name not in queue_running:
                    self.printers[printer_name]["details"]['state'] = "available"

                if self.printers[printer_name]["details"]['state'].lower() == "operational" and printer_name in queue_running:
                    self.printers[printer_name]["details"]['state'] = "finished"

                if self.printers[printer_name]["details"]['state'].lower() == "printing" and printer_name not in queue_running:
                    self.printers[printer_name]["details"]['state'] = "queue_error"
            else:
                self.printers[printer_name]["details"] = {"state": "offline"}
                # "poll_time" remains unchanged

            print(self.printers[printer_name]["details"]["state"])

    def upload(self, printer_name, filename, path=""):
        return self.printers[printer_name]["client"].upload(filename, path=path)

    def run_print(self, printer_name, filename):
        self.printers[printer_name]["client"].select(filename, print=True)

    def cancel_print(self, printer_name):
        self.printers[printer_name]["client"].cancel()
        t0 = time.time()
        while self.printers[printer_name]["client"].printer()['state']['flags']['cancelling']:
            time.sleep(0.5)
        time.sleep(0.5)
        return time.time() - t0

    def clear_files(self, printer_name):
        for file in self.printers[printer_name]["client"].files()["files"]:
            try:
                self.printers[printer_name]["client"].delete(file["display"])
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

    printer_secrets = json.loads(decrypted)["printers"]

    fleet = PrintFleet(printer_secrets)
    fleet.connect()
    for name, data in fleet.printers.items():
        print(f"{name}:\n{data}")
    fleet.update("all")
    fleet.upload("rob", "testPrint_no_extrude.gcode")
    print("upload complete")