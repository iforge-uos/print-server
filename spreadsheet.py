import io
import json

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# from oauth2client import file, client, tools
# from httplib2 import Http

from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.discovery import build


class Drive:
    def __init__(self, google_secrets):
        self.secrets = google_secrets

        self.scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
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
    def __init__(self, google_secrets):
        self.vars = google_secrets
        self.scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        self.creds = ServiceAccountCredentials.from_json_keyfile_dict(self.vars["tokens"]["serviceaccount"], self.scope)
        self.gspread_creds = gspread.authorize(self.creds)
        self.queue_sheet = self.gspread_creds.open_by_key(self.vars["tokens"]["test_sheet"]).get_worksheet(1)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # disconnect?
        return

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
