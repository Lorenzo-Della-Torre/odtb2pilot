"""

/*********************************************************************************/


Copyright © 2022 Volvo Car Corporation. All rights reserved.


NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 52289
version: 1
title: Reception of DiagnosticSessionControl(programmingSession)

purpose: >
    To prevent a reset when the bootloader is in the programmingSession state and receive a
    diagnostic request DiagnosticSessionControl(programmingSession)

description: >
    When bootloader is in programmingSession state (PBL or SBL) and receives a Diagnostic
    SessionControl (programmingSession) request, the ECU shall not reset i.e. the ECU shall stay
    in the programmingSession state.

details: >
    ECU status verification after bootloader in programming session receives
    DiagnosticSessionControl(programmingSession) request.
"""

import time
import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service27 import SupportService27

SSBL = SupportSBL()
SE22 = SupportService22()
SE27 = SupportService27()


def step_1(dut: Dut):
    """
    action: Initially set ECU to programming session and verify ECU mode and security access. Again
            set ECU to programming session and verify security access.
    expected_result: Security access should be granted when ECU enters into PBL and should be
                     denied for second request.
    """
    # Set ECU to programming session
    dut.uds.set_mode(2)
    # Sleep time to avoid NRC37
    time.sleep(5)

    # Check ECU mode is PBL
    ecu_mode = SE22.get_ecu_mode(dut)
    if ecu_mode != 'PBL':
        logging.error("Test failed: Expected ECU to be in PBL mode after DiagnosticSessionControl"
                      " request")
        return False

    # Security access to ECU
    result = SE27.activate_security_access_fixedkey(dut, sa_keys=dut.conf.default_rig_config,
                                                    step_no=272, purpose="SecurityAccess")
    if not result:
        logging.error("Test failed: Security access denied")
        return False

    # Set ECU to programming session by DiagnosticSessionControl request
    dut.uds.set_mode(2)

    # Security access again to ECU
    result = SE27.activate_security_access_fixedkey(dut, sa_keys=dut.conf.default_rig_config,
                                                    step_no=272, purpose="SecurityAccess")
    if result:
        logging.error("Test failed: Expected security access to be denied, but was granted again")
        return False

    logging.info("Security access already granted as expected")
    return True


def step_2(dut: Dut):
    """
    action: Initially download & activate SBL and verify ECU mode. After that, set ECU to
            programming session and verify ECU mode again.
    expected_result: ECU should be in SBL after download & activate SBL. ECU stays in SBL
                     after DiagnosticSessionControl request programming session.
    """
    # ECU reset
    dut.uds.ecu_reset_1101()

     # Set ECU to programming session by DiagnosticSessionControl request
    dut.uds.set_mode(2)

    # Read filenames used for transfer to ECU
    SSBL.get_vbf_files()

    # Software download and activate SBL
    result = SSBL.sbl_activation(dut, sa_keys=dut.conf.default_rig_config)
    if not result:
        logging.error("Test failed: SBL activation failed")
        return False

    # Check ECU mode is SBL after SBL activation
    ecu_mode = SE22.get_ecu_mode(dut)
    if ecu_mode != 'SBL':
        logging.error("Test failed: Expected ECU to be in SBL mode after "
                      " SBL activation")
        return False

    # Set ECU to programming session by DiagnosticSessionControl request
    dut.uds.set_mode(2)

    # Check ECU mode stays in SBL mode after DiagnosticSessionControl request
    ecu_mode = SE22.get_ecu_mode(dut)
    if ecu_mode != 'SBL':
        logging.error("Test failed: Expected ECU to be in SBL mode after "
                      " DiagnosticSessionControl request")
        return False

    logging.info("ECU is in SBL mode after DiagnosticSessionControl 1002 while in SBL"
                                                                    " as expected")

    return True


def step_3(dut: Dut):
    """
    action: Verify ECU is in default session after ECU reset
    expected_result: ECU is in default session
    """
    # Perform ECU reset
    dut.uds.ecu_reset_1101()

    # Verify ECU is in default session after ECU reset
    is_in_default = SE22.read_did_f186(dut, b'\x01')
    if not is_in_default:
        logging.error("Test failed: Expected ECU to be in default session")
        return False

    logging.info("ECU is in default session after ECU reset as expected")
    return True


def run():
    """
    ECU status verification after bootloader in programming session receives
    DiagnosticSessionControl(programmingSession) request
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False
    try:
        dut.precondition(timeout=120)

        result_step = dut.step(step_1, purpose="Initially set ECU to programming session and "
                               "verify ECU mode and security access. Again set ECU to programming "
                               "session and verify security access")
        if result_step:
            result_step = dut.step(step_2, purpose="Initially download & activate SBL and verify "
                                   "ECU mode. After that, set ECU to programming session and "
                                   "verify ECU mode again")
        if result_step:
            result_step = dut.step(step_3, purpose="Verify ECU is in default session after"
                                                   " ECU reset")
        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)

if __name__ == '__main__':
    run()
