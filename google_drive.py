import io

from oauth2client.service_account import ServiceAccountCredentials

from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.discovery import build


class Drive:
    def __init__(self, google_secrets):
        self.secrets = google_secrets

        self.scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        self.creds = ServiceAccountCredentials.from_json_keyfile_dict(self.secrets["tokens"]["serviceaccount"],
                                                                      self.scope)
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
