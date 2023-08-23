"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76172
version: 0
title: ReadMemoryByAddress (23)
purpose: >
    ReadMemoryByAddress shall primarily be used during development or for validation data written
    by WriteMemoryByAddress.

description: >
    The ECU shall support the service ReadMemoryByAddress if the ECU is involved in propulsion or
    safety functions in the vehicle. Otherwise, the ECU may support the service
    ReadMemoryByAddress. If implemented, the ECU shall implement the service accordingly:

    Supported sessions:
    The ECU shall support Service ReadMemoryByAddress in:
        • defaultSession
        • extendedDiagnosticSession
    The ECU shall not support service ReadMemoryByAddress in programmingSession.

    Response time:
    Maximum response time for the service ReadMemoryByAddress (0x23) is P2Server_max.

    Effect on the ECU normal operation:
    The service ReadMemoryByAddress (0x23) shall not affect the ECU's ability to execute
    non-diagnostic tasks.

    Entry conditions:
    The ECU shall not implement entry conditions for service ReadMemoryByAddress (0x23).

    Security access:
    The ECU may protect service ReadMemoryByAddress by using the service securityAccess (0x27). At
    least shall memory areas, which are included as data parameters in a dataIdentifier, have the
    same level of security access protection as for reading with service ReadDataByIdentifier(0x22).

details: >
    Verify response of ReadMemoryByAddress(0x23) service in all diagnostic session. Also verify
    that it shall not affect the ECU's ability to execute non-diagnostic tasks.
