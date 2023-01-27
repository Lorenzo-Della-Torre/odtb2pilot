"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76141
version: 1
title: SecurityAccess (27)
purpose: >
    Define availability of SecurityAccess service

description: >
    The ECU shall implement SecurityAccess (0x27) service accordingly:

    Supported session:
        • SecurityAccess shall not be supported in the defaultSession.
        • The services securityAccess requestSeed 0x01 and sendKey 0x02 shall only be supported
          in programmingSession, both primary and secondary bootloader.
        • The services securityAccess requestSeed in the range 0x03-0x41and sendKey in the
          range 0x04-0x42 may be supported by the ECU but only in the extendedDiagnosticSession.

    SecurityAccess algorithm:

    The requestSeed range 0x01-0x41 and corresponding sendKey range 0x02-0x42 shall use the
    standardized SecurityAccess algorithm specified by Volvo Car Corporation.The requestSeed range
    0x61-0x7E and corresponding sendKey range 0x62-0x7F are not allowed to use the standardized
    SecurityAccess algorithm specified by Volvo Car Corporation but shall use another
    SecurityAccess algorithm provided by the implementer. The number of bytes of the data parameter
    securityKey is specified by the implementer. Note that VCC tools are not required to support
    the range.

    P4Server_max response time:
    Maximum response time for the service securityAccess (0x27) is P2Server_max.

    Effect on the ECU operation:
    The service securityAccess (0x27) shall not affect the ECU's ability to execute non-diagnostic
    tasks.

    Entry conditions:
    Entry conditions for service SecurityAccess (0x27) are not allowed.

details: >
    Verify SecurityAccess(0x27) is supported in programming and extended session for security level
    (01) and security level (05,19,23,27) respectively. And verify that it is not supported in
    default session. Also verify the response time of SecurityAccess(0x27) in different session.
