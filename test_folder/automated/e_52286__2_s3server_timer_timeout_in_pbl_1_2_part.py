"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 52286
version: 2
title: S3Server timer timeout in PBL
purpose: >
    To define the behaviour when S3server times out in PBL.

description: >
    If S3server times out when running PBL, the ECU shall make a test on Complete and Compatible
    function and if Complete and Compatible function returns PASSED the ECU shall make a reset

    The S3server is defined in LC : VCC UDS Session generic reqs.

details: >
    Verify S3server times out when running PBL and also verify complete and compatible function:
    Steps:
        1. SBL activation and download ESS
        2. Verify downloaded software is not complete, compatible
        3. Verify ECU is in PBL after delay more than timeout
        4. ECU hard reset and activate SBL
        5. Download the remaining software parts and check complete and compatibility
        6. ECU hard reset and verify active diagnostic session
"""

import time
import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_can import SupportCAN
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service3e import SupportService3e
from supportfunctions.support_file_io import SupportFileIO

SIO = SupportFileIO()
SC = SupportCAN()
SSBL = SupportSBL()
SE22 = SupportService22()
SE3E = SupportService3e()


def step_1(dut: Dut):
    """
    action: SBL activation and download ESS
    expected_result: Should successfully download ESS after SBL activation
    """
    SSBL.get_vbf_files()
    result = SSBL.sbl_activation(dut, sa_keys=dut.conf.default_rig_config)
    if not result:
        logging.error("Test Failed: SBL activation not successful")
        return False

    result = SSBL.sw_part_download(dut, SSBL.get_ess_filename())
    if not result:
        logging.error("Test Failed: ESS download not successful")
        return False

    logging.info("Successfully downloaded ESS after SBL activation")
    return True


def step_2(dut: Dut):
    """
    action: Verify downloaded software is not complete, compatible
    expected_result: Downloaded software should be 'Not Complete, Compatible'
    """
    result = SSBL.check_complete_compatible_routine(dut, stepno=102)
    result = result and (SSBL.pp_decode_routine_complete_compatible
                        (SC.can_messages[dut["receive"]][0][2])
                        == 'Not Complete, Compatible')
    if not result:
        logging.error("Test Failed: Expected 'Not Complete, Compatible', received %s",
                       SC.can_messages[dut["receive"]][0][2])
        return False

    logging.info("Downloaded software is 'Not Complete, Compatible' as expected")
    return True


def step_3(dut: Dut):
    """
    action: Verify ECU is in PBL after delay more than timeout
    expected_result: ECU should be in PBL after delay more than timeout
    """
    logging.info("Stop sending tester present.")
    SE3E.stop_periodic_tp_zero_suppress_prmib()

    logging.info("Wait longer than timeout for staying in current mode.")
    time.sleep(6)

    # Verify ECU is still in PBL
    result =  SE22.verify_pbl_session(dut)
    if not result:
        logging.error("Test Failed: ECU is not in PBL")
        return False

    logging.info("Wait longer than timeout for staying in current mode.")
    time.sleep(6)

    # Verify ECU is still in PBL
    result =  SE22.verify_pbl_session(dut)
    if not result:
        logging.error("Test Failed: ECU is not in PBL")
        return False

    # Start periodic tester present
    SE3E.start_periodic_tp_zero_suppress_prmib(dut, dut.conf.rig.signal_tester_present, 1.02)
    return True


def step_4(dut: Dut):
    """
    action: ECU hard reset and activate SBL
    expected_result: SBL should be activated
    """
    # ECU hard reset
    dut.uds.ecu_reset_1101()

    result = SSBL.sbl_activation(dut, sa_keys=dut.conf.default_rig_config)
    if not result:
        logging.error("Test Failed: SBL activation not successful")
        return False

    logging.info("SBL activation successful")
    return True


def step_5(dut: Dut):
    """
    action: Download the remaining software parts and check complete and compatibility
    expected_result: Downloaded software should be complete and compatible
    """
    result = SSBL.sw_part_download(dut, SSBL.get_ess_filename())
    for swp in SSBL.get_df_filenames():
        result = result and SSBL.sw_part_download(dut, swp, stepno=105)

    if not result:
        logging.error("Test Failed: Unable to download the remaining software parts")
        return False

    result = SSBL.check_complete_compatible_routine(dut, stepno=105)
    if not result:
        logging.error("Test Failed: Downloaded software is not complete and compatible")
        return False

    logging.info("Downloaded software is complete and compatible")
    return True


def step_6(dut: Dut):
    """
    action: ECU hard reset and verify active diagnostic session
    expected_result: ECU should be in default session
    """
    # ECU hard reset
    dut.uds.ecu_reset_1101()

    # Verify active diagnostic session
    response = dut.uds.active_diag_session_f186()
    if response.data["details"]["mode"] == 1:
        logging.info("ECU is in default session as expected")
        return True

    logging.error("Test Failed: Expected ECU to be in default session, received mode %s",
                   response.data["details"]["mode"])
    return False


def run():
    """
    Verify S3server times out when running PBL and also verify complete and compatible function
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=600)

        result_step = dut.step(step_1, purpose="SBL activation and download ESS")
        if result_step:
            result_step = dut.step(step_2, purpose="Verify downloaded software is not complete,"
                                                   " compatible")
        if result_step:
            result_step = dut.step(step_3, purpose="Verify ECU is in PBL after delay more than"
                                                   " timeout")
        if result_step:
            result_step = dut.step(step_4, purpose="ECU hard reset and activate SBL")
        if result_step:
            result_step = dut.step(step_5, purpose="Download the remaining software parts and"
                                                   " check complete and compatibility")
        if result_step:
            result_step = dut.step(step_6, purpose="ECU hard reset and verify active diagnostic"
                                                   " session")
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
