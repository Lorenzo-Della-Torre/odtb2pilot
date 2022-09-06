"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 68177
version: 0
title: : Active diagnostic session data record
purpose: >
    To enable readout of the active diagnostic session.

description: >
    A data record with identifier as specified in the table below shall be implemented exactly as
    defined in Carcom - Global Master Reference Database.
    • It shall be possible to read the data record by using the diagnostic service specified in
      Ref[LC : Volvo Car Corporation - UDS Services - Service 0x22 (ReadDataByIdentifier) Reqs].

      *************************************************
        Description	                    Identifier
      *************************************************
        Active diagnostic session      	  F186
      *************************************************

    The identifier shall be implemented in the following sessions:
    • Default session
    • Programming session (which includes both primary and secondary bootloader)
    • Extended Session

details: >
    Verify positive response and validate the data in all sessions by reading DID 'F186' using
    ReadDataByIdentifier(0x22) service
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_can import SupportCAN
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_service22 import SupportService22

SSBL = SupportSBL()
SC = SupportCAN()
SUTE = SupportTestODTB2()
SE22 = SupportService22()


def verify_active_diagnostic_session(dut, mode, session):
    """
    Verify active diagnostic session
    Args:
        dut (Dut): An instance of Dut
        mode (int): Diagnostic session mode
        session (str): Diagnostic session
    Returns:
        (bool): True on successfully verifying active diagnostic session
    """
    # Read active diagnostic session
    response = dut.uds.active_diag_session_f186()

    # Verify active diagnostic session
    valid_response = '0462F1860' + str(mode)

    if response.raw[0:10] == valid_response:
        logging.info("Received positive response %s for request ReadDataByIdentifier in %s session",
                     response.raw[0:10], session)
        return True

    logging.error("Test Failed: Expected positive response %s for request ReadDataByIdentifier in"
                  " %s session, received %s", valid_response, session, response.raw)
    return False


def verify_pbl_sbl_session(dut, mode_is_pbl=False):
    """
    Verify active programming session (PBL/SBL)
    Args:
        dut (Dut): An instance of Dut
        mode_is_pbl (bool): True/False
    Return:
        result (bool): True when ECU is in expected session
    """
    eda0_result = SE22.read_did_eda0(dut)
    logging.info("Complete part/serial received: %s", SC.can_messages[dut["receive"]])

    # Check PBL/SBL session
    if mode_is_pbl:
        result = eda0_result and SUTE.test_message(SC.can_messages[dut["receive"]],
                                                                  teststring='F121')
    else:
        result = eda0_result and SUTE.test_message(SC.can_messages[dut["receive"]],
                                                                  teststring='F122')
    return result


def download_and_activate_sbl(dut):
    """
    Download and activation of SBL
    Args:
        dut (Dut): An instance of Dut
    Returns:
        (bool): True on SBL activation
    """
    # Loads the rig specific VBF files
    vbf_result = SSBL.get_vbf_files()
    if not vbf_result:
        logging.error("Test Failed: Unable to load VBF files")
        return False

    # Download and activate SBL
    sbl_result = SSBL.sbl_dl_activation(dut, sa_keys=dut.conf.default_rig_config)
    if not sbl_result:
        logging.error("Test Failed: SBL activation failed")
        return False

    logging.info("SBL activation successful")
    return True


def step_1(dut: Dut):
    """
    action: Read DID 'F186' and verify active diagnostic session is default
    expected_result: True on successfully verifying active diagnostic session as default
    """
    return verify_active_diagnostic_session(dut, mode=1, session='default')


def step_2(dut: Dut):
    """
    action: Read DID 'F186' and verify active diagnostic session is extended
    expected_result: True on successfully verifying active diagnostic session as extended
    """
    # Set to extended session
    dut.uds.set_mode(3)

    return verify_active_diagnostic_session(dut, mode=3, session='extended')


def step_3(dut: Dut):
    """
    action: Read DID 'F186' and verify active diagnostic session is programming
    expected_result: True on successfully verifying active diagnostic session as programming in
                     both PBL and SBL
    """
    # Set to programming session
    dut.uds.set_mode(2)

    result = verify_pbl_sbl_session(dut, mode_is_pbl=True)
    if not result:
        return False

    result = verify_active_diagnostic_session(dut, mode=2, session='programming')
    if not result:
        return False

    result = download_and_activate_sbl(dut)
    if not result:
        return False

    result = verify_pbl_sbl_session(dut, mode_is_pbl=False)
    if not result:
        return False

    return verify_active_diagnostic_session(dut, mode=2, session='programming')


def run():
    """
    Verify positive response and validate the data in all sessions by reading DID 'F186' using
    ReadDataByIdentifier(0x22) service
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=100)

        result_step = dut.step(step_1, purpose="Read DID 'F186' and verify active diagnostic"
                                               " session is default")
        if result_step:
            result_step = dut.step(step_2, purpose="Read DID 'F186' and verify active diagnostic"
                                                   " session is extended")
        if result_step:
            result_step = dut.step(step_3, purpose="Read DID 'F186' and verify active diagnostic"
                                                   " session is programming")
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
