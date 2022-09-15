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
    Verify response for RequestDownload(0x34) is supported in programming session and not
    in default or extended session.
"""

import time
import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_can import SupportCAN
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_service34 import SupportService34
from supportfunctions.support_service27 import SupportService27

SC = SupportCAN()
SSBL = SupportSBL()
SE34 = SupportService34()
SE27 = SupportService27()


def get_vbf_params():
    """
    To extract vbf headers and vbf block from vbf file
    Returns:
        vbf_params (dict): Dictionary containing vbf header and vbf block
    """
    vbf_params = {"vbf_header": "",
                  "vbf_block": ""}

    result = SSBL.get_vbf_files()
    if result:
        _, vbf_params["vbf_header"], vbf_data, vbf_offset = SSBL.read_vbf_file(
                                                                        SSBL.get_sbl_filename())
        SSBL.vbf_header_convert(vbf_params["vbf_header"])
        vbf_params["vbf_block"] = SSBL.block_data_extract(vbf_data, vbf_offset)[1]
        return vbf_params

    logging.error("No sbl type vbf file found")
    return None


def service_34_for_non_programming_session(dut, session, vbf_params):
    """
    Verifying RequestDownload(0x34) in default/extended session
    Args:
        dut (class object): dut instance
        session (str): Diagnostic session
        vbf_params (dict): Dictionary containing vbf parameters
    Returns:
        bool: True if positive response is not received for RequestDownload(0x34).
    """
    result = SE34.request_block_download(dut, vbf_params["vbf_header"], vbf_params["vbf_block"])[0]

    if result:
        logging.error("Test Failed: RequestDownload(0x34) is supported in %s session, but "
                      "should not be supported", session)
        return False

    logging.info("RequestDownload(0x34) is not supported in %s session as expected", session)
    return True


def check_timing(dut, time_frame):
    """
    Verify response time for request service 34.
    Args:
        dut (class object): dut instance
        time_frame (int): valid timeframe
    Returns:
        bool: True if response received within given timeframe
    """
    result = False
    try:
        time_elapsed = dut.uds.milliseconds_since_request()
        if time_elapsed > time_frame:
            logging.error("Test Failed: Received response time is greater than expected time.")
            result = False
        else:
            logging.info("Received response time as expected.")
            result = True
    except IndexError:
        logging.error("Test Failed: Unable to receive correct response time for RequestDownload.")
        result = False
    return result


def service_34_for_programming_session(dut, vbf_params):
    """
    Verifying response of RequestDownload (0x34) in programming session
    Args:
        dut (class object): dut instance
        vbf_params (dict): dictionary containing vbf parameters
    Returns:
        bool: True if positive response 74 received for request service 34.
    """
    result = SE34.request_block_download(dut, vbf_params["vbf_header"], vbf_params["vbf_block"])[0]

    # Check response time for RequestDownload within 1000ms
    result_time = True
    if not check_timing(dut, 1000):
        result_time = False
        logging.error("RequestDownload (0x34) response took longer than 1000ms")

    # RequestDownload should be supported in programming.
    if not result:
        logging.error("Test Failed: RequestDownload (0x34) is not supported in programming session"
                      " but should be supported")
    return result and result_time


def step_1(dut: Dut):
    """
    action: Extract vbf parameters from the vbf file and verify response for RequestDownload (0x34)
            in default session
    expected_result: True if RequestDownload (0x34) is not supported in default session after
                     successfully extract vbf parameters from vbf file.
    """
    vbf_params = get_vbf_params()
    if vbf_params is None :
        logging.error("Test Failed: No sbl type vbf found")
        return False, None

    result = service_34_for_non_programming_session(dut, "default", vbf_params)
    return result, vbf_params


def step_2(dut: Dut, vbf_params):
    """
    action: Verify response for RequestDownload (0x34) in programming mode with security access.
    expected_result: True if positive response received for service 34.
    """
    #Sleep time to avoid NRC37
    time.sleep(5)

    dut.uds.set_mode(2)

	# RequestDownload without security access
    result = SE34.request_block_download(dut, vbf_params["vbf_header"], vbf_params["vbf_block"])[0]
    response = SC.can_messages[dut["receive"]][0][2]

    result_without_security = False
    # Check if RequestDownload response code contains NRC 33 securityAccessDenied
    if not result and response[6:8] == '33':
        logging.info("Received NRC 33 for RequestDownload(0x34) as expected,before security unlock")
        result_without_security = True
    else:
        logging.error("NRC 33 expected, received %s",response)
        result_without_security = False

    # RequestDownload with security access
    result_with_security = SE27.activate_security_access_fixedkey(dut, dut.conf.default_rig_config,
                                    step_no=272, purpose="SecurityAccess")
    if result_with_security:
        result_with_security = service_34_for_programming_session(dut, vbf_params)
    else:
        logging.error("Test Failed: Security access failed in programming session.")

    return result_with_security and result_without_security


def step_3(dut: Dut, vbf_params):
    """
    action: Verify response for RequestDownload (0x34) in extended session
    expected_result: RequestDownload (0x34) should not be supported in extended mode
    """
    dut.uds.set_mode()
    dut.uds.set_mode(3)
    result = SE27.activate_security_access_fixedkey(dut, dut.conf.default_rig_config, step_no=274,
                                                    purpose="SecurityAccess")

    # Verify active diagnostic session
    response = dut.uds.active_diag_session_f186()
    if response.data["details"]["mode"] != 3:
        logging.error("Test Failed: ECU is not in extended session, received session %s",
                       response.data["details"]["mode"])
        return False

    if result:
        result = service_34_for_non_programming_session(dut, "extended", vbf_params)
    else:
        logging.error("Test Failed: Security access is not supported in extended session.")
    return result


def run():
    """
    Verify response for RequestDownload (0x34) is supported in programming session and not
    in default or extended session.
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False
    try:
        dut.precondition(timeout=60)

        result_step, vbf_params = dut.step(step_1, purpose="Extracting vbf parameters from vbf "
                                           "file and verify response for RequestDownload(0x34) in "
                                           "default session")
        if result_step:
            result_step = dut.step(step_2, vbf_params, purpose="Verify response for "
                                                "RequestDownload (0x34) in programming session")

        if result_step:
            result_step = dut.step(step_3, vbf_params, purpose="Verify response for "
                                            "RequestDownload (0x34) request in extended session")

        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