"""

import time
import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_can import SupportCAN
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_service27 import SupportService27

SIO = SupportFileIO()
SC = SupportCAN()
SC_CARCOM = SupportCARCOM()
SE27 = SupportService27()


def create_payload(memory_params, add_range):
    """
    Create payload for ReadMemoryByAddress
    Args:
        memory_params (dict): Memory parameters
        add_range (str): Address range
    Returns:
        payload (bytes): Payload for ReadMemoryByAddress
    """
    # Address and length format identifier(add_id)
    add_id = bytes.fromhex(memory_params['add_id'])
    add_range = bytes.fromhex(add_range)
    num_bytes = bytes.fromhex(memory_params['num_bytes'])

    # Construct the message
    message = add_id+add_range+num_bytes
    payload = SC_CARCOM.can_m_send("ReadMemoryByAddress", message, b'')
    return payload


def read_memory_by_address(dut, memory_params, add_range, session):
    """
    Verify response of ReadMemoryByAddress(0x23) service in all diagnostic session
    Args:
        dut (Dut): An instance of Dut
        memory_params (dict): Memory parameters
        add_range (str): Address range
        session (str): Diagnostic session
    Returns:
        result (bool): True when received positive response for default and extended session and
                       negative response for programming session
    """
    payload = create_payload(memory_params, add_range)
    response = dut.uds.generic_ecu_call(payload)

    # Verify response
    if session == 'programming' and response.raw[0:6] == '037F23':
        logging.info("Received negative response for ReadMemoryByAddress(0x23) with NRC-%s in "
                     "programming session as expected", response.raw[6:8])
        result = True
    elif session != 'programming' and response.raw[0:6] == '100B63':
        logging.info("Received positive response for ReadMemoryByAddress(0x23) in %s session as "
                     "expected", session)
        result = True
    else:
        logging.info("Unexpected response %s received for ReadMemoryByAddress(0x23) in %s session",
                     response.raw, session)
        result = False

    return result


def verify_response_time(dut, parameters, session):
    """
    Verify response time of ReadMemoryByAddress(0x23) service
    Args:
        dut (Dut): An instance of Dut
        parameters (Dict): Time parameters
        session (str): Diagnostic session
    Returns:
        (bool): True when response is within the time limit
    """
    jitter_testenv = parameters['jitter_testenv']
    if session == 'programming':
        p2server_max = parameters['p2server_max_prog']
    else:
        p2server_max = parameters['p2server_max_non_prog']

    t_elapsed = dut.uds.milliseconds_since_request()
    t_allowed = (p2server_max + jitter_testenv)

    if t_elapsed <= t_allowed:
        logging.info("Response time %sms is within the time limit %sms, in %s session as expected",
                      t_elapsed, t_allowed, session)
        return True

    logging.error("Test Failed: Expected response time within %sms, received %sms in %s session",
                   t_allowed, t_elapsed, session)
    return False


def step_1(dut: Dut, parameters):
    """
    action: Verify ReadMemoryByAddress(0x23) service is supported in default session
    expected_result: True when positive response received within expected time
    """
    add_range = parameters['params_for_memory_read']['add_range']
    result = read_memory_by_address(dut, parameters['params_for_memory_read'], add_range,
                                    session='extended')
    return result and verify_response_time(dut, parameters['time_parameters'], session='extended')


def step_2(dut: Dut, parameters):
    """
    action: Verify ReadMemoryByAddress(0x23) service is not supported in programming session
    expected_result: True when negative response received within expected time
    """
    # Set to programming session
    dut.uds.set_mode(2)

    # Sleep time to avoid NRC37
    time.sleep(5)

    # Security access
    result = SE27.activate_security_access_fixedkey(dut, sa_keys=dut.conf.default_rig_config)
    if not result:
        logging.error("Test Failed: Security access denied in programming session")
        return False

    # Read memory
    add_range = parameters['params_for_memory_read']['add_range']
    result = read_memory_by_address(dut, parameters['params_for_memory_read'], add_range,
                                    session='programming')
    return result and verify_response_time(dut, parameters['time_parameters'],
                                           session='programming')


def step_3(dut: Dut, parameters):
    """
    action: Read Memory from different memory areas in extended session
    expected_result: True when positive response received within expected time for all memory areas
    """
    # Set ECU in extended session
    dut.uds.set_mode(1)
    dut.uds.set_mode(3)

    # Read Memory from different memory areas
    results=[]
    for add_range in parameters['params_for_memory_read']['add_ranges_list']:
        result = read_memory_by_address(dut, parameters['params_for_memory_read'], add_range,
                                        session='extended')
        result = result and verify_response_time(dut, parameters['time_parameters'],
                                                 session='extended')
        results.append(result)

    if len(results) != 0 and all(results):
        logging.info("Positive response received within expected time for all memory areas in "
                     "extended session")
        return True

    logging.error("Test Failed: positive response is not received within expected time for all "
                  "memory areas in extended session")
    return False


def step_4(dut: Dut):
    """
    action: Verify active diagnostic session
    expected_result: True when ECU is in extended session
    """
    response = dut.uds.active_diag_session_f186()
    if response.data["details"]["mode"] == 3:
        logging.info("ECU is in extended session as expected")
        return True

    logging.error("Test Failed: Expected ECU to be in extended session, but it is in mode %s",
                  response.data["details"]["mode"])
    return False


def run():
    """
    Verify response of ReadMemoryByAddress(0x23) service in all diagnostic session. Also verify
    that it shall not affect the ECU's ability to execute non-diagnostic tasks.
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'params_for_memory_read': {},
                       'time_parameters': {}}
    try:
        dut.precondition(timeout=60)

        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step = dut.step(step_1, parameters, purpose="Verify positive response for "
                                   "ReadMemoryByAddress(0x23) service in default session")
        if result_step :
            result_step = dut.step(step_2, parameters, purpose="Verify negative response for "
                                   "ReadMemoryByAddress(0x23) service in programming session")
        if result_step :
            result_step = dut.step(step_3, parameters, purpose="Verify positive response for "
                                   "ReadMemoryByAddress(0x23) service from different memory areas "
                                   "in extended session")
        if result_step :
            result_step = dut.step(step_4, purpose="Verify ECU is in extended session")
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
