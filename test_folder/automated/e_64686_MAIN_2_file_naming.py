"""

/*********************************************************************************/



Copyright © 2023 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 64686
version: 2
title: File Naming
purpose: >
    To identify the release of the VBF file.

description: >
    All delivered or released VBF files shall be named the same as the corresponding released
    software part number which consist of (sw_part_number and sw_version) with an extension of
    ".VBF

    Examples:
    A VBF file with a header entry of
                    sw_part_number = "31808832";
                    sw_version = "AB";
    shall utilize the file name of 31808832AB.VBF

    A VBF file with a header entry of
                    sw_part_number = "31808832";
                    sw_version = "A";
    shall utilize the file name of 31808832A.VBF

    Delta files shall be released with a filename reference to its source and target version by
    including the software part number and software version of source and target in the delta
    filename.

    Example:
        sw_part_number = "31808832"; // Target version part no
        sw_version = "AB"; // Target version
        sw_current_part_number = "31808831"; // Source/current version part no
        sw_current_version = "A";
        The format of a delta filename shall be:
        <sw_current_part_number><sw_current_version><separator><sw_part_number><sw_version>.VBF

        A VBF file containing delta and the header data above shall have the name:
        31808831A _31808832AB.VBF

details: >
    Used for checking that delivered or released VBF files are named the same as the corresponding
    released software part number which consist of (sw_part_number and sw_version) with an
    extension of ".VBF
"""

import time
import re
import sys
import logging
import os.path as path_mod
from os import listdir
from datetime import datetime
from hilding.dut import Dut
from hilding.dut import DutTestError

# Regular Expressions
RE_FILE_NAME = re.compile(r'(?P<file_name_sw_part_number>\d{8})\s*(?P<file_name_sw_version>\w+)')
RE_SW_PART_NUMBER = re.compile(r'\s*sw_part_number\s*=\s*"?(?P<sw_part_number>\w*)')
RE_SW_VERSION = re.compile(r'\s*sw_version\s*=\s*"?(?P<sw_version>\w*)')
RE_SW_PART_TYPE = re.compile(r'\s*sw_part_type\s*=\s*(?P<sw_part_type>\w*)')


def validate_vbf_name(infile):
    """
    action:
        Reads the vbf-files and compares the file name with the information in the header
    expected_result:
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

    # Open file
    with open(infile, encoding="ascii", errors="surrogateescape") as vbf_file:
        # os.path is a module which helps splitting file and path (works with both
        # forward slashes (/) and backward slashes (\)
        file_name = path_mod.basename(infile)

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
        logging.info('\n----------------\nsw_part_number = %s\nsw_version = %s\nsw_part_type = %s',
                    sw_part_number, sw_version, sw_part_type)
    else:
        # Did not find the necessary header information to make the comparison
        logging.fatal('\nDid not find the necessary header information to make the comparison')
        return False

    # Compare
    retval = compare_part_number_and_version(sw_part_number, sw_version, file_name)
    return retval


def compare_part_number_and_version(sw_part_number, sw_version, file_name):
    """
    action:
        Splits the file name into part number and version and compares them with the
        part number and version from the file header (input parameters to this function)
    expected_result:
        True - If they match
        False - If they do not match
    """
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


def run():
    """Call other functions from here"""
    dut = Dut()
    start_time = dut.start()
    result = False

    try:
        vbfs = listdir(dut.conf.rig.vbf_path)
        paths_to_vbfs = [str(dut.conf.rig.vbf_path) + "/" + x for x in vbfs]
        if not paths_to_vbfs:
            logging.error("VBFs not found, expected in %s ... aborting", dut.conf.rig.vbf_path)
            sys.exit()

        # A second result variable because we want the other one to be False until the end in case
        # we get an exception.
        test_result = True

        # Creating generator for looping paths_to_vbfs while test result is True
        gen = (vbf for vbf in paths_to_vbfs if test_result if vbf.endswith('.vbf'))

        # Looping using the generator
        for vbf in gen:
            # Validating file names
            test_result = validate_vbf_name(vbf)

        result = test_result

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        # Can't use postcondition since we have not communicated with the ECU
        logging.info("Testcase end: %s", datetime.now())
        logging.info("Time needed for testrun (seconds): %s", int(time.time() - start_time))

        if result:
            logging.info("Testcase result: PASSED")
        else:
            logging.info("Testcase result: FAILED")

if __name__ == "__main__":
    run()
