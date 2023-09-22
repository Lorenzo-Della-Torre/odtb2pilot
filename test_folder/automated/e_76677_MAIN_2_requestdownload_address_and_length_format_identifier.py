"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76677
version: 2
title: RequestDownload (34) - addressAndLengthFormatIdentifier (ALFID)
purpose: >
    Compliance with VCC tools.

description: >
    The ECU shall support RequestDownload, addressAndLengthFormatIdentifier (ALFID)
    with the value 0x44:
    MemorySize = 4 bytes
    MemoryAddress = 4 bytes

details: >
    Verify RequestDownload(34) response for the following scenarios-
        1. Positive response 74 for a valid addressAndLengthFormatIdentifier 0x44.
        2. Negative Response 31(requestOutOfRange) for invalid addressAndLengthFormatIdentifier.
"""

import time
import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_service27 import SupportService27

SSBL = SupportSBL()
SE27 = SupportService27()


def step_1(dut: Dut):
    """
    action: Extract vbf header and vbf block from VBF file.
    expected_result: Vbf header and vbf block are available in vbf file and could be extracted
                     properly.
    """
    # pylint: disable=unused-argument
    vbf_params = {"vbf_header": "",
                  "vbf_block": ""}

    vbf_result = SSBL.get_vbf_files()
    if not vbf_result:
        logging.error("Test Failed: Unable to load VBF files")
        return False, None

    _, vbf_params["vbf_header"], vbf_data, vbf_offset = SSBL.read_vbf_file(SSBL.get_df_filenames()[0])
    SSBL.vbf_header_convert(vbf_params["vbf_header"])
    vbf_params["vbf_block"] = SSBL.block_data_extract(vbf_data, vbf_offset)[1]
    logging.info("Successfully extract vbf block from SBL type vbf file")
    return True, vbf_params


def step_2(dut: Dut):
    """
    action: Enter into programming session and unlock security with valid key.
    expected_result: ECU is in programming session and security unlock successful.
    """
    dut.uds.set_mode(2)
    # Sleep time to avoid NRC37
    time.sleep(5)
    result = SE27.activate_security_access_fixedkey(dut, sa_keys=dut.conf.default_rig_config)
    if result:
        logging.info("Security access successful in programming session")
        return True

    logging.error("Test Failed: Security access denied in programming session")
    return False


def step_3(dut: Dut, vbf_params):
    """
    action: Send RequestDownload(34) with a valid addressAndLengthFormatIdentifier 0x44.
    expected_result: ECU should send a positive response 0x74.
    """
    # Preparing payload for RequestDownload(34)
    data_format_identifier = vbf_params['vbf_header']['data_format_identifier'].to_bytes(1, 'big')
    # Valid value for addressAndLengthFormatIdentifier
    address_length_format_identifier = b'\x44'
    addr_b = vbf_params['vbf_block']['StartAddress'].to_bytes(4, 'big')
    len_b = vbf_params['vbf_block']['Length'].to_bytes(4, 'big')

    payload = b'\x34' + data_format_identifier + address_length_format_identifier + addr_b + len_b
    response = dut.uds.generic_ecu_call(payload)

    # Expecting positive response '74' for requestDownload(34) in response.raw[2:4]
    if response.raw[2:4] == '74':
        logging.info("Received positive response 74 as expected for valid "
                     "addressAndLengthFormatIdentifier in requestDownload(34)")
        return True

    logging.error("Test Failed: Expected positive response 74 for requestDownload(34), received %s"
                  , response.raw)
    return False


def step_4(dut: Dut, vbf_params):
    """
    action: Send RequestDownload(34) with invalid addressAndLengthFormatIdentifier.
    expected_result: ECU should send negative Response 31(requestOutOfRange).
    """
    # Preparing payload for RequestDownload(34)
    data_format_identifier = vbf_params['vbf_header']["data_format_identifier"].to_bytes(1, 'big')
    # Invalid value for addressAndLengthFormatIdentifier
    address_length_format_identifier = b'\x33'
    addr_b = vbf_params['vbf_block']['StartAddress'].to_bytes(4, 'big')
    len_b = vbf_params['vbf_block']['Length'].to_bytes(4, 'big')

    payload = b'\x34' + data_format_identifier + address_length_format_identifier + addr_b + len_b
    response = dut.uds.generic_ecu_call(payload)

    # Expecting negative response '7F' in response.raw[2:4] and
    # NRC 31 in response.raw[6:8]
    if response.raw[2:4] == '7F' and response.raw[6:8] == '31':
        logging.info("Received NRC 31(requestOutOfRange) as expected for invalid "
                     "addressAndLengthFormatIdentifier in requestDownload(34)")
        result = True
    else:
        logging.error("Test Failed: Expected NRC 31(requestOutOfRange), received %s for "
                      "requestDownload(34)", response.raw)
        result = False
    return result


def run():
    """
    Send requestDownload(34) for the following:
        1. Valid addressAndLengthFormatIdentifier 0x44 and receive positive response 74.
        2. Invalid addressAndLengthFormatIdentifier and receive NRC 31(requestOutOfRange).
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=60)
        result_step, vbf_params = dut.step(step_1, purpose="Read VBF file and extract vbf header "
                                                           "and vbf block.")
        if result_step:
            result_step = dut.step(step_2, purpose='Security Access to ECU.')
        if result_step:
            result_step = dut.step(step_3, vbf_params, purpose="Verify positive response 74 for "
                            "valid addressAndLengthFormatIdentifier 0x44 in requestDownload(34).")
        if result_step:
            result_step = dut.step(step_4, vbf_params, purpose="Verify NRC 31 for invalid "
                                   "addressAndLengthFormatIdentifier in requestDownload(34).")
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
