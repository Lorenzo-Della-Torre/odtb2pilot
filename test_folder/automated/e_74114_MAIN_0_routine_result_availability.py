"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 74114
version: 1
title: Routine result availability
purpose: >
    Define how long time the route shall keep the result of the routine.

description: >
   The result of the routine shall at least be available (via requestRoutineResults) under the
   complete duration of the diagnostic session or until the routine is re-started.

details: >
    Verify the result of the routine shall be available via requestRoutineResult
    for the complete duration of diagnostic session or until routine is restarted.
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_can import SupportCAN

SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
SIO = SupportFileIO()
SC= SupportCAN()


def verify_active_diagnostic_session(dut, mode, session):
    """
    Verify active diagnostic session
    Args:
        dut (Dut): An instance of Dut
        mode (int): Diagnostic mode
        session (str): Diagnostic session
    Returns:
        (bool): True on successfully verifying active diagnostic session
    """
    result = False
    # Read active diagnostic session
    active_session = dut.uds.active_diag_session_f186()

    # Verify active diagnostic session
    if active_session.data["details"]["mode"] == mode:
        logging.info("ECU is in %s as expected", session)
        result = True
    else:
        logging.error("Test Failed: ECU is not in %s", session)

    return result


def step_1(dut: Dut):
    """
    action: Set to extended session and verify active diagnostic session
    expected_result: ECU should be in extended session
    """
    # Set to extended session
    dut.uds.set_mode(3)

    return verify_active_diagnostic_session(dut, mode=3, session='extended')


def step_2(dut: Dut, routine_id):
    """
    action: Verify result availability before requesting the routine control type3 in extended
            session
    expected_result: Should get negative response '7F' with NRC-24
    """
    dut.uds.generic_ecu_call(SC_CARCOM.can_m_send("RoutineControlRequestSID",
                                                  bytes.fromhex(routine_id),
                                                  b'\x03'))
    result = SUTE.test_message(SC.can_messages[dut["receive"]], teststring='7F3124')
    decoded_7f_res = SUTE.pp_decode_7f_response(SC.can_frames[dut["receive"]][0][2])
    if result:
        logging.info('Received NRC %s as expected', decoded_7f_res)
    else:
        logging.error("Test Failed: Expected NRC-24, received %s", decoded_7f_res)

    return result


def step_3(dut: Dut, routine_id):
    """
    action: Verify Routine Type3 is in status running after start request is sent
    expected_result: Should get positive response '71'
    """
    dut.uds.generic_ecu_call(SC_CARCOM.can_m_send("RoutineControlRequestSID",
                                                  bytes.fromhex(routine_id),
                                                  b'\x01'))
    result = SUTE.pp_decode_routine_control_response(SC.can_frames[dut["receive"]][0][2],
                                                     "Type3,Currently active")
    if result:
        logging.info("Received response 'Type3,Currently active' for routine identifier"
                     " as expected")
    else:
        logging.error("Test Failed: Expected response 'Type3,Currently active'")

    return result


def step_4(dut: Dut, routine_id):
    """
    action: Verify routine control request is completed after routine control stop is sent in
            extended session
    expected_result: Should get positive response '71'
    """
    dut.uds.generic_ecu_call(SC_CARCOM.can_m_send("RoutineControlRequestSID",
                                                  bytes.fromhex(routine_id),
                                                  b'\x02'))
    result = SUTE.pp_decode_routine_control_response(SC.can_frames[dut["receive"]][0][2],
                                                     "Type3,Completed")
    if result:
        logging.info ("Received response 'Type3,Completed' for routine identifier as expected")
    else:
        logging.error("Test Failed: Expected response 'Type3,Completed'")

    return result


