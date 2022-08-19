"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76696
version: 5
title: RequestTransferExit (37) - transferResponseParameterRecord
purpose: >
    There are two transferResponseParameterRecord alternatives: with/without CRC.
    An integrity check of the programmed data is performed at the ECU authenticity
    verification (Check Memory), according to the Software Authentication concept.
    Hence, the calculation of a checksum at RequestTransferExit is omitted (time consuming)
    for that case. A checksum calculation is also not suitable when delta encoding is used,
    as the location and number of transferred data block and written data block might differ.

description: >
    If the ECU does not support Software Authentication (CheckMemory routine) as defined in
    Ref[LC => General Software Authentication] the transferResponseParameterRecord
    shall contain a checksum for downloaded or uploaded data block.
    If the ECU supports Software Authentication, no transferResponseParameterRecord
    shall be used for downloaded block but only for upload.

    Examples - Data transfer initiated by RequestDownload

    Example 1. CheckMemory is not implemented.(RequestTransferExit positive
    response when CheckMemory is not implemented)
    ----------------------------------------------------------
    Description                 Data
    ----------------------------------------------------------
    RequestTransferExit (S.F)	01	37	00	00	00	00	00	00
    Positive response	        03	77	xx	xx	00	00	00	00
    ----------------------------------------------------------
    EXPLANATION => 2-byte CRC

    Example 2: CheckMemory is implemented.(RequestTransferExit positive response when
    CheckMemory is implemented (i.e. Software Authentication supported))
    ----------------------------------------------------------
    Description                 Data
    ----------------------------------------------------------
    RequestTransferExit (S.F)	01	37	00	00	00	00	00	00
    Positive response	        01	77	00	00	00	00	00	00
    ----------------------------------------------------------
    EXPLANATION => CRC omitted

details: >
    Verifying support software authentication (CheckMemory routine) after
    calling RequestTransferExit (37)
    1. Extract vbf parameters for Transfer Data (36) request
    2. Send Transfer Data (36) request
    3. After Transfer Data request (36) completion, based on vbf version:
        i. Check 2-byte CRC or,
        ii. Check CRC omitted
"""

import logging
from glob import glob
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_can import SupportCAN
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_service34 import SupportService34
from supportfunctions.support_service36 import SupportService36
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_service37 import SupportService37
from supportfunctions.support_service31 import SupportService31

SC = SupportCAN()
SSBL = SupportSBL()
SE34 = SupportService34()
SE36 = SupportService36()
SE27 = SupportService27()
SE37 = SupportService37()
SE31 = SupportService31()


def get_vbf_params(dut):
    """
    Extract vbf parameters from vbf file
    Args:
        dut (Dut): An instance of Dut
    Returns:
        vbf_params (dict): VBF header, block, block data and version
    """
    vbf_params = {"vbf_header": "",
                  "vbf_block": "",
                  "vbf_block_data": ""}

    rig_vbf_path = dut.conf.rig.vbf_path
    vbf_file_paths = glob(str(rig_vbf_path) + "/*.vbf")
    if len(vbf_file_paths) > 0:
        for vbf_file_path in vbf_file_paths:
            _ , vbf_params["vbf_header"], vbf_data, vbf_offset = SSBL.read_vbf_file(
                vbf_file_path)
            vbf_header = dict(vbf_params["vbf_header"])
            if vbf_header['sw_part_type'] == 'SBL':
                SSBL.vbf_header_convert(vbf_params["vbf_header"])
                _, vbf_params["vbf_block"], vbf_params["vbf_block_data"] = SSBL.block_data_extract(
                    vbf_data, vbf_offset)
                return True, vbf_params
    logging.error("No SBL VBF found in %s", rig_vbf_path)
    return False, None


def transfer_data(dut, vbf_params):
    """
    Send transfer data(36) request
    Args:
        dut (Dut): An instance of Dut
        vbf_params (dict): VBF header, block and block data
    Returns:
        (bool): True when successfully sent request
    """
    result, nbl = SE34.request_block_download(
        dut, vbf_params["vbf_header"], vbf_params["vbf_block"])
    if not result:
        logging.error("Test Failed: SE34 request failed")
        return False

    result = SE36.flash_blocks(
        dut, vbf_params["vbf_block_data"], vbf_params["vbf_block"], nbl)
    if not result:
        logging.error("Test Failed: SE36 request failed")
        return False

    result = SE37.transfer_data_exit(dut)
    if not result:
        logging.error("Test Failed: SE37 request failed")
        return False
    return result


def step_1(dut: Dut):
    """
    action: Extract vbf parameters
    expected_result: vbf parameters
    """
    return get_vbf_params(dut)


def step_2(dut: Dut, vbf_params):
    """
    action: Request transfer data(36) in sequence i.e. security access(27), SE34, SE36 and SE37
    expected_result: True when successfully sent request
    """
    # Set to programming session
    dut.uds.set_mode(2)

    result = SE27.activate_security_access_fixedkey(dut, sa_keys=dut.conf.default_rig_config)
    if result:
        result = transfer_data(dut, vbf_params)
    return result


def step_3(dut: Dut, vbf_params):
    """
    action: Verify software authentication(CheckMemory routine) in
            transferResponseParameterRecord
    expected_result: True when successfully verified CheckMemory routine
    """
    result = False
    se37_response = SC.can_messages[dut["receive"]][0][2]
    check_memory_bool = SE31.check_memory(dut, vbf_params["vbf_header"], stepno=3)
    if check_memory_bool:
        # if Checkmemory implemented, se37_response[4:8] will be 0000
        result = int(se37_response[4:8], 16) == 0
        if not result:
            logging.error("Test Failed: Checkmemory routine implemented, but still receiving CRC")
    else:
        # if Checkmemory not implemented, se37_response[4:8] will be xxxx(2 byte CRC)
        logging.info("VBF file version received: %s, Checkmemory is not supported",
                      vbf_params["version"])
        result = int(se37_response[4:8], 16) != 0
        if not result:
            logging.error("Test Failed: Checkmemory routine not implemented, So 2 byte CRC is"
                          " expected")
    return result


def run():
    """
    Verifying checksum after check memory routine
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=30)
        result_step, vbf_params = dut.step(step_1, purpose='Extract vbf parameters')
        if result_step:
            result_step = dut.step(step_2, vbf_params, purpose='Request transfer data(36) request')
        if result_step:
            result_step = dut.step(step_3, vbf_params, purpose='Verify software authentication'
                                                               '(CheckMemory routine)')
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
