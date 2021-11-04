from spreadsheet import Spreadsheet, Drive


class PrintQueue:
    def __init__(self):
        self.running_prints = []
        self.joblist = []
        self.next_job = []
        self.printer_type = ""
        self.status_type = "Queued"

        self.printSheet = Spreadsheet()

        self.gcodeDrive = Drive()

    def set_printer_type(self, type):
        self.printer_type = type

    def set_status_type(self, type):  # for debug only - allows search for other status' in queue
        self.status_type = type

    def update_joblist(self):
        self.joblist = []
        with Spreadsheet() as ps:
            for row in ps.find_status_rows(self.status_type, self.printer_type):
                self.joblist.append(row)

        queueAwaitingApproval = []
        for i, row in enumerate(self.joblist):
            if row[6] == "Awaiting Approval":
                queueAwaitingApproval.append(self.joblist.pop(i))

    def print_joblist(self):
        print("Current joblist:")
        for job in self.joblist:
            print(job)

    def get_next_job(self):
        if len(self.joblist) > 0:
            self.job = self.joblist.pop(0)
            return [0,self.job]
        else:
            # print(f"No queued jobs for {self.printer_type} printers")
            return [1,[]]

    def download_job(self):
        job_filename = self.job[14] + '.gcode'
        self.gcodeDrive.download_file(self.job[14], job_filename)
        return job_filename

