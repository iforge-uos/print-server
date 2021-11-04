import print_interact
import print_queue
import timeIt


if __name__ == '__main__':
    pq = print_queue.PrintQueue()
    with print_interact.PrintHub() as pi:
        # print(pi.list_printers())
        pq.set_printer_type("Prusa")
        pq.set_status_type("Running")
        pq.update_joblist()
        pq.print_joblist()
        job_details = pq.get_next_job()
        print("\nNext job details:")
        print(job_details)
        if job_details[0]:
            print(f"No queued jobs to do")
        else:
            available_printers = []
            for printer in pi.list_printers():
                if pi.get_printer_status(printer) == "Waiting":
                    available_printers.append(printer)

            # print(available_printers)

            # TODO: improve printer selection (include catch for printbed empty)
            printer = available_printers.pop(0)

            # job_filename = pq.download_job()

