"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 53913
version: 1
title: ECUs with multiple networks
purpose: >
    To define the implementation of ECUs with multiple networks.

description: >
    The bootloader shall only support software download from the network which is defined to be
    the incoming network for diagnostic communication.

details: >
    Verify no message received in routine control type-1(start) for check complete and compatible
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_can           import SupportCAN, CanTestExtra, CanPayload
from supportfunctions.support_test_odtb2    import SupportTestODTB2
from supportfunctions.support_carcom        import SupportCARCOM
from supportfunctions.support_service27     import SupportService27

SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
SE27 = SupportService27()


def step_1(dut):
    """
    action: Security access in programming session
    expected_result: True when security access successful
    """
    # Set ECU in programming session
    dut.uds.set_mode(2)

    # Security access
    result = SE27.activate_security_access_fixedkey(dut, sa_keys=dut.conf.default_rig_config)
    if result:
        logging.info("security access successful in programming session")
        return True

    logging.error("Test Failed: Security access denied in programming session")
    return False


def step_2(dut):
    """
    action: Verify no message received in routine control type-1(start) for check complete and
            compatible
    expected_result: True when no message receive in CAN frame
    """
    cpay: CanPayload = {
                        "payload": SC_CARCOM.can_m_send("RoutineControlRequestSID",
                                                        b'\x02\x05',
                                                        b'\x01'),
                        "extra": ''
                        }

    etp: CanTestExtra = {
                        "step_no": 2,
                        "purpose": " ",
                        "timeout": 1,
                        "min_no_messages": -1,
                        "max_no_messages": -1
                        }

    result = SUTE.teststep(dut, cpay, etp)

    if not result:
        logging.error("Test Failed: Routine control request failed")
        return False

    # Verify the message has been sent to the ECU
    if not bool(SC.can_frames.get(dut["send"])):
        logging.error("Test Failed: Successfully verified the message has been sent to the ECU")
        return False

    # Verify no message has been receive
    msg_receive = SC.can_frames[dut["receive"]]
    if not len(msg_receive) == 0:
        logging.error("Test Failed: Expected no message receive, but received %s", msg_receive)
        return False

    logging.info("Successfully verified complete and compatibility")
    return True


def step_3(dut):
    """
    action: ECU reset and verify default session
    expected_result: True when ECU is in default session
    """
    # ECU hard reset
    dut.uds.ecu_reset_1101()

    # Verify default session
    response = dut.uds.active_diag_session_f186()
    if response.data["details"]["mode"] == 1:
        logging.info("ECU is in default session as expected")
        return True

    logging.error("Test Failed: Expected ECU in default session, but it is in mode %s",
                  response.data["details"]["mode"])
    return False


def run():
    """
    Verify no message received in routine control type-1(start) for check complete and compatible
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=90)

        result_step = dut.step(step_1, purpose="Security access in programming session")
        if result_step:
            result_step = dut.step(step_2, purpose="Verify no message received in routine control"
                                               " type-1(start) for check complete and compatible")
        if result_step:
            result_step = dut.step(step_3, purpose="ECU reset and verify default session")

        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
