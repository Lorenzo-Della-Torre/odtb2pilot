"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 52287
version: 2
title: S3Server timer timeout in SBL
purpose: >
    To define the behaviour when the S3server times out in SBL

description: >
    When the S3server times out when running SBL, the ECU shall make a reset.

details: >
    Verify ECU will be in default session from SBL, for delay more than S3 server timeout.
    Also verify ECU will be in PBL from SBL, after software download for delay more than timeout.
"""

import time
import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service3e import SupportService3e
from supportfunctions.support_can import SupportCAN

SSBL = SupportSBL()
SE22 = SupportService22()
SE3E = SupportService3e()
SC = SupportCAN()


def step_1(dut: Dut):
    """
    action: Activate SBl and verify ECU is in SBL
    expected_result: ECU should be in SBL after successful activation of SBL
    """
    SSBL.get_vbf_files()
    result = SSBL.sbl_activation(dut, sa_keys=dut.conf.default_rig_config)
    if not result:
        logging.error("Test Failed: SBL activation failed")
        return False

    result = SE22.verify_sbl_session(dut)
    if not result:
        logging.error("Test Failed: ECU is not in SBL")
        return False

    logging.info("Successfully activate SBL and ECU is in SBL")
    return True


def step_2(dut: Dut):
    """
    action: Verify SBL after delay shorter than timeout
    expected_result: ECU should be in SBL after delay shorter than timeout
    """
    # Stop sending tester present
    SE3E.stop_periodic_tp_zero_suppress_prmib()

    # Waiting 4 seconds to send a diagnostic request just before S3 Server times out
    time.sleep(4)

    # Verify sbl
    result = SE22.verify_sbl_session(dut)
    if not result:
        logging.error("Test Failed: ECU is not in SBL")
        return False

    logging.info("ECU is in SBL after waiting shorter than timeout as expected")
    return True


def step_3(dut: Dut):
    """
    action: Verify ECU is in default session after delay more than timeout
    expected_result: ECU should be in default session after delay more than timeout
    """
    # Waiting 6 seconds to send a diagnostic request just after S3 Server times out
    time.sleep(6)

    # Verify active diagnostic session
    response = dut.uds.active_diag_session_f186()
    if response.data["details"]["mode"] == 1:
        logging.info("ECU is in default session as expected")
        return True

    logging.error("Test Failed: Expected ECU to be in default session, but it is in mode %s",
                  response.data["details"]["mode"])
    return False


def step_4(dut: Dut):
    """
    action: Software download and verify software is not complete, compatible
    expected_result: Downloaded software should not be complete, compatible
    """
    # SBl activation
    result = SSBL.sbl_activation(dut, sa_keys=dut.conf.default_rig_config)
    if not result:
        logging.error("Test Failed: ECU is not in SBL")
        return False

    # Software download
    result = SSBL.sw_part_download(dut, SSBL.get_ess_filename())
    if not result:
        logging.error("Test Failed: Software download is failed for ESS file")
        return False

    # Check complete and compatibility
    result = SSBL.check_complete_compatible_routine(dut, stepno=101)
    response = SSBL.pp_decode_routine_complete_compatible(SC.can_messages[dut["receive"]][0][2])
    result = result and (response == 'Not Complete, Compatible')
    if result:
        logging.info("Downloaded software is %s as expected", response)
        return True

    logging.error("Test Failed: Expected not complete, compatible, but software is %s", response)
    return False


def step_5(dut: Dut):
    """
    action: Verify ECU is in PBL after delay more than timeout
    expected_result: ECU should be in PBL after delay more than timeout
    """
    # Stop sending tester present
    SE3E.stop_periodic_tp_zero_suppress_prmib()

    # Waiting 6 seconds to send a diagnostic request just after S3 Server times out
    time.sleep(6)

    # Verify ECU is still in mode programming session
    result =  SE22.verify_pbl_session(dut)
    if not result:
        logging.error("Test Failed: ECU is not in PBL")
        return False

    # Start periodic tester present
    SE3E.start_periodic_tp_zero_suppress_prmib(dut, dut.conf.rig.signal_tester_present, 1.02)
    return True


def step_6(dut: Dut):
    """
    action: Software part download and check complete and compatibility
    expected_result: Downloaded software part should be complete and compatible
    """
    # ECU hard reset
    dut.uds.ecu_reset_1101()

    # SBl activation
    result = SSBL.sbl_activation(dut, sa_keys=dut.conf.default_rig_config)
    if not result:
        logging.error("Test Failed: SBL activation failed")
        return False

    # Software download
    result = SSBL.sw_part_download(dut, SSBL.get_ess_filename())
    if not result:
        logging.error("Test Failed: Software part download failed")
        return False

    logging.info("Software download successful")
    for swp in SSBL.get_df_filenames():
        result = result and SSBL.sw_part_download(dut, swp)

    # Check complete and compatible
    result = result and SSBL.check_complete_compatible_routine(dut, stepno=103)
    if not result:
        logging.error("Test Failed: Software is not complete and compatible")
        return False

    logging.info("Download software is complete and compatible as expected")
    # ECU hard reset
    dut.uds.ecu_reset_1101()
    return True


def run():
    """
    Verify S3 server timeout in SBL
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = True

    try:
        dut.precondition(timeout=1800)

        result_step = dut.step(step_1, purpose="Activate SBl and verify ECU is in SBL")
        if result_step:
            result_step = dut.step(step_2, purpose="Verify SBL after delay shorter than timeout")
        if result_step:
            result_step = dut.step(step_3, purpose="Verify ECU is in default session after delay "
                                                   "more than timeout")
        if result_step:
            result_step = dut.step(step_4, purpose="Software download and verify software is not "
                                                   "complete, compatible")
        if result_step:
            result_step = dut.step(step_5, purpose="Verify ECU is in PBL after delay more than "
                                                   "timeout")
        if result_step:
            result_step = dut.step(step_6, purpose="Software part download and check complete and "
                                                   "compatibility")
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
