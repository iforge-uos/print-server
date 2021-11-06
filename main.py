import print_fleet
import print_queue
import timeIt
import time


if __name__ == '__main__':
    sleep_time = 10

    queue = print_queue.PrintQueue()
    with print_fleet.PrintFleet("printers.json") as fleet:
        loop = True
        while loop:
            # loop = False  # only run single loop for testing
            # get count of available printers
            available_printers = fleet.get_available_printers()

            if len(available_printers) == 0:  # if none free, wait and restart loop
                print("No printers available, please wait...")
                time.sleep(sleep_time)
                continue

            print(f"Printers available: {len(available_printers)}\n")

            # Setup, mostly for testing
            queue.set_printer_type("Prusa")
            queue.set_status_type("Queued")

            # update and display the joblist from sheet
            queue.update_joblist()
            joblist = queue.get_jobs()

            if len(joblist) == 0:  # if none free, wait and restart loop
                print("No jobs queued, please wait...")
                time.sleep(sleep_time)
                continue

            print("Current joblist:")
            for i, job in enumerate(joblist):
                print(f"{i}.\t{job[0]:20s}\t{job[3]:8s}\t{job[6]}")

            # select a job by number
            print("\nEnter job number to select:")
            n = int(input())
            queue.select_job(n)
            filename = queue.download_job()

            print("Available printers:")
            for printer_name in available_printers.keys():
                print(f" - {printer_name}")

            # select a job by number
            print("\nEnter printer name to select:")
            selection_name = input()
            fleet.select_printer(selection_name)
            fleet.add_print(filename)
            fleet.run_print(filename)
