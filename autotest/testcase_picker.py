"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

#!/usr/bin/env python
"""
Script to rename scripts according to SWRS
"""

import logging
import argparse
import os
import sys
import re
import yaml
from pathlib import Path
import req_parser.rif_swrs_to_graph as rif_mod
import req_parser.csv_swrs_to_graph as csv_parser
from blacklisted_tests_handler import match_swrs_with_yml

# Logging has different levels: DEBUG, INFO, WARNING, ERROR, and CRITICAL
# Set the level you want to have printout in the console.
logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)
LOGGER = logging.getLogger(__name__)

# Constants
OWN_ID = "Own UUID"
PARENT_ID = "Parent UUID"
VER_ID = "Version id"
ID = 'ID'
TYPE_LIST = ["REQPROD"] # Only interested in the REQPRODS

RE_FILE_NAME = re.compile(r'^(e|cw)_(?P<reqprod>\d+)_(?P<var>[a-zA-Z]*|-)_?(?P<rev>\d+)$',
                          flags=re.IGNORECASE)

def parse_some_args():
    """Get the command line input, using the defined flags."""
    parser = argparse.ArgumentParser(description='Picks the desired testscripts from a selection')
    parser.add_argument("--swrs",
                        help="Elektra rif export, xml-file. SWRS file with requirements which "\
                        "should be tested.",
                        type=str,
                        action='store',
                        dest='swrs')
    parser.add_argument("--txtfile",
                        help="Textfile with list of files which should be tested",
                        type=str,
                        action='store',
                        dest='txt_file')
    parser.add_argument("--scripts",
                        help="List of files which should be tested",
                        type=str,
                        action='append',
                        dest='scripts')
    parser.add_argument("--scriptfolder",
                        help="Folder where the scripts are located",
                        type=str,
                        action='store',
                        dest='script_folder',
                        default='./')
    ret_args = parser.parse_args()
    return ret_args


def swrs_parse(swrs):
    """
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
    """
    reqprod_dict = dict()
    # check the extension of swrs export file:
    # 1- 'xml' --> Elektra export   --> use xml parser
    if swrs.endswith('.xml'):
        sp_dict, spobj_dict, _ = rif_mod.parse_rif_to_dicts(swrs)
        col_names = rif_mod.create_col_names(sp_dict, TYPE_LIST)
        for type_name in TYPE_LIST:
            for obj_id in spobj_dict[type_name]:
                reqprod_obj = dict()
                reqprod_id = spobj_dict[type_name][obj_id].get(ID)
                for _, col in enumerate(col_names, 1):
                    if col not in (OWN_ID, PARENT_ID, VER_ID):
                        reqprod_obj[col] = spobj_dict[type_name][obj_id].get(col, "-")
                reqprod_dict[str(reqprod_id)] = reqprod_obj
    # 2- 'csv' --> CarWeaver export --> use csv parser
    elif swrs.endswith('.csv'):
        reqprod_dict = csv_parser.parse_csv_to_dicts(swrs)
    # 3- unknown format --> pass and return empty dict
    else: pass
    
    return reqprod_dict


def match_f(req, var, rev, reqprod_dict):
    """
    Checks if the reqprod id is in the SWRS dictionary.
    If it exists, then return True. Otherwise False
    """
    req_obj = dict()
    match = False

    if req in reqprod_dict:
        req_obj = reqprod_dict[req]
        d_var = req_obj.get('Variant', 'VAR')
        d_rev = req_obj.get('Revision', 'REV')
        if (d_var == var and d_rev == rev):
            match = True
    return match

def load_reqprod_map():
    map_file_path = str(Path(__file__).parent.parent)
    print("The path is: {}".format(map_file_path))
    with open(map_file_path + '/req_script_mapping.yml') as mapping_file:
        req_mapping_dict = yaml.safe_load(mapping_file)
    return req_mapping_dict

def script_picker(file, req_mapping_dict, reqprod_dict):
    # extract file name from the long path
    file_name = Path(file).stem
    for key, value in req_mapping_dict.items():
        # if file name found in mapping file
        if file_name == key:
            # for all the entries for a file in mapping
            for req in value.split(" "):
                # if the reqprod present in the input swrs list
                if match_checker(req, reqprod_dict):
                    return True, req
    return False, None


