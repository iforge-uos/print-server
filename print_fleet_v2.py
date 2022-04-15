import octorest
from requests.exceptions import ConnectionError
import json
import time
from cryptography.fernet import Fernet
import multiprocessing


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

    def thread_connect(self, param_dict):
        client = octorest.OctoRest(
            url="http://" + param_dict["ip"]
                + ":" + param_dict["port"],
            apikey=param_dict["apikey"])
        param_dict["client"] = client

    def connect(self, printer_name):
        if printer_name == "all":
            for i_printer in self.printers.keys():
                self.printers[i_printer]["client"] = None
                self.connect(i_printer)

        # TODO: implement something like this for offline printers only - needs to also handle printers going offline?

        else:
            print(f"Connecting to {printer_name:10s}...\t", end="")
            # self.printers[printer_name]["client"] = octorest.OctoRest(
            #     url="http://" + self.printers[printer_name]["ip"]
            #         + ":" + self.printers[printer_name]["port"],
            #     apikey=self.printers[printer_name]["apikey"])

            arg_return_dict = multiprocessing.Manager().dict()
            arg_return_dict["ip"] = self.printers[printer_name]["ip"]
            arg_return_dict["port"] = self.printers[printer_name]["port"]
            arg_return_dict["apikey"] = self.printers[printer_name]["apikey"]
            arg_return_dict["client"] = self.printers[printer_name]["client"]

            p = multiprocessing.Process(target=self.thread_connect, args=(arg_return_dict,))
            p.start()
            p.join(5)

            if p.is_alive():
                p.terminate()
                p.join()

            self.printers[printer_name]["client"] = arg_return_dict["client"]

            if not self.printers[printer_name]["client"]:
                self.printers[printer_name]["details"] = {'state': "offline"}
                # print("Failed")

            try:
                # attempt to get job_info - will except if octopi is disconnected from printer?
                self.printers[printer_name]["client"].job_info()
                self.printers[printer_name]["details"] = {'state': "operational"}
                print("Success")
            except AttributeError or ConnectionError or RuntimeError or TypeError as e:
                # print(f"Connection error: {e}")
                self.printers[printer_name]["details"] = {'state': "offline"}
                print("Failed")

            self.update(printer_name)

    def update(self, printer_name, queue_running=[]):
        if printer_name == "all":
            for i_printer in self.printers.keys():
                self.update(i_printer, queue_running)

        else:
            if self.printers[printer_name]["details"]["state"] != "offline":
                try:
                    self.printers[printer_name]["details"] = self.printers[printer_name]["client"].job_info()
                    # Can't be bothered dealing with this state, just wait until it has cleared
                    while self.printers[printer_name]["details"]['state'] == "Connecting":
                        time.sleep(0.5)
                        self.printers[printer_name]["details"] = self.printers[printer_name]["client"].job_info()

                    if "error" in self.printers[printer_name]["details"]:
                        self.printers[printer_name]["details"]['state'] = "error"
                    else:
                        self.printers[printer_name]["details"]["status"] = self.printers[printer_name]['client'].printer()

                    # fix bad standards from octorest
                    self.printers[printer_name]["details"]["state"] = self.printers[printer_name]["details"]["state"].lower()

                    self.printers[printer_name]["poll_time"] = int(time.time())

                    if self.printers[printer_name]["details"]['state'] == "operational" and printer_name not in queue_running:
                        self.printers[printer_name]["details"]['state'] = "available"

                    if self.printers[printer_name]["details"]['state'] == "operational" and printer_name in queue_running:
                        self.printers[printer_name]["details"]['state'] = "finished"

                    if self.printers[printer_name]["details"]['state'] == "printing" and printer_name not in queue_running:
                        self.printers[printer_name]["details"]['state'] = "queue_error"
                except ConnectionError:
                    self.printers[printer_name]["details"] = {"state": "offline"}
            else:
                pass
                # "poll_time" remains unchanged

            # print(f"{printer_name:8s}\t-\t{self.printers[printer_name]['details']['state']}")

    def upload(self, printer_name, filename, path=""):
        print(f"Uploading {filename} to {printer_name}...\t", end="")
        val = self.printers[printer_name]["client"].upload(filename, path=path)
        print("Complete")
        return val

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
