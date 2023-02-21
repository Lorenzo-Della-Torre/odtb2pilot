"""

/*********************************************************************************/



Copyright © 2023 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76169
version: 2
title: TesterPresent (3E) - zeroSubFunction (00, 80)
purpose: >
    Keep ECUs in a desired session for a longer period of time.  Although TesterPresent is not
    necessary for keeping an ECU in defaultSession, all ECUs shall support TesterPresent in
    default session since the response of the TesterPresent can be used as an indication of an
    operational ECU.

description: >
    The ECU must support the service testerPresent. The ECU shall implement the service
    accordingly:

    Supported session:
        The ECU shall support Service testerPresent in:
        •   defaultSession
        •   extendedDiagnosticSession
        •   programmingSession, both primary and secondary bootloader

    Response time:
        Maximum response time for the service testerPresent (0x3E) is P2Server_max.

    Effect on ECU normal operation:
        The service testerPresent (0x3E) shall not affect the ECU's ability to execute
        non-diagnostic tasks.

    Entry conditions:
        The ECU shall not implement entry conditions for service TesterPresent (0x3E).

    Security access:
        The ECU shall not protect service TesterPresent by using the service securityAccess (0x27).

details: >
    Verify ECU supports service testerPresent(0x3E) in default, extended, PBL and SBL session.
"""

import time
import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_SBL import SupportSBL

SSBL = SupportSBL()


def verify_active_diagnostic_session(dut, ecu_session):
    """
    Request to check active diagnostic session
    Args:
        dut (Dut): An instance of Dut
        ecu_session (int): Diagnostic session
    Return:
        (bool): True when ECU is in expected session
    """
    result = dut.uds.active_diag_session_f186()

    if result.data["details"]["mode"] == ecu_session :
        logging.info("ECU is in mode %s as expected", ecu_session)
        return True

    logging.error("Test Failed: Expected session %s, received session %s",
                   ecu_session, result.data["details"]["mode"])
    return False


def verify_3e_service_response(dut, p2_server_max):
    """
    Verify maximum response time
    Args:
        dut (Dut): An instance of Dut
        p2_server_max (int): Maximum response time
    Return:
        (bool): True when ECU is in default session
    """
    dut.SE3e.tester_present_zero_subfunction(dut)
    time_elapsed = dut.uds.milliseconds_since_request()
    response = dut.SC.can_messages[dut["receive"]][0][2]
    if response[2:4] == '7E':
        logging.info("Received positive rsponse %s for request TesterPresernt(3E) service",
                      response)
        # P2Server_max is 50ms in default and extended session and 25ms in programming session
        if time_elapsed >= p2_server_max:
            logging.error("Test Failed: Elapsed time %sms is greater than p2Server_max %sms",
                           time_elapsed, p2_server_max)
            return False

        logging.info("Elapsed time %sms is less than p2Server_max %sms as expected",
                     time_elapsed, p2_server_max)
        return True

    logging.error("Test Failed: Expected positive response '7E' for request TesterPresernt(3E) "
                  "service, received %s", response)
    return False


def activate_sbl(dut):
    """
    Activate SBL and verify ECU is in SBL
    Args:
        dut (Dut): An instance of Dut
    Return:
        (bool): True when ECU is in SBL
    """
    SSBL.get_vbf_files()
    result = SSBL.sbl_activation(dut, sa_keys=dut.conf.default_rig_config)
    if not result:
        logging.error("Test Failed: SBL activation failed")
        return False

    result = dut.SE22.verify_sbl_session(dut)
    if not result:
        logging.error("Test Failed: ECU is not in SBL")
        return False

    return True


def step_1(dut: Dut, parameters):
    """
    action: Verify ECU stays in default session as no testerPresent is sent and also verify
            response of 3E service in default session
    expected_result: ECU should stay in default session and send positive response '7E' within
                     p2server max time
    """
    # Set to default session
    dut.uds.set_mode(1)

    # Verify ECU is in default session
    result = verify_active_diagnostic_session(dut, ecu_session=1)
    if not result:
        return False

    # Wait longer than timeout
    time.sleep(6)

    # Verify that ECU is still in default session after timeout due to testerPresent sent
    result = verify_active_diagnostic_session(dut, ecu_session=1)
    if not result:
        return False

    # Stop sending tester present
    dut.SE3e.stop_periodic_tp_zero_suppress_prmib()

    result = verify_3e_service_response(dut,
                                        p2_server_max=parameters['p2_server_max_non_programming'])
    if not result:
        return False

    # Wait longer than timeout for fallback while not sending testerPresent
    time.sleep(6)

    # Verify ECU stays in default as no testerPresent sent
    result = verify_active_diagnostic_session(dut, ecu_session=1)
    if not result:
        return False

    # Start sending TesterPresent
    dut.SE3e.start_periodic_tp_zero_suppress_prmib(dut, can_id=dut.conf.rig.signal_tester_present)
    return True


