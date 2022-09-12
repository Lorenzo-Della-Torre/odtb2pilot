"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 52283
version: 1
title: Non complete or compatible software(s)
purpose: >
    To define the action when software(s) is/are neither complete nor compatible.

description: >
    If the return value from the Complete & Compatible function is not equal to
    PASSED it means the ECU is either not complete or compatible, and therefore
    the ECU shall go to “programmingSession” state.

details: >
    Verify downloaded software is Complete & Compatible to start the application
    1. Extracting vbf_header, vbf_block, vbf_block_data.
    2. Software download request and verify downloaded software is not Complete, not
       Compatible with manipulated data block and confirm ECU is in “programmingSession”.
"""

import time
import logging
from glob import glob
from hilding.dut import Dut
from hilding.dut import DutTestError
from hilding.conf import Conf
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_service34 import SupportService34
from supportfunctions.support_service36 import SupportService36
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_service37 import SupportService37
from supportfunctions.support_service31 import SupportService31

CNF = Conf()
SSBL = SupportSBL()
SE34 = SupportService34()
SE36 = SupportService36()
SE27 = SupportService27()
SE37 = SupportService37()
SE31 = SupportService31()


def extract_vbf_blocks(vbf_data, vbf_offset):
    """
    Extract all the Verification Block File(VBF) blocks & block data
    Args:
        vbf_data (str): Complete vbf data
        vbf_offset (int): vbf offset
    Returns:
        vbf_block_details (list): list of dictionaries containing blockwise details
                                 (vbf_block, vbf_block_data)
    """
    vbf_blocks_details = []
    # Extract the 1st Vbf Block
    vbf_offset, vbf_block, vbf_block_data = SSBL.block_data_extract(vbf_data, vbf_offset)
    vbf_blocks_details.append({'vbf_block': vbf_block, 'vbf_block_data': vbf_block_data})

    # Extract Remaining Vbf Blocks
    while int(vbf_block['StartAddress']) != 0:
        vbf_offset, vbf_block, vbf_block_data = SSBL.block_data_extract(vbf_data, vbf_offset)
        # Preparing vbf_blocks_details list
        if int(vbf_block['StartAddress']) != 0:
            vbf_blocks_details.append({'vbf_block': vbf_block, 'vbf_block_data': vbf_block_data})

    logging.info("Number of VBF blocks extracted from the VBF file: %s", len(vbf_blocks_details))
    return vbf_blocks_details


def read_vbf(dut, vbf_type):
    """
    Read vbf file and extract vbf header, vbf block and vbf block data
    Args:
        dut (class obj): dut instance
        vbf_type (str): SBL, ESS, DATA or EXE
    Returns:
        vbf_header (dict): vbf header dictionary
        vbf_blocks_details (dict): list of dictionaries containing blockwise details
                                    (vbf_block, vbf_block_data)
    """
    rig_vbf_path = dut.conf.rig.vbf_path
    vbf_file_paths = glob(str(rig_vbf_path) + "/*.vbf")

    if len(vbf_file_paths) > 0:
        for vbf_file_path in vbf_file_paths:
            _, vbf_header, vbf_data, vbf_offset = SSBL.read_vbf_file(vbf_file_path)
            vbf_header = dict(vbf_header)

            if vbf_header['sw_part_type'] == vbf_type:
                SSBL.vbf_header_convert(vbf_header)
                vbf_blocks_details = extract_vbf_blocks(vbf_data, vbf_offset)
                return True, vbf_header, vbf_blocks_details

    logging.error("No %s VBF found in %s", vbf_type, rig_vbf_path)
    return False, None, None


def transfer_data(dut, vbf_header, vbf_block, vbf_block_data):
    """
    Initiate Software Download(SWDL) for a particular VBF block
    Args:
        dut (class object): Dut instance
        vbf_header (dict): VBF file header
        vbf_block (dict): dictionary containing StartAddress, Length & Checksum
        vbf_block_data (str): VBF block data byte string
    Returns:
        bool: True when software download is successful
    """
    result, nbl = SE34.request_block_download(dut, vbf_header, vbf_block)
    if not result:
        logging.error("Test failed: RequestDownload(0x34) request failed")
        return False

    result_36 = SE36.flash_blocks(dut, vbf_block_data, vbf_block, nbl)
    if not result_36:
        logging.error("Test failed: RequestDownload(0x36) request failed")

    result_37 = SE37.transfer_data_exit(dut)
    if not result_37:
        logging.error("Test failed: TransferExit(0x37) request failed")

    return result_36 and result_37


def block_wise_software_download(dut, vbf_header, vbf_blocks_details):
    """
    Blockwise software download(SWDL)
    Args:
        dut (class object): Dut instance
        vbf_header (dict): VBF file header
        vbf_blocks_details (list): list of dictionaries containing blockwise details
                                   (vbf_block, vbf_block_data)
    Returns:
        (bool): True on successful blockwise software download
    """
    # Software Download(SWDL) on all blocks of respective VBF file
    results = []
    for counter, block_details in enumerate(vbf_blocks_details):
        #  Manipulate 2nd vbf data block for non sbl vbf
        if vbf_header['sw_part_type'] != 'SBL' and counter == 1:
            manipulated_vfb_block_data = bytes(block_details["vbf_block_data"][::-1])
            block_details["vbf_block_data"] = manipulated_vfb_block_data

        result = transfer_data(dut, vbf_header, block_details["vbf_block"],
                            block_details["vbf_block_data"])
        if not result:
            logging.error("Block %s failed", counter)
            results.append(False)
            break
        results.append(True)

    if len(results) != 0 and all(results):
        return True

    logging.error("Software Download failed for %s VBF file", vbf_header['sw_part_type'])
    return False


def software_download(dut: Dut, stepno):
    """
    Software download(SWDL) for all VBF file
    Args:
        dut (class object): Dut instance
        stepno (int): step number
    Returns:
        (bool): True on successful software download
    """
    results = []
    vbf_type_list = ['SBL', 'ESS', 'DATA', 'EXE']
    for vbf_type in vbf_type_list:
        result, vbf_header, vbf_blocks_details = read_vbf(dut, vbf_type)
        if result:
            if vbf_type != vbf_type_list[0]:
                result_flash_erase = SSBL.flash_erase(dut, vbf_header, stepno)
                if not result_flash_erase:
                    logging.error("Test Failed: Unable to complete Flash Erase")
                    return False
            result = block_wise_software_download(dut, vbf_header,
                                                  vbf_blocks_details)

            if result and vbf_type == 'SBL':
                results.append(True)
            elif not result and vbf_type != 'SBL':
                logging.info("%s VBF download failed as expected.", vbf_type)
                results.append(True)
                continue
            else:
                results.append(False)
                logging.error("Unexpected result for SBL VBF file, download not successful")
                break

            SE31.check_memory(dut, vbf_header, stepno)
            if vbf_type == vbf_type_list[0]:
                SSBL.activate_sbl(dut, vbf_header, stepno)

    if len(results) == len(vbf_type_list) and all(results):
        return True
    return False


def step_1(dut: Dut):
    """
    action: Set to Programming Session and security access to ECU.

    expected_result: True on successful security access.
    """
    # Sleep time to avoid NRC37
    time.sleep(5)

    dut.uds.set_mode(2)
    result = SE27.activate_security_access_fixedkey(dut, sa_keys=CNF.default_rig_config,
                                                    step_no=272, purpose="SecurityAccess")
    if result:
        return True
    logging.error("Test Failed: Security access denied")
    return False


def step_2(dut: Dut):
    """
    action: Download Software for all VBF files and verify the downloaded
            software is Not Complete, Compatible and ECU is in in programming session

    expected_result: True when downloaded software is Not Complete, Compatible
    """
    result = software_download(dut, stepno=2)

    if not result:
        logging.error("Test failed: Expected SBL type to be downloaded"
                        " and other VBF type to be failed")
        return False

    # Check for Not Complete with Manipulated Data
    response = SSBL.check_complete_compatible_routine(dut, stepno=2)

    complete_compatible_list = response.split(",")
    if complete_compatible_list[0] == 'Not Complete':
        active_session = dut.uds.active_diag_session_f186()
        # Verify active session is Programming session
        if active_session.data["details"]["mode"] == 2:
            logging.info("ECU is in Programming Session")
            return True
        logging.error("Test failed: Expected ECU to be in Programming Session,"
                       " received %s", active_session.data["details"]["mode"])
        return False
    logging.error("Test Failed: Complete & Compatible check failed, expected Not Complete, "
                "received %s: ", complete_compatible_list[0])
    return False


def run():
    """
    Verifying current downloaded software is Not Complete, Compatible
    """
    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False
    try:
        dut.precondition(timeout=150)

        result_step = dut.step(step_1, purpose='Security access')

        if result_step:
            result_step = dut.step(step_2, purpose='Verify current downloaded software is Not'
                                   'Complete, Compatible with manipulated data block and ECU is'
                                   ' in programming session')
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