def match_checker(reqprod, reqprod_dict):
    """ Checks if the reqprod matches with the SWRS list """
    fn_regexp = RE_FILE_NAME.match(reqprod)

    if fn_regexp:
        req = str(fn_regexp.group('reqprod'))
        var = str(fn_regexp.group('var'))
        # In some cases we have removed the hyphen from the script name,
        # but we still want to use it for comparison. So we set var to '-'
        if var == '':
            var = '-'
        rev = str(fn_regexp.group('rev'))
        match = match_f(req, var, rev, reqprod_dict)
        return match

def filter_files(reqprod_dict, script_folder):
    """ Rename files according to SWRS """
    included = list()
    excluded = list()

    # load the reqprod mapping file into a dictionary
    req_mapping_dict = load_reqprod_map()

    for root, _, files in os.walk(script_folder): # For root and each subfolder
        for file in files:  # For each file
            match, reqprod = script_picker(file, req_mapping_dict, reqprod_dict)
            file_path = os.path.join(root, file)
            if match and file_path.endswith('.py'):
                LOGGER.debug('%s', match)
                included.append(file_path + "-->" + reqprod)
            else: # Not matching rev and variant
                LOGGER.debug('No match! %s', file)
                excluded.append(file_path)

    return included, excluded


def match_list(input_fl, script_folder):
    """
    Match files in script_folder (and subfolders) with input_fl list
    """
    included = list()
    excluded = list()
    LOGGER.debug('input_fl: %s', input_fl)

    for root, _, files in os.walk(script_folder): # For root and each subfolder
        for file in files:  # For each file
            file_path = os.path.join(root, file)
            if file in input_fl:
                LOGGER.debug('Included! %s', file)
                included.append(file_path)
            else:
                LOGGER.debug('Excluded! %s', file)
                excluded.append(file_path)
    return included, excluded


def read_file(file_name):
    """
    Read file and return content in form of a list
    """
    files_for_test = list()
    with open(file_name, encoding='utf8') as file:
        script_names = file.readlines()
    for script_name in script_names:
        files_for_test.append(script_name.rstrip()) # removing a trailing newline
    return files_for_test


def pp_result(included):
    """
    Prints the list
    When using the old batchfile we use the output on stdout as input
    when executing the scripts instead of the returning lists
    Using print because we should never turn this off
    """
    for script in included:
        print(script)

def pp_dict_result(include):
    """Print a dictionary to stdout

    Args:
        include (dictionary): A dictionary containing dictionaries
    """

    for category, scripts in include.items():
        print(category)
        for reqprod_id, info in scripts.items():
            print(reqprod_id + " | " + info)


def complete_test(script_folder):
    """
    Will look through the script folder (and subfolders) and return all files ending with .py
    in a list.
    """
    included = list()
    excluded = list()

    for root, _, files in os.walk(script_folder):
        LOGGER.debug('Root = %s', root)

        for file in files:
            file_path = os.path.join(root, file)
            if file.endswith('.py'):
                LOGGER.debug('Included! %s', file)
                included.append(file_path)
            else:
                LOGGER.debug('Excluded! %s', file)
                excluded.append(file_path)
    return included, excluded


def execute(swrs, txt_file, scripts, script_folder):
    """
    This file is used when executing from another python script
    And from main when running
    """

    included = list()
    if swrs: #SWRS argument
        swrs_dict = swrs_parse(swrs)
        matching_reqprods, swrs_dict_modified = match_swrs_with_yml(swrs_dict)
        included, excluded = filter_files(swrs_dict_modified, script_folder)
        pp_result(included)
        pp_dict_result(matching_reqprods)
    elif txt_file: #Textfile argument
        files_from_file = read_file(txt_file)
        included, excluded = match_list(files_from_file, script_folder)
        pp_result(included)
    elif scripts: #script argument
        included, excluded = match_list(scripts, script_folder)
        pp_result(included)
    else: # Test everything in folder and subfolders
        included, excluded = complete_test(script_folder)
        pp_result(included)
    return included, excluded


def main(margs):
    """
    Main function
    When using the old batchfile we use the output on stdout as input
    when executing the scripts instead of the returning lists
    """
    execute(margs.swrs, margs.txt_file, margs.scripts, margs.script_folder)


if __name__ == "__main__":
    # Boilerplate to launch the main function with the command line arguments.
    ARGS = parse_some_args()
    main(ARGS)
