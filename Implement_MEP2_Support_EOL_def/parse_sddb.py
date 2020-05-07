#!/usr/bin/env python3

# Date: 2020-01-14
# Author: Anton Svensson (asvens37), Fredrik Jansson (fjansso8)

"""
Parsing of diagnosic file SDDB. Returns dict of DIDs (Name, ID, and Size)
Usage: python3 parse_sddb.py --sddb <sddb.xml>
Output: dict in file named after the daig part number
"""

import logging
import argparse
import os
import sys
import pprint
from lxml import etree as ET
import parameters as parammod


#LOGGER = logging.getLogger(__name__)
#LOGGER.setLevel(logging.DEBUG)

### Constants ###
SERV_22 = './/Service[@ID="22"]/DataIdentifiers/DataIdentifier'
RESP_ITEMS = './/ResponseItems/ResponseItem'
FORMULAS = 'Formula'
UNITS = 'Unit'
COMPARE_VALUES = 'CompareValue'
SOFTWARE_LABELS = 'SoftwareLabel'
ECU = './/ECU'
DIAG_PART = 'DiagnosticPartNumber'


### Code ###
def parse_some_args():
    """Get the command line input, using the defined flags."""
    parser = argparse.ArgumentParser(description=
                                     'Compare generated diag arxmls with DTC-matrix data.')
    parser.add_argument("--sddb", help="input sddb xml file", type=str, action='store',
                        dest='sddb', required=True,)
    ret_args = parser.parse_args()
    return ret_args

def ecu_determination(root, mode):
    '''
    Checking in the tree and look for ECU type (HVBM or BECM)
    returns the corresponding search string
    '''
    ecu_type_name = root.find(ECU).attrib['Name']
    software = './/ECU[@Name="%s"]/SWs/SW[@Type="%s"]' % (ecu_type_name, mode)
    return software

def parse_xml_did_info(sddb_path, mode):
    """Parse given sddb and return a dict with relevant data."""
    tree = ET.parse(sddb_path)
    root = tree.getroot()
    did_dict = dict()
    logging.debug(root.attrib)

    # Determine which ECU the SDDB is for
    ecu = ecu_determination(root, mode)
    logging.debug('\n ECU: %s\n', ecu)

    diag_part_num_washed = str()
    for ecu_app in root.findall(ecu):
        diag_part_num = ecu_app.attrib[DIAG_PART]
        diag_part_num_washed = diag_part_num.replace(" ", "_")

        for did in ecu_app.findall(SERV_22):
            # did.attrib is a dict containing the info we need
            parent_id = "22"
            did_key = parent_id + did.attrib["ID"]
            did_dict[did_key] = did.attrib
    return did_dict, diag_part_num_washed

def parse_xml_response_items(sddb_path, mode):
    """Parse given sddb and return a dict with relevant data."""
    tree = ET.parse(sddb_path)
    root = tree.getroot()
    logging.debug(root.attrib)

    # Determine which ECU the SDDB is for
    ecu = ecu_determination(root, mode)
    logging.debug('\n ECU: %s\n', ecu)

    response_items_dict = {}
    for ecu_app in root.findall(ecu):
        logging.info('Name= %s', ecu_app.attrib["Name"])
        for did in ecu_app.findall(SERV_22):
            # did.attrib is a dict containing the info we need
            logging.debug('%s', did.attrib["Name"])
            parent_id = "22"
            did_key = parent_id + did.attrib["ID"]
            response_items_dict[did_key] = []

            for sddb_resp_item in did.findall(RESP_ITEMS):
                logging.debug('      attrib = %s', sddb_resp_item.attrib)
                logging.debug('      Name = %s', sddb_resp_item.attrib['Name'])

                # Makes a new dict with the sddb_resp_item as a base
                resp_item = sddb_resp_item.attrib

                # Adding the rest of the information
                for formula in sddb_resp_item.findall(FORMULAS):
                    logging.debug('          FORMULA = %s', formula.text)
                    resp_item['Formula'] = formula.text
                for unit in sddb_resp_item.findall(UNITS):
                    logging.debug('          UNIT = %s', unit.text)
                    resp_item['Unit'] = unit.text
                for compare_value in sddb_resp_item.findall(COMPARE_VALUES):
                    logging.debug('          COMPARE_VALUE = %s', compare_value.text)
                    resp_item['CompareValue'] = compare_value.text
                for software_label in sddb_resp_item.findall(SOFTWARE_LABELS):
                    logging.debug('          SOFTWARE_LABEL = %s', software_label.text)
                    resp_item['SoftwareLabel'] = software_label.text
                response_items_dict[did_key].append(resp_item)
    return response_items_dict


