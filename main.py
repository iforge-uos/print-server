import print_fleet
import print_queue
import json
from cryptography.fernet import Fernet


class Backend:
    def __init__(self):
        self.secrets = {}
        self.load_secrets()

        self.printer_status_dict = {}
        self.queue = print_queue.PrintQueue(self.secrets["google_secrets"])
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
        self.fleet.update_status(self.queue.get_running_printers())
        self.printer_status_dict = self.fleet.get_status()


if __name__ == '__main__':
    # parser = argparse.ArgumentParser(description='iForge 3D Print Queue Management System')
    # parser.add_argument('secrets_key', type=str,
    #                     help='decryption key for secrets.json')
    #
    # args = parser.parse_args()
    # secrets_key = args.secrets_key

    backend = Backend()

    loop = True
    while loop:  # loop = False  # only run single loop for testing

        backend.update()

        print("Select action: 'l' List status, 'p' run a Print, 'c' handle Completed print")
        choice = input()
        if choice == "l":  # list status'
            print(f"Current printer status:")
            print(f"{len(backend.printer_status_dict['available'])} / {len(backend.fleet.printers)} - Available")
            print(f"{len(backend.printer_status_dict['printing'])} / {len(backend.fleet.printers)} - Printing")
            print(f"{len(backend.printer_status_dict['finished'])} / {len(backend.fleet.printers)} - Finished")
            print(f"{len(backend.printer_status_dict['invalid'])} / {len(backend.fleet.printers)} - Invalid")
            print(f"{len(backend.printer_status_dict['offline'])} / {len(backend.fleet.printers)} - Offline")

        elif choice == "p":  # select print and printer
            if len(backend.printer_status_dict["available"]) == 0:
                print("No available printers, try again later")
                continue

            backend.queue.set_printer_type("Prusa")
            backend.queue.set_status_type("Queued")

            backend.queue.update_joblist()
            joblist = backend.queue.get_jobs()

            if len(joblist) == 0:  # if none free, wait and restart loop
                print("\nNo jobs queued, try again later")
                continue

            print("\nCurrent joblist:")
            for i, job in enumerate(joblist):
                print(f"{i}.\t{job[0]:20s}\t{job[3]:8s}\t{job[6]}")

            # select a job by number
            print("\nEnter job number to select:")
            n = None
            while n not in list(range(0, len(joblist))):
                n = int(input())
            backend.queue.select_job(n)
            # filename = queue.download_job()
            filename = "testPrint.gcode"  # firmware version checks freeze prints - use test print instead of downloaded file

            print("Available printers:")
            for printer_name in backend.printer_status_dict['available']:
                print(f" - {printer_name}")

            # select a job by number
            print("\nEnter printer name to select:")
            selection_name = ""
            while selection_name not in backend.printer_status_dict['available']:
                selection_name = input()
                if selection_name not in backend.printer_status_dict['available']:
                    print(f"{selection_name} printer not available")
            backend.fleet.select_printer(selection_name)
            backend.fleet.add_print(filename)
            backend.fleet.run_print(filename)

            # TODO: Update spreadsheet

        elif choice == "c":  # unhandled, will select "finished" print and mark complete/fail
            if len(backend.printer_status_dict["finished"]) == 0:
                print("No printers finished, try again later")
                continue
