print(2)
import argparse
import os
from ..bubble import Bubble

def main():
    cla = argparse.ArgumentParser()

    # file path 
    cla.add_argument(
        '-f',
        '--file',
        dest='file_path_alias',
        metavar='FILE_PATH_ALIAS',
        help='Shortcut alias for the file path'
    )

    args = cla.parse_args()

    base_file_path = args.file_path_alias
    file_path = os.path.abspath(base_file_path)

    scaner = Bubble(base_path=file_path)
    scaner.scan()





if __name__ == "__main__":
    raise SystemExit(main())