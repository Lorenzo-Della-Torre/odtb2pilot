#!/usr/bin/env python3

""" Upadete the test cases to include the files from the modules in flat structure """

import os
import re
import shutil

FOLDER = "test_folder"
MOD_FOLDER = "supportfunctions"
GEN_FOLDER = "protogenerated"
CONF_FOLDER = "parameters"

# List of existing files in the new module folders?
## Ensure to add the config files as well (eg odtb_conf.py)

# Loop over the includes/from and check if it is part of internal files
## Then add the prefix

def get_module_file(mod_folder, gen_folder):
    """ Dict to translate includes """
    mod_name_dict = {}
    # odtb_conf file is special, 
    # could do another loop if need
    ODTB_CONF_NAME = 'odtb_conf'
    ODTB_FIX_NAME = f'{CONF_FOLDER}.{ODTB_CONF_NAME}'
    #mod_name_dict[ODTB_CONF_NAME] = f"{CONF_FOLDER}.{ODTB_CONF_NAME}"
    mod_name_dict[ODTB_CONF_NAME] = f"{ODTB_FIX_NAME} as {ODTB_CONF_NAME}"

    for file in os.listdir(mod_folder):
        if file.endswith(".py"):
            file_nosuff = file.split('.')[0]
            print(file_nosuff)
            mod_name_dict[file_nosuff] = f"{MOD_FOLDER}.{file_nosuff}"
    for file in os.listdir(gen_folder):
        if file.endswith(".py"):
            file_nosuff = file.split('.')[0]
            print(file_nosuff)
            mod_name_dict[file_nosuff] = f"{GEN_FOLDER}.{file_nosuff} as {file_nosuff}"
    return mod_name_dict

def replacer_func(name, mod_dict):
    """ if name exists then return the folder name """
    ret_name = name
    if name in mod_dict:
        ret_name = mod_dict[name]
        print(ret_name)
    return ret_name

def dashrepl(matchobj):
    if matchobj.group(0) == '-': return ' '
    else: return '-'

def update_files_incl(test_folder, mod_dict):
    """ Modify exisiting scripts to do correct imports """
    re_import = re.compile(r"import\s+([\w\.]+)")
    re_from = re.compile(r"from\s+(\w+)")
    for file in os.listdir(test_folder):
        if file.endswith(".py"):
            file_path = test_folder + '/' + file
            shutil.move(file_path, file_path + '~')
            dest_file = open(file_path, "wb")

            with open(file_path + '~', "r", encoding='utf8') as f:
                print(file_path)
                py_text = f.readlines()
            for line in py_text:
                match_import = re_import.match(line)
                match_from = re_from.match(line)
                if match_import:
                    #print(line)
                    replace_name = replacer_func(match_import.group(1), mod_dict)
                    tmp_str = re.sub(r'(import\s+)([\w\.]+)(.*)', r'\1' + replace_name + r'\3', line)
                    #print(tmp_str)

                elif match_from:
                    #print(f'yaya {line}')
                    replace_name = replacer_func(match_from.group(1), mod_dict)
                    tmp_str = re.sub(r'(from\s+)(\w+)(.*)', r'\1' + replace_name + r'\3', line)
                    #print(tmp_str)
                else:
                    tmp_str = line
                dest_file.write(tmp_str.encode('utf8'))
            dest_file.close() 

if __name__ == "__main__":
    # Boilerplate to launch the main function with the command line arguments.
    mod_dict = get_module_file(FOLDER + '/' + MOD_FOLDER, FOLDER + '/' + GEN_FOLDER)
    update_files_incl(FOLDER, mod_dict)
    update_files_incl(FOLDER + '/' + MOD_FOLDER, mod_dict)
