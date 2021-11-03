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
        print("Download: {}% complete".format(int(0 * 100.0)))
        while done is False:
            status, done = downloader.next_chunk()
            print("Download: {}% complete".format(int(status.progress() * 100.0)))


class Spreadsheet:
    def __init__(self):
        self.vars = {}
        self.scope = []
        self.creds = []
        self.gspread_creds = []
        self.queue_sheet = []

        self.load_vars()
        self.auth()

    def load_vars(self):
        with open("secrets.json") as file:
            self.vars = json.load(file)

    def auth(self):
        self.scope = self.vars["scope"]  # ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        self.creds = ServiceAccountCredentials.from_json_keyfile_dict(self.vars["tokens"]["serviceaccount"], self.scope)
        self.gspread_creds = gspread.authorize(self.creds)

    def load_queue_sheet(self):
        self.queue_sheet = self.gspread_creds.open_by_key(self.vars["tokens"]["sheet"]).get_worksheet(1)
