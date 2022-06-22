"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 400704
version: 3
title: : Secondary Bootloader - Condition for activation
purpose: >
    The authenticity of the secondary bootloader must be verified. Otherwise, the
    verification mechanism could be bypassed and arbitrary application could be started.

description: >
    The primary bootloader must ensure that the authenticity verification of the secondary
    bootloader is passed prior to it is activated. If the verification fails, the ECU shall
    remain in the primary bootloader and the volatile memory buffer shall be cleared. The used
    address parameter of the ActivateSBL routine control must be within the address range of the
    validated block(s).

details: >
    Verify the authenticity of the secondary bootloader
"""

import time
import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from hilding.conf import Conf
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_service31 import SupportService31

CNF = Conf()
SSBL = SupportSBL()
SC_CARCOM = SupportCARCOM()
SE22 = SupportService22()
SE27 = SupportService27()
SE31 = SupportService31()


def routinecontrol_start_routine(dut, vbf_header):
    """
    Send RoutineControl request SID startRoutine (01), activate secondary boot-loader
    Args:
        dut (Dut): dut instance
        vbf_header (dict): vbf header
    Returns:
        bool: True when Received NRC-31
    """
    call = vbf_header['call'].to_bytes((vbf_header['call'].bit_length()+7) // 8, 'big')
    payload = SC_CARCOM.can_m_send("RoutineControlRequestSID", b'\x03\x01' + call, b'')
    response = dut.uds.generic_ecu_call(payload)

    if response.raw[2:8] == "7F3131":
        logging.info("Received NRC-31(requestOfRange) as expected")
        return True
    logging.error("Test Failed: Expected NRC-31(requestOfRange) received, %s", response.raw)
    return False


def step_1(dut: Dut):
    """
    action: Verify routine control start sent for check prog precondition
    expected_result: True on preconditions to programming are fulfilled
    """
    SSBL.get_vbf_files()

    result = SE31.routinecontrol_requestsid_prog_precond(dut, stepno=1)

    if result:
        logging.info("Preconditions to programming are fulfilled")
        # Set programming Diagnostic Session
        dut.uds.set_mode(2)
        return True

    logging.error("Test Failed: Routine control requestsid prog precond Unsuccessful")
    return False


def step_2(dut: Dut):
    """
    action: SBL activation with correct call
    expected_result: True on successful SBL activation with correct call.
    """
    result = SE27.activate_security_access_fixedkey(dut, sa_keys=CNF.default_rig_config,
                                                    step_no=272, purpose="SecurityAccess")
    if not result:
        logging.error("Test Failed: Security access denied")
        return False

    result, vbf_header = SSBL.sbl_download_no_check(dut, SSBL.get_sbl_filename())
    if not result:
        logging.error("Test Failed: sbl download no check failed")
        return False

    result = routinecontrol_start_routine(dut, vbf_header)
    if not result:
        logging.error("Test Failed: Routine control start routine Failed")
        return False

    # ECU reset
    dut.uds.ecu_reset_1101()
    time.sleep(5)
    result = SE22.read_did_f186(dut, dsession=b'\x01')
    if not result:
        logging.error(" ECU not in default session")
        return False

    logging.info("ECU is in default session")
    return True


def run():
    """
    Verify the authenticity of the secondary bootloader
    """
    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False
    try:
        dut.precondition(timeout=120)

        result_step = dut.step(step_1, purpose="Verify Routine Control start sent for Check"
                                               " Prog Precondition")
        if result_step:
            result_step = dut.step(step_2, purpose='Verify SBL activation with correct call')
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
