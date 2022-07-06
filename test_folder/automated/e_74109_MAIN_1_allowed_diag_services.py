"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 74109
version: 1
title: Allowed diagnostic services
purpose: >
    Define which diagnostic services to allow. Ensures all suppliers uses the same diagnostic
    services as well as preventing supplier from using not allowed diagnostic services.

description: >
    The ECU shall only support the diagnostic services specified in the requirement sections from
    Volvo Car Corporation.

details: >
    Verify negetive response for services which are not present in services in sddb, in default
    session, PBL and SBL
"""

import logging
import hilding.flash as swdl
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_file_io import SupportFileIO

SIO = SupportFileIO()


def verify_response_time(dut, p2server_max, jitter_testenv):
    """
    Verify response time is within the time limit
    Args:
        dut (Dut): Dut instance
        p2server_max (float): P2server_max time
        jitter_testenv (float): Test environment jitter time
    Returns:
        (bool): True when response recieved within the defined limit
    """
    t_elapsed = dut.uds.milliseconds_since_request()
    t_allowed = (p2server_max+jitter_testenv)*1000

    if t_elapsed <= t_allowed:
        return True
    logging.error("Response time %s is greater than allowed time %s ", round(t_allowed, 2),
                   round(t_elapsed, 2))
    return False


def verify_diagnostic_services(dut, sddb_services, p2server_max, jitter_testenv):
    """
    Verify negetive response for services which are not present in services in sddb, in default
    session/pbl/sbl
    Args:
        dut (Dut): Dut instance
        sddb_services (dict): Sddb services
        p2server_max (float): P2server_max time
        jitter_testenv (float): Test environment jitter time
    Returns:
        (bool): True when negetive response for services not present in sddb
    """
    payload = b'\x00'
    result_list = []

    # Valid service byte range is (0-256). And 0x40 added with service id in can_receive(). So
    # service id hex range(0x00 to 0xC0) will be validated.
    for service_id in range(0xC0):
        service = f'{service_id:X}'
        result = True

        if service not in sddb_services:
            service = service_id.to_bytes((service_id.bit_length() + 7) // 8 or 1, 'big')
            payload = service + bytes.fromhex('0000')

            response = dut.uds.generic_ecu_call(payload)
            response_result = verify_response_time(dut, p2server_max, jitter_testenv)

            # Verify negetive response and response time for services not in sddb
            if response.raw[2:4] != '7F' and not response_result:
                logging.error("Expected negetive response for "
                               "service %s but recieved %s", service, response.raw)
                result = False
        else:
            logging.info("Service %s is defined in sddb", service)

        result_list.append(result)

    if all(result_list) and len(result_list) > 0:
        return True
    return False


def step_1(dut, services_app, parameters):
    """
    action: Verify negative response of application services are not preset in sddb in defaul
            session
    expected_result: True when recieved negative response for sddb application services are not
                     present
    """
    # Test environment jitter estimated at 30ms.
    jitter_testenv = parameters["jitter_testenv"]
    # P2Server_max is 50ms in default
    p2server_max = parameters["p2server_max_default"]

    result = verify_diagnostic_services(dut, services_app, p2server_max, jitter_testenv)
    if result:
        logging.info("Recieved negetive response of application services are not present in sddb "
                     "as expected")
        return True
    logging.error("Test Failed: Unexpected response recieved for some of services in default "
                  "session")
    return False


def step_2(dut, services_pbl, parameters):
    """
    action: Verify negative response of pbl services are not preset in sddb
    expected_result: True when recieved negative response for pbl services are not present in sddb
    """
    jitter_testenv = parameters["jitter_testenv"]
    p2server_max = parameters["p2server_max_programming"]

    # Set ECU in programming session
    dut.uds.set_mode(2)

    result = verify_diagnostic_services(dut, services_pbl, p2server_max, jitter_testenv)
    if result:
        logging.info("Recieved negetive response of pbl services are not present in sddb "
                     "as expected")
        return True
    logging.error("Test Failed: Unexpected response recieved for some services in PBL")
    return False


def step_3(dut, services_sbl, parameters):
    """
    action: Verify negative response of sbl services are not preset in sddb
    expected_result: True when recieved negative response for pbl services are not present in sddb
    """
    vbf_result = swdl.load_vbf_files(dut)
    if not vbf_result:
        return False
    # SBL activation
    sbl_result = swdl.activate_sbl(dut)
    if not sbl_result:
        logging.error("Test Failed: SBL activation failed")
        return False

    jitter_testenv = parameters["jitter_testenv"]
    p2server_max = parameters["p2server_max_programming"]

    result = verify_diagnostic_services(dut, services_sbl, p2server_max, jitter_testenv)
    if result:
        logging.info("Recieved negetive response of sbl services are not present in sddb "
                     "as expected")
        return True
    logging.error("Test Failed: Unexpected response recieved for some services in SBL")
    return False


def run():
    """
    Verify negetive response for services which are not present in services in sddb, in default
    session, PBL and SBL
    """
    dut = Dut()

    services = dut.conf.rig.sddb_services

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {"p2server_max_programming": 0.0,
                       "p2server_max_default": 0.0,
                       "jitter_testenv": 0.0}

    try:
        dut.precondition(timeout=1000)

        parameters = SIO.parameter_adopt_teststep(parameters_dict)

        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step = dut.step(step_1, services["app"], parameters, purpose="Verify negative "
                               "response of application services are not preset in sddb in default"
                               "session")
        if result_step:
            result_step = dut.step(step_2, services["pbl"], parameters, purpose="Verify negative "
                                   "response of pbl services are not preset in sddb")
        if result_step:
            result_step = dut.step(step_3, services["sbl"], parameters, purpose="Verify negative "
                                   "response of sbl services are not preset in sddb")

        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
