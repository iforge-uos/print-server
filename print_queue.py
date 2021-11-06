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

    def get_jobs(self):
        return self.joblist

    def select_job(self, n):
        self.job = self.joblist[n]

    def download_job(self):
        job_filename = self.job[14] + '.gcode'
        print(f"Downloading: {self.job[0]} - {self.job[3]} - {self.job[6]}, {job_filename}")
        self.gcodeDrive.download_file(self.job[14], job_filename)
        print("Download complete")
        return job_filename

