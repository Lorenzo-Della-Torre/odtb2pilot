"""

/*********************************************************************************/



Copyright © 2023 Volvo Car Corporation. All rights reserved.



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
        •   defaultSession
        •   extendedDiagnosticSession
        •   programmingSession, both primary and secondary bootloader

    The ECU shall support Service RoutineControl of Routine type 2 - Long routine and
    Routine type 3 - Continuous routine in:
        •   extendedDiagnosticSession
        •   programmingSession, both primary and secondary bootloader

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
    Verify RoutineControl(31) request response for different types in default, extended, PBL
    and SBL diagnostic session
"""

import time
import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_SBL import SupportSBL

SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
SE22 = SupportService22()
SE27 = SupportService27()
SIO = SupportFileIO()
SSBL = SupportSBL()


def request_routine_control_31(dut, routine_id):
    """
    Request RoutineControl(0x31)
    Args:
        dut (Dut): An instance of Dut
        routine_id (bytes): Routine identifier
    Returns:
        response.raw (str): ECU response
    """
    response = dut.uds.generic_ecu_call(SC_CARCOM.can_m_send("RoutineControlRequestSID",
                                                              bytes.fromhex(routine_id),
                                                              b'\x01'))
    return response.raw


def validate_positive_response(response, session, routine_type):
    """
    Validate positive response of request RoutineControl(0x31)
    Args:
        response (str): ECU response
        session (str): Diagnostic session
        routine_type (str): Routine types
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


def validate_response_time(elapsed_time, max_response_time):
    """
    Validate response time of request RoutineControl(0x31)
    Args:
        elapsed_time (int): Elapsed time of ECU request
        max_response_time (int): Maximum response time for routine types
    Returns:
        (bool): True when elapsed time is less than or equal to maximum response time
    """
    if elapsed_time <= max_response_time:
        logging.info("Response time %sms is less than or equal to %sms as expected",
                      elapsed_time, max_response_time)
        return True

    logging.error("Test Failed: Response time %sms is greater than %sms which is not expected",
                   elapsed_time, max_response_time)
    return False


def download_and_activate_sbl(dut):
    """
    Download and activation of SBL
    Args:
        dut (Dut): An instance of Dut
    Returns:
        (bool): True on SBL activation
    """
    # Loads the rig specific VBF files
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


def step_1(dut: Dut, parameters):
    """
    action: Verify RoutineControl(31) request is sent for type1 in default session
    expected_result: ECU should send positive response '71' and elapsed time should be less than or
                     equal to maximum response time
    """
    response = request_routine_control_31(dut, parameters['rid']['type1_non_programming'])

    # Calculate response time in milliseconds
    elapsed_time = dut.uds.milliseconds_since_request()

    result = validate_positive_response(response, session='default',
                                        routine_type='Type1,Completed')
    if result:
        return validate_response_time(elapsed_time, parameters['resp_time_type1'])

    return False


def step_2(dut: Dut, parameters):
    """
    action: Verify RoutineControl(31) request is sent for type1 in extended session
    expected_result: ECU should send positive response '71' and elapsed time should be less than or
                     equal to maximum response time
    """
    # Set to extended session
    dut.uds.set_mode(3)

    response = request_routine_control_31(dut, parameters['rid']['type1_non_programming'])

    # Calculate response time in milliseconds
    elapsed_time = dut.uds.milliseconds_since_request()

    result = validate_positive_response(response, session='extended',
                                        routine_type='Type1,Completed')
    if not result:
        return False

    resp_time_result = validate_response_time(elapsed_time, parameters['resp_time_type1'])
    if resp_time_result:
        # Check active diagnostic session
        active_session = SE22.read_did_f186(dut, b'\x03')
        if active_session:
            logging.info("ECU is in extended session as expected")
            return True

        logging.error("Test Failed: ECU is not in extended session")
        return False

    return False


def step_3(dut: Dut, parameters):
    """
    action: Verify RoutineControl(31) request is sent for type2 in extended session
    expected_result: ECU should send positive response '71'
    """
    # Type2 and type3 routine identifiers needs security access in extended session
    # Security access to ECU in extended session
    sa_result = SE27.activate_security_access_fixedkey(dut, sa_keys=dut.conf.default_rig_config,
                                                            step_no=272, purpose="SecurityAccess")
    if not sa_result:
        logging.error("Test Failed: Security access denied in extended session")
        return False

    response = request_routine_control_31(dut, parameters['rid']['type2_non_programming'])

    return validate_positive_response(response, session='extended',
                                      routine_type='Type2,Aborted')


def step_4(dut: Dut, parameters):
    """
    action: Verify RoutineControl(31) request is sent for type3 in extended session
    expected_result: ECU should send positive response '71'
    """
    response = request_routine_control_31(dut, parameters['rid']['type3_non_programming'])

    return validate_positive_response(response, session='extended',
                                      routine_type='Type3,Completed')


def step_5(dut: Dut, parameters):
    """
    action: Verify RoutineControl(31) request is sent for type1 in PBL
    expected_result: ECU should send positive response '71' and elapsed time should be less than or
                     equal to maximum response time
    """
    # Set to programming session
    dut.uds.set_mode(2)

    # Sleep time to avoid NRC-37
    time.sleep(5)

    # Security access to ECU in programming session
    sa_result = SE27.activate_security_access_fixedkey(dut, sa_keys=dut.conf.default_rig_config,
                                                            step_no=272, purpose="SecurityAccess")
    if not sa_result:
        logging.error("Test Failed: Security access denied in programming session")
        return False

    response = request_routine_control_31(dut, parameters['rid']['type1_pbl_sbl'])

    # Calculate response time in milliseconds
    elapsed_time = dut.uds.milliseconds_since_request()

    result = validate_positive_response(response, session='PBL',
                                        routine_type='Type1,Completed')
    if not result:
        return False

    resp_time_result = validate_response_time(elapsed_time, parameters['resp_time_type1'])
    if resp_time_result:
        # Verify current ECU mode is PBL session
        ecu_mode = SE22.verify_pbl_session(dut)
        if ecu_mode:
            logging.info("ECU is in PBL session as expected")
            return True

        logging.error("Test Failed: Expected ECU to be in PBL session")
        return False

    return False


def step_6(dut: Dut, parameters):
    """
    action: Verify RoutineControl(31) request is sent for type1 in SBL
    expected_result: ECU should send positive response '71' and elapsed time should be less than or
                     equal to maximum response time
    """
    # ECU hard reset
    dut.uds.ecu_reset_1101()

    result = download_and_activate_sbl(dut)
    if not result:
        return False

    # Verify current ECU mode is SBL session
    ecu_mode = SE22.verify_sbl_session(dut)
    if not ecu_mode:
        logging.error("Test Failed: Expected ECU to be in SBL session")
        return False

    logging.info("ECU is in SBL session as expected")

    response = request_routine_control_31(dut, parameters['rid']['type1_pbl_sbl'])

    # Calculate response time in milliseconds
    elapsed_time = dut.uds.milliseconds_since_request()

    result = validate_positive_response(response, session='SBL',
                                        routine_type='Type1,Completed')
    if not result:
        return False

    return validate_response_time(elapsed_time, parameters['resp_time_type1'])


def run():
    """
    Verify RoutineControl(31) request response for different types in default, extended, PBL
    and SBL diagnostic session
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'rid' : {},
                       'resp_time_type1': 0}
    try:
        dut.precondition(timeout=150)

        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step = dut.step(step_1, parameters, purpose="Verify RoutineControl(31) request "
                                                   "is sent for type1 in default session")
        if result_step:
            result_step = dut.step(step_2, parameters, purpose="Verify RoutineControl(31) request "
                                                       "is sent for type1 in extended session")
        if result_step:
            result_step = dut.step(step_3, parameters, purpose="Verify RoutineControl(31) request "
                                                       "is sent for type2 in extended session")
        if result_step:
            result_step = dut.step(step_4, parameters, purpose="Verify RoutineControl(31) request "
                                                       "is sent for type3 in extended session")
        if result_step:
            result_step = dut.step(step_5, parameters, purpose="Verify RoutineControl(31) request "
                                                       "is sent for type1 in PBL")
        if result_step:
            result_step = dut.step(step_6, parameters, purpose="Verify RoutineControl(31) request "
                                                       "is sent for type1 in SBL")
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
