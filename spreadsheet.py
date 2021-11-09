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
        self.update_data()

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

    def get_running(self):
        # return dict of two dataframes, one for each printer type, for rows where "Status" column is "Running"
        prusaDf = self.dataframe.loc[
            (self.dataframe.loc[:, "Status"] == "Running") & (self.dataframe.loc[:, "Printer Type"] == "Prusa")]
        ultiDf = self.dataframe.loc[
            (self.dataframe.loc[:, "Status"] == "Running") & (self.dataframe.loc[:, "Printer Type"] == "Ultimaker")]
        return {"Prusa": prusaDf, "Ultimaker": ultiDf}

    #####

    def get_queued(self):
        # return dict of two dataframes, one for each printer type, for rows where "Status" column is "Queued"
        prusaDf = self.dataframe.loc[
            (self.dataframe.loc[:, "Status"] == "Queued") & (self.dataframe.loc[:, "Printer Type"] == "Prusa")]
        ultiDf = self.dataframe.loc[
            (self.dataframe.loc[:, "Status"] == "Queued") & (self.dataframe.loc[:, "Printer Type"] == "Ultimaker")]
        return {"Prusa": prusaDf, "Ultimaker": ultiDf}

        # out_rows = []
        # for cell in self.queue_sheet.findall(search_str):
        #     if cell.col == 9:  # only search "Status" column
        #         if printer_type == "" or printer_type == self.get_cell_value(cell.row, 10):
        #             out_rows.append(self.queue_sheet.row_values(cell.row))
        # return out_rows

    def get_cell_value(self, row, col):
        return self.queue_sheet.cell(row, col).value

    def set_cell_value(self, row, col, value):
        self.queue_sheet.update_cell(row, col, value)


if __name__ == "__main__":
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)

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
    print(queue.get_running()["Prusa"]["Printer"].tolist())

    pd.reset_option('display.max_rows')
    pd.reset_option('display.max_columns')
    pd.reset_option('display.width')
    pd.reset_option('display.max_colwidth')

