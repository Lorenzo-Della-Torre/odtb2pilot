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
version: 2
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
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_can import SupportCAN
from supportfunctions.support_file_io import SupportFileIO

SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
SE22 = SupportService22()
SE27 = SupportService27()
SC = SupportCAN()
SIO = SupportFileIO()


def request_routine_control_31(dut: Dut, routine_id):
    """
    Request RoutineControl(0x31)
    Args:
        dut(Dut): dut instance
        routine_id(bytes): Routine identifier
    Returns:
        response.raw(str): ECU response
    """
    response = dut.uds.generic_ecu_call(SC_CARCOM.can_m_send("RoutineControlRequestSID",
                                                              routine_id, b'\x01'))
    return response.raw


def validate_positive_response(response, session, routine_type):
    """
    Validate positive response of request RoutineControl(0x31)
    Args:
        response(str): ECU response
        session(str): Diagnsotic session
        routine_type(str): Routine types
    Returns:
        (bool): True when received positive response
    """
    result = SUTE.pp_decode_routine_control_response(response, routine_type)
    if result:
        logging.info("Received routine identifier response %s in %s session as expected",
                      routine_type, session)
        return True

    logging.error("Test Failed: Routine identifier response %s not received in %s session",
                   routine_type, session)
    return False


def validate_negative_response(dut: Dut, response):
    """
    Validate negative response of request RoutineControl(0x31)
    Args:
        dut(Dut): dut instance
        response(str): ECU response
    Returns:
        (bool): True when received negative response
    """
    result = SUTE.test_message(SC.can_messages[dut["receive"]], teststring='7F3131')
    if result:
        logging.info("Received NRC-31(requestOutOfRange) for routine identifier in default "
                     "session as expected")
        return True

    logging.error("Test Failed: Expected NRC-31(requestOutOfRange) for routine identifier in "
                  "default session, received %s", response)
    return False


def validate_response_time(elapsed_time, max_response_time):
    """
    Validate response time of request RoutineControl(0x31)
    Args:
        elapsed_time(int): Elapsed time of ECU request
        response_time(int): Maximum response time for routine types
    Returns:
        (bool): True when elapsed time is less than or equal to maximum response time
    """
    if elapsed_time <= max_response_time:
        logging.info("Response time %sms is less than or eqaul to %sms as expected",
                      elapsed_time, max_response_time)
        return True

    logging.error("Test Failed: Response time %sms is greater than %sms which is not expected",
                    elapsed_time, max_response_time)
    return False


def step_1(dut: Dut, max_response_time):
    """
    action: Verify RoutineControl(31) request is sent for type1(0x0206) in default session
    expected_result: True when received positive response and elapsed time is less than or
                     equal to maximum response time
    """
    response = request_routine_control_31(dut, routine_id=b'\x02\x06')

    # Calculate response time in milliseconds
    elapsed_time = dut.uds.milliseconds_since_request()

    result = validate_positive_response(response, session='default',
                                        routine_type='Type1,Completed')
    if result:
        return validate_response_time(elapsed_time, max_response_time)

    return False


def step_2(dut: Dut):
    """
    action: Verify RoutineControl(31) request is not applicable for type2(0x4050) in
            default session
    expected_result: True when received negative response
    """
    response = request_routine_control_31(dut, routine_id=b'\x40\x50')

    return validate_negative_response(dut, response)


def step_3(dut: Dut):
    """
    action: Verify RoutineControl(31) request is not applicable for type3(0x4000) in
            default session
    expected_result: True when received negative response
    """
    response = request_routine_control_31(dut, routine_id=b'\x40\x00')

    return validate_negative_response(dut, response)


def step_4(dut: Dut, max_response_time):
    """
    action: Verify RoutineControl(31) request is sent for type1(0x0206) in extended session
    expected_result: True when received positive response and elapsed time is less than or
                     equal to maximum response time
    """
    # Set to extended session
    dut.uds.set_mode(3)

    response = request_routine_control_31(dut, routine_id=b'\x02\x06')

    # Calculate response time in milliseconds
    elapsed_time = dut.uds.milliseconds_since_request()

    result = validate_positive_response(response, session='extended',
                                        routine_type='Type1,Completed')
    if not result:
        return False

    resp_time_result = validate_response_time(elapsed_time, max_response_time)
    if resp_time_result:
        # Check active diagnostic session
        active_session = SE22.read_did_f186(dut, b'\x03')
        if active_session:
            logging.info("ECU is in extended session as expected")
            return True

        logging.error("Test Failed: ECU is not in extended session")
        return False

    return False


def step_5(dut: Dut, max_response_time):
    """
    action: Verify RoutineControl(31) request is sent for type2(0x4050) in extended session
    expected_result: True when received positive response and elapsed time is less than or
                     equal to maximum response time
    """
    response = request_routine_control_31(dut, routine_id=b'\x40\x50')

    # Calculate response time in milliseconds
    elapsed_time = dut.uds.milliseconds_since_request()

    result = validate_positive_response(response, session='extended',
                                        routine_type='Type2,Completed')
    if result:
        return validate_response_time(elapsed_time, max_response_time)

    return False


