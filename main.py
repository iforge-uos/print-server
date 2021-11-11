import backend
import time


if __name__ == '__main__':
    # parser = argparse.ArgumentParser(description='iForge 3D Print Queue Management System')
    # parser.add_argument('secrets_key', type=str,
    #                     help='decryption key for secrets.json')
    #
    # args = parser.parse_args()
    # secrets_key = args.secrets_key

    backend = backend.Backend()

    loop = True
    while loop:  # loop = False  # only run single loop for testing

        print("Select action: 'l' List status, 'p' run a Print, 'c' handle Completed print, 'x' to exit")
        choice = input()

        backend.update()

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

            backend.prusa_queue.update()
            joblist = backend.prusa_queue.get_jobs()

            if joblist.shape[0] == 0:  # if none free, wait and restart loop
                print("\nNo jobs queued, try again later")
                continue

            print("\nCurrent joblist:")
            for i, job in enumerate(joblist.loc[:].values.tolist()):
                print(f"{i}.\t{job[0]:20s}\t{time.strftime('%H:%M:%S', time.gmtime(job[3]*24*60*60)):8s}\t{job[7]}")

            # select a selected by number
            print("\nEnter selected number to select:")
            n = None
            while True:
                n = input()
                try:
                    n = int(n)
                except TypeError:
                    pass

                if n in list(range(0, joblist.shape[0])):
                    break
                print(f"{n} not recognised, try again")

            backend.prusa_queue.select_by_id(joblist.loc[:, "Unique ID"].values[n])

            print("Available printers:")
            for printer_name in backend.printer_status_dict['available']:
                print(f" - {printer_name}")

            # select a selected by number
            print("\nEnter printer name to select:")
            while True:
                printer_name = input()
                if printer_name in backend.printer_status_dict['available']:
                    break
                print(f"{printer_name} not recognised, try again")

            backend.do_print(printer_name)

        elif choice == "c":  # unhandled, will select "finished" print and mark complete/fail
            if len(backend.printer_status_dict["finished"]) == 0:
                print("No printers finished, try again later")
                continue

            print("Finished printers:")
            for printer_name in backend.printer_status_dict['finished']:
                print(f" - {printer_name}")

            # select a selected by number
            print("\nEnter printer name to select:")
            while True:
                printer_name = input()
                if printer_name in backend.printer_status_dict['finished']:
                    break
                print(f"{printer_name} not recognised, try again")

            print("Was the print successful? [Complete/Failed]")
            while True:
                cf = input()
                if cf in ['Complete', 'Failed']:
                    break
                print(f"{cf} not recognised, try again")

            if cf == "Failed":
                print(f"Please enter failure comment for printer: {printer_name}")
                comment = input()
            else:
                comment = ""

            backend.end_print(printer_name, cf, comment)

        elif choice == "x":
            exit()
