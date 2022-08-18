"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76496
version: 0
title: ClearDiagnosticInformation (14)
purpose: >
    It shall be possible to erase DTCs and DTC related information

description: >
    The ECU must support the service ClearDiagnosticInformation. The ECU shall implement the
    service accordingly:

    Supported sessions:
    The ECU shall support Service ClearDiagnosticInformation in:
        •	defaultSession
        •	extendedDiagnosticSession
    The ECU may, but are not required to, support clearDiagnosticInformation in programmingSession

    Response time:
    Maximum response time for the service ClearDiagnosticInformation (0x14) is 3500ms.

    Effect on the ECU normal operation:
    The service ClearDiagnosticInformation (0x14) shall not affect the ECU's ability to execute
    non-diagnostic tasks.

    Entry conditions:
    If the ECU implement safety requirements with an ASIL higher than QM it shall, in all
    situations when diagnostic services may violate any of those safety requirements, reject the
    critical diagnostic service requests. Note that if the ECU rejects such critical diagnostic
    service requests, this requires an approval by Volvo Car Corporation.

    Security access:
    The ECU shall not protect service ClearDiagnosticInformation by using the service
    securityAccess (0x27).

details: >
    Verify clear diagnostic information(0x14) is supported in default and extended session
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_carcom import SupportCARCOM

SC_CARCOM = SupportCARCOM()


def verify_clear_diagnostic_info(dut: Dut, session):
    """
    Verify clear diagnostic information
    Args:
        dut(Dut): Dut instance
        session(str): Diagnostic session
    Return:
        (bool): True on successfully verified positive response
    """
    response = dut.uds.generic_ecu_call(SC_CARCOM.can_m_send("ClearDiagnosticInformation",
                                                              b'\x0B\x4A\x00',
                                                              b''))
    if response.raw[2:4] == '54':
        logging.info("Successfully verified clear diagnostic information in %s session", session)
        return True

    logging.error("Test Failed: Unable to verify clear diagnostic information in %s session",
                  session)
    return False


def step_1(dut: Dut):
    """
    action: Verify clear diagnostic information in default session
    expected_result: True when received positive response '54'
    """
    return verify_clear_diagnostic_info(dut, session='default')


def step_2(dut: Dut):
    """
    action: Verify clear diagnostic information in extended session
    expected_result: True when received positive response '54'
    """
    # Set ECU in extended session
    dut.uds.set_mode(3)

    result = verify_clear_diagnostic_info(dut, session='extended')
    if result:
        # Check active diagnostic session
        response = dut.uds.active_diag_session_f186()
        if response.data["details"]["mode"] == 3:
            logging.info("ECU is in extended session as expected")
            return True

        logging.error("Test Failed: Not in extended session, received session %s",
                      response.data["details"]["mode"])
    return False


def run():
    """
    Verify clear diagnostic information(0x14) is supported in default and extended session
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=30)

        result_step = dut.step(step_1, purpose="Verify clear diagnostic information in "
                                               "default session")
        if result_step:
            result_step = dut.step(step_2, purpose="Verify clear diagnostic information in "
                                                   "extended session")
        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)

    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
