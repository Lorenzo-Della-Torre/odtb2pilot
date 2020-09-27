#!/usr/bin/env python3

""" Upadete the test cases to include the files from the modules in flat structure """

import os

#FOLDER = "test_folder"
FOLDER = "Implement_MEP2_Support_EOL_def"

def update_files_incl(test_folder):
    """ Modify exisiting scripts to do correct imports """
    for file in os.listdir(test_folder):
        if file.endswith(".py"):
            with open(test_folder + '/' + file, "r") as f:
                py_text = f.readlines()
            for line in py_text:
                if line.startswith("import"):
                    print(line)
                elif line.startswith("from"):
                    print(f'yaya {line}')

if __name__ == "__main__":
    # Boilerplate to launch the main function with the command line arguments.
    update_files_incl(FOLDER)
