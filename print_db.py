import print_queue_api_client as api
import logging


class ResponseError(Exception):
    """Generic error to raise when request returns error"""
    pass


class PrintQueue:
    def __init__(self, db_secrets):
        self.db = api.database_api_factory(server_ip=db_secrets["server_ip"],
                                   server_port=db_secrets["server_port"],
                                   api_key=db_secrets["api_key"])
        self.selected = None  # job id of 'selected' job for operations, only used to aid back-compatibility

    def update(self):
        # stand-in for direct mirroring of `PrintQueue` in `print_sheet.py`
        pass

    def get_running_printers(self):
        resp = self.db.jobs.get('running')
        if resp['error']:
            return []  # TODO: better handling of this, any error just assumes no printers are printing...
        return resp['data']['printer'].to_list()

    def get_jobs(self):
        resp = self.db.jobs.get('queued')
        if resp['error']:
            raise ResponseError(f"Error requesting queued jobs\n"
                                f"message: {resp['message']}")
        return resp['data']

    def select_by_id(self, id):
        self.selected = id

    def select_by_printer(self, printer_name):
        # selecting job by which printer it's on
        resp = self.db.printers.get(printer_name)
        if resp['error']:
            raise ResponseError(f"Error requesting printer: {printer_name}\n"
                                f"message: {resp['message']}")
        printer = resp['data']
        self.selected = printer['job_id'].values[0]

        if self.selected is None:
            logging.warning("printer specified has no job")
            raise KeyError("Printer does not have a job to select")

    def download_selected(self):
        filename = self.selected.loc[:, 'Gcode Filename'].values[0].split(',')[-1][1:-2]
        print("Downloading, please wait...", end="")
        logging.log(f"Downloading print ID: {self.selected}")
        self.gcode_drive.download_file(self.selected.loc[:, 'Unique ID'].values[0], filename)
        logging.log("Download complete")
        print("Download complete")
        return filename

    def mark_running(self, printer_name):
        # Check job is selected
        if self.selected is None:
            logging.warning(f"attempted to start job with no job selected")
            raise ValueError(f"No job selected, cannot start job")

        # Get printer ID from name
        resp = self.db.printers.get(printer_name)
        if resp['error']:
            logging.warning(f"Error locating printer: {printer_name}\n"
                            f"message: {resp['message']}")
            raise ResponseError(f"Error locating printer: {printer_name}\n"
                                f"message: {resp['message']}")
        printer_id = resp['data']['id'].values[0]

        # Start job
        resp = self.db.jobs.start(job_id=self.selected, printer_id=printer_id)
        if resp['error']:
            logging.warning(f"Failed to start job #{self.selected} on printer: #{printer_id} ({printer_name})")
            raise ResponseError(f"Failed to start job #{self.selected} on printer: #{printer_id} ({printer_name})\n"
                                f"message: {resp['message']}")



    def mark_result(self, printer_name, result, requeue=False, comment=""):
        pass

if __name__ == "__main__":
    from cryptography.fernet import Fernet
    import json

    with open('secrets.key', 'rb') as file:
        key = file.read()

    # load plain secrets
    with open('secrets.json.enc', 'rb') as f:
        data = f.read()

    # encrypt
    fernet = Fernet(key)
    decrypted = fernet.decrypt(data)

    secrets = json.loads(decrypted)

    pq = PrintQueue(secrets['db_secrets'])
    # print(pq.db.jobs.get('queued')['data'])
    pq.select_by_printer("Turing")
    print(pq.selected)