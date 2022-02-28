import time
from main_backend import Backend


def get_number_in_list(elem_list):
    i = 0
    for i, elem in enumerate(elem_list):
        print(f"{i}.\t{elem}")
        if i > 15:
            break

    print("Enter number to select ('c' to cancel)")
    n = None
    while True:
        n = input()
        try:
            n = int(n)
        except (ValueError, TypeError):
            if n == "c":
                return -1
            if n == "l":
                return -2

        if n in list(range(i+1)):
            return n

        print(f"{n} not recognised, try again")


def list_printers(backend):
    print(f"Current printer status':")
    for printer in backend.fleet.printers.keys():
        print(f"{printer:20s} - {backend.fleet.printers[printer]['details']['state']}")


def print_print(backend):
    available_printers = []
    for i_printer in backend.printers.keys():
        if backend.printers[i_printer]["details"]["state"] == "available":
            available_printers.append(i_printer)

    if len(available_printers) == 0:
        print("No available printers, try again later")
        return

    backend.queue.update()
    joblist = backend.queue.get_jobs()
    do_level_print = False

    if joblist.shape[0] == 0:  # if none free, wait and restart loop
        print("\nNo jobs queued, try again later")
        return

    print("\nCurrent joblist:")

    n = get_number_in_list([f"{job[0]:20s}"
                            f"\t{time.strftime('%H:%M:%S', time.gmtime(job[3] * 24 * 60 * 60)):8s}"
                            f"\t{job[7]}"
                            for job in joblist.loc[:].values.tolist()])
    if n == -1:  # cancel action
        return
    if n == -2:  # levelling print
        do_level_print = True
    else:
        backend.queue.select_by_id(joblist.loc[:, "Unique ID"].values[n])

    print("Available printers:")

    n = get_number_in_list(available_printers)
    if n == -1:
        return

    if not do_level_print:
        backend.do_print(available_printers[n])
    else:
        level_print_id = "1VeY6MftN5HmBQ4uVGZw_FNZT8KfvY3R9"  # TODO: MOVE THIS

        backend.queue.gcode_drive.download_file(level_print_id, "bed_test.gcode")
        backend.fleet.upload(available_printers[n], "bed_test.gcode")
        backend.fleet.run_print(available_printers[n], "bed_test.gcode")


def finish_print(backend):
    finished_printers = []
    for i_printer in backend.printers.keys():
        if backend.printers[i_printer]["details"]["state"] == "finished":
            finished_printers.append(i_printer)

    if len(finished_printers) == 0:
        print("No printers finished, try again later")
        return

    print("Select printer to process:")

    n = get_number_in_list(finished_printers)
    if n == -1:
        return

    requeue = False
    comment = ""

    print("Was the print successful? [Complete/Failed]")
    while True:
        cf = input().upper()
        if cf in ['COMPLETE', 'FAILED', 'C', 'F']:
            break
        print(f"{cf} not recognised, try again")

    if cf in ["FAILED", "F"]:
        cf = "Failed"

        print("Re-Queue the print? [Yes/No]")
        while True:
            yn = input().upper()
            if yn in ['YES', 'Y', 'NO', 'N']:
                break
            print(f"{yn} not recognised, try again")

        if yn in ['YES', 'Y']:
            requeue = True

        if not requeue:
            print(f"Please enter failure comment for printer: {finished_printers[n]}")
            comment = input()
    else:
        cf = "Complete"

    backend.end_print(finished_printers[n], cf, requeue, comment)


def cancel_print(backend):
    printing_printers = []
    for i_printer in backend.printers.keys():
        if backend.printers[i_printer]["details"]["state"] == "printing":
            printing_printers.append(i_printer)

    if len(printing_printers) == 0:
        print("No printing printers, try again later")
        return

    print("Select printer to cancel:")

    n = get_number_in_list(printing_printers)
    if n == -1:
        return

    print("Re-Queue the print? [Yes/No]")
    while True:
        yn = input().upper()
        if yn in ['YES', 'Y', 'NO', 'N']:
            break
        print(f"{yn} not recognised, try again")

    if yn in ['YES', 'Y']:
        requeue = True
    else:
        requeue = False

    comment = ""
    if not requeue:
        print(f"Please enter failure comment for printer: {printing_printers[n]}")
        comment = input()

    backend.cancel_print(printing_printers[n], requeue, comment)

    print(f"Go and check {printing_printers[n]} is clear and ready to print again.")
    time.sleep(10)

if __name__ == '__main__':
    # parser = argparse.ArgumentParser(description='iForge 3D Print Queue Management System')
    # parser.add_argument('secrets_key', type=str,
    #                     help='decryption key for secrets.json')
    #
    # args = parser.parse_args()
    # secrets_key = args.secrets_key

    backend = Backend(printer_type="Ultimaker")

    # start with some information
    backend.update()
    list_printers(backend)

    loop = True
    while loop:  # loop = False  # only run single loop for testing

        print("\nSelect action:\n"
              "'l'\t-\tList\n"
              "'p'\t-\tPrint\n"
              "'f'\t-\tFinish print handling (Complete/Fail)\n"
              "'c'\t-\tCancel print\n"
              "'r'\t-\tRefresh printers (slow)")
        choice = input().upper()

        backend.update()

        if choice == "L":  # list status'
            list_printers(backend)

        elif choice == "P":  # select print and printer
            print_print(backend)

        elif choice == "F":  # unhandled, will select "finished" print and mark complete/fail
            finish_print(backend)

        elif choice == "C":  # unhandled, will select "finished" print and mark complete/fail
            cancel_print(backend)

        elif choice == "R":  # unhandled, will select "finished" print and mark complete/fail
            backend.connect()

        elif choice in ["Q"]:
            exit()
