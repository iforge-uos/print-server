import time

import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from cryptography.fernet import Fernet
import json
import time


class Spreadsheet:
    def __init__(self, google_secrets):
        self.vars = google_secrets
        self.scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        self.creds = ServiceAccountCredentials.from_json_keyfile_dict(self.vars["tokens"]["serviceaccount"], self.scope)
        self.gspread_creds = gspread.authorize(self.creds)
        self.queue_sheet = self.gspread_creds.open_by_key(self.vars["tokens"]["sheet"]).worksheet("Queue")
        self.dataframe = None
        self.update_data()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # disconnect?
        return

    def update_data(self):
        while True:
            try:
                # TODO: fixme
                """
                breaks here with:
                    requests.exceptions.ReadTimeout: HTTPSConnectionPool(host='sheets.googleapis.com', port=443): Read timed out. (read timeout=120)
                if left active for too long
                """
                self.dataframe = pd.DataFrame(self.queue_sheet.get_all_records(value_render_option="FORMULA", head=3))
                break
            except gspread.exceptions.APIError as e:
                # temporary error, keep trying
                print(f"APIError: {e}\nRetrying every 5 seconds")
                time.sleep(5)

        # example usage
        # print(self.dataframe)
        # print(self.dataframe.loc[:, "prus"] == "Alistair Mitchell")
        # print(self.dataframe.loc[self.dataframe.loc[:, "prus"] == "Alistair Mitchell"])

    def get_printers(self, status):
        result = {}

        self.update_data()
        df = self.dataframe.loc[self.dataframe.loc[:, "Status"] == status]

        printer_types = list(set(df.loc[:, "Printer Type"]))
        for printer_type in printer_types:
            try:
                result[printer_type] = df.loc[
                    (df.loc[:, "Status"] == status) & (df.loc[:, "Printer Type"] == printer_type)]
            except KeyError:
                result[printer_type] = pd.DataFrame()

        return result
    def get_running(self):
        # return dict of two dataframes, one for each printer type, for rows where "Status" column is "Running"
        return self.get_printers("Running")

    def get_queued(self):
        # return dict of two dataframes, one for each printer type, for rows where "Status" column is "Queued"
        return self.get_printers("Queued")

    def get_cell_value(self, row, col):
        return self.queue_sheet.cell(row, col).value

    def set_row(self, data):
        self.update_data()  # ensure data is up to date
        row = self.dataframe.index[self.dataframe.loc[:, "Unique ID"] == data.loc[:, "Unique ID"].values[0]].tolist()
        if len(row) != 1:
            raise TypeError(f"Multiple rows match: {data.loc[:, 'Unique ID']}")

        row = row[0] + 4  # +4 for header & zero-indexing,

        # values = []
        # for val in data.values.tolist():  # elementwise convert numpy numbers to standard numbers
        #     try:
        #         values.append(val.item())
        #     except AttributeError:  # for inconvertible data-types
        #         values.append(val)

        self.queue_sheet.update(f"{row}:{row}", data.values.tolist(), raw=False)  # [values] must be a 2x-nested list to write correctly
        """
        [[1, 2], [3, 4]]        - writes 2x2
        [[1, 2, 3, 4]]          - writes 1x4
        [[1], [2], [3], [4]]    - writes 4x1
        """


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

