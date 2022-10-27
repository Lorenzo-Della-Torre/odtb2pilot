"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 397292
version: 2
title: Software parts per logical block
purpose: >
    Define the software structure to enable that each software part is possible to individually
    sign and verify.

description: >
    The content (data blocks) of a software part must be within a single logical block range, i.e.
    two different logical blocks must not be addressed by a single software part.

details: >
    Verify two different logical blocks must not be addressed by a single software part:
        1. Update the length of logical block and verify RequestDownload(0x34) with
           NRC-31(requestOutOfRange)
        2. Flash erase with memory range more than application and verify NRC-31(requestOutOfRange)
"""

import time
import logging
from glob import glob
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_service31 import SupportService31
from supportfunctions.support_service34 import SupportService34
from supportfunctions.support_can import SupportCAN

SSBL = SupportSBL()
SE27 = SupportService27()
SE31 = SupportService31()
SE34 = SupportService34()
SC = SupportCAN()


def extract_vbf_header_and_block(dut: Dut, swp):
    """
    Extract vbf header and block
    Args:
        dut (Dut): An instance of Dut
        swp (int): Software parts
    Returns:
        (bool): True when Vbf header and vbf block are available in vbf file and can be
                extracted properly
        vbf_params (dict): VBF parameters
    """
    vbf_params = {"vbf_header": '',
                  "vbf_block": ''}

    rig_vbf_path = dut.conf.rig.vbf_path
    vbf_file_paths = glob(str(rig_vbf_path) + "/*.vbf")
    if len(vbf_file_paths) == 0:
        logging.error("Test Failed: VBF file not found in path: %s", rig_vbf_path)
        return False, None

    _, vbf_params["vbf_header"], vbf_data, vbf_offset = SSBL.read_vbf_file(vbf_file_paths[swp])
    SSBL.vbf_header_convert(vbf_params["vbf_header"])
    # Extract vbf_params of first logical block
    vbf_params["vbf_block"] = SSBL.block_data_extract(vbf_data, vbf_offset)[1]
    return True, vbf_params


def calculate_vbf_block_length(dut: Dut):
    """
    Calculate vbf block length dynamically
    Args:
        dut (Dut): An instance of Dut
    Returns:
        total_vbf_block_length (int): Total vbf block length
    """
    block_length = []
    # Extract vbf header and block of each software part
    for swp in range(4):
        result, vbf_params = extract_vbf_header_and_block(dut, swp)
        if not result:
            return False
        block_length.append([vbf_params['vbf_block']['Length']])

    total_vbf_block_length = 0
    for index, _ in enumerate(block_length):
        total_vbf_block_length = total_vbf_block_length + block_length[index][0]

    return total_vbf_block_length


def get_memory_range():
    """
    Get memory range more than one logical block
    Args: None
    Returns:
        memory_range_more_than_app (str): Memory range
    """
    # Read VBF for DATA file
    vbf_header_data = SSBL.read_vbf_file(SSBL.get_df_filenames()[1])[1]

    # Read VBF for APP file
    vbf_header_app = SSBL.read_vbf_file(SSBL.get_df_filenames()[0])[1]

    # Get combined block length by adding block length of APP and DATA
    # [13:23] indicates block length
    combined_block_length = hex(int(vbf_header_data['erase'][13:23], 16) + \
                                int(vbf_header_app['erase'][13:23], 16))

    # Get memory range more than application block by adding combined block length of APP and DATA
    # [0:13] indicates memory start address
    # [len(vbf_header_app['erase'])-2:] it ignores the curly braces from string
    memory_range_more_than_app = vbf_header_app['erase'][0:13] + str(combined_block_length) + \
                                 vbf_header_app['erase'][len(vbf_header_app['erase'])-2:]
    return memory_range_more_than_app


def step_1(dut: Dut):
    """
    action: Enter into programming session and unlock security with valid key
    expected_result: ECU is in programming session and security unlock successful
    """
    # Set to programming session
    dut.uds.set_mode(2)

    # Sleep time to avoid NRC37
    time.sleep(5)

    # Security access to ECU
    result = SE27.activate_security_access_fixedkey(dut, sa_keys=dut.conf.default_rig_config)
    if result:
        logging.error("Security access granted")
        return True

    logging.error("Test Failed: Security access denied")
    return False


def step_2(dut: Dut):
    """
    action: RequestDownload(0x34) with updated VBF block length
    expected_result: ECU should give NRC-31(requestOutOfRange) after updating length
                     of logical block
    """
    result, vbf_params = extract_vbf_header_and_block(dut, swp=3)
    if not result:
        return False

    # Read VBF files for sbl file (1st logical block)
    vbf_header = vbf_params['vbf_header']
    vbf_block = vbf_params['vbf_block']

    # Update VBF block length
    block_length = calculate_vbf_block_length(dut)
    vbf_block.update({'Length': block_length})

    # Request download
    result = SE34.request_block_download(dut, vbf_header, vbf_block)[0]

    response = SC.can_messages[dut["receive"]][0][2]
    if response[2:4] == '7F' and response[6:8] == '31':
        logging.info("Received NRC-%s(requestOutOfRange) after updating length of logical block "
                     "as expected", response[6:8])
        return True

    logging.error("Test Failed: NRC-31(requestOutOfRange) not received after updating length of "
                  "logical block, received %s", response)
    return False


def step_3(dut: Dut):
    """
    action: ECU hardreset and verify active diagnostic session
    expected_result: ECU should be in default session after ECU hard reset
    """
    # ECU reset
    dut.uds.ecu_reset_1101()

    # Verify active diagnostic session
    active_session = dut.uds.active_diag_session_f186()
    if active_session.data["details"]["mode"] == 1:
        logging.info("ECU is in default session as expected")
        return True

    logging.error("Test Failed: ECU is not in default session")
    return False


def step_4(dut: Dut):
    """
    action: Download and activate SBL
    expected_result: SBL should be successfully activated
    """
    # Loads the rig specific VBF files
    vbf_result = SSBL.get_vbf_files()
    if not vbf_result:
        logging.error("Test Failed: Unable to load VBF files")
        return False

    # Download and activate SBL
    sbl_result = SSBL.sbl_dl_activation(dut, sa_keys=dut.conf.default_rig_config)
    if not sbl_result:
        logging.error("Test Failed: SBL activation failed")
        return False

    logging.info("SBL activation successful")
    return True


def step_5(dut: Dut):
    """
    action: Send routine control(erase memory) to erase one block of the application software
    expected_result: ECU should give NRC-31(requestOutOfRange) after flash erase with memory range
                     more than application block
    """
    # Read VBF for APP file
    vbf_header = SSBL.read_vbf_file(SSBL.get_df_filenames()[0])[1]

    # Get memory range more than one logical block
    memory_add = get_memory_range()
    vbf_header.update({'erase': memory_add})

    SSBL.vbf_header_convert(vbf_header)

    # Verify programming preconditions
    result = SE31.routinecontrol_requestsid_flash_erase(dut, header=vbf_header)
    if not result:
        logging.error("Test Failed: Routine control(erase memory) unsuccessful")
        return False

    response = SC.can_messages[dut["receive"]][0][2]

    if response[2:4] == '7F' and response[6:8] == '31':
        logging.info("Received NRC-%s(requestOutOfRange) after flash erase with memory range "
                     "more than application", response[6:8])
        return True

    logging.error("Test Failed: Expected NRC-31(requestOutOfRange) after flash erase with "
                  "memory range more than application, received %s", response)
    return False


def run():
    """
    Verify two different logical blocks must not be addressed by a single software part:
        1. Update the length of logical block and verify RequestDownload(0x34) with
           NRC-31(requestOutOfRange)
        2. Flash erase with memory range more than application and verify NRC-31(requestOutOfRange)
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=150)

        result_step = dut.step(step_1, purpose='Enter into programming session and unlock security'
                                               ' with valid key')
        if result_step:
            result_step = dut.step(step_2, purpose='RequestDownload(0x34) with updated VBF block'
                                                   ' length')
        if result_step:
            result_step = dut.step(step_3, purpose='ECU hardreset and verify active diagnostic'
                                                   ' session')
        if result_step:
            result_step = dut.step(step_4, purpose='Download and activate SBL')
        if result_step:
            result_step = dut.step(step_5, purpose='Send routine control(erase memory) to erase one'
                                                   ' block of the application software')
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
