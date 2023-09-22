"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76690
version: 3
title: TransferData (36)
purpose: >
    Purpose Transfers data via the client and the ECU.

description: >
    The ECU shall support the service TransferData (0x36).
    The ECU shall implement the service accordingly:

    Supported sessions:
    The ECU shall support service TransferData in programmingSession,
    both primary and secondary bootloader.

    The ECU shall not support service TransferData in:
    •   defaultSession
    •   extendedDiagnosticSession
    Response time:
    Maximum response time for the service transferData (0x36) is 5000ms.

    Entry conditions:
    The ECU shall not implement entry conditions for service TransferData (0x36).

    Security access:
    The ECU shall not protect service TransferData (0x36) by
    using the service securityAccess (0x27).

details: >
    Checking response for transferData(36) in programming session with
    response code 76 and it should not support in default & extended session

    Also the maximum response time for the service transferData (0x36) should
    be less than 5000ms.
"""
import time
import logging
from glob import glob
from hilding.conf import Conf
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_service34 import SupportService34
from supportfunctions.support_service36 import SupportService36
from supportfunctions.support_service37 import SupportService37
from supportfunctions.support_service27 import SupportService27

CNF = Conf()
SSBL = SupportSBL()
SE34 = SupportService34()
SE36 = SupportService36()
SE37 = SupportService37()
SE27 = SupportService27()


def get_vbf_params(dut):
    """
    To Extract vbf headers, vbf block data and vbf block from VBF file
    Args:
        dut (class object): dut instance

    Returns:
        bool: True if data extraction is completed
        dict: dictionary containing vbf header, block and block data
    """
    vbf_params = {"vbf_header": "",
                  "vbf_block": "",
                  "vbf_block_data": ""}

    rig_vbf_path = dut.conf.rig.vbf_path
    # Read VBF file path with file-name
    vbf_paths = glob(str(rig_vbf_path) + "/*.vbf")
    if len(vbf_paths) == 0:
        msg = "Test Failed: VBF file not found in path: {}".format(rig_vbf_path)
        logging.error(msg)
        return False, None
    vbf_path = vbf_paths[0]
    _, vbf_params["vbf_header"], vbf_data, vbf_offset = SSBL.read_vbf_file(
        vbf_path)
    SSBL.vbf_header_convert(vbf_params["vbf_header"])
    _, vbf_params["vbf_block"], vbf_params["vbf_block_data"] = SSBL.block_data_extract(
        vbf_data, vbf_offset)
    return True, vbf_params


def service_36_check_non_programming(dut, session, vbf_params):
    """
    Verifying Transfer data(36) request in default/extended mode
    Args:
        dut (class object): dut instance
        session (str): default/extended
        vbf_params (dict): dictionary containing all vbf parameters

    Returns:
        bool: True if Positive response 76 not received in Transfer data(36) request
    """
    result, nbl = SE34.request_block_download(
        dut, vbf_params["vbf_header"], vbf_params["vbf_block"])

    # Check if SE34 is supported, then terminate test since it should not be supported
    # else check SE36
    if not result:
        result = not SE36.flash_blocks(
            dut, vbf_params["vbf_block_data"], vbf_params["vbf_block"], nbl)
    else:
        msg = "Test Failed: SE34 is supported in {} session,"\
            "but should not be supported".format(session)
        logging.error(msg)
        return False

    # Check if SE36 is supported, then terminate test since it should not be supported
    # else check SE37
    if result:
        result = not SE37.transfer_data_exit(dut)
    else:
        msg = "Test Failed: SE36 is supported in {} session,"\
                "but should not be supported".format(session)
        logging.error(msg)
        return False

    # Check if SE37 is supported, then terminate test since it should
    # not be supported
    if not result:
        msg = "Test Failed: SE37 is supported in {} session, "\
            "but should not be supported".format(session)
        logging.error(msg)
        return False

    msg = "Service 36(TransferData request) is not supported in {} "\
        "session as expected".format(session)
    logging.info(msg)
    return result


def check_timing(dut, time_frame, service):
    """
    To verify response time for Transfer data(36)
    Args:
        dut (class object): dut instance
        time_frame (int): valid timeframe
        service (str): service 36

    Returns:
        bool: True if response received within given timeframe
    """
    result = False
    try:
        time_elapsed = dut.uds.milliseconds_since_request()
        if time_elapsed > time_frame:
            msg = "Test Failed: Received response time {} is greater"\
            "than expected time {} for service {}".format(time_elapsed, time_frame, service)
            logging.error(msg)
            result = False
        else:
            msg = "{}ms elapsed for service {}".format(time_elapsed, service)
            logging.info(msg)
            result = True
    except IndexError:
        msg = "Test Failed: Unable to receive correct response for time_elapsed for {}".format(
            service)
        logging.error(msg)
        result = False
    return result


def service_36_check_programming(dut, vbf_params):
    """
    Verifying Transfer data(36) request in programming mode
    Args:
        dut (class object): dut instance
        vbf_params (dict): dictionary containing all vbf parameters

    Returns:
        bool: True if Positive response 76 received in Transfer data(36) request
    """
    result, nbl = SE34.request_block_download(
        dut,  vbf_params["vbf_header"], vbf_params["vbf_block"])

    # if request 34 is successful, check SE36 otherwise log SE34
    # failed since it should be supported
    if result:
        result = SE36.flash_blocks(
            dut, vbf_params["vbf_block_data"], vbf_params["vbf_block"], nbl)
    else:
        logging.error("Test Failed: SE34 is not supported in programming session,"\
                      "but should be supported")
        return False

    # Check if SE36 responds within 5000ms
    result_time = True
    if not check_timing(dut, 5000, "SE36"):
        result_time = False
        logging.error("SE36 response took longer than 5000ms")

    # if request 36 is successful, check SE37 otherwise log
    # SE36 failed since it should be supported
    if result:
        result = SE37.transfer_data_exit(dut)
    else:
        logging.error("Test Failed: SE36 is not supported in programming session,"\
                      "but should be supported")
        return False

    # if SE37 Failed, log error since it should be supported
    if not result:
        logging.error(
            "Test Failed: SE37 is not supported in programming session,"\
            "but should be supported")
        return False
    return result and result_time


def step_1(dut: Dut):
    """
    action: Extract vbf headers, vbf block data and vbf block from the vbf file.

    expected_result: Vbf headers, vbf block data and vbf block are available
                    in vbf file and could be extracted properly.
    """
    return get_vbf_params(dut)


def step_2(dut: Dut, vbf_params):
    """
    action: Verify Transfer data(36) in default mode

    expected_result: Request 36 should not support in default mode
    """

    return service_36_check_non_programming(dut, "default", vbf_params)


def step_3(dut: Dut, vbf_params):
    """
    action: Verify Transfer data(36) in programming mode
            with security access

    expected_result: A positive response 0x76 should be received
    """
    # SE36 without security access
    dut.uds.set_mode(2)
    payload = b'\x36' + bytes([0]) + vbf_params["vbf_block_data"][0:4064]
    response = dut.uds.generic_ecu_call(payload)
    result_without_security = False
    if response.raw[2:4] == '7F':
        if response.raw[6:8] == '13' or response.raw[6:8] == '24':
            msg = "Received NRC {} for Transfer Data(36) as"\
                " expected before security unlock".format(response.raw[6:8])
            logging.info(msg)
            result_without_security = True
        else:
            msg = "NRC 13 or 24 expected, received {}".format(response.raw[6:8])
            logging.error(msg)
            result_without_security = False

    # SE36 with security access
    result_with_security = SE27.activate_security_access_fixedkey(dut, CNF.default_rig_config,
                                    step_no=272, purpose="SecurityAccess")
    if result_with_security:
        result_with_security = service_36_check_programming(dut, vbf_params)
    return result_with_security and result_without_security


def step_4(dut: Dut, vbf_params):
    """
    action: Verify Transfer data(36) in extended mode

    expected_result: Request 36 should not support in extended mode
    """
    dut.uds.set_mode(1)
    time.sleep(3)
    dut.uds.set_mode(3)
    result = SE27.activate_security_access_fixedkey(dut, CNF.default_rig_config,
                                    step_no=272, purpose="SecurityAccess")
    if result:
        result = service_36_check_non_programming(dut, "extended", vbf_params)
    else:
        logging.error(
            "Test Failed: Security Access is not supported in extended session.")
    return result


def run():
    """
    Verification of transfer data(36) request
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False
    try:
        dut.precondition(timeout=60)
        result_step, vbf_params = dut.step(step_1,
                                      purpose='Read vbf file and extracting vbf parameters')
        if result_step:
            result_step = dut.step(step_2, vbf_params,
                              purpose='TransferData request in default session')

        if result_step:
            result_step = dut.step(step_3, vbf_params,
                              purpose='TransferData request in programming session')
        if result_step:
            result_step = dut.step(step_4, vbf_params,
                              purpose='TransferData request in extended session')
        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
