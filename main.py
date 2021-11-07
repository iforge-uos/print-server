import print_fleet
import print_queue
import timeIt
import time
import json
import argparse
from cryptography.fernet import Fernet

if __name__ == '__main__':
    # parser = argparse.ArgumentParser(description='iForge 3D Print Queue Management System')
    # parser.add_argument('secrets_key', type=str,
    #                     help='decryption key for secrets.json')
    #
    # args = parser.parse_args()
    # secrets_key = args.secrets_key

    with open('secrets.key', 'rb') as file:
        key = file.read()

    # load plain secrets
    with open('secrets.json.enc', 'rb') as f:
        data = f.read()

    # encrypt
    fernet = Fernet(key)
    decrypted = fernet.decrypt(data)

    sleep_time = 10

    secret_vars = json.loads(decrypted)

    queue = print_queue.PrintQueue(secret_vars["google_secrets"])
    with print_fleet.PrintFleet(secret_vars["printers"]) as fleet:
        loop = True
        while loop:  # loop = False  # only run single loop for testing

            fleet.update_status(queue.get_running_printers())
            printer_status_dict = fleet.get_status()

            print("Select action: 'l' List status, 'p' run a Print, 'c' handle Completed print")
            choice = input()
            if choice == "l":  # list status'
                print(f"Current printer status:")
                print(f"{len(printer_status_dict['available'])} / {len(fleet.printers)} - Available")
                print(f"{len(printer_status_dict['printing'])} / {len(fleet.printers)} - Printing")
                print(f"{len(printer_status_dict['finished'])} / {len(fleet.printers)} - Finished")
                print(f"{len(printer_status_dict['invalid'])} / {len(fleet.printers)} - Invalid")

            elif choice == "p":  # select print and printer
                if len(printer_status_dict["available"]) == 0:
                    print("No available printers, try again later")
                    continue

                queue.set_printer_type("Prusa")
                queue.set_status_type("Queued")

                queue.update_joblist()
                joblist = queue.get_jobs()

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
                queue.select_job(n)
                filename = queue.download_job()
                filename = "testPrint.gcode"  # firmware version checks freeze prints - use test print instead of downloaded file

                print("Available printers:")
                for printer_name in printer_status_dict['available']:
                    print(f" - {printer_name}")

                # select a job by number
                print("\nEnter printer name to select:")
                selection_name = ""
                while selection_name not in printer_status_dict['available']:
                    selection_name = input()
                    if selection_name not in printer_status_dict['available']:
                        print(f"{selection_name} printer not available")
                fleet.select_printer(selection_name)
                fleet.add_print(filename)
                fleet.run_print(filename)

                # TODO: Update spreadsheet

            elif choice == "c":  # unhandled, will select "finished" print and mark complete/fail
                if len(printer_status_dict["finished"]) == 0:
                    print("No printers finished, try again later")
                    continue
