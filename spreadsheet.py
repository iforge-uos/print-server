import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from cryptography.fernet import Fernet
import json


class Spreadsheet:
    def __init__(self, google_secrets):
        self.vars = google_secrets
        self.scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        self.creds = ServiceAccountCredentials.from_json_keyfile_dict(self.vars["tokens"]["serviceaccount"], self.scope)
        self.gspread_creds = gspread.authorize(self.creds)
        self.queue_sheet = self.gspread_creds.open_by_key(self.vars["tokens"]["test_sheet"]).get_worksheet(1)
        self.dataframe = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # disconnect?
        return

    def update_data(self):
        self.dataframe = pd.DataFrame(self.queue_sheet.get_all_records())

        # example usage
        # print(self.dataframe)
        # print(self.dataframe.loc[:, "prus"] == "Alistair Mitchell")
        # print(self.dataframe.loc[self.dataframe.loc[:, "prus"] == "Alistair Mitchell"])

    def get_running_printers(self):
        running_printers = []

        self.update_data()
        for printer_name in self.dataframe.loc[self.dataframe.loc[:, "Status"] == "Running", "Printer"]:
            running_printers.append(printer_name)

        return running_printers

    #####

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


if __name__ == "__main__":
    with open('secrets.key', 'rb') as file:
        key = file.read()

    # load plain secrets
    with open('secrets.json.enc', 'rb') as f:
        data = f.read()

    # encrypt
    fernet = Fernet(key)
    decrypted = fernet.decrypt(data)

    sleep_time = 10

    secret_vars = json.loads(decrypted)

    queue = Spreadsheet(secret_vars["google_secrets"])
    queue.update_data()
    print(queue.get_running_printers())
