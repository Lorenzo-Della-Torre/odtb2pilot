"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 400425
version: 2
title: Programming of Logical Blocks
purpose: >
    Define properties for a logical block, that are required for the ECU to be able to manage each
    logical block independently but also to simplify the signing process at the trust centre.

description: >
    Each logical block shall be possible to sign separately, i.e. each logical block must be
    possible to erase, program and verify independently in the ECU.

details: >
    All logical blocks of a VBF are signed separately.
"""

import logging
from glob import glob
from hilding.dut import Dut
from hilding.dut import DutTestError
from hilding.conf import Conf
from supportfunctions.support_can import SupportCAN
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_service31 import SupportService31
from supportfunctions.support_service34 import SupportService34
from supportfunctions.support_service36 import SupportService36
from supportfunctions.support_service37 import SupportService37


CNF = Conf()
SC = SupportCAN()
SSBL = SupportSBL()
SE27 = SupportService27()
SE31 = SupportService31()
SE34 = SupportService34()
SE36 = SupportService36()
SE37 = SupportService37()


def read_vbf(dut, vbf_type):
    """
    Read vbf file and extract vbf header, vbf block and vbf block data
    Args:
        dut (class obj): dut instance
        vbf_type (str): SBL/ESS/DATA/EXE
    Returns:
        vbf_header (dict): vbf header dictionary
        vbf_blocks_details (dict): VBF Block details (vbf_block, vbf_block_data)
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
                logging.info("Number of VBF blocks extracted from the %s VBF file: %s",
                                vbf_type, len(vbf_blocks_details))
                return True, vbf_header, vbf_blocks_details

    logging.error("No %s VBF found in %s", vbf_type, rig_vbf_path)
    return False, None, None


def extract_vbf_blocks(vbf_data, vbf_offset):
    """
    Extract all the Verification Block File(VBF) blocks & block data
    Args:
        vbf_data (str): Complete vbf data
        vbf_offset (int): vbf offset
    Returns:
        vbf_block_details (list): VBF Block details (vbf_block, vbf_block_data)
    """
    vbf_blocks_details = []
    # Extract first VBF block
    vbf_offset, vbf_block, vbf_block_data = SSBL.block_data_extract(vbf_data, vbf_offset)
    vbf_blocks_details.append({'vbf_block': vbf_block, 'vbf_block_data': vbf_block_data})

    while vbf_block['StartAddress'] != 0:
        vbf_offset, vbf_block, vbf_block_data = SSBL.block_data_extract(vbf_data, vbf_offset)
        # Break if no more blocks found
        if vbf_block['StartAddress'] != 0:
            vbf_blocks_details.append({'vbf_block': vbf_block, 'vbf_block_data': vbf_block_data})

    return vbf_blocks_details


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

    result = SE36.flash_blocks(dut, vbf_block_data, vbf_block, nbl)
    if not result:
        logging.error("Test failed: TransferData(0x36) request failed")
        return False

    result = SE37.transfer_data_exit(dut)
    if not result:
        logging.error("Test failed: TransferExit(0x37) request failed")
        return False

    return True


def block_wise_software_download(dut, vbf_header, vbf_blocks_details):
    """
    Blockwise software download(SWDL)
    Args:
        dut (class object): Dut instance
        vbf_header (dict): VBF file header
        vbf_blocks_details (list): VBF Block details (vbf_block, vbf_block_data)
    Returns:
        (bool): True on successful blockwise software download
    """
    # Software Download(SWDL) on all blocks of respective VBF file
    results = []
    for counter, block_details in enumerate(vbf_blocks_details):
        logging.info("Initiating SWDL for Block %s of %s VBF", counter, vbf_header['sw_part_type'])
        result = transfer_data(dut, vbf_header, block_details["vbf_block"],
                                block_details["vbf_block_data"])
        results.append(result)
        if not result:
            logging.error("Block %s failed", counter)
            break

    if len(results) != 0 and all(results):
        logging.info("Software download completed for %s VBF", vbf_header['sw_part_type'])
        return True

    logging.error("Software Download failed for %s VBF file", vbf_header['sw_part_type'])
    return False


def software_download(dut: Dut, stepno):
    """
    Software download(SWDL) for all VBF file types
    Args:
        dut (class object): Dut instance
        stepno (int): step number
    Returns:
        (bool): True on successful software download
    """
    results = []
    vbf_type_list = ['SBL','ESS', 'DATA', 'EXE']
    for vbf_type in vbf_type_list:
        result, vbf_header, vbf_blocks_details = read_vbf(dut, vbf_type)
        if not result:
            logging.error("Test Failed: Unable to extract parameters of %s VBF", vbf_type)
            return False

        if vbf_type != vbf_type_list[0]:
            result_flash_erase = SSBL.flash_erase(dut, vbf_header, stepno)
            if not result_flash_erase:
                logging.error("Test Failed: Unable to complete Flash Erase")
                return False

        result = block_wise_software_download(dut, vbf_header, vbf_blocks_details)
        if result:
            results.append(True)
        else:
            logging.error("Software download failed for %s VBF file", vbf_type)
            return False

        SE31.check_memory(dut, vbf_header, stepno)
        if vbf_type == vbf_type_list[0]:
            SSBL.activate_sbl(dut, vbf_header, stepno)

    if len(results) == len(vbf_type_list) and all(results):
        logging.info("Software download completed")
        return True

    return True


def step_1(dut: Dut):
    """
    action: Set to Programming Session and security access to ECU.

    expected_result: ECU is in programming session and Security access granted
    """
    dut.uds.set_mode(2)
    result = SE27.activate_security_access_fixedkey(dut, sa_keys=CNF.default_rig_config,
                                                    step_no=272, purpose="SecurityAccess")
    if result:
        logging.info("Security access granted")
        return True
    logging.error("Test Failed: Security access denied")
    return False


def step_2(dut: Dut):
    """
    action: Download Software for all VBF files and verify the downloaded
            software is complete and compatible

    expected_result: True when downloaded software is Complete&Compatible
    """
    result = software_download(dut, stepno=2)
    if not result:
        logging.error("Test Failed: Software download failed")
        return False

    response = SSBL.check_complete_compatible_routine(dut, stepno=2)
    complete_compatible_list = response.split(",")

    if complete_compatible_list[0] == 'Complete' and \
        complete_compatible_list[1].strip() == 'Compatible':
        logging.info("Received %s as expected after software download", response)
        return True

    logging.error("Test Failed: Complete & Compatible check failed, expected Complete"
                    "& Compatible, received %s", response)
    return False


def run():
    """
    All logical blocks of a VBF are signed separately.
    """
    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=400)
        result_step = dut.step(step_1, purpose='Security access to ECU')

        if result_step:
            result_step = dut.step(step_2, purpose='Verify current Downloaded '
                                   'Software is Complete & Compatible')

        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
