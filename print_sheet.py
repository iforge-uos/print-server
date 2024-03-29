import datetime

from google_spreadsheet import Spreadsheet
from google_drive import Drive
import pandas as pd
import time
import logging


def sheets2date(days_from_epoch):
    """ Convert google sheets raw datetime (days from 30/12/1899 00:00:00) into python datetime """
    sheet_epoch = datetime.datetime(year=1899, month=12, day=30)
    sheet_time = datetime.timedelta(days=days_from_epoch)
    return sheet_epoch + sheet_time


class PrintQueue:
    def __init__(self, google_secrets, printer_type):
        self.google_secrets = google_secrets
        self.joblist = pd.DataFrame()
        self.selected = pd.DataFrame()
        self.printer_type = printer_type

        self.print_sheet = Spreadsheet(self.google_secrets)

        self.gcode_drive = Drive(self.google_secrets)

        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', None)

    def update(self):
        self.print_sheet.update_data()
        self.joblist = pd.DataFrame()
        try:
            self.joblist = self.print_sheet.get_queued()[self.printer_type]
        except KeyError:
            # no prints queued for this printer_type
            pass

    def get_running_printers(self):
        running_list = []
        running_printers = self.print_sheet.get_running()
        if self.printer_type in running_printers.keys():
            running_list = running_printers[self.printer_type]["Printer"].tolist()

        return running_list

    def get_jobs(self):
        return self.joblist

    def select_by_id(self, id):
        self.update()
        self.selected = self.print_sheet.dataframe.loc[self.print_sheet.dataframe.loc[:, "Unique ID"] == id, :].copy()
        if self.selected.shape[0] > 1:  # multiple instances of id
            logging.error("Multiple Unique IDs in dataset")
            raise ValueError("Multiple Unique IDs in dataset")

    def select_by_printer(self, printer_name):
        self.update()
        filtered_queue = self.print_sheet.dataframe.loc[self.print_sheet.dataframe.loc[:, "Status"] == "Running", :]
        self.selected = filtered_queue.loc[self.print_sheet.dataframe.loc[:, "Printer"] == printer_name, :].copy()
        if self.selected.shape[0] > 1:  # multiple instances of printer
            raise ValueError(f"Multiple {printer_name}s in dataset")

    def download_selected(self):
        filename = self.selected.loc[:, 'Gcode Filename'].values[0].split(',')[-1][1:-2]
        print(
            f"Downloading: {self.selected.loc[:, 'Name'].values[0]} - {time.strftime('%H:%M:%S', time.gmtime(self.selected.loc[:, 'Print Time'].values[0] * 24 * 60 * 60))} - {self.selected.loc[:, 'Date Added'].values[0]}, {filename}...\t",
            end="")
        self.gcode_drive.download_file(self.selected.loc[:, 'Unique ID'].values[0], filename)
        print("Complete")
        return filename

    def mark_running(self, printer_name):
        # print(f"Running: {self.selected.loc[:, 'Unique ID'].values[0]}.gcode, on: {printer_name}")
        self.selected.loc[:, "Status"] = "Running"
        self.selected.loc[:, "Printer"] = printer_name
        self.selected.loc[:, "Printed colour"] = "auto-print"
        duration = datetime.timedelta(days=float(self.selected.loc[:, "Print Time"]))
        start_time = datetime.datetime.now()
        end_time = start_time + duration

        self.selected.loc[:, "Printed colour"] = "auto-print"
        self.selected.loc[:, "time print put on"] = start_time.strftime("%d/%m/%Y %H:%M:%S")
        self.selected.loc[:, "time print due"] = end_time.strftime("%d/%m/%Y %H:%M:%S")
        self.selected.loc[:,
        "ETA"] = f"Started: {start_time.strftime('%H:%M:%S')}\nDue at: {end_time.strftime('%H:%M:%S')}"
        self.print_sheet.set_row(self.selected)

    def mark_result(self, printer_name, result, requeue=False, comment=""):
        self.select_by_printer(printer_name)
        # print(f"Completing: {self.selected.loc[:, 'Unique ID'].values[0]}.gcode, on: {printer_name}")
        current_notes = self.selected['Notes'].values[0]
        if requeue:
            self.selected.loc[:, "Status"] = "Queued"
            self.selected.loc[:, "Printer"] = ""
            self.selected.loc[:, "Printed colour"] = ""
            self.selected.loc[:, "time print put on"] = ""
            self.selected.loc[:, "time print due"] = ""
            self.selected.loc[:, "ETA"] = ""

            if current_notes:
                self.selected.loc[:, "Notes"] = f"{current_notes}\nre-queued"
            else:
                self.selected.loc[:, "Notes"] = f"re-queued"
        else:
            self.selected.loc[:, "Status"] = result
            t_now = datetime.datetime.now()
            self.selected.loc[:, "ETA"] = t_now.strftime("%d/%m/%Y")
            self.selected.loc[:, "time taken for print"] = (t_now - sheets2date(
                float(self.selected.loc[:, "Date Added"]))).total_seconds() / datetime.timedelta(days=1).total_seconds()

            if current_notes:
                self.selected.loc[:, "Notes"] = f"{current_notes}\n{comment}"
            else:
                self.selected.loc[:, "Notes"] = f"{comment}"

        self.print_sheet.set_row(self.selected)
