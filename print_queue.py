from spreadsheet import Spreadsheet, Drive
import octorest


class PrintQueue:
    def __init__(self):
        self.running_prints = []
        self.joblist = []

        self.printSheet = Spreadsheet()

        self.gcodeDrive = Drive()

    def update_joblist(self):
        self.joblist = []
        for row in self.printSheet.find_status_rows("Queued", "Prusa"):
            self.joblist.append(row)

        queueAwaitingApproval = []
        for i, row in enumerate(self.joblist):
            if row[6] == "Awaiting Approval":
                queueAwaitingApproval.append(self.joblist.pop(i))

    def get_next_job(self):
        if len(self.joblist) > 0:
            filename = 'job.gcode'
            job = self.joblist.pop(0)
            self.gcodeDrive.download_file(job[14], filename)
            return filename
        else:
            return -1