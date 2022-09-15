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
    Purpose	Compliance with VCC tools.

description: >
    The ECU shall encode the dataFormatIdentifier (DFI_) as stated in the table below:
    ------------------------------------------------------------------
    High   |	Low 	|   Hex	 |	Description
    nibble |   nibble   |        |
    ------------------------------------------------------------------
    0000		0000		00		No compression nor delta encoding
    0001		0000		10		Compression Method #1
    0010		0000		20		Compression Method #2
    0011		0000		30		Compression Method #3
    0100		0000		40		RESERVED
    0101		0000		50		RESERVED
    0110		0000		60		RESERVED
    0111		0000		70		Supplier specific compression method
    1000		0000		80		Delta encoding no compression method
    1001		0000		90		Delta encoding with Compression Method #1
    1010		0000		A0		Delta encoding with Compression Method #2
    1011		0000		B0		Delta encoding with Compression Method #3
    1100		0000		C0		RESERVED
    1101		0000		D0		RESERVED
    1110		0000		E0		RESERVED
    1111		0000		F0		Delta encoding with supplier specific compression method

details: >
    Verify RequestDownload(34) response for the following scenerios-
        1. Positive response 0x74 for a valid dataFormatIdentifier.
        2. Negative Response 31(requestOutOfRange) for invalid dataFormatIdentifier.
"""

import time
import logging

from glob import glob
from hilding.conf import Conf
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_file_io import SupportFileIO

SIO = SupportFileIO()
CNF = Conf()
SSBL = SupportSBL()
SE27 = SupportService27()


def get_vbf_block(dut):
    """
    Read vbf file and extract vbf_block(StartAddress, Length and Checksum)
     Args:
         dut (class obj): Dut instance

     Returns:
        (bool): True
        vbf_block (dict): dictionary containing StartAddress, Length and Checksum
     """

    rig_vbf_path = dut.conf.rig.vbf_path
    vbf_file_paths = glob(str(rig_vbf_path) + "/*.vbf")

    if len(vbf_file_paths) == 0:
        msg = "Test Failed: VBF file not found in path: {}".format(rig_vbf_path)
        logging.error(msg)
        return False, None

    vbf_data, vbf_offset = SSBL.read_vbf_file(vbf_file_paths[0])[2:4]
    vbf_block = SSBL.block_data_extract(vbf_data, vbf_offset)[1]
    return True, vbf_block


def read_yml_parameters(dut: Dut):
    """
    Read parameters from yml file.
    Args:
        dut (class obj): Dut instance

    Returns:
        parameters (dict): dictionary containing yml parameters
    """
    # pylint: disable=unused-argument
    parameters = {"allowed_data_format_identifiers" : {},
                "supported_data_format_identifiers" : []}
    parameters = SIO.extract_parameter_yml("*", parameters)
    if parameters is None:
        logging.error("Test failed: yml parameters are not present")
        return False
    return parameters

def request_download(dut, dfi, vbf_block):
    """
    Call RequestDownload(0x34) with provided dataFormatIdentifier
     Args:
        dut (class obj): Dut instance
        data_format_identifier(str): dataFormatIdentifier hex
        vbf_block (dict): dictionary containing StartAddress & Length
     Returns:
        response (str): response code
     """
    # Preparing payload for RequestDownload(34)
    data_format_identifier = int(dfi, 16).to_bytes(1, 'big')
    addr_b = vbf_block['StartAddress'].to_bytes(4, 'big')
    len_b = vbf_block['Length'].to_bytes(4, 'big')

    payload = b'\x34' + data_format_identifier + b'\x44' + addr_b + len_b
    # ECU call
    response = dut.uds.generic_ecu_call(payload)

    return response.raw


def security_access(dut: Dut):
    """
    Enter into Programming Session and Unlock security with valid key.
    Args:
        dut (class obj): Dut instance
    Returns:
        (bool): True when security access is granted
    """

    dut.uds.set_mode(2)
    sa_keys = CNF.default_rig_config
    result = SE27.activate_security_access_fixedkey(dut, sa_keys, step_no=272,
                                                    purpose="SecurityAccess")

    if result:
        return True
    return False


def step_1(dut: Dut):
    """
    action: Extract vbf block from VBF file

    expected_result: vbf_block is available in vbf file and could be extracted properly.
    """

    result, vbf_block = get_vbf_block(dut)


    if result:
        return True, vbf_block

    logging.error("Test Failed: Unable to extract vbf_block from vbf file")
    return False, None


def step_2(dut: Dut, vbf_block):
    """
    action: Send RequestDownload(34) with a supported dataFormatIdentifier('0x00', '0x10', '0x20')

    expected_result: ECU should send a positive response 0x74 for all supported
                    dataFormatIdentifier.
    """

    parameters = read_yml_parameters(dut)
    allowed_dfi = parameters["allowed_data_format_identifiers"]

    results = []
    # Sleep time to avoid NRC37
    time.sleep(5)

    for dfi in parameters["supported_data_format_identifiers"]:
        sa_result = security_access(dut)
        if not sa_result:
            logging.error("Test Failed: Security Access Denied")
            return False

        response = request_download(dut, dfi, vbf_block)

        if response[2:4] == '74':
            msg = "Received positive response 0x74 as expected for valid "\
            "dataFormatIdentifier - '{}' ({}) in requestDownload(34)".format(dfi,allowed_dfi[dfi])
            logging.info(msg)
            results.append(True)
        else:
            msg = "Expected positive response 0x74 for dataFormatIdentifier - '{}' ({}),"\
                " received {}".format(dfi, allowed_dfi[dfi],response)
            logging.error(msg)
            results.append(False)

    if len(results) != 0 and all(results):
        return True

    logging.error("Test failed: Received invalid response for valid dataFormatIdentifier")
    return False

def step_3(dut: Dut, vbf_block):
    """
    action: Send RequestDownload(34) with a unsupported(invalid) dataFormatIdentifier.

    expected_result: ECU should send Negative Response 31(requestOutOfRange).
    """
    # Request Security Access
    sa_result = security_access(dut)
    if not sa_result:
        logging.error("Test Failed: Security Access Denied")
        return False

    # Invalid value for data_format_identifier
    dfi = '0x50'
    response = request_download(dut, dfi, vbf_block)

    if response[2:4] == '7F' and response[6:8] == '31':
        logging.info("Received NRC 31(requestOutOfRange) as expected for invalid "\
                     "dataFormatIdentifier in requestDownload(34)")
        result = True
    else:
        msg = "Test failed: Expected NRC 31(requestOutOfRange), received {} for"\
            " requestDownload(34)".format(response)
        logging.error(msg)
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
    try:
        dut.precondition(timeout=60)

        result_step, vbf_block = dut.step(step_1, purpose='Read VBF file and extract '\
                                           'vbf header and vbf block.')

        if result_step:
            result_step = dut.step(step_2, vbf_block, purpose='Verify positive response 0x74 for '
                                   'valid dataFormatIdentifier in requestDownload(34)')

        if result_step:
            result_step = dut.step(step_3, vbf_block, purpose='Verify NRC 31(requestOutOfRange) '
                                   'for invalid dataFormatIdentifier in requestDownload(34)')

        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
