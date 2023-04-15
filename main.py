import argparse
import config

# parser = argparse.ArgumentParser(description='iForge 3D Print Queue Management System')
# parser.add_argument('secrets_key', type=str,
#                     help='decryption key for secrets.json')
#
# args = parser.parse_args()
# secrets_key = args.secrets_key

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='iForge 3D Print Queue Management System')
    parser.add_argument('--use_db', type=bool, help='Boolean to enable Database Backend (default is Sheet Backend)', default=False)

    args = parser.parse_args()

    if args.use_db:
        config.USE_DB = True

        import frontend_db

        frontend_db.run()

    else:
        config.USE_DB = False

        import frontend_sheet

        frontend_sheet.run()

