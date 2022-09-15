"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 53858
version: 1
title: Secondary bootloader diagnostic services
purpose: >
    To define the diagnostic services supported in the secondary bootloader.

description: >
    The SBL shall support the diagnostic services required in programming session which are
    specified in [VCC - UDS Services].

details: >
    Verify diagnostic services 3E,22,10 and 11 are supported in SBL. Received NRC 31 for
    WriteDataByIdentifier(2E) with wrong message and negative response for send key of security
    access(27)
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_sec_acc import SupportSecurityAccess
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service3e import SupportService3e
from supportfunctions.support_service27 import SupportService27

SC_CARCOM = SupportCARCOM()
SUTE = SupportTestODTB2()
SSBL = SupportSBL()
SSA = SupportSecurityAccess()
SE22 = SupportService22()
SE27 = SupportService27()
SE3E = SupportService3e()


def step_1(dut: Dut):
    """
    action: Activate SBL, verify service 3E and 22 are supported in SBL
    expected_result: True when service 3E and 22 are supported in SBL
    """
    SSBL.get_vbf_files()
    result = SSBL.sbl_activation(dut, sa_keys=dut.conf.default_rig_config)
    if not result:
        logging.error("Test Failed: SBL activation failed")
        return False

    result = SE3E.tester_present_zero_subfunction(dut)
    if not result:
        logging.error("Test Failed: Tester present of zero sub-function is not supported in SBL")
        return False

    result = SE22.read_did_eda0(dut)
    if not result:
        logging.error("Test Failed: Unable to read DID EDA0")
        return False

    logging.info("Service 3E and 22 are supported in SBL as expected")
    return True


def step_2(dut: Dut):
    """
    action: Verify response of service 2E with wrong message in SBL
    expected_result: True when received NRC 31 for service 2E with wrong message
    """
    payload = SC_CARCOM.can_m_send("WriteDataByIdentifier", bytes.fromhex('F18602'), b'')
    response = dut.uds.generic_ecu_call(payload)
    if response.raw[2:8] == '7F2E31':
        logging.info("Received NRC 31 for service 2E with wrong message as expected")
        return True

    logging.error("Test Failed: Expected NRC 31 for service 2E with wrong message, but received %s"
                  , response.raw)
    return False


def step_3(dut: Dut):
    """
    action: Verify service 27 in SBL
    expected_result: True when request seed successful and received negative response for send key
    """
    result, seed = SE27.security_access_request_seed(dut, sa_keys=dut.conf.default_rig_config)
    if not result:
        logging.error("Test Failed: request seed failed in SBL")
        return False

    sec_key = SSA.set_security_access_pins(seed, sa_keys=dut.conf.default_rig_config)
    payload = SC_CARCOM.can_m_send("SecurityAccessSendKey", sec_key, b'')
    response = dut.uds.generic_ecu_call(payload)
    if response.raw[2:6] == '7F27':
        logging.info("Request seed successful and received negative response for send key as "
                     "expected")
        return True

    logging.error("Test Failed: Expected negative response for send key of security access, but "
                  "received %s", response.raw)
    return False


def step_4(dut: Dut):
    """
    action: Set ECU in programming session and verify SBL
    expected_result: True when ECU is in SBL
    """
    dut.uds.set_mode(2)
    result = SE22.verify_sbl_session(dut)
    if result:
        logging.info("ECU is in SBL as expected")
        return True

    logging.error("Test Failed: ECU is not in SBL")
    return False


def step_5(dut: Dut):
    """
    action: ECU hard reset and verify default session
    expected_result: True when ECU is in default session
    """
    # Set ECU in default session
    dut.uds.set_mode(1)

    # ECU hard reset
    dut.uds.ecu_reset_1101()

    # Verify active diagnostic session
    response = dut.uds.active_diag_session_f186()
    if response.data["details"]["mode"] == 1:
        logging.info("ECU is in default session as expected")
        return True

    logging.error("Test Failed: Expected ECU to be in default session, but it is in mode %s",
                  response.data["details"]["mode"])
    return False


def run():
    """
    Verify diagnostic services 3E,22,10 and 11 are supported in SBL. Received NRC 31 for
    WriteDataByIdentifier(2E) with wrong message and negative response for send key of security
    access(27)
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=150)
        result_step = dut.step(step_1, purpose="Activate SBL, verify service 3E and 22")
        if result_step:
            result_step = dut.step(step_2, purpose="Verify service 2E in SBL")
        if result_step:
            result_step = dut.step(step_3, purpose="Verify service 27 in SBL")
        if result_step:
            result_step = dut.step(step_4, purpose="Set ECU in programming session and verify SBL")
        if result_step:
            result_step = dut.step(step_5, purpose="ECU hard reset and verify default session")
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
