#!/usr/bin/env python3

# Date: 2019-09-26
# Author: Anton Svensson (asvens37)

"""
Parsing of diagnosic file SSDB. Returns dict of DIDs (Name, ID, and Size)
Usage: python3 parse_ssdb.py --ssdb <ssdb.xml>
Output: dict in file named after the daig part number
"""

import logging
import argparse
import os
from lxml import etree as ET

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

### Constants ###
OUTPUT_FOLDER = 'output/'

HVBM_SW_APP = './/ECU[@Name="HVBM"]/SWs/SW[@Type="APP"]'
SERV_22 = './/Service[@ID="22"]/DataIdentifiers/DataIdentifier'
HVBM_SW_APP3 = './/ECU'
DIAG_PART = 'DiagnosticPartNumber'


### Code ###
def parse_some_args():
    """Get the command line input, using the defined flags."""
    parser = argparse.ArgumentParser(description='Compare generated diag arxmls with DTC-matrix data.')
    parser.add_argument("--ssdb", help="input ssdb xml file", type=str, action='store', dest='ssdb',)
    ret_args = parser.parse_args()
    return ret_args

def parseXml(ssdb_path):
    """Parse given ssdb and return a dict with relevant data."""
    tree = ET.parse(ssdb_path)
    root = tree.getroot()
    did_dict = {}

    for hvbm_app in root.findall(HVBM_SW_APP):
        DIAG_PART_NUM = hvbm_app.attrib[DIAG_PART]
        print(DIAG_PART_NUM)
        print(hvbm_app.attrib["Name"])
        for did in hvbm_app.findall(SERV_22):
            # did.attrib is a dict containing the info we need
            print(did.attrib["Name"])
            parent_id = "22"
            did_key = parent_id + did.attrib["ID"]
            did_dict[did_key] = did.attrib
    return did_dict, DIAG_PART_NUM

def create_folder(path):
    """If folder does not exisists, then it will be created."""
    if not os.path.isdir(path):
        os.makedirs(path)

def write_dict(path, data):
    """Write dict to a json file."""
    with open(path, 'w+') as f:
        LOGGER.info('Writing dict to %s', path)
        head = "parse_ssdb_dict = "
        f.write(head + str(data))

def main(margs):
    """Parse diagnostic file and output the data in a file."""
    if margs.ssdb:
        print(margs.ssdb)
        d_dict, diag_num = parseXml(margs.ssdb)
        dig_num_washed = diag_num.replace(" ", "_")
        create_folder(OUTPUT_FOLDER)
        file_name = '%s/did_from_%s.py' % (OUTPUT_FOLDER, dig_num_washed)
        write_dict(file_name, d_dict)

if __name__ == "__main__":
    # Boilerplate to launch the main function with the command line arguments.
    ARGS = parse_some_args()
    main(ARGS)
