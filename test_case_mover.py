#!/usr/bin/env python3

""" Move files from hierach folder structure to new flat structure """

import shutil
import os

SRC_FOLDER = "test_cases"
DEST_FOLDER = ""

def move_subfiles_to_flat(src_folder, dest_folder):
    """ Find and move all python files from given parent directory """
    cnt = 0
    for root, dirs, files in os.walk(src_folder):
        for file in files:
            if file.endswith(".py"):
                print(file)
                cnt += 1
    print(f'There were {cnt} files in da folder!!')


if __name__ == "__main__":
    # Boilerplate to launch the main function with the command line arguments.
    move_subfiles_to_flat(SRC_FOLDER, DEST_FOLDER)
