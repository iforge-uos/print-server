import io
import json

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# from oauth2client import file, client, tools
# from httplib2 import Http

from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.discovery import build


class Drive:
    def __init__(self):
        self.secrets = {}
        self.scope = []
        self.creds = []
        self.drive_service = []

        self.load_vars()
        self.auth()

    def load_vars(self):
        with open("secrets.json") as file:
            self.secrets = json.load(file)

    def auth(self):
        self.scope = self.secrets["scope"]  # ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        self.creds = ServiceAccountCredentials.from_json_keyfile_dict(self.secrets["tokens"]["serviceaccount"], self.scope)
        self.drive_service = build('drive', 'v3', credentials=self.creds)

    def download_file(self, file_id, filename):
        # Get file from Google Drive
        request = self.drive_service.files().get_media(fileId=file_id)
        fh = io.FileIO(filename, mode='wb')
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        # print("Download: {}% complete".format(int(0 * 100.0)))
        while done is False:
            status, done = downloader.next_chunk()
            # print("Download: {}% complete".format(int(status.progress() * 100.0)))


class Spreadsheet:
    def __init__(self):
        self.vars = {}
        self.scope = []
        self.creds = []
        self.gspread_creds = []
        self.queue_sheet = []

        self.load_vars()
        self.auth()
        self.load_queue_sheet()

    def load_vars(self):
        with open("secrets.json") as file:
            self.vars = json.load(file)

    def auth(self):
        self.scope = self.vars["scope"]  # ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        self.creds = ServiceAccountCredentials.from_json_keyfile_dict(self.vars["tokens"]["serviceaccount"], self.scope)
        self.gspread_creds = gspread.authorize(self.creds)

    def load_queue_sheet(self):
        self.queue_sheet = self.gspread_creds.open_by_key(self.vars["tokens"]["sheet"]).get_worksheet(1)

    def find_status_rows(self, search_str, printer_type=""):
        """
        :param search_str: String to match (case-sensitive)
        :type search_str: string
        :param printer_type: Filter results by printer_type "Prusa" / "Ultimaker" / ""
        :type printer_type: string
        :return out_rows: List of rows from sheet
        """
        out_rows = []
        for cell in self.queue_sheet.findall(search_str):
            if cell.col == 9:  # only search "Status" column
                if printer_type == "" or printer_type == self.get_cell_value(cell.row, 10):
                    out_rows.append(self.queue_sheet.row_values(cell.row))
        return out_rows

    def get_cell_value(self, row, col):
        return self.queue_sheet.cell(row, col).value

    def set_cell_value(self, row, col, value):
        self.queue_sheet.update_cell(row, col, value)
