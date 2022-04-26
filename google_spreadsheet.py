import copy
import logging
import random
import threading
import time

import gspread
import pandas
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
        self.last_update = None
        self.df_lock = threading.Lock()

        # Start update daemon
        update_daemon = threading.Thread(target=self._update_data, daemon=True)
        update_daemon.start()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # disconnect?
        return

    def get_data(self):
        with self.df_lock:
            df = copy.deepcopy(self.dataframe)
        return df

    def _update_data(self):
        s = 5.0
        while True:
            try:
                with self.df_lock:
                    self.dataframe = pd.DataFrame(self.queue_sheet.get_all_records(value_render_option="FORMULA", head=3))
                self.last_update = time.time()
                time.sleep(5)
            except gspread.exceptions.APIError as e:
                # temporary error, keep trying
                logging.warning(f"APIError: {e}\nRetrying in {s:.2f} seconds")
                s += random.random() * 5.0  # Increase backoff
                time.sleep(s)

    def force_update_data(self):
        while True:
            try:
                with self.df_lock:
                    self.dataframe = pd.DataFrame(self.queue_sheet.get_all_records(value_render_option="FORMULA", head=3))
                self.last_update = time.time()
                return
            except gspread.exceptions.APIError as e:
                # temporary error, keep trying
                logging.error(f"APIError: {e}\nForce update so not retrying")
                with self.df_lock:
                    self.dataframe = pd.DataFrame()

    def get_running(self):
        df = self.get_data()
        # return dict of two dataframes, one for each printer type, for rows where "Status" column is "Running"
        prusa_df = df.loc[(df.loc[:, "Status"] == "Running") & (df.loc[:, "Printer Type"] == "Prusa")]
        ulti_df = df.loc[(df.loc[:, "Status"] == "Running") & (df.loc[:, "Printer Type"] == "Ultimaker")]
        return {"Prusa": prusa_df, "Ultimaker": ulti_df}

    def get_queued(self):
        df = self.get_data()
        # return dict of two dataframes, one for each printer type, for rows where "Status" column is "Queued"
        try:
            prusa_df = df.loc[(df.loc[:, "Status"] == "Queued") & (df.loc[:, "Printer Type"] == "Prusa")]
        except KeyError:
            prusa_df = pandas.DataFrame()

        try:
            ulti_df = df.loc[(df.loc[:, "Status"] == "Queued") & (df.loc[:, "Printer Type"] == "Ultimaker")]
        except KeyError:
            ulti_df = pandas.DataFrame()

        return {"Prusa": prusa_df, "Ultimaker": ulti_df}

    def get_cell_value(self, row, col):
        return self.queue_sheet.cell(row, col).value

    def set_row(self, data):
        df = self.get_data()
        # self.update_data()  # ensure data is up to date
        row = df.index[df.loc[:, "Unique ID"] == data.loc[:, "Unique ID"].values[0]].tolist()
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
    # queue.update_data()
    print(queue.get_running()["Prusa"]["Printer"].tolist())

    pd.reset_option('display.max_rows')
    pd.reset_option('display.max_columns')
    pd.reset_option('display.width')
    pd.reset_option('display.max_colwidth')
