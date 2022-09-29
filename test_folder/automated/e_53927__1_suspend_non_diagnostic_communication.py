"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 53927
version: 1
title: Suspend non diagnostic communication
purpose: >
    To only have diagnostic communication between tester and ECU when executing the bootloader.

description: >
    Whenever an ECU is executing the bootloader, it shall ensure that non diagnostic communication
    e.g. network management messages between ECUs are suspended.

details: >
    Verify subscribed non-diagnostic signal is suspended
"""

import time
import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_can import SupportCAN, CanParam
from supportfunctions.support_SBL import SupportSBL

SIO = SupportFileIO()
SC = SupportCAN()
SSBL = SupportSBL()


def clear_can_messages(dut, parameters):
    """
    Clear CAN messages and CAN frames
    Args:
        dut (Dut): An instance of Dut
        parameters (dict): waiting_time
    Returns: None
    """
    SC.clear_all_can_messages()
    SC.clear_all_can_frames()
    SC.update_can_messages(dut)
    time.sleep(parameters['waiting_time'])


def step_1(dut: Dut, parameters):
    """
    action: Register non diagnostic signal
    expected_result: Received number of frames should be more than 10
    """
    # Fetch any signal sent from HVBM when awake
    can_p_ex: CanParam = {"netstub" : dut.network_stub,
                          "send" : parameters['send'],
                          "receive" : parameters['receive'],
                          "namespace" : dut.namespace}

    SC.subscribe_signal(can_p_ex, timeout=100)

    time.sleep(1)
    # Clear CAN messages and CAN frames
    clear_can_messages(dut, parameters)

    frames_received = len(SC.can_frames[can_p_ex["receive"]])
    logging.info("Number of frames received %s", frames_received)
    logging.info("Frames: %s", SC.can_frames[can_p_ex["receive"]])

    if frames_received > parameters['min_non_diag']:
        logging.info("Received number of frames %s as expected", frames_received)
        return True, frames_received

    logging.error("Test Failed: Expected frames more than 10, received %s", frames_received)
    return False, None


def step_2(dut: Dut):
    """
    action: Download and activate SBL
    expected_result: SBL should be activated
    """
    # Loads the rig specific VBF files
    vbf_result = SSBL.get_vbf_files()
    if not vbf_result:
        return False

    # Download and activate SBL on the ECU
    sbl_result = SSBL.sbl_activation(dut, sa_keys=dut.conf.default_rig_config)
    if not sbl_result:
        logging.error("Test Failed: SBL activation failed")
        return False

    logging.info("SBL activation successful")
    return True


def step_3(dut: Dut, parameters):
    """
    action: Verify subscribed non-diagnostic signal is suspended
    expected_result: Subscribed non-diagnostic signal should be suspended
    """
    can_rec = parameters['receive']
    # Clear CAN messages and CAN frames
    clear_can_messages(dut, parameters)

    logging.info("Frames received %s", len(SC.can_frames[can_rec]))
    logging.info("Frames: %s", SC.can_frames[can_rec])

    result = len(SC.can_frames[can_rec]) == 0
    if result:
        logging.info("Subscribed non-diagnostic signal is suspended, %s frame received as expected"
                     , len(SC.can_frames[can_rec]))
        return True

    logging.error("Test Failed: Subscribed non-diagnostic signal is not suspended")
    return False


def step_4(dut: Dut):
    """
    action: Set and verify ECU is in default session
    expected_result: ECU should be in default session
    """
    # Set to default session
    dut.uds.set_mode(1)

    # Verify active diagnostic session
    res = dut.uds.active_diag_session_f186()
    if res.data['details']['mode'] != 1:
        logging.error("ECU is not in default session")
        return False

    logging.info("ECU is in default session as expected")
    return True


def step_5(dut: Dut, frames_received_step_1, parameters):
    """
    action: Verify subscribed non-diagnostic signal is received
    expected_result: Subscribed non-diagnostic signal should be received
    """
    can_rec = parameters['receive']

    # Clear CAN messages and CAN frames
    clear_can_messages(dut, parameters)

    logging.info("Frames received %s", len(SC.can_frames[can_rec]))
    logging.info("Fames: %s", SC.can_frames[can_rec])

    result = ((len(SC.can_frames[can_rec]) + parameters['max_diff']) > frames_received_step_1 >
              (len(SC.can_frames[can_rec]) - parameters['max_diff']))

    if result:
        logging.info("Subscribed non-diagnostic signal is received")
        return True

    logging.error("Test Failed: Subscribed non-diagnostic signal is not received")
    return False


def run():
    """
    Verify subscribed non-diagnostic signal is suspended
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'waiting_time': 0,
                       'max_diff': 0,
                       'min_non_diag': 0,
                       'send': '',
                       'receive': ''}
    try:
        dut.precondition(timeout=90)

        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step, frames_received_step_1 = dut.step(step_1, parameters,
                                                       purpose="Register non diagnostic signal")
        if result_step:
            result_step = dut.step(step_2, purpose="Download and activate SBL")
        if result_step:
            result_step = dut.step(step_3, parameters, purpose="Verify subscribed non-diagnostic "
                                                               "signal is suspended")
        if result_step:
            result_step = dut.step(step_4, purpose="Set and verify ECU is in default session")
        if result_step:
            result_step = dut.step(step_5, frames_received_step_1, parameters, purpose="Verify "
                                                 "subscribed non-diagnostic signal is received")
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
