"""
/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



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
    EXPLAINATION => 2-byte CRC

    Example 2: CheckMemory is implemented.(RequestTransferExit positive response when
    CheckMemory is implemented (i.e. Software Authentication supported))
    ----------------------------------------------------------
    Description                 Data
    ----------------------------------------------------------
    RequestTransferExit (S.F)	01	37	00	00	00	00	00	00
    Positive response	        01	77	00	00	00	00	00	00
    ----------------------------------------------------------
    EXPLAINATION => CRC omitted

details: >
    Verifying support Software Authentication (CheckMemory routine) after
    calling RequestTransferExit (37)
    1. Retriving vbf parameters for Transfer Data (36) request
    2. Send Transfer Data (36) request
    3. After Transfer Data request (36) completion, based on vbf version:
        i. Check 2-byte CRC or,
        ii. Check CRC omitted
"""

import logging
import inspect
from glob import glob
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_can import SupportCAN
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_sec_acc import SecAccessParam
from supportfunctions.support_service34 import SupportService34
from supportfunctions.support_service36 import SupportService36
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_service37 import SupportService37
from supportfunctions.support_service31 import SupportService31


SC = SupportCAN()
SE34 = SupportService34()
SSBL = SupportSBL()
SE36 = SupportService36()
SIO = SupportFileIO()
SE27 = SupportService27()
SE37 = SupportService37()
SE31 = SupportService31()


def get_vbf_params(dut):
    """
     Extract VBF parameters from VBF file
     Args:
         dut (class object): Dut instance

     Returns:
        bool: Success
        dict: dictionary containing VBF header,block,block data,version
     """
    vbf_params = {"vbf_header": "",
                  "vbf_block": "",
                  "vbf_block_data": ""
                  }

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
    Send Transfer Data (36) request
    Args:
        dut (class object): Dut instance
        vbf_params (dict): dictionary containing VBF header,block,block data
    Returns:
        bool: True if request is successful
    """
    result, nbl = SE34.request_block_download(
        dut, vbf_params["vbf_header"], vbf_params["vbf_block"])
    if not result:
        logging.error("Test failed: SE34 request failed")
        return False

    result = SE36.flash_blocks(
        dut, vbf_params["vbf_block_data"], vbf_params["vbf_block"], nbl)
    if not result:
        logging.error("Test failed: SE36 request failed")
        return False

    result = SE37.transfer_data_exit(dut)
    if not result:
        logging.error("Test failed: SE37 request failed")
        return False
    return result


def step_1(dut: Dut):
    """
    action: To Extract VBF parameters

    expected_result: Response VBF parameters
    """
    return get_vbf_params(dut)


def step_2(dut: Dut, vbf_params):
    """
    action: calling transfer_data() for Transfer Data (36) request in
                        sequence ie Security access(27) and then SE34-36-37

    expected_result: On success return True
    """
    dut.uds.set_mode(2)
    sa_keys: SecAccessParam = {
        "SecAcc_Gen": 'Gen2',
        "fixed_key": '0102030405',
        "auth_key": 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF',
        "proof_key": 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), sa_keys)

    result = SE27.activate_security_access_fixedkey(
        dut, sa_keys, step_no=2, purpose="SecurityAccess")
    if result:
        result = transfer_data(dut, vbf_params)
    return result


def step_3(dut: Dut, vbf_params):
    """
    action: Verifying Software Authentication (CheckMemory routine)
            in transferResponseParameterRecord

    expected_result: Receive a checksum if CRC not implemented otherwise no checksum
    """
    result = False
    se37_response = SC.can_messages[dut["receive"]][0][2]
    check_memory_bool = SE31.check_memory(dut, vbf_params["vbf_header"], 3)
    if check_memory_bool:
        # if Checkmemory implemented, se37_response[4:8] will be 0000
        result = int(se37_response[4:8], 16) == 0
        if not result:
            msg = "Test failed: Checkmemory routine implemented,"\
                " but still reciving CRC."
            logging.error(msg)
    else:
        # if Checkmemory not implemented, se37_response[4:8] will be xxxx(2 byte CRC)
        msg = "VBF file version recieved: {},"\
            " Checkmemory is not supported".format(vbf_params["version"])
        logging.info(msg)
        result = int(se37_response[4:8], 16) != 0
        if not result:
            msg = "Test failed: Checkmemory routine not"\
                " implemented, So 2 byte CRC is expected."
            logging.info(msg)
    return result


def run():
    """
    action: Verifying checksum after check memory routine

    expected_result: A Positive Response
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    try:
        dut.precondition(timeout=60)
        result, vbf_params = dut.step(
            step_1, purpose='To extract VBF parameters for Transfer Data (36) request')

        if result:
            result = dut.step(
                step_2, vbf_params, purpose='Calling Transfer Data (36) request')

        if result:
            result = dut.step(
                step_3, vbf_params, purpose='Verifying Software Authentication'\
                    ' (CheckMemory routine)')
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
