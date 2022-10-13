"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76692
version: 2
title: TransferData (36) - blockSequenceCounter (BSC) received with the same value
purpose: >
    Define behavior of how a ECU shall react when receiving the
    same blockSequenceCounter value twice.

description: >
    If an ECU receives a transferData request during an active download sequence
    with the same blockSequenceCounter as the last accepted transferData request,
    it shall respond with a positive response without writing the data once again
    to its memory.

details: >
    Verifying transfer data(0x36) response for the following scenarios:
        1. Positive response 0x76, for a large block sequence, when a particular block
           sequence counter is requested with the same data for second time.
           complete & compatible check to verify repeated block is ignored.
        2. Positive response 0x76, for a large block sequence, when a particular block
           sequence counter is requested with manipulated data.
           complete & compatible check to verify manipulated block is ignored.
"""

import time
import logging
from glob import glob
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_service34 import SupportService34
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_service37 import SupportService37
from supportfunctions.support_service31 import SupportService31

SSBL = SupportSBL()
SE34 = SupportService34()
SE27 = SupportService27()
SE37 = SupportService37()
SE31 = SupportService31()


def get_vbf_params(dut):
    """
    Read vbf file and extract vbf header, largest vbf block & vbf block data
    Args:
        dut (Dut): An instance of dut
    Returns:
        (bool): True when data extraction is completed
        vbf_params (dict): vbf_header, largest vbf_block & vbf_block_data
    """
    vbf_params = {"vbf_header": "",
                  "largest_vbf_block": "",
                  "largest_vbf_block_data":""}

    rig_vbf_path = dut.conf.rig.vbf_path
    vbf_file_paths = glob(str(rig_vbf_path) + "/*.vbf")

    if len(vbf_file_paths) > 0:
        # Iterate through all the files
        for vbf_file_path in vbf_file_paths:
            # Read vbf file
            _, vbf_params["vbf_header"], vbf_data, vbf_offset = SSBL.read_vbf_file(vbf_file_path)
            vbf_header = dict(vbf_params["vbf_header"])

            # Compare vbf header 'sw_part_type' with 'SBL' to get a reliable source of longer block
            if vbf_header['sw_part_type'] == 'SBL':
                SSBL.vbf_header_convert(vbf_params["vbf_header"])

                # Extract largest block and block data from vbf file
                vbf_blocks = extract_vbf_blocks(vbf_data, vbf_offset)
                vbf_params["largest_vbf_block"], vbf_params["largest_vbf_block_data"] =\
                    filter_largest_vbf_block(vbf_blocks)

                return True, vbf_params

    logging.error("No SBL VBF found in %s", rig_vbf_path)
    return False, None


def extract_vbf_blocks(vbf_data, vbf_offset):
    """
    Extract all the verification block file(VBF) blocks & block data
    Args:
        vbf_data (str): Complete vbf data
        vbf_offset (int): vbf offset
    Returns:
        vbf_block_details (dict): dictionary containing vbf_block_list and vbf_block_data_list
    """
    vbf_block_list = []
    vbf_block_data_list = []

    # Extracting the first block
    vbf_offset, vbf_block, vbf_block_data = SSBL.block_data_extract(vbf_data, vbf_offset)
    vbf_block_data_list.append(vbf_block_data)
    vbf_block_list.append(vbf_block)

    for _ in range(20):
        # Extracting the remaining blocks
        vbf_offset, vbf_block, vbf_block_data = SSBL.block_data_extract(vbf_data, vbf_offset)

        if vbf_block['StartAddress'] == 0:
            # Terminate the loop if no more blocks are present
            break

        vbf_block_data_list.append(vbf_block_data)
        vbf_block_list.append(vbf_block)

    logging.info("Number of vbf blocks extracted from the vbf file: %s", len(vbf_block_list))

    vbf_block_details = {"vbf_block_list": vbf_block_list,
                         "vbf_block_data_list": vbf_block_data_list}

    return vbf_block_details


def filter_largest_vbf_block(vbf_block_details):
    """
    Filter largest vbf block from block list
    Args:
        vbf_block_details (dict): List of all vbf_block and vbf_block_data of a VBF File
    Returns:
        largest_vbf_block (dict): startAddress, Length and checksum of largest data block
        largest_vbf_block_data (str): Largest data block data of vbf file
    """
    # Filter the index of the largest block based on block length
    max_index = 0
    max_length = 0

    for index, block in enumerate(vbf_block_details["vbf_block_list"]):
        if block['Length'] > max_length:
            max_length = block['Length']
            max_index = index

    # Extract largest block and block data based on index
    largest_vbf_block = vbf_block_details["vbf_block_list"][max_index]
    largest_vbf_block_data = vbf_block_details["vbf_block_data_list"][max_index]

    # Log the start address and length of largest VBF block
    logging.info("Largest vbf block extracted from the list of blocks: %s ", largest_vbf_block)

    return largest_vbf_block, largest_vbf_block_data


def software_download(dut, vbf_params, manipulated_block=False):
    """
    Software download(SWDL) in sequence of RequestDownload(0x34), TransferData(0x36)
    and RequestTransferExit(0x37)
    Args:
        dut (Dut): An instance of dut
        vbf_params (dict): vbf_header, largest_vbf_block and largest_vbf_block_data
        manipulated_block (bool): Flag for transfer_data()
    Returns:
        result (bool): True when software download(SWDL) is successful
    """
    result, nbl = SE34.request_block_download(dut, vbf_params["vbf_header"],
                  vbf_params["largest_vbf_block"])

    if not result:
        logging.error("RequestDownload(0x34) request failed")
        return False

    transfer_data_parameters = {"vbf_block_length" : vbf_params["largest_vbf_block"]["Length"],
                                "vbf_block_data": vbf_params["largest_vbf_block_data"],
                                "nbl": nbl}
    result = transfer_data(dut, transfer_data_parameters, manipulated_block)
    if not result:
        logging.error("TransferData(0x36) request failed")
        return False

    result = SE37.transfer_data_exit(dut)
    if not result:
        logging.error("RequestTransferExit(0x37) request failed")
        return False

    return True


def transfer_data(dut, transfer_data_parameters, manipulated_block=False):
    """
    Calling TransferData(0x36) request
    Args:
        dut (Dut): An instance of dut
        transfer_data_parameters (dict): vbf_block_length, vbf_block_data and nbl
        manipulated_block(bool): Flag to test TransferData(0x36) with manipulated block
    Returns:
        (bool): True when TransferData(0x36) request is successfully called
    """
    nbl = transfer_data_parameters["nbl"]
    vbf_block_data = transfer_data_parameters["vbf_block_data"]
    request_36_iterations = int(transfer_data_parameters["vbf_block_length"]/(nbl-2))+1

    # If the block is not big enough, terminate the test case
    if request_36_iterations <= 1:
        logging.error("Vbf block is not big enough to split into sub blocks")
        return False

    counter = 0
    for block_index in range(request_36_iterations):
        # Preparing payload
        pad = (nbl-2)*block_index
        block_index += 1
        payload = b'\x36' + bytes([block_index % 256]) + vbf_block_data[pad:pad + nbl-2]

        response = dut.uds.generic_ecu_call(payload)

        # Check for positive response 0x76 for TransferData(0x36)
        if response.raw[2:4] != '76':
            logging.error("Transfer data(0x36) for block %s failed, received %s", counter,
                                                                            response.raw)
            return False

        if counter == 2:
            # Transfer data(0x36) on the same block or manipulated block
            if manipulated_block:
                # Prepare payload with manipulated data block
                manipulated_block_data = list(vbf_block_data[pad:pad + nbl-2])
                manipulated_block_data = manipulated_block_data[::-1]
                manipulated_block_data = bytes(manipulated_block_data)

                payload = b'\x36' + bytes([block_index % 256]) + manipulated_block_data

            response_block_with_condition = dut.uds.generic_ecu_call(payload)
            # Check for positive response 0x76 for transfer data(0x36)
            if response_block_with_condition.raw[2:4] != '76':
                msg_block_condition = "manipulated" if manipulated_block else "same"
                logging.error("Transfer data(0x36) for %s block %s failed, received %s ",
                                              msg_block_condition, counter, response.raw)
                return False
        counter += 1

    if response.raw[2:4] == '76' and response_block_with_condition.raw[2:4] == '76':
        return True

    return False


def check_routines(dut, vbf_header, step_number):
    """
    Verifying check memory and complete & compatible
    Args:
        dut (Dut): An instance of dut
        vbf_header (dict): vbf header
        step_number (int): step number
    Returns:
        (bool): True when complete & compatible check is successful
    """
    result_check_memory = SE31.check_memory(dut, vbf_header, step_number)
    if not result_check_memory:
        logging.error("Test failed: Check memory routine failed")
        return False

    # Check complete&compatible
    result_complete_compatible = SSBL.check_complete_compatible_routine(dut, step_number)
    complete_compatible_list = result_complete_compatible.split(",")
    if complete_compatible_list[0] == 'Complete' and \
       complete_compatible_list[1].strip() == 'Compatible':
        return True

    logging.error("Test Failed: Check complete & compatible failed, received %s",
                   result_complete_compatible)
    return False


def step_1(dut: Dut):
    """
    action: Extract vbf header, and largest vbf block details from vbf file
    expected_result: Vbf header and largest vbf block details are available in vbf file
                     and could be extracted properly.
    """
    result, vbf_params = get_vbf_params(dut)
    if result:
        logging.info("Successfully extracted vbf header, and largest vbf block details "
                     "from vbf file")
        return result, vbf_params

    logging.error("Test Failed: Failed to get vbf parameters")
    return False, None


def step_2(dut: Dut):
    """
    action: Enter into programming session and unlock security with valid key
    expected_result: ECU is in programming session and security unlock successful
    """
    # Sleep time to avoid NRC37
    time.sleep(5)
    dut.uds.set_mode(2)

    # Security access
    result = SE27.activate_security_access_fixedkey(dut, sa_keys=dut.conf.default_rig_config,
                                                     step_no=272, purpose="SecurityAccess")
    if result:
        logging.info("Security access successful")
        return True

    logging.error("Test Failed: Security access denied")
    return False


def step_3(dut: Dut, vbf_params):
    """
    action: Initiate software download(SWDL) for a large block and verify response of transfer data
            (0x36) when a block sequence is sent twice with same data. verify check memory and
            complete & compatible routines.
    expected_result: ECU send a positive response 0x76 for transfer data(0x36) request when a block
                     sequence counter sent twice with the same data. verify check memory and
                     complete & compatible check is passed.
    """
    result = software_download(dut, vbf_params, False)

    if result:
        result = check_routines(dut, vbf_params["vbf_header"], 3)
    else:
        logging.error("Test Failed: Software download(SWDL) failed for block sequence"
                      " counter with same block twice")
        return False

    if result:
        logging.info("Software download(SWDL) completed for repeated block sequence"
                     " with same data")
        return True

    logging.error("Test Failed: Received negative response for check memory or"
                  " complete & compatible after software download(SWDL) for block"
                  " sequence counter with same block data twice")
    return False


def step_4(dut: Dut, vbf_params):
    """
    action: Initiate software download(SWDL) for a large block sequence and verify response of
            transfer data(0x36) when a block sequence is sent twice with manipulated data second
            time. Verify check memory and complete & compatible routines.
    expected_result: ECU send a positive response 0x76 for transfer data(0x36) request when a block
                     sequence sent twice with manipulated data second time. verify check memory and
                     complete & compatible check is passed.
    """
    result = software_download(dut, vbf_params, True)

    if result:
        result = check_routines(dut, vbf_params["vbf_header"], 4)
    else:
        logging.error("Test Failed: Software download(SWDL) failed for block sequence"
                      " counter with manipulated data")
        return False

    if result:
        logging.info("Software download(SWDL) completed for repeated block sequence"
                     " with manipulated data")
        logging.info("ECU passes check memory routine proving that the repeated block sequence"
                     "with manipulated data is ignored as expected")
        return True

    logging.error("Test Failed: Received negative response for check memory or"
                  " complete & compatible after software download(SWDL) for block"
                  " sequence counter with manipulated data.")
    return False


def step_5(dut: Dut):
    """
    action: Verify software can be booted in default session and programming session
    expected_result: ECU mode is in default session and then programming session
    """
    # Set to default session
    dut.uds.set_mode(1)

    response_default = dut.uds.active_diag_session_f186()
    if response_default.data["details"]["mode"] == 1:
        logging.info("ECU changes to default session as expected")
        result_mode_default = True
    else:
        logging.error("Test Failed: ECU mode did not change to default session")
        result_mode_default = False

    # Set to programming session
    dut.uds.set_mode(2)

    response_programming = dut.uds.active_diag_session_f186()
    if response_programming.data["details"]["mode"] == 2:
        logging.info("ECU mode changes to programming session as expected")
        result_mode_prog = True
    else:
        logging.error("Test Failed: ECU mode did not change to programming session")
        result_mode_prog = False

    return result_mode_default and result_mode_prog


def run():
    """
    Verifying ECU behavior for following scenarios:
        1. For a large block sequence, sending transfer data(0x36) request and a particular
           block sequence counter is requested with the same data for second time, should
           receive positive response 0x76. complete & compatible check should pass to verify
           same block is ignored.
        2. For a large block sequence, sending transfer data(0x36) request and a particular
           block sequence counter is requested a second time with the manipulated data, should
           receive positive response 0x76. complete & compatible check should pass to verify
           manipulated block is ignored.
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=130)

        result_step, vbf_params = dut.step(step_1, purpose='Read vbf file and extract vbf header,'
                                           ' largest vbf block & vbf block data')
        if result_step:
            result_step = dut.step(step_2, purpose='Entering into programming session and'
                                                   ' security access')
        if result_step:
            result_step = dut.step(step_3, vbf_params, purpose='Verify positive response 0x76 on'
                                   ' transfer data(0x36) request for same block twice')
        if result_step:
            result_step = dut.step(step_4, vbf_params, purpose='Verify positive response 0x76 on'
                                   ' transfer data(0x36) request for same block with manipulated'
                                   ' data')
        if result_step:
            result_step = dut.step(step_5, purpose='Verify software can be booted in default'
                                                   ' session and programming session')
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
