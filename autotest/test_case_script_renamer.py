#!/usr/bin/env python
"""
Script to rename scripts according to SWRS
"""

import logging
import argparse
import os
import re
import shutil
import req_parser.rif_swrs_to_graph as rif_mod

# Logging has different levels: DEBUG, INFO, WARNING, ERROR, and CRITICAL
# Set the level you want to have printout in the console.
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

# Constants
OWN_ID = "Own UUID"
PARENT_ID = "Parent UUID"
VER_ID = "Version id"
ID = 'ID'
TYPE_LIST = ["REQPROD"] # Only interested in the REQPRODS


RE_REQPROD_ID = re.compile(r'\s*BSW_REQPROD_(?P<reqprod>\d+)_(?P<desc>\w+).py', flags=re.IGNORECASE)

def parse_some_args():
    """Get the command line input, using the defined flags."""
    parser = argparse.ArgumentParser(description='Parse Elektra rif export,'\
        'and give result on prefered format.')
    parser.add_argument("--elektra",
                        help="Elektra rif export, xml-file",
                        type=str,
                        action='store',
                        dest='rif',
                        default='NOTE-SWRS-33754905-01-2.xml')
    parser.add_argument("--script_folder",
                        help="Folder where the scripts are located",
                        type=str,
                        action='store',
                        dest='script_folder',
                        default='test_folder/automated')
    ret_args = parser.parse_args()
    return ret_args


def swrs_parse(margs):
    '''
    Parsing the SWRS file returning a dictionary with reqprod objects.
    The reqprod id's are the keys.
    The reqprod objects are also dictionaries.
    They contain information like:
        ID
        Revision
        Variant
        Name
        Object
        State
        ...
    '''
    sp_dict, spobj_dict, _ = rif_mod.parse_rif_to_dicts(margs.rif)
    col_names = rif_mod.create_col_names(sp_dict, TYPE_LIST)
    reqprod_dict = dict()

    for type_name in TYPE_LIST:
        for obj_id in spobj_dict[type_name]:
            reqprod_obj = dict()
            reqprod_id = spobj_dict[type_name][obj_id].get(ID)
            for _, col in enumerate(col_names, 1):
                if col not in (OWN_ID, PARENT_ID, VER_ID):
                    reqprod_obj[col] = spobj_dict[type_name][obj_id].get(col, "-")
            reqprod_dict[str(reqprod_id)] = reqprod_obj
    return reqprod_dict


def rename_file(script_folder, file_name, new_file_name):
    '''
    Makes a copy of the script with the new file name
    '''
    file_and_path = script_folder + '/' + file_name
    new_file_and_path = script_folder + '/' + new_file_name
    shutil.copy(file_and_path, new_file_and_path) # Make a copy with the new name


def gen_file_name(req_id, var, rev, desc):
    '''
    Returns the new file name
    '''
    if (req_id == '' or var == '' or rev == ''):
        logging.warning('req_id(%s), var(%s) or rev(%s)', req_id, var, rev)
        return ''
    file_name = f'e_{req_id}_{var}_{rev}_{desc}'
    return file_name


def get_file_name(reqprod_dict, req_id, desc):
    '''
    Checks if the reqprod id is in the SWRS dictionary.
    If it exists, then create and return new file name.
    If it doesn't then return empty string
    '''
    reqprod_obj = dict()
    file_name = str()

    if req_id in reqprod_dict:
        reqprod_obj = reqprod_dict[req_id]
        var = reqprod_obj.get('Variant', 'VAR')
        rev = reqprod_obj.get('Revision', 'REV')
        file_name = gen_file_name(req_id, var, rev, desc)
    return file_name


def rename_files(reqprod_dict, script_folder):
    """ Rename files according to SWRS """
    for file in os.listdir(script_folder):
        e_match = RE_REQPROD_ID.match(file)
        if e_match and file.endswith(".py"):
            e_key = str(e_match.group('reqprod'))
            desc = e_match.group('desc')
            new_file_name = get_file_name(reqprod_dict, e_key, desc)
            if new_file_name:
                rename_file(script_folder, file, new_file_name)


def main(margs):
    """ Main function """
    reqprod_dict = swrs_parse(margs)
    rename_files(reqprod_dict, margs.script_folder)


if __name__ == "__main__":
    # Boilerplate to launch the main function with the command line arguments.
    ARGS = parse_some_args()
    main(ARGS)
