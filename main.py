from spreadsheet import Spreadsheet, Drive
import timeIt


if __name__ == '__main__':
    sheet = Spreadsheet()
    drive = Drive()
    sheet.load_queue_sheet()

    with timeIt.Timer("Get Cells"):
        sheet.queue_sheet.cell(2, 15).value
        sheet.queue_sheet.cell(3, 15).value
        sheet.queue_sheet.cell(4, 15).value
        sheet.queue_sheet.cell(5, 15).value

    file_id = '1k-GMjGqOcsurrn_7KsFZBQ0xRp7_VpXx'
    filename = 'test.gcode'

    with timeIt.Timer("Get Gcode"):
        drive.download_file(file_id, filename)