"""

import time
import logging
import odtb_conf
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_sec_acc import SupportSecurityAccess
from supportfunctions.support_can import SupportCAN, CanParam, CanPayload
from supportfunctions.support_file_io import SupportFileIO

SIO = SupportFileIO()
SSBL = SupportSBL()
SSA = SupportSecurityAccess()
SC = SupportCAN()


def register_non_diagnostic_signal(dut, parameters):
    """
    Register a non diagnostic signal
    Args:
        dut (Dut): An instance of Dut
        parameters (dict): signals
    Returns:
        result (bool): True when successfully register non-diagnostic signal
        num_frames (int): Number of CAN frames
        can_p_ex (dict): CAN params
    """
    can_p_ex: CanParam = {"netstub": SC.connect_to_signalbroker(odtb_conf.ODTB2_DUT,
                                                                odtb_conf.ODTB2_PORT),
                          "send": parameters['send'],
                          "receive": parameters['receive'],
                          "namespace": dut["namespace"]}

    SC.subscribe_signal(can_p_ex, timeout=15)
    time.sleep(1)

    SC.clear_all_can_messages()
    SC.clear_all_can_frames()
    SC.update_can_messages(dut)
    time.sleep(4)

    num_frames = len(SC.can_frames[can_p_ex["receive"]])
    logging.info("Number of CAN frames received: %s", num_frames)
    # Check CAN frames are more than 10
    result = (num_frames > 10)
    return result, num_frames, can_p_ex


def send_security_access_cyclically(dut):
    """
    Send request seed for multiple times to keep the ECU busy while non-diagnostic signal is being
    sent
    Args:
        dut (Dut): An instance of Dut
    Returns: None
    """
    cpay: CanPayload = {"payload": b'\x27\x05', "extra": ''}
    SIO.parameter_adopt_teststep(cpay)

    # If cyclical - send request multiple times to keep the ECU busy while non-diagnostic signal
    # is being sent.
    for _ in range(20):
        SC.t_send_signal_can_mf(dut, cpay, True, 0x00)


def verify_registered_signal(can_p_ex, num_frames, can_frame_tolerance):
    """
    Verify registered signal is still present
    Args:
        can_p_ex (dict): CAN params
        num_frames (int): Number of CAN frames
        can_frame_tolerance (int): Tolerance value for number of CAN frames
    Returns:
        result (bool): True when registered signal is present
    """
    SC.clear_all_can_frames()
    SC.update_can_messages(can_p_ex)

    time.sleep(4)
    latest_num_frames = len(SC.can_frames[can_p_ex["receive"]])
    result = ((latest_num_frames + can_frame_tolerance) > num_frames >
              (latest_num_frames - can_frame_tolerance))

    return result


def security_access(dut, sa_level):
    """
    SecurityAccess(0x27) with supported security level in all diagnostic session
    Args:
        dut (Dut): An instance of Dut
        sa_level (str): SecurityAccess(0x27) level
    Returns:
        (bool): True when SecurityAccess(0x27) successful for respective session
    """
    # Sleep time to avoid NRC-37
    time.sleep(5)

    SSA.set_keys(sa_keys=dut.conf.default_rig_config)
    SSA.set_level_key(int(sa_level, 16))

    client_req_seed = SSA.prepare_client_request_seed()
    response = dut.uds.generic_ecu_call(client_req_seed)
    time_req_seed = dut.uds.milliseconds_since_request()
    if response.raw[4:6] != '67':
        logging.error("Security access request seed failed for level %s", sa_level)
        return False, time_req_seed, None

    success = SSA.process_server_response_seed(bytearray.fromhex(response.raw[4:]))
    if success != 0:
        logging.error("Server response seed for security access is failed for level %s", sa_level)
        return False, time_req_seed, None

    sa_key_calculated = SSA.prepare_client_send_key()
    response = dut.uds.generic_ecu_call(sa_key_calculated)
    time_send_key = dut.uds.milliseconds_since_request()
    if response.raw[2:4] != '67':
        logging.error("Security access send key failed for level %s", sa_level)
        return False, time_req_seed, time_send_key

    result = (SSA.process_server_response_key(bytearray.fromhex(response.raw[6:10])) == 0)
    if result:
        logging.info("Security access successful for security level %s", sa_level)
        return True, time_req_seed, time_send_key

    logging.error("Security access failed for security level %s", sa_level)
    return False, time_req_seed, time_send_key


def verify_response_time(time_req_seed, time_send_key, parameters, session):
    """
    Verify response time for SecurityAccess(0x27)
    Args:
        time_req_seed (int): Response time for request seed
        time_send_key (int): Response time for send key
        parameters (dict): Time parameters
        session (str): Diagnostic session
    Returns:
        (bool): True when response is within the time limit
        time_req_seed (int): Response time for request seed
        time_req_seed (int): Response time for send key
        t_allowed (int): Response time allowed
    """
    jitter_testenv = parameters['jitter_testenv']
    if session == 'programming':
        p2server_max = parameters['p2server_max_prog']
    else:
        p2server_max = parameters['p2server_max_non_prog']
    if time_send_key is None:
        time_send_key = 0

    t_allowed = p2server_max + jitter_testenv

    if time_req_seed <= t_allowed and time_send_key <= t_allowed:
        return True, time_req_seed, time_send_key, t_allowed

    return False, time_req_seed, time_send_key, t_allowed


def create_response_time_dict(res_time_allowed, res_time_received, t_elapsed, t_allowed, session):
    """
    Create dictionary of response time for all diagnostic session
    Args:
        res_time_allowed (dict): Allowed response time
        res_time_received (dict): Response time received
        t_elapsed (list): Response time calculated for request seed and send key respectively
        t_allowed (int): Response time allowed
        session (str): Diagnostic session
    Returns:
        res_time_allowed (dict): Allowed response time
        res_time_received (dict): Response time received
    """
    res_time_allowed.update({session: t_allowed})
    res_time_received.update({session: t_elapsed})
    return res_time_allowed, res_time_received


def step_1(dut: Dut, parameters):
    """
    action: Verify SecurityAccess(0x27) doesn't affect the ECU's ability to execute
            non-diagnostic tasks
    expected_result: SecurityAccess(0x27) should not affect on non-diagnostic task
    """
    # Set to extended session
    dut.uds.set_mode(3)

    result, num_frames, can_p_ex = register_non_diagnostic_signal(dut, parameters)
    if not result:
        logging.error("Test Failed: Unable to register non-diagnostic signal")
        return False

    # Send SecurityAccess(0x27) signal cyclically to keep the ECU busy while non-diagnostic signal
    # is being sent
    send_security_access_cyclically(dut)

    # Verify signal is still present after cyclically send SecurityAccess(0x27) signal
    result = result and verify_registered_signal(can_p_ex, num_frames,
                                                 parameters['can_frame_tolerance'])
    if not result:
        logging.error("Test Failed: Unable to verify registered signal")
        return False

    logging.info("Successfully verified SecurityAccess(0x27) service has no effect on "
                 "non-diagnostic tasks")
    return True


def step_2(dut: Dut, parameters):
    """
    action: Verify SecurityAccess(0x27) with supported security level(05,19,23,27) in extended
            session and also verify response time
    expected_result: SecurityAccess(0x27) should be successful with proper response time for all
                     security levels
    """
    result_list = []
    res_time_allowed = {}
    res_time_received = {}
    res_time = []

    for sa_level in parameters['sa_level_extended_session']:
        sa_result, time_req_seed, time_send_key = security_access(dut, sa_level)
        res_time_result, time_req_seed, time_send_key, t_allowed = verify_response_time(
                                                time_req_seed, time_send_key,
                                                parameters['time_parameters'], session='extended')
        res_time.append((time_req_seed, time_send_key))
        result = sa_result and res_time_result
        result_list.append(result)

    res_time_allowed, res_time_received = create_response_time_dict(res_time_allowed,
                                          res_time_received, res_time, t_allowed,
                                          session='extended')

    if len(result_list) != 0 and all(result_list):
        logging.info("Security access successful for all security level with proper response time "
                     "in extended session")
        return True, res_time_allowed, res_time_received

    logging.error("Test Failed: Security access is not successful or response time is not proper "
                  "in extended session")
    return False, res_time_allowed, res_time_received


def step_3(dut: Dut, parameters, res_time_allowed, res_time_received):
    """
    action: Verify SecurityAccess(0x27) with security level(01) in default session and also
            verify response time
    expected_result: SecurityAccess(0x27) should be denied in default session and response time
                     within the time limit
    """
    # Set to default session
    dut.uds.set_mode(1)
    res_time = []

    sa_result, time_req_seed, time_send_key = security_access(dut, sa_level='01')
    if not sa_result:
        logging.info("Security access denied in default session as expected")
        sa_result = True
    else:
        logging.error("Test Failed: Security access successful in default session")
        sa_result = False

    res_time_result, time_req_seed, time_send_key, t_allowed = verify_response_time(time_req_seed,
                                                                 time_send_key,
                                                                 parameters['time_parameters'],
                                                                 session='default')

    res_time.append((time_req_seed, time_send_key))

    res_time_allowed, res_time_received = create_response_time_dict(res_time_allowed,
                                                                    res_time_received, res_time,
                                                                    t_allowed, session='default')

    result = sa_result and res_time_result
    if result:
        logging.info("Response time is within the allowed time limit in default session")
        return True, res_time_allowed, res_time_received

    logging.error("Test Failed: Response time is not within the allowed time limit in "
                  "default session")
    return False, res_time_allowed, res_time_received


def step_4(dut: Dut, parameters, res_time_allowed, res_time_received):
    """
    action: Verify SecurityAccess(0x27) with security level(01) in programming session and also
            verify response time
    expected_result: SecurityAccess(0x27) should be successful with proper response time
    """
    # Set to programming session
    dut.uds.set_mode(2)
    res_time = []

    sa_result, time_req_seed, time_send_key = security_access(dut, sa_level='01')
    res_time_result, time_req_seed, time_send_key, t_allowed = verify_response_time(time_req_seed,
                                                                 time_send_key,
                                                                 parameters['time_parameters'],
                                                                 session='programming')

    res_time.append((time_req_seed, time_send_key))

    res_time_allowed, res_time_received = create_response_time_dict(res_time_allowed,
                                                                  res_time_received, res_time,
                                                                  t_allowed, session='programming')

    result = sa_result and res_time_result
    if result:
        logging.info("Allowed response time(ms) in respective session: %s, received "
                     "response time for request seed(ms) and response time for send key(ms) in "
                     "different security levels: %s", res_time_allowed, res_time_received)
        return True

    logging.error("Test Failed: Allowed response time(ms) in respective session: %s, but received "
                  "response time for request seed(ms) and response time for send key(ms) in "
                  "different security levels: %s", res_time_allowed, res_time_received)
    return False


def step_5(dut: Dut):
    """
    action: Download and activate SBL
    expected_result: SBL download and activation should be successful
    """
    # ECU hard reset
    dut.uds.ecu_reset_1101()

    # Load VBF files
    vbf_result = SSBL.get_vbf_files()
    if not vbf_result:
        logging.error("Test Failed: Unable to load VBF files")
        return False

    # Download and activate SBL
    sbl_result = SSBL.sbl_dl_activation(dut, sa_keys=dut.conf.default_rig_config)
    if not sbl_result:
        logging.error("Test Failed: SBL activation failed")
        return False

    logging.info("SBL activation successful")
    return True


def run():
    """
    Verify SecurityAccess(0x27) is supported in programming and extended session for security level
    (01) and security level (05,19,23,27) respectively. And verify that it is not supported in
    default session. Also verify the response time of SecurityAccess(0x27) in different session.
    """
    dut = Dut()

    start_time = dut.start()

    parameters_dict = {'receive': '',
                       'send': '',
                       'sa_level_extended_session': [],
                       'time_parameters': {},
                       'can_frame_tolerance': 0}
    try:
        dut.precondition(timeout=150)

        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result = dut.step(step_1, parameters, purpose="Verify SecurityAccess(0x27) "
                          "don't affect the ECU's ability to execute non-diagnostic tasks")

        result_step, res_time_allowed, res_time_received = dut.step(step_2, parameters,
                                        purpose="Verify SecurityAccess(0x27) with supported "
                                                "security level(05,19,23,27) in extended session")
        result = result_step and result

        result_step, res_time_allowed, res_time_received = dut.step(step_3, parameters,
                                        res_time_allowed, res_time_received, purpose="Verify "
                                        "SecurityAccess(0x27) with security level(01) in default "
                                        "session")
        result = result_step and result

        result_step = dut.step(step_4, parameters, res_time_allowed, res_time_received,
                               purpose="verify SecurityAccess(0x27) with security level(01) in "
                                       "programming session")
        result = result_step and result

        result_step = dut.step(step_5, purpose="Download and activate SBL")

        result = result_step and result

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