def step_2(dut: Dut, parameters):
    """
    action: Verify ECU fallback to default session as no testerPresent sent also verify response
            of 3E service in extended session
    expected_result: ECU should fallback to default session and send positive response '7E' within
                     p2server max time
    """
    # Set to extended session
    dut.uds.set_mode(3)

    # Verify ECU is in extended session
    result = verify_active_diagnostic_session(dut, ecu_session=3)
    if not result:
        return False

    # Wait longer than timeout for fallback while sending testerPresent
    time.sleep(6)

    # Verify that ECU is still in extended session after timeout due to testerPresent sent
    result = verify_active_diagnostic_session(dut, ecu_session=3)
    if not result:
        return False

    # Stop sending tester present
    dut.SE3e.stop_periodic_tp_zero_suppress_prmib()

    result = verify_3e_service_response(dut,
                                        p2_server_max=parameters['p2_server_max_non_programming'])
    if not result:
        return False

    # Wait longer than timeout for fallback while not sending testerPresent
    time.sleep(6)

    # Verify ECU fallback to default as no testerPresent sent
    result = verify_active_diagnostic_session(dut, ecu_session=1)
    if not result:
        return False

    # Start sending TesterPresent
    dut.SE3e.start_periodic_tp_zero_suppress_prmib(dut, can_id=dut.conf.rig.signal_tester_present)
    return True


def step_3(dut: Dut, parameters):
    """
    action: Verify ECU fallback to default session as no testerPresent sent also verify response
            of 3E service in PBL session
    expected_result: ECU should fallback to default session and send positive response '7E' within
                     p2server max time
    """
    # Set to programming session
    dut.uds.set_mode(2)

    # Verify PBL session
    pbl_result = dut.SE22.verify_pbl_session(dut)
    if not pbl_result:
        logging.error("Test Failed : ECU is not in PBL session")
        return False

    # Wait longer than timeout for fallback while sending testerPresent
    time.sleep(6)

    # Verify that ECU is still in PBL session after timeout due to testerPresent sent
    pbl_result = dut.SE22.verify_pbl_session(dut)
    if not pbl_result:
        logging.error("Test Failed : ECU is not in PBL session")
        return False

    # Stop sending tester present
    dut.SE3e.stop_periodic_tp_zero_suppress_prmib()

    result = verify_3e_service_response(dut, p2_server_max=parameters['p2_server_max_programming'])
    if not result:
        return False

    # Wait longer than timeout for fallback while not sending testerPresent
    time.sleep(6)

    # Verify ECU fallback to default as no testerPresent sent
    result = verify_active_diagnostic_session(dut, ecu_session=1)
    if not result:
        return False

    # Start sending TesterPresent
    dut.SE3e.start_periodic_tp_zero_suppress_prmib(dut, can_id=dut.conf.rig.signal_tester_present)
    return True


def step_4(dut: Dut, p2_server_max_programming):
    """
    action: Verify ECU fallback to default session as no testerPresent sent also verify response
            of 3E service in SBL session
    expected_result: ECU should fallback to default session send positive response '7E' within
                     p2server max time
    """
    result = activate_sbl(dut)
    if not result:
        return False

    # Wait longer than timeout for fallback while sending testerPresent
    time.sleep(6)

    # Verify that ECU is still in SBL after timeout due to testerPresent sent
    sbl_result = dut.SE22.verify_sbl_session(dut)
    if not sbl_result:
        logging.error("Test Failed: ECU is not in SBL session")
        return False

    # Stop sending tester present
    dut.SE3e.stop_periodic_tp_zero_suppress_prmib()

    result = verify_3e_service_response(dut, p2_server_max=p2_server_max_programming)
    if not result:
        return False

    # Wait longer than timeout for fallback while not sending testerPresent
    time.sleep(6)

    # Verify ECU fallback to default as no testerPresent sent
    result = verify_active_diagnostic_session(dut, ecu_session=1)
    if not result:
        return False

    return True


def run():
    """
    Verify ECU supports service testerPresent(0x3E) in default, extended, PBL and SBL session
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'p2_server_max_programming' : 0,
                       'p2_server_max_non_programming' : 0}

    try:
        dut.precondition(timeout=180)

        parameters = dut.SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step = dut.step(step_1, parameters, purpose="Verify ECU stays in default session "
                               "as no testerPresent is sent and also verify response of 3E "
                               "service in default session")
        if result_step:
            result_step = dut.step(step_2, parameters, purpose="Verify ECU fallback to default "
                                   "session as no testerPresent sent also verify response "
                                   "of 3E service in extended session")
        if result_step:
            result_step = dut.step(step_3, parameters, purpose="Verify ECU fallback to default "
                                   "session as no testerPresent sent also verify response of 3E "
                                   "service in PBL session")
        if result_step:
            result_step = dut.step(step_4, parameters['p2_server_max_programming'], purpose=
                                   "Verify ECU fallback to default session as no testerPresent "
                                   "sent also verify response of 3E service in SBL session")
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
