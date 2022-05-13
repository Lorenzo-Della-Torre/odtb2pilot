"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 481795
version: 3
title: : Security Access Levels
purpose: >
    Definition of the request seed subfunction parameter "Level".

description: >
    The request seed subfunction parameter for security access level shall be according
    to "Table - Security Access Levels definition".

    01 - Diagnostic services in programmingSession, e.g. software download (DID 0xF103)
    05 - Diagnostic services in extendedSession(DID 0xF10A)
    19 - Security Log (DID 0xF115)
    23 - Secure Debug (0xF112)
    27 - Secure On-board Communication (DID 0xF117)

    The ECU teams must ensure that:
    -New/changed usage of Security Access Levels, key usage and any diagnostics protected
    by Security Access are approved by OEM stakeholder and documented, e.g. for diagnostics
    used in OEM EoL and workshops.
    -Keys are programmed and applied at EoL and workshops
    -The authentication_method is documented in Global Master Reference Database.
    Example.
    An ECU with software download and supporting security access protected service
    (in extendedSession) shall by default support level 1 and 5.

details: >
    Verify respective security access key are programmed for different access levels in all
    diagnostic sessions.
    Steps-
    • Verify security access request & response seed for levels 01, 19 in programming session
    • Verify security access request & response seed for levels 05, 19, 23, 27 in extended
      session
"""

import logging
import time
from hilding.dut import DutTestError
from hilding.dut import Dut
from hilding.conf import Conf
from supportfunctions.support_sec_acc import SupportSecurityAccess
from supportfunctions.support_file_io import SupportFileIO

SIO = SupportFileIO()
SSA = SupportSecurityAccess()
CNF = Conf()


def security_access_seed(dut: Dut, level):
    """
    security access to ECU for request seed
    Args:
        dut(class object): dut instance
        level(str): Security access level
    Returns: ECU response seed
    """
    # Set security access key and level
    SSA.set_keys(CNF.default_rig_config)
    SSA.set_level_key(int(level, 16))

    # Prepare client request seed
    client_req_seed = SSA.prepare_client_request_seed()
    response = dut.uds.generic_ecu_call(client_req_seed)

    # Truncate initial 2 bytes from response to process server response seed
    server_res_seed = response.raw[4:]
    result = SSA.process_server_response_seed(
        bytearray.fromhex(server_res_seed))

    # Check serverResponseSeed is successful or not
    if result == 0:
        logging.info("serverResponseSeed successful")
        return server_res_seed
    logging.error("Security Access Request Seed not successful")
    return None


def verify_ecu_response(response, level):
    """
    Verify serverResponseSeed response is 0x67
    Args:
        response(str): response
        level(str): Security access level
    Returns: True on successful verification
    """
    if response is not None:
        # Extract first byte from response and compare with '0x67'
        if response[:2] == '67':
            return True

    msg = "Response expected 0x67 but received: {} for Security level: {}".format(response, level)
    logging.error(msg)
    return False


def step_1(dut: Dut):
    """
    action: Read yml parameters and Set ECU to programming session. clientRequestSeed for
            security access levels 01, 19 and validate the server seed response 0x67.

    expected_result: Positive response when security access responseSeed is 67 for all
                     supported security access levels
    """
    result = []

    # Read yml parameters
    parameters_dict = {'sa_levels_programming': '',
                       'sa_levels_extended': ''}
    parameters = SIO.parameter_adopt_teststep(parameters_dict)
    if not all(list(parameters.values())):
        logging.error("Test Failed: yml parameter not found")
        return False, None
    # Verify supported programming session security access level
    dut.uds.set_mode(2)
    for level in parameters['sa_levels_programming']:
        response = security_access_seed(dut, level)
        result.append(verify_ecu_response(response, level))

    if len(result) != 0 and all(result):
        return True, parameters

    logging.error("Test Failed: Invalid response or security access requestSeed not successful "
                  "in programming session")
    return False, None


def step_2(dut: Dut, parameters):
    """
    action: Set ECU to Extended session. clientRequestSeed for security access levels 05, 19,
            23, 27 and validate the server seed response 0x67.
    expected_result: Positive response when security access responseSeed is 67 for all
                     supported security access levels
    """
    result = []
    if parameters is None:
        logging.error("Test Failed: yml parameter not found")
        return False

    dut.uds.set_mode(1)
    # Verify supported extended session security access level
    dut.uds.set_mode(3)
    #Adding a sleep time to avoid NRC 37 (requiredTimeDelayNotExpired)
    time.sleep(5)

    for level in parameters['sa_levels_extended']:
        response = security_access_seed(dut, level)
        result.append(verify_ecu_response(response, level))

    if len(result) != 0 and all(result):
        return True
    logging.error("Test Failed: Invalid response or security access requestSeed not successful "
                  "in extended session")
    return False


def run():
    """
    Verify respective security access key are programmed for different access levels in all
    diagnostic sessions.
    """
    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False
    try:
        dut.precondition(timeout=100)

        result_step, parameters = dut.step(step_1, purpose="Verify security access request seed "
                               "for supported security levels in programming session")
        if result_step:
            result_step = dut.step(step_2, parameters,
                                    purpose="Verify security access request seed for "
                                   "supported security levels in extended session")
        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
