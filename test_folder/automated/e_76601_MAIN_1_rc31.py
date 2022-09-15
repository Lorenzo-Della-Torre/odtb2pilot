"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76601
version: 1
title: : RoutineControl(31)
purpose: >
    To be able to execute specific functionality in the ECU

description: >
    The ECU shall support the service RoutineControl. The ECU shall implement the service
    accordingly:

    Supported sessions:
    The ECU shall support Service RoutineControl of Routine type 1 - Short routine in:
        •	defaultSession
        •	extendedDiagnosticSession
        •	programmingSession, both primary and secondary bootloader

    The ECU shall support Service RoutineControl of Routine type 2 - Long routine and
    Routine type 3 - Continuous routine in:
        •	extendedDiagnosticSession
        •	programmingSession, both primary and secondary bootloader

    The ECU shall not support Service RoutineControl of Routine type 2 - Long routine and Routine
    type 3 - Continuous routine in defaultSession.

    Response time:
    These are general response timing requirements. Any exceptions from these requirements are
    specified in the requirements for specific control routines.
    Maximum response time for the service RoutineControl (0x31) startRoutine (1),
    Routine type = 1 is 5000ms.
    Maximum response time for the service RoutineControl (0x31) except for startRoutine (1),
    Routine type = 1 is 200 ms.

    Effect on the ECU normal operation:
    The service RoutineControl (0x31) is allowed to affect the ECU's ability to execute
    non-diagnostic tasks. The service is only allowed to affect execution of the non-diagnostic
    tasks during the execution of the diagnostic service. After the diagnostic service is completed
    any effect on the non-diagnostic tasks is not allowed anymore (normal operational functionality
    resumes). The service shall not reset the ECU.

    Entry conditions:
    Entry conditions for service RoutineControl (0x31) are allowed only if approved by Volvo Car
    Corporation.
    If the ECU implement safety requirements with an ASIL higher than QM it shall, in all
    situations when diagnostic services may violate any of those safety requirements, reject the
    critical diagnostic service requests. Note that if the ECU rejects such critical diagnostic
    service requests,this requires an approval by Volvo Car Corporation.

    Security access:
    The ECU may protect the service RoutineControl (0x31) by using the service securityAccess
    (0x27) in other sessions than programmingSession but only if Volvo Car Corporation requires
    or approves it. The ECU is required to protect service RoutineControl (0x31) by service
    securityAccess (0x27) in programmingSession.

details:
    Verify RoutineControl(31) request response for different types in default, programming
    and extended diagnostic session
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_can import SupportCAN

SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
SE22 = SupportService22()
SC = SupportCAN()


def routine_control_request(dut: Dut, routine_id):
    """
    Request RoutineControl(0x31) and return the ECU response
    Args:
        dut (Dut): dut instance
        routine_id(byte): Routine identifier
    Returns:
        response(str): ECU response
    """
    payload = SC_CARCOM.can_m_send("RoutineControlRequestSID", routine_id, b'\x01')
    response = dut.uds.generic_ecu_call(payload)
    return response.raw


def step_1(dut: Dut):
    """
    action: Verify RoutineControl(31) request is sent for type1(0x0206) in default session
    expected_result: True when received positive response
    """
    response = routine_control_request(dut, routine_id=b'\x02\x06')
    result = SUTE.pp_decode_routine_control_response(response, 'Type1,Completed')

    if result:
        logging.info("Received routine identifier response 'Type1,Completed' as expected")
        return True

    logging.error("Test Failed: Routine identifier response 'Type1,Completed' not received")
    return False


def step_2(dut: Dut):
    """
    action: Verify RoutineControl(31) request is not applicable for type2(0x4050) in default session
    expected_result: True on receiving negative response
    """
    response = routine_control_request(dut, routine_id=b'\x40\x50')
    result = SUTE.test_message(SC.can_messages[dut["receive"]], teststring='7F3131')

    if result:
        logging.info("Received NRC 31 for routine identifier as expected")
        return True

    logging.error("Test Failed: Expected NRC 31 for routine identifier, received %s", response)
    return False


def step_3(dut: Dut):
    """
    action: Verify RoutineControl(31) request is not applicable for type3(0x4000) in default session
    expected_result: True on receiving negative response
    """
    response = routine_control_request(dut, routine_id=b'\x40\x00')
    result = SUTE.test_message(SC.can_messages[dut["receive"]], teststring='7F3131')

    if result:
        logging.info("Received NRC 31 for routine identifier as expected")
        return True

    logging.error("Test Failed: Expected NRC 31 for routine identifier, received %s", response)
    return False


def step_4(dut: Dut):
    """
    action: Verify RoutineControl(31) request is sent for type1(0x0206) in extended session
    expected_result: True on receiving positive response
    """
    # Set to extended session
    dut.uds.set_mode(3)

    response = routine_control_request(dut, routine_id=b'\x02\x06')
    result = SUTE.pp_decode_routine_control_response(response, 'Type1,Completed')

    if not result:
        logging.error("Test Failed: Routine identifier response 'Type1,Completed' not received")
        return False

    # Check active diagnostic session
    active_session = SE22.read_did_f186(dut, b'\x03')
    if active_session:
        logging.info("ECU is in extended session")
        # Set to default session
        dut.uds.set_mode(1)
        return True

    logging.error("ECU is not in extended session")
    return False


def step_5(dut: Dut):
    """
    action: Verify RoutineControl(31) request is not applicable for type2(0x0301) in programming
            session
    expected_result: True on receiving negative response
    """
    # Set to programming session
    dut.uds.set_mode(2)

    response = routine_control_request(dut, routine_id=b'\x03\x01')
    result = SUTE.test_message(SC.can_messages[dut["receive"]], teststring='7F3133')
    if not result:
        logging.error("Test Failed: Expected NRC 33 for routine identifier, received %s", response)
        return False

    # Check active diagnostic session
    active_session = SE22.read_did_f186(dut, b'\x02')
    if active_session:
        logging.info("ECU is in programming session")
        # Set to default session
        dut.uds.set_mode(1)
        return True

    logging.error("ECU is not in programming session")
    return False


def run():
    """
    Verify ECU response of RoutineControl(31) request in default, programming and extended session
    """
    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False
    try:
        dut.precondition(timeout=60)

        result_step = dut.step(step_1, purpose="Verify RoutineControlRequest with positive "
                                               "response 'Type1,Completed' for type 1 in default "
                                               "session")
        if result_step:
            result_step = dut.step(step_2, purpose="Verify RoutineControlRequest with NRC 31 "
                                                   "for type 2 in default session")
        if result_step:
            result_step = dut.step(step_3, purpose="Verify RoutineControlRequest with NRC 31 "
                                                   "for type 3 in default session")
        if result_step:
            result_step = dut.step(step_4, purpose="Verify RoutineControlRequest with positive "
                                                   "response 'Type1,Completed' for type 1 in "
                                                   "extended session")
        if result_step:
            result_step = dut.step(step_5, purpose="Verify RoutineControlRequest with NRC 33 "
                                                    "for type 2 in programming session")

        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
