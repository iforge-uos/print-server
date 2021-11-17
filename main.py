import backend
import time


def get_number_in_list(elem_list):
    i = 0
    for i, elem in enumerate(elem_list):
        print(f"{i}.\t{elem}")

    print("Enter number to select ('c' to cancel)")
    n = None
    while True:
        n = input()
        try:
            n = int(n)
        except TypeError:
            if n == "c":
                return -1

        if n in list(range(i+1)):
            return n

        print(f"{n} not recognised, try again")


def list_printers(backend):
    print(f"Current printer status':")
    for printer in backend.fleet.printer_access.keys():
        print(f"{printer:20s} - {backend.fleet.printers[printer]['status']}")


def print_print(backend):
    if len(backend.printer_status_dict["available"]) == 0:
        print("No available printers, try again later")
        return

    backend.prusa_queue.update()
    joblist = backend.prusa_queue.get_jobs()

    if joblist.shape[0] == 0:  # if none free, wait and restart loop
        print("\nNo jobs queued, try again later")
        return

    print("\nCurrent joblist:")

    n = get_number_in_list([f"{job[0]:20s}"
                            f"\t{time.strftime('%H:%M:%S', time.gmtime(job[3] * 24 * 60 * 60)):8s}"
                            f"\t{job[7]}"
                            for job in joblist.loc[:].values.tolist()])

    if n == -1:
        return
    #
    # for i, job in enumerate(joblist.loc[:].values.tolist()):
    #     print(f"{i}.\t{job[0]:20s}\t{time.strftime('%H:%M:%S', time.gmtime(job[3] * 24 * 60 * 60)):8s}\t{job[7]}")
    #
    # # select a print by number
    # print("\nEnter number to select:")
    # n = None
    # while True:
    #     n = input()
    #     try:
    #         n = int(n)
    #     except TypeError:
    #         pass
    #
    #     if n in list(range(0, joblist.shape[0])):
    #         break
    #     print(f"{n} not recognised, try again")

    backend.prusa_queue.select_by_id(joblist.loc[:, "Unique ID"].values[n])

    print("Available printers:")

    n = get_number_in_list(backend.printer_status_dict['available'])

    if n == -1:
        return

    # for printer_name in backend.printer_status_dict['available']:
    #     print(f" - {printer_name}")
    #
    # # select a selected by number
    # print("\nEnter printer name to select:")
    # while True:
    #     printer_name = input()
    #     if printer_name in backend.printer_status_dict['available']:
    #         break
    #     print(f"{printer_name} not recognised, try again")

    backend.do_print(backend.printer_status_dict['available'][n])


def finish_print(backend):
    if len(backend.printer_status_dict["finished"]) == 0:
        print("No printers finished, try again later")
        return

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

        print("Select action: 'l' List status, 'p' run a Print, 'f' handle Completed print, 'x' to exit")
        choice = input()

        backend.update()

        if choice == "l":  # list status'
            list_printers(backend)

        elif choice == "p":  # select print and printer
            print_print(backend)

        elif choice == "f":  # unhandled, will select "finished" print and mark complete/fail
            finish_print(backend)

        elif choice in ["x", "q"]:
            exit()
