"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76621
version: 1
title: RoutineControl (31) - routineControlOptionRecord (RCEOR)
purpose: >
    To have the optional ability to define control parameters for a control routine. The control
    parameters can be used in one, several or all sub-functions supported by the control routine.

description: >
    The ECU may support the data parameter routineControlOptionRecord in one or several of the
    implemented sub-functions for a control routine. The data parameter is defined by the
    implementer.

details: >
    Verify RoutineControl response in extended and programming session
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_can import SupportCAN
from supportfunctions.support_test_odtb2 import SupportTestODTB2

SC_CARCOM = SupportCARCOM()
SIO = SupportFileIO()
SC = SupportCAN()
SUTE = SupportTestODTB2()


def verify_active_session(dut, expected_session):
    """
    Verify active diagnostic session
    Args:
        dut (Dut): An instance of Dut
        expected_session (int): Integer value of diagnostic session
    Returns:
        (bool): True on successfully verifying active diagnostic session
    """
    # Read active diagnostic session
    active_session = dut.uds.active_diag_session_f186()
    current_session = active_session.data["details"]["mode"]

    # Verify active diagnostic session
    if current_session == expected_session:
        logging.info("ECU is in session %s as expected", current_session)
        return True

    logging.error("Test Failed: ECU is in %s session, expected to be in %s session",
                   current_session, expected_session)
    return False


def verify_routine_control_response(dut, message, mask):
    """
    Verify RoutineControl response
    Args:
        dut (Dut): An instance of Dut
        parameters (dict): Message and mask
    Return:
        (bool): True when ECU sends positive response for RoutineControlRequest
    """
    # Send RoutineControlReques for Type 1
    payload = SC_CARCOM.can_m_send("RoutineControlRequestSID",
                                    bytes.fromhex(message),
                                    bytes.fromhex(mask))

    response = dut.uds.generic_ecu_call(payload)

    routine_control_response = SUTE.pp_decode_routine_control_response\
                               (SC.can_frames[dut["receive"]][0][2], 'Type1,Completed')

    expected_response = '71'+ mask + message[:4]
    if response.raw[2:10] != expected_response and not routine_control_response:
        logging.error("Test Failed: Expected positive response %s, received %s",
                       expected_response, response.raw[2:10])
        return False

    return True


def step_1(dut: Dut, parameters):
    """
    action: Verify RoutineControl response in extended session
    expected_result: True when received positive response for RoutineControlRequest for Type 1
    """
    # Set extended session
    dut.uds.set_mode(3)

    result = verify_routine_control_response(dut, parameters['message'], parameters['mask'])
    if not result:
        logging.error("Test Failed: RoutineControl response in extended session failed")
        return False

    # Verify active diagnostic session
    active_session = verify_active_session(dut, expected_session=3)
    if not active_session:
        return False

    return True


def step_2(dut: Dut, parameters):
    """
    action: Verify RoutineControl response in programming session
    expected_result: True when received positive response for RoutineControlRequest for Type 3
    """
    # Set programming session
    dut.uds.set_mode(2)

    result = verify_routine_control_response(dut, parameters['message'], parameters['mask'])
    if not result:
        logging.error("Test Failed: RoutineControl response in programming session failed")
        return False

    # Verify active diagnostic session
    active_session = verify_active_session(dut, expected_session=2)
    if not active_session:
        return False

    return True


def run():
    """
    Verify RoutineControl response in extended and programming session
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'message':'',
                       'mask': ''}

    try:
        dut.precondition(timeout=70)

        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step = dut.step(step_1, parameters, purpose='Verify RoutineControl response in'
                                                           ' extended session')
        if result_step:
            result_step = dut.step(step_2, parameters, purpose='Verify RoutineControl response'
                                                               ' in programming session')
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
