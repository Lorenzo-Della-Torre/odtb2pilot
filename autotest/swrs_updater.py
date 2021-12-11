"""
/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

#!/usr/bin/env python
"""
Creates scripts with new revision and refers to older revision of script
"""

import logging
import argparse
import os
import sys
import re
from os.path import join
from os.path import isfile
import req_parser.rif_swrs_to_graph as rif_mod

# Logging has different levels: DEBUG, INFO, WARNING, ERROR, and CRITICAL
# Set the level you want to have printout in the console.
logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
OWN_ID = "Own UUID"
PARENT_ID = "Parent UUID"
VER_ID = "Version id"
ID = 'ID'
TYPE_LIST = ["REQPROD"] # Only interested in the REQPRODS
IMPORT_SCRIPT_TXT = 'Import script - Inherited from older version of requirement'
RE_REQPROD_ID = re.compile(r'e_(?P<reqprod>\d+)_(?P<var>[a-zA-Z]*|-)_(?P<rev>\d+)_(?P<desc>.*).py',
                           flags=re.IGNORECASE)

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
    parser.add_argument("--scriptfolder",
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


def is_not_import_script(script_folder, file_name):
    '''
    Check if it is valid test script.
    i.e. not an import script or an unreadable script.
    '''
    file_path = join(script_folder, file_name)

    with open(file_path, encoding='utf-8') as file:
        try:
            if IMPORT_SCRIPT_TXT in file.read():
                return False
        except Exception as exception: # pylint: disable=broad-except
            logger.info("%s (%s)", file_path, exception)
            return False
    return True


def get_content(old_file_name):
    '''
    The content which will be written to the import script.
    '''
    content = ('\'\'\'' + IMPORT_SCRIPT_TXT + '\'\'\'\n\n'
               'from ' + old_file_name.removesuffix('.py') + ' import run\n\n'
               'if __name__ == \'__main__\':\n'
               '    run()\n'
              )
    return content


def create_import_script(script_folder, old_file_name, file_name):
    '''
    Creates the import script
    '''
    file_path = join(script_folder, file_name)
    file = open(file_path, "x")
    content = get_content(old_file_name)
    file.write(content)
    file.close()


def check_against_swrs(reqprod_dict, e_match, script_folder, file_name):
    '''
    Checks if the reqprod id is in the SWRS dictionary.
    If it exists, then check if it is a newer revision and
    create new script if it is a newer revision and not already exists.
    '''
    reqprod_obj = dict()
    reqprod = str(e_match.group('reqprod'))
    var = str(e_match.group('var'))
    # In some cases we have removed the hyphen from the script name,
    # but we still want to use it for comparison. So we set var to '-'
    if var == '':
        var = '-'
    rev = str(e_match.group('rev'))
    desc = e_match.group('desc').lower()

    if reqprod in reqprod_dict:
        # Is this a proper script or is it only an import-script
        if is_not_import_script(script_folder, file_name):
            reqprod_obj = reqprod_dict[reqprod]
            new_var = reqprod_obj.get('Variant', 'VAR')
            new_rev = reqprod_obj.get('Revision', 'REV')
            # Is the variant and revision in the swrs dict same as the current one?
            if (var == new_var and rev == new_rev):
                logger.info("No new revision found (%s) - Skipping", join(script_folder, file_name))
            else:
                # We want to avoid create scripts with hyphen(-) in the name, so we remove it.
                if new_var == '-':
                    new_var = ''
                new_file_name = f'e_{reqprod}_{new_var}_{new_rev}_{desc}.py'
                # Does it already exist a script for this revision?
                exists = isfile(join(script_folder, new_file_name))
                if not exists:
                    logger.info("New revision found - Creating (%s)", new_file_name)
                    create_import_script(script_folder, file_name, new_file_name)
                else:
                    logger.info("File already exists (%s) - Skipping", new_file_name)
        else:
            logger.info("This is an import script (%s) - Skipping", file_name)
        return True
    return False


def check_scripts(reqprod_dict, script_folder):
    """ Check if there is a newer revision of the script """
    # Check in all subfolders
    for root, _, files in os.walk(script_folder):
        for file in files:
            #Does the filename match the regexp pattern?
            e_match = RE_REQPROD_ID.match(file)
            if e_match:
                check_against_swrs(reqprod_dict, e_match, root, file)
            else:
                logger.info("Not a reqprod script (%s) - Skipping", file)


def main(margs):
    """ Main function """
    reqprod_dict = swrs_parse(margs)
    check_scripts(reqprod_dict, margs.script_folder)


if __name__ == "__main__":
    # Boilerplate to launch the main function with the command line arguments.
    ARGS = parse_some_args()
    main(ARGS)
