"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76673
version: 3
title: RequestDownload (34)
purpose: >
    Used in the SWDL process.

description: >
    The ECU shall support the service RequestDownload (0x34).
    The ECU shall implement the service accordingly:

    Supported sessions:
    The ECU shall support service RequestDownload in programmingSession,
    both primary and secondary bootloader.

    The ECU shall not support service RequestDownload in:
    •	defaultSession
    •	extendedDiagnosticSession

    Response time:
    Maximum response time for the service RequestDownload (0x34) is 1000ms.

    Entry conditions:
    The ECU shall not implement entry conditions for service RequestDownload (0x34).

    Security access:
    The ECU shall protect service RequestDownload (0x34) by using the service securityAccess (0x27).

details: >
    Checking response for RequestDownload(34) in programming session with
    response code 74 and it should not support in default & extended session.

    Also the maximum response time for the service RequestDownload(34) should
    be less than 1000ms.
"""
import logging
from glob import glob
from hilding.dut import Dut
from hilding.dut import DutTestError
from hilding.conf import Conf
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_service34 import SupportService34
from supportfunctions.support_service27 import SupportService27

CNF = Conf()
SSBL = SupportSBL()
SE34 = SupportService34()
SE27 = SupportService27()


def get_vbf_params(dut):
    """
    To Extract vbf headers and vbf block from VBF file
    Args:
        dut (class object): dut instance

    Returns:
        bool: True if data extraction is completed
        dict: dictionary containing vbf header and vbf block
    """
    vbf_params = {"vbf_header": "",
                  "vbf_block": ""}

    rig_vbf_path = dut.conf.rig.vbf_path
    # Read VBF file path with file-name
    vbf_paths = glob(str(rig_vbf_path) + "/*.vbf")

    if len(vbf_paths) == 0:
        msg = "Test Failed: VBF file not found in path: {}".format(
            rig_vbf_path)
        logging.error(msg)
        return False, None

    _, vbf_params["vbf_header"], vbf_data, vbf_offset = SSBL.read_vbf_file(
        vbf_paths[0])
    SSBL.vbf_header_convert(vbf_params["vbf_header"])
    vbf_params["vbf_block"] = SSBL.block_data_extract(vbf_data, vbf_offset)[1]
    return True, vbf_params


def service_34_check_non_programming(dut, session, vbf_params):
    """
    Verifying RequestDownload (34) request in default/extended mode
    Args:
        dut (class object): dut instance
        session (str): default/extended
        vbf_params (dict): dictionary containing all vbf parameters

    Returns:
        bool: True if Positive response 34 not received in RequestDownload (34) request
    """
    result = SE34.request_block_download(
        dut, vbf_params["vbf_header"], vbf_params["vbf_block"])[0]
    # Check if SE34 is not supported in default/extended session
    if result:
        msg = "Test Failed: SE34 is supported in {} session, "\
            "but should not be supported".format(session)
        logging.error(msg)
        return False
    msg = "Service 34(RequestDownload) request is not supported in {} "\
        "session as expected".format(session)
    logging.info(msg)
    return True


def check_timing(dut, time_frame, service):
    """
    To verify response time for RequestDownload (34)
    Args:
        dut (class object): dut instance
        time_frame (int): valid timeframe
        service (str): service 34

    Returns:
        bool: True if response received within given timeframe
    """
    result = False
    try:
        time_elapsed = dut.uds.milliseconds_since_request()
        if time_elapsed > time_frame:
            msg = "Test Failed: Received response time {} is greater"\
                "than expected time {} for service {}".format(
                    time_elapsed, time_frame, service)
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


def service_34_check_programming(dut, vbf_params):
    """
    Verifying RequestDownload (34) request in programming mode
    Args:
        dut (class object): dut instance
        vbf_params (dict): dictionary containing all vbf parameters

    Returns:
        bool: True if Positive response 74 received in RequestDownload (34) request
    """
    result = SE34.request_block_download(
        dut,  vbf_params["vbf_header"], vbf_params["vbf_block"])[0]

    # Check if SE34 responds within 1000ms
    result_time = True
    if not check_timing(dut, 1000, "SE34"):
        result_time = False
        logging.error("SE34 response took longer than 1000ms")

    # if request 34 is successful, set result as True since it should be supported
    if not result:
        logging.error("Test Failed: SE34 is not supported in programming session,"
                      " but should be supported")
    return result and result_time


def step_1(dut: Dut):
    """
    action: Extract vbf headers, vbf block data and vbf block from the vbf file.

    expected_result: Vbf headers, vbf block data and vbf block are available in
                                vbf file and could be extracted properly.
    """
    return get_vbf_params(dut)


def step_2(dut: Dut, vbf_params):
    """
    action: Verify RequestDownload (34) in default mode

    expected_result: Request 34 should not support in default mode
    """

    return service_34_check_non_programming(dut, "default", vbf_params)


def step_3(dut: Dut, vbf_params):
    """
    action: Verify RequestDownload (34) in programming mode with security access

    expected_result: A positive response 0x74 should be received
    """
    dut.uds.set_mode(2)
	# SE34 without security access
    # Preparing payload for SE34
    addr_b = vbf_params['vbf_block']['StartAddress'].to_bytes(4, 'big')
    len_b = vbf_params['vbf_block']['Length'].to_bytes(4, 'big')
    data_format_identifier = vbf_params['vbf_header']["data_format_identifier"].to_bytes(
        1, 'big')
    payload = b'\x34' + data_format_identifier + b'\x44' + addr_b + len_b

    response = dut.uds.generic_ecu_call(payload)

    # Check if SE34 response code contains NRC 33 securityAccessDenied
    result_without_security = False
    if response.raw[2:4] == '7F':
        if response.raw[6:8] == '33':
            msg = "Received NRC {} for RequestDownload (34) as"\
                " expected before security unlock".format(response.raw[6:8])
            logging.info(msg)
            result_without_security = True
        else:
            msg = "NRC 33 expected, received {}".format(response.raw[6:8])
            logging.error(msg)
            result_without_security = False

    # SE34 with security access
    result_with_security = SE27.activate_security_access_fixedkey(dut, CNF.default_rig_config,
                                    step_no=272, purpose="SecurityAccess")
    if result_with_security:
        result_with_security = service_34_check_programming(dut, vbf_params)
    else:
        logging.error("Test Failed: Security Access failed in programming session.")

    return result_with_security and result_without_security


def step_4(dut: Dut, vbf_params):
    """
    action: Verify RequestDownload (34) in extended mode

    expected_result: Request 34 should not support in extended mode
    """
    dut.uds.set_mode()
    dut.uds.set_mode(3)
    result = SE27.activate_security_access_fixedkey(dut, CNF.default_rig_config, step_no=272,
                                                    purpose="SecurityAccess")
    if result:
        result = service_34_check_non_programming(dut, "extended", vbf_params)
    else:
        logging.error("Test Failed: Security Access is not supported in extended session.")
    return result


def run():
    """
    Verification of RequestDownload (34) request
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
                                   purpose='RequestDownload request in default session')

        if result_step:
            result_step = dut.step(step_3, vbf_params,
                                   purpose='RequestDownload request in programming session')

        if result_step:
            result_step = dut.step(step_4, vbf_params,
                                   purpose='RequestDownload request in extended session')

        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
