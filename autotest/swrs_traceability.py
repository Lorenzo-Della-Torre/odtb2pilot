"""
/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

#!/usr/bin/env python3

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


RE_REQPROD_ID = re.compile(r'\s*BSW_REQPROD_(?P<reqprod>\d+)_', flags=re.IGNORECASE)

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


def file_append(script_folder, file_name, text):
    '''
    Write 'text' to the top of the 'file'.
    The file is located in the 'script_folder'.
    '''
    file_path = script_folder + '/' + file_name
    shutil.copy(file_path, file_path + '~') # Make a backup copy with ~ at the end

    with open(file_path, "r+", encoding='utf8') as file:
        content = file.read()
        file.seek(0, 0) #get to the first position
        file.write(text.rstrip('\r\n') + '\n' + content)


def gen_trace_info(req_id, variant, rev):
    '''
    Returns the trace string
    '''
    if (req_id == '' or variant == '' or rev == ''):
        return 'REQ_DICT = {}'
    return 'REQ_DICT = {"e_' + req_id + '_' + variant + '": [' + rev + ']}'


def gen_trace_text(reqprod_dict, req_id):
    '''
    Checks if the reqprod id is in the SWRS dictionary.
    If it exists, then create traceabilty information.
    If it doesn't then create empty traceability dictionary.
    '''
    reqprod_obj = dict()
    trace_text = str()

    if req_id in reqprod_dict:
        reqprod_obj = reqprod_dict[req_id]
        variant = reqprod_obj.get('Variant', 'VAR')
        rev = reqprod_obj.get('Revision', 'REV')
        trace_text = gen_trace_info(req_id, variant, rev)
    else:
        # When the script's id is not in the SWRS
        trace_text = gen_trace_info(req_id, '', '')
        LOGGER.warning('Key not found: %s', req_id)
    return trace_text


def update_files(reqprod_dict, script_folder):
    """ Modify exisiting scripts to do correct imports """
    for file in os.listdir(script_folder):
        e_match = RE_REQPROD_ID.match(file)
        if e_match and file.endswith(".py"):
            e_key = str(e_match.group('reqprod'))
            trace_text = gen_trace_text(reqprod_dict, e_key)
            file_append(script_folder, file, trace_text)


def main(margs):
    """ Main function """
    reqprod_dict = swrs_parse(margs)
    update_files(reqprod_dict, margs.script_folder)


if __name__ == "__main__":
    # Boilerplate to launch the main function with the command line arguments.
    ARGS = parse_some_args()
    main(ARGS)
