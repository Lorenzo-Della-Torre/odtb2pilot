#!/usr/bin/env python3

""" Move files from hierach folder structure to new flat structure """

import shutil
import os

SRC_FOLDER = "temp1"
DEST_FOLDER = "temp2"

def move_subfiles_to_flat(src_folder, dest_folder):
    """ Find and move all python files from given parent directory """
    cnt = 0
    listOfFiles = []
    for root, dirs, files in os.walk(src_folder):
        listOfFiles += [os.path.join(root, file) for file in files if file.endswith(".py")]
    print(f'list of files: {listOfFiles}')

    for full_path in listOfFiles:
        shutil.move(full_path, DEST_FOLDER)


if __name__ == "__main__":
    # Boilerplate to launch the main function with the command line arguments.
    move_subfiles_to_flat(SRC_FOLDER, DEST_FOLDER)
