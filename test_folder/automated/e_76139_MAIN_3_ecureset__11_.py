"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76139
version: 3
title: : ECUReset (11)
purpose: >
    ECU reset is used in the SWDL process and may be useful when testing an ECU

description: >
    The ECU must support the service ECUReset. The ECU shall implement the service accordingly.

    Supported sessions-
    The ECU shall support Service ECUReset in
    •	defaultSession
    •	extendedDiagnosticSession
    •	programmingSession, both primary and secondary bootloader

    Response time-
    Maximum response time for the service ECUReset (0x11) is P2Server_max.

    Effect on the ECU normal operation-
    The service ECUReset (0x11) is allowed to affect the ECUs ability to execute non-diagnostic
    tasks. The service is only allowed to affect execution of the non-diagnostic tasks during
    the execution of the diagnostic service.

    After the diagnostic service is completed any effect on the non-diagnostic tasks is not
    allowed anymore (normal operational functionality resumes).

    Entry conditions-
    Entry conditions for service ECUReset (0x11) are allowed only if approved by Volvo Car
    Corporation.
    If the ECU implement safety requirements with an ASIL higher than QM it shall, in all
    situations when diagnostic services may violate any of those safety requirements, reject
    the critical diagnostic service requests. Note that if the ECU rejects such critical
    diagnostic service requests, this requires an approval by Volvo Car Corporation.

    Security access-
    The ECU shall not protect service ECUReset by using the service securityAccess (0x27).


details: >
    Verify ECUReset service in all supported diagnostic session
    •	defaultSession
    •	extendedDiagnosticSession
    •	programmingSession
"""


import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_service11 import SupportService11
from supportfunctions.support_service22 import SupportService22

SE11 = SupportService11()
SE22 = SupportService22()


def ecu_reset(dut):
    """
    Reset ECU with service 0x11
    Args:
        dut (Dut): dut instance
    Returns:
        (bool): True when ECU is in default session
    """
    # Reset ECU (1101)
    dut.uds.ecu_reset_1101()

    result = SE22.read_did_f186(dut, dsession=b'\x01')
    if not result:
        logging.error("ECU is not in default session")
        return False

    logging.info("ECU is in default session")
    return True


def set_ecu_to_programming_sesssion(dut):
    """
    Set and verify ECU is in programming session
    Args:
        dut (Dut): dut instance
    Returns:
        (bool): True when ECU is in programming session
    """
    # Set ECU in programming session
    dut.uds.set_mode(2)

    # Verify ECU is in programming session
    result = SE22.read_did_f186(dut, dsession=b'\x02')
    if not result:
        logging.error("ECU is not in programming session")
        return False

    logging.info("ECU is in programming session")
    return True


def step_1(dut: Dut):
    """
    action: Verify ECU is in default session after reset(1101) and reset no reply(1181)
    expected_result: True when ECU is in default session
    """
    # Reset ECU (1101)
    result = ecu_reset(dut)
    if not result:
        logging.error("Test Failed: ECU is not in default session")
        return False

    # Reset ECU no reply (1181)
    SE11.ecu_hardreset_noreply(dut)

    # Verify ECU is in default session
    result = SE22.read_did_f186(dut, dsession=b'\x01')
    if not result:
        logging.error("Test Failed: ECU is not in default session")
        return False

    logging.info("ECU is in default session")
    return True


def step_2(dut: Dut):
    """
    action: ECU set to extended session and verify ECU is in default session after reset(1101)
            and reset no reply(1181)
    expected_result: True when ECU is in default session
    """
    # Set ECU in extended session
    dut.uds.set_mode(3)

    # Reset ECU (1101)
    result = ecu_reset(dut)
    if not result:
        logging.error("Test Failed: ECU is not in default session")
        return False

    # Set ECU in extended session
    dut.uds.set_mode(3)

    # Reset ECU no reply (1181)
    SE11.ecu_hardreset_noreply(dut)

    # Verify ECU is in default session
    result = SE22.read_did_f186(dut, dsession=b'\x01')
    if not result:
        logging.error("Test Failed: ECU is not in default session")
        return False

    logging.info("ECU is in default session")
    return True


def step_3(dut: Dut):
    """
    action: ECU set to programming session and verify ECU is in default session after reset(1101)
            and reset no reply(1181)
    expected_result: True when ECU is in default session
    """
    result = set_ecu_to_programming_sesssion(dut)
    if not result:
        return False

    # Reset ECU (1101)
    result = ecu_reset(dut)
    if not result:
        logging.error("Test Failed: ECU is not in default session")
        return False

    result = set_ecu_to_programming_sesssion(dut)
    if not result:
        return False

    # Reset ECU no reply (1181)
    SE11.ecu_hardreset_noreply(dut)

    # Verify ECU is in default session
    result = SE22.read_did_f186(dut, dsession=b'\x01')
    if result:
        logging.info("ECU is in default session")
        return True

    logging.error("Test Failed: ECU is not in default session")
    return False


def run():
    """
    Verify ECU reset service supported in default session, extended session
    and programming session
    """
    dut = Dut()
    start_time = dut.start()
    result = False

    try:
        dut.precondition(timeout=60)
        result_step = dut.step(step_1, purpose="Verify ECU is in default session after reset"
                                               "(1101) and reset no reply(1181)")

        if result_step:
            result_step = dut.step(step_2, purpose="ECU set to extended session and verify"
                                                   " ECU is in default session after reset(1101)"
                                                   " and reset no reply(1181)")
        if result_step:
            result_step = dut.step(step_3, purpose="ECU set to programming session and verify"
                                                   " ECU is in default session after reset(1101)"
                                                   " and reset no reply(1181)")
        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