def step_6(dut: Dut, max_response_time):
    """
    action: Verify RoutineControl(31) request is sent for type3(0x4000) in extended session
    expected_result: True when received positive response and elapsed time is less than or
                     equal to maximum response time
    """
    response = request_routine_control_31(dut, routine_id=b'\x40\x00')

    # Calculate response time in milliseconds
    elapsed_time = dut.uds.milliseconds_since_request()

    result = validate_positive_response(response, session='extended',
                                        routine_type='Type3,Completed')
    if result:
        return validate_response_time(elapsed_time, max_response_time)

    return False


def step_7(dut: Dut, max_response_time):
    """
    action: Verify RoutineControl(31) request is sent for type1(0x0206) in programming session
    expected_result: True when received positive response and elapsed time is less than or
                     equal to maximum response time
    """
    # Set to programming session
    dut.uds.set_mode(2)

    # Security access to ECU in programming session
    sa_result = SE27.activate_security_access_fixedkey(dut, sa_keys=dut.conf.default_rig_config,
                                                            step_no=272, purpose="SecurityAccess")
    if not sa_result:
        logging.error("Test Failed: Security access denied in programming session")
        return False

    response = request_routine_control_31(dut, routine_id=b'\x02\x06')

    # Calculate response time in milliseconds
    elapsed_time = dut.uds.milliseconds_since_request()

    result = validate_positive_response(response, session='programming',
                                        routine_type='Type1,Completed')
    if not result:
        return False

    resp_time_result = validate_response_time(elapsed_time, max_response_time)
    if resp_time_result:
        # Check active diagnostic session
        active_session = SE22.read_did_f186(dut, b'\x02')
        if active_session:
            logging.info("ECU is in programming session as expected")
            return True

        logging.error("Test Failed: ECU is not in programming session")
        return False

    return False


def step_8(dut: Dut, max_response_time):
    """
    action: Verify RoutineControl(31) request is sent for type2(0x4050) in programming session
    expected_result: True when received positive response and elapsed time is less than or
                     equal to maximum response time
    """
    response = request_routine_control_31(dut, routine_id=b'\x40\x50')

    # Calculate response time in milliseconds
    elapsed_time = dut.uds.milliseconds_since_request()

    result = validate_positive_response(response, session='programming',
                                        routine_type='Type2,Completed')
    if result:
        return validate_response_time(elapsed_time, max_response_time)

    return False


def step_9(dut: Dut, max_response_time):
    """
    action: Verify RoutineControl(31) request is sent for type3(0x4000) in programming session
    expected_result: True when received positive response and elapsed time is less than or
                     equal to maximum response time
    """
    response = request_routine_control_31(dut, routine_id=b'\x40\x00')

    # Calculate response time in milliseconds
    elapsed_time = dut.uds.milliseconds_since_request()

    result = validate_positive_response(response, session='programming',
                                        routine_type='Type3,Completed')
    if result:
        return validate_response_time(elapsed_time, max_response_time)

    return False


def run():
    """
    Verify ECU response of RoutineControl(31) request in default, programming and extended session
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'resp_time_type1': 0,
                       'resp_time_type2_type3': 0}
    try:
        dut.precondition(timeout=60)
        parameters = SIO.parameter_adopt_teststep(parameters_dict)

        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step = dut.step(step_1, parameters['resp_time_type1'], purpose="Verify "
                              "RoutineControl(31) request is sent for type1(0x0206) in "
                              "default session")
        if result_step:
            result_step = dut.step(step_2, purpose="Verify RoutineControl(31) request is "
                                  "not applicable for type2(0x4050) in default session")
        if result_step:
            result_step = dut.step(step_3, purpose="Verify RoutineControl(31) request is "
                                  "not applicable for type3(0x4000) in default session")
        if result_step:
            result_step = dut.step(step_4, parameters['resp_time_type1'], purpose="Verify "
                                  "RoutineControl(31) request is sent for type1(0x0206) in "
                                  "extended session")
        if result_step:
            result_step = dut.step(step_5, parameters['resp_time_type2_type3'], purpose="Verify "
                                  "RoutineControl(31) request is sent for type2(0x4050) in "
                                  "extended session")
        if result_step:
            result_step = dut.step(step_6, parameters['resp_time_type2_type3'], purpose="Verify "
                                  "RoutineControl(31) request is sent for type3(0x4000) in "
                                  "extended session")
        if result_step:
            result_step = dut.step(step_7, parameters['resp_time_type1'], purpose="Verify "
                                  "RoutineControl(31) request is sent for type1(0x0206) in "
                                  "programming session")
        if result_step:
            result_step = dut.step(step_8, parameters['resp_time_type2_type3'], purpose="Verify "
                                  "RoutineControl(31) request is sent for type2(0x4050) in "
                                  "programming session")
        if result_step:
            result_step = dut.step(step_9, parameters['resp_time_type2_type3'], purpose="Verify "
                                  "RoutineControl(31) request is sent for type3(0x4000) in "
                                  "programming session")
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