def step_5(dut: Dut, routine_id):
    """
    action: Verify routine control result available for type3
    expected_result: Should get positive response '71'
    """
    dut.uds.generic_ecu_call(SC_CARCOM.can_m_send("RoutineControlRequestSID",
                                                  bytes.fromhex(routine_id),
                                                  b'\x03'))
    result = SUTE.pp_decode_routine_control_response(SC.can_frames[dut["receive"]][0][2],
                                                     "Type3,Completed")
    if result:
        logging.info ("Received response 'Type3,Completed' for routine identifier as expected")
    else:
        logging.error("Test Failed: Expected response 'Type3,Completed'")

    return result


def step_6(dut: Dut):
    """
    action: Verify ECU is in extended session
    expected_result: ECU should be in extended session
    """
    return verify_active_diagnostic_session(dut, mode=3, session='extended')


def step_7(dut: Dut, routine_id):
    """
    action: Verify routine control result available for further requests
    expected_result: Should give positive response '71'
    """
    dut.uds.generic_ecu_call(SC_CARCOM.can_m_send("RoutineControlRequestSID",
                                                  bytes.fromhex(routine_id),
                                                  b'\x03'))
    result = SUTE.pp_decode_routine_control_response(SC.can_frames[dut["receive"]][0][2],
                                                     "Type3,Completed")
    if result:
        logging.info ("Received response 'Type3,Completed' for routine identifier as expected")
    else:
        logging.error("Test Failed: Expected response 'Type3,Completed'")

    return result


def step_8(dut: Dut):
    """
    action: Set and verify ECU in default session
    expected_result: ECU should be in default session
    """
    # Set to default session
    dut.uds.set_mode(1)

    return verify_active_diagnostic_session(dut, mode=1, session='default')


def step_9(dut: Dut):
    """
    action: Set to extended session and verify active diagnostic session
    expected_result: ECU should be in extended session
    """
    # Set to extended session
    dut.uds.set_mode(3)

    return verify_active_diagnostic_session(dut, mode=3, session='extended')


def step_10(dut: Dut, routine_id):
    """
    action: Verify routine still accessible after session change
    expected_result: Should get positive response '71'
    """
    dut.uds.generic_ecu_call(SC_CARCOM.can_m_send("RoutineControlRequestSID",
                                                  bytes.fromhex(routine_id),
                                                  b'\x03'))
    result = SUTE.pp_decode_routine_control_response(SC.can_frames[dut["receive"]][0][2],
                                                     "Type3,Completed")
    if result:
        logging.info ("Received response 'Type3,Completed' for routine identifier as expected")
    else:
        logging.error("Test Failed: Expected response 'Type3,Completed'")

    return result


def run():
    """
    Verify the result of the routine shall be available via requestRoutineResult
    for the complete duration of diagnostic session or until routine is restarted.
    """
    dut = Dut()

    start_time = dut.start()
    result = False

    parameters_dict = {'routine_id': ''}

    try:
        dut.precondition(timeout=60)

        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result = dut.step(step_1, purpose="Set to extended session and verify active "
                                          "diagnostic session")

        result = result and dut.step(step_2, parameters['routine_id'],
                                     purpose="Verify result availability before requesting the "
                                             "routine control type3 in extended session")

        result = result and dut.step(step_3, parameters['routine_id'],
                                     purpose="Verify Routine Type 3 is running after start"
                                             " request is sent in extended session")

        result = result and dut.step(step_4, parameters['routine_id'],
                                     purpose="Verify routine control request is completed after"
                                             " routine control stop is sent in extended session")

        result = result and dut.step(step_5, parameters['routine_id'],
                                     purpose="Verify routine control result available for type3")

        result = result and dut.step(step_6, purpose="Verify ECU is in extended session")

        result = result and dut.step(step_7, parameters['routine_id'],
                                     purpose="Verify routine control result available for further"
                                             " requests")

        result = result and dut.step(step_8, purpose="Set and verify ECU in default session")

        result = result and dut.step(step_9, purpose="Set to extended session and verify active "
                                                     "diagnostic session")

        result = result and dut.step(step_10, parameters['routine_id'],
                                     purpose="Verify routine still accessible after session"
                                             " change")

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
