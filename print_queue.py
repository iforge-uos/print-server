from spreadsheet import Spreadsheet
from drive import Drive
import pandas as pd


class PrintQueue:
    def __init__(self, google_secrets, printer_type):
        self.google_secrets = google_secrets
        self.joblist = pd.DataFrame()
        self.job = pd.DataFrame()
        self.printer_type = printer_type

        self.print_sheet = Spreadsheet(self.google_secrets)

        self.gcode_drive = Drive(self.google_secrets)

    def update(self):
        self.print_sheet.update_data()
        self.joblist = self.print_sheet.get_queued()[self.printer_type]

    def get_running_printers(self):
        return self.print_sheet.get_running()[self.printer_type]["Printer"].tolist()

    def get_jobs(self):
        return self.joblist

    def select_job(self, n):
        self.job = self.joblist.iloc[n]

    def download_job(self):
        job_filename = self.job.values[13] + '.gcode'
        print(f"Downloading: {self.job.values[0]} - {self.job.values[3]} - {self.job.values[6]}, {job_filename}")
        self.gcode_drive.download_file(self.job.values[13], job_filename)
        print("Download complete")
        return job_filename
