"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76500
version: 1
title: ReadDTCInformation (19) - reportDTCByStatusMask (02)
purpose: >
    It shall be possible to read out DTCs with a specific status

description: >
    The ECU shall support the service ReadDTCInformation - reportDTCByStatusMask in all sessions
    where the ECU supports the service ReadDTCInformation.

details: >
    Verify DTC information & read DTC with a specific status mask in default and extended diagnostic
    session
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from hilding.uds import UdsEmptyResponse
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_can import SupportCAN

SC_CARCOM = SupportCARCOM()
SC = SupportCAN()


def verify_dtc_info(dut: Dut, session):
    """
    Verify DTC information
    Args:
        dut(Dut) : Dut instance
        session(str) : Diagnostic session
    Return:
        (bool) : True on successfully verified positive response
    """
    dtc = SC_CARCOM.can_m_send("ReadDTCByStatusMask", b'', b'confirmedDTC')
    response = dut.uds.generic_ecu_call(dtc)

    if response.raw[4:6] == '59':
        logging.info("Successfully verified DTC information in %s session", session)
        return True

    logging.error("Test Failed: Unable to verify DTC information in %s session", session)
    return False


def read_dtc_with_mask(dut: Dut, session):
    """
    Read DTC with a specific status mask
    Args:
        dut(Dut) : Dut instance
        session(str) : Diagnostic session
    Return:
        (bool): True on successfully verified empty response
    """
    dtc = SC_CARCOM.can_m_send("ReadDTCByStatusMask(82)", b'', b'confirmedDTC')
    try:
        dut.uds.generic_ecu_call(dtc)
    except UdsEmptyResponse:
        pass

    if not SC.can_messages[dut["receive"]]:
        logging.info("Empty response received from ECU in %s session", session)
        return True

    logging.error("Test Failed: Expected empty response, received %s in %s session",
                   SC.can_messages[dut["receive"]], session)
    return False


def step_1(dut):
    """
    action: Verify DTC information in default session
    expected_result: True when received positive response
    """
    return verify_dtc_info(dut, session='default')


def step_2(dut):
    """
    action: Read DTCs with a specific status mask in default session
    expected_result: True when received positive response
    """
    return read_dtc_with_mask(dut, session='default')


def step_3(dut):
    """
    action: Verify DTC information in extended session
    expected_result: True when received positive response
    """
    # set ECU in extended session
    dut.uds.set_mode(3)

    return verify_dtc_info(dut, session='extended')


def step_4(dut):
    """
    action: Read DTCs with a specific status mask in extended session
    expected_result: True when received positive response
    """
    return read_dtc_with_mask(dut, session='extended')


def run():
    """
    Verify DTC information & read DTC with a specific status mask in default and extended
    diagnostic session
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=30)

        result_step = dut.step(step_1, purpose="Verify DTC information in default session")
        if result_step:
            result_step = dut.step(step_2, purpose="Read DTCs with a specific status mask in "
                                                   "default session")
        if result_step:
            result_step = dut.step(step_3, purpose="Verify DTC information in extended session")
        if result_step:
            result_step = dut.step(step_4, purpose="Read DTCs with a specific status mask in "
                                                   "extended session")
        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
