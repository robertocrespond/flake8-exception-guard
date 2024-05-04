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
        metavar='FILE_PATH',
        help='Shortcut alias for the file path'
    )

    # entrypoint function name
    cla.add_argument(
        '-e',
        '--entrypoint',
        dest='entrypoint',
        metavar='ENTRYPOINT_FUNCTION_NAME',
        help='Name of function to be used as entrypoint'
    )

    args = cla.parse_args()

    base_file_path = args.file_path_alias
    entrypoint = args.entrypoint
    file_path = os.path.abspath(base_file_path)

    scaner = Bubble(base_path=file_path, entrypoint=entrypoint)
    return scaner.scan()


if __name__ == "__main__":
    raise SystemExit(main())