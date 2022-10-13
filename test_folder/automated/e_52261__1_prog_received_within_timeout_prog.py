"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 52261
version: 1
title: PROG received within Timeout_Prog
purpose: >
    To be able to enter the programmingSession state when the DiagnosticSessionControl
    (ProgrammingSession) request is received within Timeout_prog.

description: >
    When the ECU receives the diagnostic request DiagnosticSessionControl(ProgrammingSession)
    within Timeout_Prog shall the ECU enter the “programmingSession” state.

details: >
    Verify whether the ECU is entering into programming session within Timeout_Prog(5ms)
"""

import time
import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_can import SupportCAN, PerParam
from supportfunctions.support_service3e import SupportService3e

SC = SupportCAN()
SS3E = SupportService3e()


def start_heartbeat(dut: Dut):
    """
    Start heartbeat
    Args:
        dut (Dut): Dut instance
    Return: None
    """
    # Start heartbeat
    heartbeat_param: PerParam = {
                        "name" : "Heartbeat",
                        "send" : True,
                        "id" : dut.conf.rig.signal_periodic,
                        "nspace" : dut.namespace.name,
                        "protocol" : "can",
                        "framelength_max" : 8,
                        "padding" : True,
                        "frame" : bytes.fromhex(dut.conf.rig.wakeup_frame),
                        "intervall" : 0.4}
    SC.start_heartbeat(dut.network_stub, heartbeat_param)


def step_1(dut: Dut):
    """
    action: Verify whether the ECU is entering into programming session within Timeout_Prog after
            request for programming session.
    expected_result: ECU should enter into programming session within Timeout_Prog
    """

    # Stop NM frames
    SC.stop_heartbeat()

    # Wait 15 seconds for ECU full shutdown.
    time.sleep(15)

    # Start sending NM frames
    start_heartbeat(dut)

    # Send burst diagnostic session control programming session with periodicity of 1ms
    # for 10ms
    burst_param: PerParam = {
                    "name" : "Burst",
                    "send" : True,
                    "id" : dut.conf.rig.signal_tester_present,
                    "nspace" : dut["namespace"],
                    "frame" : bytes.fromhex('0210820000000000'),
                    "intervall" : 0.001}

    SC.send_burst(dut["netstub"], burst_param, 10)

    # Wait 5 seconds
    time.sleep(5)

    response = dut.uds.active_diag_session_f186()
    if response.data["details"]["mode"] == 2:
        logging.info("ECU enters into programming session within Timeout_Prog as expected")
        return True

    logging.error("Test Failed: ECU is not in programming session within the Timeout_Prog, "
                  "received session: %s ", response.data["details"]["mode"])
    return False


def run():
    """
    Verify whether the ECU is entering into programming session within Timeout_Prog
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False
    try:
        dut.precondition(timeout=90)

        result_step = dut.step(step_1, purpose="Verify whether the ECU is entering "
                               "into programming session within Timeout_Prog after request for "
                               "programming session")

        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
