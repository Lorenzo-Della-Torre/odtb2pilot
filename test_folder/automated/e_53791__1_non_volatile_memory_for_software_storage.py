"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 53791
version: 1
title: Non-volatile memory for software storage
purpose: >
    To be able to modify/upgrade stored software(s)

description: >
    All software(s) shall be stored in a non-volatile memory, SBL excluded.

details: >
    Verify all downloaded software is completed in a sequence.
        1. Software Download(SWDL) for SBL VBF file
        2. Software Download(SWDL) for ESS VBF file and it should fail while trying to write in
           volatile memory
"""

import time
import logging
from glob import glob
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_can import SupportCAN
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_service34 import SupportService34
from supportfunctions.support_service36 import SupportService36
from supportfunctions.support_service37 import SupportService37
from supportfunctions.support_service31 import SupportService31

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
        vbf_type (str): SBL or ESS
    Returns:
        (bool): True when extracted VBF parameters successfully
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

    for _ in range(20):
        vbf_offset, vbf_block, vbf_block_data = SSBL.block_data_extract(vbf_data, vbf_offset)
        # Break if no more blocks found
        if vbf_block['StartAddress'] == 0:
            break

        # Preparing vbf_blocks_details list
        vbf_blocks_details.append({'vbf_block': vbf_block, 'vbf_block_data': vbf_block_data})

    msg = "Number of VBF blocks extracted from the VBF file: {}".format(len(vbf_blocks_details))
    logging.info(msg)

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
        bool: True if SWDL is successful
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


def block_wise_software_download(dut, vbf_header, vbf_blocks_details, vbf_type):
    """
    Blockwise software download(SWDL)
    Args:
        dut (class object): Dut instance
        vbf_header (dict): VBF file header
        vbf_blocks_details (list): list of dictionaries containing blockwise details
                                (vbf_block, vbf_block_data)
        vbf_type (str): SBL or ESS
    Returns:
        (bool): True on successful software download
    """
    # Software Download(SWDL) on all blocks of respective VBF file
    results = []
    for block_id, block_details in enumerate(vbf_blocks_details):
        logging.info("SWDL on %s of %s VBF", block_id+1, vbf_type)

        result = transfer_data(dut, vbf_header, block_details["vbf_block"],
                                block_details["vbf_block_data"])
        results.append(result)

    if len(results) != 0 and all(results):
        logging.info("Software Download for %s VBF Completed", vbf_type)
        return True

    logging.error("Software Download for %s VBF failed", vbf_type)
    return False


def step_1(dut: Dut):
    """
    action: Enter into Programming Session and security access with valid key.

    expected_result: ECU is in programming session and security access is successful.
    """
    dut.uds.set_mode(2)

    # Sleep time to avoid NRC37
    time.sleep(5)

    result = SE27.activate_security_access_fixedkey(dut, sa_keys=dut.conf.default_rig_config)

    if result:
        return True

    logging.error("Test Failed: Security access denied")
    return False


def step_2(dut: Dut):
    """
    action: Verify Software Download(SWDL) for VBF file of SBL software part type.

    expected_result: ECU should send positive response for all SBL VBF blocks
    """
    result, vbf_header, vbf_blocks_details = read_vbf(dut, 'SBL')
    volatile_start_address = vbf_blocks_details[0]['vbf_block']['StartAddress']

    if not result:
        logging.error("Test failed: Unable to extract VBF file parameters")
        return False, None

    result = block_wise_software_download(dut, vbf_header, vbf_blocks_details, 'SBL')

    result_check_mem = SE31.check_memory(dut, vbf_header, stepno=2)
    result_activation = SSBL.activate_sbl(dut, vbf_header, stepno=2)

    if not (result_check_mem and result_activation):
        logging.error("Test Failed: CheckMemory or SBL Activation failed")
        return False, None

    if result:
        return True, volatile_start_address

    logging.error("Test failed: Software Download(SWDL) failed for SBL VBF file")
    return False, None


def step_3(dut: Dut, volatile_start_address):
    """
    action: Verify Software Download(SWDL) for VBF file of ESS software part type into volatile
			memory and it should fail.

    expected_result: ECU should send negative response
    """
    result, vbf_header, vbf_blocks_details = read_vbf(dut, 'ESS')

    if not result:
        logging.error("Test failed: Unable to extract VBF file parameters")
        return False

    # Manipulating start address to volatile memory range
    first_ess_vbf_block = vbf_blocks_details[0]['vbf_block']
    first_ess_vbf_block['StartAddress'] = volatile_start_address

	# Flash Erase
    result_flash_erase = SSBL.flash_erase(dut, vbf_header, stepno=3)
    if not result_flash_erase:
        logging.error("Test Failed: Unable to complete Flash Erase")
        return False

	# Initiate RequestDownload(0x34) request into volatile storage
    result, _ = SE34.request_block_download(dut, vbf_header, first_ess_vbf_block)
    se34_response = SC.can_messages[dut["receive"]][0][2]

    # RequestDownload(0x34) request fails and receive NRC 31(requestOutOfRange) in response
    if not result and se34_response[6:8] == '31':
        return True

    msg = "Test failed: Expected NRC 31(requestOutOfRange) for RequestDownload(0x34),"\
			" received {}".format(se34_response)
    logging.error(msg)
    return False

def run():
    """
    While trying download software into volatile memory, it should fail for ESS software part type.
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=150)

        result_step = dut.step(step_1, purpose="Enter into programming session and security"
                                                " access to ECU.")

        if result_step:
            result_step, volatile_start_address = dut.step(step_2, purpose="Verify Software"
                                    " Download(SWDL) request for VBF of SBL software part type.")

        if result_step:
            result_step = dut.step(step_3, volatile_start_address, purpose="Verify Software"
                                    " Download(SWDL) request for VBF of ESS software part type"
									" into volatile memory and it should fail.")

        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
