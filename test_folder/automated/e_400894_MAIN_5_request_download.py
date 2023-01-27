"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 400894
version: 5
title: Request Download - restrictions on number of addressed logical blocks
purpose: >
    To enable verification of each logical block independently by only allowing that a single
    logical block is being updated (active) at a given time. The purpose is also to inform the
    diagnostic client directly when the software download sequence will fail, as well as support
    diagnostic client fault-handling and retry strategies.

description: >
    The ECU shall check that only one logical block is being updated for a single downloaded
    software part, i.e. one logical block is allowed to be addressed from a valid RequestDownload
    to a CheckMemory request is detected. If any memory outside that first logical block is
    addressed by a RequestDownload request(s), e.g. a second logical block or some location not
    defined by the ESS at all, the ECU shall abort the RequestDownload and inform the client via a
    NRC.

    As the processed length (compressed/encrypted) length is used as memorySize parameter of the
    RequestDownload request, there are scenarios when it is not possible to detect this at the
    RequestDownload stage but identified later when the data is uncompressed/decrypted and about
    to be written to the memory. Anyhow, the download shall be aborted when it is detected.

    To be able to recover when download sequence is aborted, for example trying download the same
    software part once again or continue downloading the next software part (another logical block),
    the ECU shall upon a rejected request enter a state where no logical block is active and wait
    for next request to erase or program the memory.

details: >
    Verify restrictions on number of addressed logical blocks
    Steps:
        1. Request block download for 1st logical block
        2. Verify NRC-31(requestOfOutRange) in RequestDownload(0x34) for 2nd logical block
        3. Check complete and compatibility
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_can import SupportCAN, CanTestExtra, CanPayload
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_service34 import SupportService34

SC = SupportCAN()
SC_CARCOM = SupportCARCOM()
SUTE = SupportTestODTB2()
SSBL = SupportSBL()
SE34 = SupportService34()


def read_vbf_files_and_extract_data(swp, msg):
    """
    Read VBF file and extract data for the 1st data block from SWP
    Args:
        swp (int): Index of software part
        msg (str): Message string for software part
    Returns:
        (bool): True when successfully extract block data
        vbf_header (dict): VBF header
        vbf_block (dict):  VBF block
    """
    # Read VBF files for SWP file (1st Logical Block)
    data_files = SSBL.get_df_filenames()
    if len(data_files) > 0:
        _, vbf_header, data, data_start = SSBL.read_vbf_file(data_files[swp])
        if len(data) > 0:
            logging.info("Successfully read and decode %s SWP file", msg)
        else:
            logging.error("Test Failed: Failed to read and decode %s SWP file", msg)
            return False
    else:
        logging.error("Test Failed: Unable to return filenames used for data in SWDL")
        return False

    # Extract data for the 1st data block from SWP
    vbf_block = SSBL.block_data_extract(data, data_start)[1]
    if len(vbf_block) > 0:
        logging.info("Successfully extract block data from %s SWP file", msg)
        return True, vbf_header, vbf_block

    logging.error("Test Failed: Failed to extract block data from %s SWP file", msg)
    return False, None, None


def step_1(dut: Dut):
    """
    action: Download SBL & ESS and activate SBL
    expected_result: ESS download should be successful
    """
    # Loads the rig specific VBF files
    SSBL.get_vbf_files()

    # Download and activate SBL on the ECU
    dut.uds.enter_sbl()

    # Download the ESS file
    ess_result = SSBL.sw_part_download(dut, SSBL.get_ess_filename(), stepno='1',
                                                                     purpose="ESS download")
    if not ess_result:
        logging.error("Test Failed: ESS Download failed")
        return False

    logging.info("ESS download successful")
    return True


def step_2(dut: Dut):
    """
    action: Request block download
    expected_result: Request block download should be successful
    """
    result, vbf_header, vbf_block = read_vbf_files_and_extract_data(swp=0, msg='1st')
    if not result:
        return False

    # Request Download the 1st data block (1st Logical Block)
    SSBL.vbf_header_convert(vbf_header)
    result, _ = SE34.request_block_download(dut, vbf_header, vbf_block, stepno=340,
                                            purpose='Request download of block to ECU')
    if result:
        logging.info("Request download 1st data block successful")
        return True

    logging.error("Test Failed: Request download 1st data block failed")
    return False


def step_3(dut: Dut):
    """
    action: Verify RequestDownload(0x34) 1st data block
    expected_result: ECU should send NRC-31(requestOutOfRange)
    """
    result, vbf_header, vbf_block = read_vbf_files_and_extract_data(swp=1, msg='2nd')
    if not result:
        return False

    # Verify request download the 1st data block (2nd Logical Block) is rejected
    SSBL.vbf_header_convert(vbf_header)

    data_format= vbf_header["data_format_identifier"].to_bytes(1, 'big')
    start_add= vbf_block['StartAddress'].to_bytes(4, 'big')
    add_len= vbf_block['Length'].to_bytes(4, 'big')

    cpay: CanPayload = {"payload": SC_CARCOM.can_m_send("RequestDownload",
                                   data_format + bytes.fromhex('44') + start_add + add_len, b''),
                        "extra": ''}

    etp: CanTestExtra = {"step_no": 103,
                         "purpose": '',
                         "timeout": 0.05,
                         "min_no_messages": -1,
                         "max_no_messages": -1}

    result = SUTE.teststep(dut, cpay, etp)
    result = result and SUTE.test_message(SC.can_messages[dut["receive"]], teststring='7F3431')
    if result:
        logging.info('Received message: %s',
                     SUTE.pp_decode_7f_response(SC.can_frames[dut["receive"]][0][2]))
        return True

    logging.error("Test Failed: Expected NRC-31(requestOfRange) but received %s",
                  SC.can_messages[dut["receive"]][0][2])
    return False


def step_4(dut: Dut):
    """
    action: Download remaining software parts and check complete and compatibility
    expected_result: Downloaded software should be complete and compatible
    """
    result = True
    for swp in SSBL.get_df_filenames():
        result = result and SSBL.sw_part_download(dut, swp, stepno='103', purpose='')

    if not result:
        logging.error("Test Failed: Unable to download remaining software parts")
        return False

    logging.info("Successfully downloaded remaining software parts")

    # Check Complete and Compatible
    cc_result = SSBL.check_complete_compatible_routine(dut, stepno=4)
    if not cc_result:
        logging.error("Test Failed: Downloaded software is not complete and compatible")
        return False

    logging.info("Downloaded software is complete and compatible")
    return True


def step_5(dut: Dut):
    """
    action: ECU hard reset and verify default session
    expected_result: ECU should be in default session
    """
    # ECU reset
    dut.uds.ecu_reset_1101()

    # Verify active diagnostic session
    response = dut.uds.active_diag_session_f186()
    if response.data["details"]["mode"] == 1:
        logging.info("ECU is in default session as expected")
        return True

    logging.error("Test Failed: ECU is not in default session")
    return False


def run():
    """
    Verify restrictions on number of addressed logical blocks
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=600)

        result_step = dut.step(step_1, purpose='Download SBL & ESS and activate SBL')
        if result_step:
            result_step = dut.step(step_2, purpose='Request block download')
        if result_step:
            result_step = dut.step(step_3, purpose='Verify RequestDownload(0x34) 1st data block')
        if result_step:
            result_step = dut.step(step_4, purpose='Download remaining software parts and check '
                                                   'complete and compatibility')
        if result_step:
            result_step = dut.step(step_5, purpose='ECU hard reset and verify default session')

        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
