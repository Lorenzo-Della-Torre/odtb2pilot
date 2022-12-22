"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 459337
version: 3
title: RequestDownload (34) - dataFormatIdentifier (DFI_)
purpose: >
    Compliance with VCC tools.

description: >
    The ECU shall encode the dataFormatIdentifier (DFI_) as stated in the table below:
    ------------------------------------------------------------------
    High   |    Low     |   Hex     |    Description
    nibble |   nibble   |        |
    ------------------------------------------------------------------
    0000        0000        00        No compression nor delta encoding
    0001        0000        10        Compression Method #1
    0010        0000        20        Compression Method #2
    0011        0000        30        Compression Method #3
    0100        0000        40        RESERVED
    0101        0000        50        RESERVED
    0110        0000        60        RESERVED
    0111        0000        70        Supplier specific compression method
    1000        0000        80        Delta encoding no compression method
    1001        0000        90        Delta encoding with Compression Method #1
    1010        0000        A0        Delta encoding with Compression Method #2
    1011        0000        B0        Delta encoding with Compression Method #3
    1100        0000        C0        RESERVED
    1101        0000        D0        RESERVED
    1110        0000        E0        RESERVED
    1111        0000        F0        Delta encoding with supplier specific compression method

details: >
    Verify RequestDownload(34) response for the following scenerios-
        1. Positive response 0x74 for a valid dataFormatIdentifier.
        2. Negative Response 31(requestOutOfRange) for invalid dataFormatIdentifier.
"""

import time
import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_file_io import SupportFileIO

SIO = SupportFileIO()
SSBL = SupportSBL()
SE27 = SupportService27()


def request_download(dut, dfi, vbf_block):
    """
    RequestDownload(0x34) with provided dataFormatIdentifier
    Args:
        dut (Dut): An instance of Dut
        data_format_identifier (str): dataFormatIdentifier hex
        vbf_block (dict): dictionary containing StartAddress & Length of memory block
    Returns:
        response (str): response of RequestDownload(0x34)
     """
    # Preparing payload for RequestDownload(34)
    data_format_identifier = int(dfi, 16).to_bytes(1, 'big')
    addr_b = vbf_block['StartAddress'].to_bytes(4, 'big')
    len_b = vbf_block['Length'].to_bytes(4, 'big')

    payload = b'\x34' + data_format_identifier + b'\x44' + addr_b + len_b
    response = dut.uds.generic_ecu_call(payload)
    return response.raw


def security_access(dut):
    """
    Set ECU in programming session and security access
    Args:
        dut (Dut): An instance of Dut
    Returns:
        (bool): True when security access successful in programming session
    """
    dut.uds.set_mode(2)
    # sleep to avoid NRC-37
    time.sleep(5)
    result = SE27.activate_security_access_fixedkey(dut, sa_keys=dut.conf.default_rig_config)
    if result:
        logging.info("Security access successful in programming session")
        return True

    logging.error("Test Failed: Security access denied in programming session")
    return False


def step_1(dut: Dut):
    """
    action: Extract vbf block from SBL type vbf file
    expected_result: vbf_block is available in vbf file and could be extract properly
    """
    # pylint: disable=unused-argument
    vbf_result = SSBL.get_vbf_files()
    if not vbf_result:
        logging.error("Test Failed: Unable to load VBF files")
        return False, None

    _, vbf_header, vbf_data, vbf_offset = SSBL.read_vbf_file(SSBL.get_sbl_filename())
    SSBL.vbf_header_convert(vbf_header)
    vbf_block = SSBL.block_data_extract(vbf_data, vbf_offset)[1]
    logging.info("Successfully extract vbf block from SBL type vbf file")
    return True, vbf_block


def step_2(dut: Dut, vbf_block, parameters):
    """
    action: RequestDownload(34) with a supported dataFormatIdentifier('0x00', '0x10', '0x20')
    expected_result: ECU should send a positive response 0x74 for all supported
                     dataFormatIdentifier.
    """
    allowed_dfi = parameters["allowed_data_format_identifiers"]
    results = []

    for dfi in parameters["supported_data_format_identifiers"]:
        sa_result = security_access(dut)
        if not sa_result:
            return False

        response = request_download(dut, dfi, vbf_block)
        if response[2:4] == '74':
            logging.info("Received positive response for dataFormatIdentifier - '%s' (%s) as "
                         "expected", dfi,allowed_dfi[dfi])
            results.append(True)
        else:
            logging.error("Expected positive response 0x74 for dataFormatIdentifier - '%s' (%s),"
                          " received %s", dfi, allowed_dfi[dfi], response)
            results.append(False)

    if len(results) != 0 and all(results):
        logging.info("Received positive response for all supported dataFormatIdentifier")
        return True

    logging.error("Test Failed: Positive response is not received for all valid "
                  "dataFormatIdentifier")
    return False


def step_3(dut: Dut, vbf_block):
    """
    action: RequestDownload(34) with a unsupported(invalid) dataFormatIdentifier.
    expected_result: ECU should send Negative Response with NRC-31(requestOutOfRange).
    """
    sa_result = security_access(dut)
    if not sa_result:
        return False

    # Invalid value for data_format_identifier
    dfi = '0x50'
    response = request_download(dut, dfi, vbf_block)
    if response[2:4] == '7F' and response[6:8] == '31':
        logging.info("Received NRC 31(requestOutOfRange) as expected for invalid "
                     "dataFormatIdentifier")
        result = True
    else:
        logging.error("Test Failed: Expected NRC 31(requestOutOfRange), received %s for "
                      "invalid dataFormatIdentifier", response)
        result = False

    return result


def run():
    """
    Send requestDownload(34) for the following:
        1. Valid dataFormatIdentifier and receive positive response 0x74.
        2. Invalid dataFormatIdentifier and receive NRC 31(requestOutOfRange).
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {"allowed_data_format_identifiers" : {},
                       "supported_data_format_identifiers" : []}

    try:
        dut.precondition(timeout=90)

        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step, vbf_block = dut.step(step_1, purpose="Read VBF file and extract vbf block ")

        if result_step:
            result_step = dut.step(step_2, vbf_block, parameters, purpose="Verify positive "
                                   "response 0x74 for RequestDownload(34) with valid "
                                   "dataFormatIdentifier")
        if result_step:
            result_step = dut.step(step_3, vbf_block, purpose="Verify NRC 31(requestOutOfRange) "
                                   "for RequestDownload(34) with invalid dataFormatIdentifier ")
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
