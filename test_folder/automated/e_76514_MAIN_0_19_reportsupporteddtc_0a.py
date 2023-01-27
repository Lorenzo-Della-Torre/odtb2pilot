"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76514
version: 0
title: ReadDTCInformation (19) - reportSupportedDTC (0A)
purpose: >
    Read out supported DTCs from an ECU

description: >
    The ECU may support the service ReadDTCInformation - reportSupportedDTC in all sessions where
    the ECU supports the service ReadDTCInformation.

details: >
    Verify response of read DTC information (19) - reportSupportedDTC(0A) in default and extended
    session
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_can import SupportCAN, CanPayload, CanTestExtra
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM

SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()


def read_dtc_info(dut, session):
    """
    Read DTC information (19) - reportSupportedDTC(0A) in default/extended session
    Args:
        dut (Dut): An instance of Dut
        session (str): Diagnostic session
    Returns:
        (bool): True when positive response received for read DTC information(19)-
                reportSupportedDTC(0A)
    """
    cpay: CanPayload = {"payload": SC_CARCOM.can_m_send("ReadDTCInfoReportSupportedDTC", b'', b''),
                        "extra": ''}

    etp: CanTestExtra = {"step_no": 101,
                         "purpose": "",
                         "timeout": 5,
                         "min_no_messages": -1,
                         "max_no_messages": -1 }

    result = SUTE.teststep(dut, cpay, etp)
    response = SC.can_messages[dut["receive"]][0][2]
    if result and response[4:8]=='590A':
        logging.info("Successfully read out supported DTCs in %s session", session)
        return True

    logging.error("Test Failed: Unable to read out supported DTCs in %s session", session)
    return False


def step_1(dut: Dut):
    """
    action: Read DTC information (19) - reportSupportedDTC(0A) and verify ECU supports the service
            ReadDTCInformation - reportSupportedDTC in default session.
    expected result: Read DTC information(19) - reportSupportedDTC(0A) should give positive
                     response '590A'.
    """
    return read_dtc_info(dut, session='default')


def step_2(dut: Dut):
    """
    action: Read DTC information (19) - reportSupportedDTC(0A) and verify ECU supports the service
            ReadDTCInformation - reportSupportedDTC in extended session.
    expected result: ECU should be in extended session after receiving positive response '590A'
                     for read DTC information(19) - reportSupportedDTC(0A).
    """
    # Set ECU in extended session
    dut.uds.set_mode(3)

    result = read_dtc_info(dut, session='extended')
    if not result:
        return False

    # Verify extended session
    response = dut.uds.active_diag_session_f186()
    if response.data["details"]["mode"] == 3:
        logging.info("ECU is in extended session as expected")
        return True

    logging.error("Test Failed: Expected ECU to be in extended session, received mode %s",
                  response.data["details"]["mode"])
    return False


def run():
    """
    Verify response of read DTC information (19) - reportSupportedDTC(0A) in default and extended
    session
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=40)
        result_step = dut.step(step_1, purpose='Verify ECU supports the service ReadDTCInformation'
                               ' - reportSupportedDTC in default session')
        if result_step:
            result_step = dut.step(step_2, purpose='Verify ECU supports the service'
                                   ' ReadDTCInformation - reportSupportedDTC in extended session')
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
