"""

/*********************************************************************************/



Copyright © 2023 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 53933
version: 1
title: Time window (Timeout_Prog)
purpose: >
    To have the possibility to reprogram the ECU believes if it believes it has valid software(s)
    present, but the application software is not correctly jumping to the PBL.

description: >
    The primary bootloader (PBL) shall have a time window (Timeout_Prog) of 5 ms (-0% / +10%) for
    detection of the DiagnosticSessionControl service. If a DiagnosticSessionControl service with
    diagnosticSessionType equal to programmingSession is received during the time window the ECU
    shall enter programmingSession state.

    The Timeout_prog timer is started when the ECU is able to receive incoming messages.

details: >
    Verify Timeout_Prog for detection of diagnostic session control service
    Steps:
        1. Send burst diagnostic session control programming session with periodicity of 10ms
           for 40ms window.
        2. Send burst diagnostic session control programming session with periodicity of 1ms
           for 40ms window.
"""

import time
import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_can import SupportCAN, PerParam
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_service3e import SupportService3e

SIO = SupportFileIO()
SC = SupportCAN()
SE3E = SupportService3e()


def periodic_start_and_stop(dut):
    """
    Periodic start and stop
    Args:
        dut (Dut): An instance of Dut
    Returns: None
    """
    # Stop NM frames
    SC.stop_heartbeat()

    # Send stop periodic
    SE3E.stop_periodic_tp_zero_suppress_prmib()

    # Wait for 15 secs
    time.sleep(15)

    # Send start periodic
    heartbeat_param: PerParam = {
        "name" : "Heartbeat",
        "send" : True,
        "id" : dut.conf.rig.signal_periodic,
        "nspace" : dut.namespace,
        "protocol" : "can",
        "framelength_max" : 8,
        "padding" : True,
        "frame" : bytes.fromhex(dut.conf.rig.wakeup_frame),
        "intervall" : 0.4
        }
    SC.start_heartbeat(dut.network_stub, heartbeat_param)

    # Send start periodic
    SE3E.start_periodic_tp_zero_suppress_prmib(dut)


def send_burst_of_diagnostic_session(dut, send, id_value, interval, quantity):
    """
    Send diagnostic session control programming session burst
    Args:
        dut (Dut): An instance of Dut
        send (str): Send signal
        id_value (str): Id signal
        interval (float): Interval
        quantity (int): Quantity
    Returns: None
    """
    burst_param: PerParam = {"name" : "Burst",
                             "send" : send,
                             "id" : id_value,
                             "nspace" : dut["namespace"],
                             "frame" : b'\x02\x10\x82\x00\x00\x00\x00\x00',
                             "intervall" : interval}

    SC.send_burst(dut["netstub"], burst_param, quantity)


def verify_active_diagnostic_session(dut, mode, session):
    """
    Verify active diagnostic session
    Args:
        dut (Dut): An instance of Dut
        mode (int): ECU mode
        session (str): Diagnostic session
    Returns:
        (bool): True on successfully verifying active diagnostic session
    """
    response = dut.uds.active_diag_session_f186()
    if response.data["details"]["mode"] == mode:
        logging.info("ECU is in %s session as expected", session)
        return True

    logging.error("Test Failed: ECU is not in %s session", session)
    return False


def step_1(dut: Dut, parameters):
    """
    action: Send burst diagnostic session control programming session with periodicity of 10ms for
            40 ms window
    expected_result: ECU should be in default session
    """
    periodic_start_and_stop(dut)
    send_burst_of_diagnostic_session(dut, parameters['send'],
                                     parameters['brust_id_for_periodicity_high_freq_window'],
                                     parameters['interval_periodicity_high_freq_window'],
                                     parameters['quantity_periodicity_high_freq_window'])

    return verify_active_diagnostic_session(dut, mode=1, session='default')


def step_2(dut: Dut, parameters):
    """
    action: Send burst diagnostic session control programming session with periodicity of 1ms for
            40 ms window
    expected_result: ECU should be in programming session
    """
    periodic_start_and_stop(dut)
    send_burst_of_diagnostic_session(dut, parameters['send'],
                                     parameters['brust_id_for_periodicity_low_freq_window'],
                                     parameters['interval_periodicity_low_freq_window'],
                                     parameters['quantity_periodicity_low_freq_window'])

    return verify_active_diagnostic_session(dut, mode=2, session='programming')


def step_3(dut: Dut):
    """
    action: ECU hard reset and verify active diagnostic session
    expected_result:  ECU should be in default session
    """
    # ECU hard reset
    dut.uds.ecu_reset_1101()

    return verify_active_diagnostic_session(dut, mode=1, session='default')


def run():
    """
    Verify Timeout_Prog for detection of diagnostic session control service
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'send' : '',
                       'brust_id_for_periodicity_high_freq_window': '',
                       'brust_id_for_periodicity_low_freq_window': '',
                       'interval_periodicity_high_freq_window': 0.0,
                       'quantity_periodicity_high_freq_window': 0,
                       'interval_periodicity_low_freq_window': 0.0,
                       'quantity_periodicity_low_freq_window': 0,}

    parameters = SIO.parameter_adopt_teststep(parameters_dict)
    if not all(list(parameters.values())):
        raise DutTestError("yml parameters not found")

    try:
        dut.precondition(timeout=90)

        result_step = dut.step(step_1, parameters, purpose="Send burst diagnostic session control"
                                                           " programming session with periodicity"
                                                           " of 10ms for 40 ms window")
        if result_step:
            result_step = dut.step(step_2, parameters, purpose="Send burst diagnostic session "
                                                               "control programming session with"
                                                               " periodicity of 1ms for 40 ms"
                                                               " window")
        if result_step:
            result_step = dut.step(step_3, purpose="ECU hard reset and verify active diagnostic"
                                                   " session")
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