def create_folder(path):
    """If folder does not exisists, then it will be created."""
    if not os.path.isdir(path):
        os.makedirs(path)

def write_data(path, data, head, mode):
    """Write data to a json file."""
    with open(path, mode) as file:
        logging.debug('Writing dict to %s', path)
        head = "\n\n" + head + " = "
        file.write(head + str(data))

def change_encoding(input_file_name, output_file_name):
    """ Washing script to remove non utf-8 char, until CarCom has fixed their export. """
    with open(output_file_name, 'w+') as washed_file:
        with open(input_file_name, encoding='latin1') as input_file:
            for line in input_file:
                line = bytes(line, 'utf-8').decode('latin1', 'ignore')
                washed_file.write(line)

def wash_xml(input_file_name, output_file_name):
    """ Washing script to remove non utf-8 char, until CarCom has fixed their export. """
    with open(output_file_name, 'w+') as washed_file:
        with open(input_file_name, encoding='latin1') as input_file:
            for line in input_file:
                line = line.replace('°C', 'degC')
                line = line.replace('µC', 'uC')
                line = line.replace(u'\xa0', u' ') #non-breaking space
                washed_file.write(line)

def stringify(string):
    ''' Surround string with hyphens '''
    return '\'' + string + '\''

def main(margs):
    """Parse diagnostic file and output the data in a file."""
    # Setting up logging
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)
    if margs.sddb:
        # Picking only the filename of the path
        input_file_name = margs.sddb.split('\\')[-1]
        create_folder(parammod.OUTPUT_FOLDER)

        # Generate output_file_name based on input_file_name(add _WASHED)
        # Supports both the ending .txt and .sddb
        tmp_output_file_name = input_file_name.replace(".txt", "_")
        tmp_output_file_name = input_file_name.replace(".sddb", "_")
        output_file_name = '%s/%s%s.txt' % (parammod.OUTPUT_FOLDER, tmp_output_file_name, 'WASHED')

        # Read file, decode ugly character to pretty characters, then write it.
        change_encoding(input_file_name, output_file_name)
        # Remove unwanted characters
        wash_xml(input_file_name, output_file_name)

        # Read information from SDDB XML file, put in dicts
        pbl_dict, pbl_diag_part_num = parse_xml_did_info(output_file_name, 'PBL')
        sbl_dict, sbl_diag_part_num = parse_xml_did_info(output_file_name, 'SBL')
        app_dict, app_diag_part_num = parse_xml_did_info(output_file_name, 'APP')
        response_item_dict = parse_xml_response_items(output_file_name, 'APP')

        # File used to write the dicts in
        file_name = '%s/%s.py' % (parammod.OUTPUT_FOLDER, parammod.OUTPUT_FILE_NAME)

        # To make the output nicer
        pretty_print = pprint.PrettyPrinter(indent=4)

        # Write all information to file.
        # First file mode should be w+ so we start with empty file, then we append to that file.
        write_data(file_name, stringify(pbl_diag_part_num), parammod.PBL_PART_NUM_NAME, 'w+')
        write_data(file_name, pretty_print.pformat(pbl_dict), parammod.PBL_DICT_NAME, 'a+')
        write_data(file_name, stringify(sbl_diag_part_num), parammod.SBL_PART_NUM_NAME, 'a+')
        write_data(file_name, pretty_print.pformat(sbl_dict), parammod.SBL_DICT_NAME, 'a+')
        write_data(file_name, stringify(app_diag_part_num), parammod.APP_PART_NUM_NAME, 'a+')
        write_data(file_name, pretty_print.pformat(app_dict), parammod.APP_DICT_NAME, 'a+')
        write_data(file_name, pretty_print.pformat(response_item_dict),
                   parammod.RESP_ITEM_DICT_NAME, 'a+')

if __name__ == "__main__":
    # Boilerplate to launch the main function with the command line arguments.
    ARGS = parse_some_args()
    main(ARGS)
