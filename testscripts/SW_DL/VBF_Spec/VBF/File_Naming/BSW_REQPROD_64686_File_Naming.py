#!/usr/bin/env python3

# Date: 2020-01-08
# Authors: Fredrik Jansson (fjansso8)

"""
Used for checking that delivered or released VBF files are named the same as the corresponding
released software part number which consist of (sw_part_number and sw_version) with an extension
of ".VBF
Usage:  python REQ_64686_File_Naming.py --vbf_file 32325019AA.vbf
Output: Testcase result: PASSED/FAILED
"""

import time
import argparse
import logging
import sys
import ntpath
from datetime import datetime
import re


# Regular Expressions
RE_FILE_NAME = re.compile('(?P<file_name_sw_part_number>\d{8})\s*(?P<file_name_sw_version>\w+)')
RE_SW_PART_NUMBER = re.compile('\s*sw_part_number\s*=\s*"?(?P<sw_part_number>\w*)')
RE_SW_VERSION = re.compile('\s*sw_version\s*=\s*"?(?P<sw_version>\w*)')
RE_SW_PART_TYPE = re.compile('\s*sw_part_type\s*=\s*(?P<sw_part_type>\w*)')

### Code ###
def parse_some_args():
    """Get the command line input, using the defined flags."""
    parser = argparse.ArgumentParser(description='Check format of VBF file')
    parser.add_argument("--vbf_file", help="VBF-File", type=str,
                        action='store', dest='vbf_file', required=True,)
    return parser.parse_args()


def validate_vbf_name(infile):
    """
    Returns result of the validation
    True - If file_name match the information in the vbf file header
    False - If it doesn't match
    """

    # Variables
    match_sw_part_number = False
    match_sw_version = False
    match_sw_part_type = False
    sw_part_number = None
    sw_version = None
    sw_part_type = None
    UNSUPPORTED_PART_TYPES = ['SBL', 'ESS']

    # Open file
    with open(infile, encoding="ascii", errors="surrogateescape") as vbf_file:
        # ntpath is a module which helps splitting file and path (works with both
        # forward slashes (/) and backward slashes (\)
        file_name = ntpath.basename(infile)

        # Iterate line by line
        for line in vbf_file:
            # Break if we have all the information we need
            if sw_part_number and sw_version and sw_part_type:
                break
            # If we don't have a match, keep looking in each line
            if not match_sw_part_number:
                match_sw_part_number = RE_SW_PART_NUMBER.match(line)
            if not match_sw_version:
                match_sw_version = RE_SW_VERSION.match(line)
            if not match_sw_part_type:
                match_sw_part_type = RE_SW_PART_TYPE.match(line)

    # If we have all necessary info from the vbf file header
    if match_sw_part_number and match_sw_version and match_sw_part_type:
        sw_part_number = match_sw_part_number.group('sw_part_number')
        sw_version = match_sw_version.group('sw_version')
        sw_part_type = match_sw_part_type.group('sw_part_type')
        logging.info('\nsw_part_number = %s\nsw_version = %s\nsw_part_type = %s', sw_part_number,
                     sw_version, sw_part_type)
    else:
        # Did not find the necessary header information to make the comparison
        logging.fatal('\nDid not find the necessary header information to make the comparison')
        return False

    # Some VBF files are not supported
    if sw_part_type in UNSUPPORTED_PART_TYPES:
        logging.fatal('\nSW_PART_TYPE: %s Not supported!', sw_part_type)
        return False

    # Compare
    retval = compare_part_number_and_version(sw_part_number, sw_version, file_name)
    return retval


def compare_part_number_and_version(sw_part_number, sw_version, file_name):
    '''
    Splits the file name into part number and version and compares them with the
    part number and version from the file header (input parameters to this function)
    '''
    result = True
    match_file_name = RE_FILE_NAME.match(file_name)

    file_name_sw_part_number = None
    file_name_sw_version = None
    if match_file_name:
        file_name_sw_part_number = match_file_name.group('file_name_sw_part_number')
    if match_file_name:
        file_name_sw_version = match_file_name.group('file_name_sw_version')

    # Comparing part numbers
    if sw_part_number != file_name_sw_part_number:
        logging.fatal('\nPart numbers not matching.\nHeader: %s\nFile name: %s', sw_part_number,
                      file_name_sw_part_number)
        result = False
    # Comparing versions
    if sw_version != file_name_sw_version:
        logging.fatal('\nVersions not matching.\nHeader: %s\nFile name: %s', sw_version,
                      file_name_sw_version)
        result = False
    return result


def main(margs):
    """Call other functions from here"""
    # Setup logging
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

    logging.info('\nTestcase start: %s', datetime.now())
    start_time = time.time()

    # Validating file name
    test_result = validate_vbf_name(margs.vbf_file)

    logging.info('\nTestcase end: %s', datetime.now())
    logging.info('\nTime needed for testrun (seconds): %i', int(time.time() - start_time))

    if test_result:
        logging.info('\nTestcase result: PASSED')
    else:
        logging.info('\nTestcase result: FAILED')


if __name__ == "__main__":
    # Boilerplate to launch the main function with the command line arguments.
    ARGS = parse_some_args()
    main(ARGS)
