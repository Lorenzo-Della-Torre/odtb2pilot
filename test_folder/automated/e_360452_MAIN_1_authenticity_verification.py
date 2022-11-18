"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 360452
version: 1
title: Authenticity verification at software download (Program mode)
purpose: >
    Verifying code after a software download (at installation) is the minimum level of the concept.

description: >
   The authenticity verification function shall always be performed at software download
   (installation).

details: >
    Check authenticity verification function
    Steps:
        1. Download and activate SBL
        2. Verify complete and compatible messages are different before and after check memory
        3. Download remaining software parts and check complete and compatibility
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_can import SupportCAN
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_service31 import SupportService31

SC = SupportCAN()
SSBL = SupportSBL()
SE31 = SupportService31()


def check_not_complete_and_compatible_routine(dut):
    """
    Check the not complete and compatible routine
    Args:
        dut (Dut): An instance of Dut
    Returns:
        (bool): True when complete and compatible routine return 'Not Complete, Compatible'
    """
    result = SSBL.check_complete_compatible_routine(dut, stepno=2)
    result = result and (SSBL.pp_decode_routine_complete_compatible(
                         SC.can_messages[dut["receive"]][0][2]) == 'Not Complete, Compatible')
    if not result:
        logging.error("Test Failed: Complete and compatible routine does not return "
                     "'Not Complete, Compatible'")
        return False

    return True


def step_1(dut):
    """
    action: Download and activate SBL
    expected_result: SBL should be activated
    """
    # Load the VBF files
    vbf_result = SSBL.get_vbf_files()
    if not vbf_result:
        logging.error("Test Failed: Unable to load VBF files")
        return False

    # Download and activate SBL
    sbl_result = SSBL.sbl_activation(dut, sa_keys=dut.conf.default_rig_config)
    if not sbl_result:
        logging.error("Test Failed: SBL activation failed")
        return False

    logging.info("SBL activation successful")
    return True


def step_2(dut):
    """
    action: Verify complete and compatible messages are different before and after check memory
    expected_result: Complete and compatible messages should be different before and after
                     check memory
    """
    # Download ESS software part without check
    ess_result, vbf_header = SSBL.sw_part_download_no_check(dut, SSBL.get_ess_filename(),
                                                            stepno='2')
    if not ess_result:
        logging.error("Test Failed: ESS download (without check) failed")
        return False

    result = check_not_complete_and_compatible_routine(dut)
    if not result:
        return False

    res_before_check_memory = SC.can_messages[dut["receive"]][0][2]

    result = SE31.check_memory(dut, vbf_header, stepno=2)
    result = result and (SSBL.pp_decode_routine_check_memory(SC.can_messages[dut["receive"]][0][2])
                                                             == 'The verification is passed')
    if not result:
        logging.error("Test Failed: Expected response 'The verification is passed' from check "
                      "memory routine but not received")
        return False

    result = check_not_complete_and_compatible_routine(dut)
    if not result:
        return False

    res_after_check_memory = SC.can_messages[dut["receive"]][0][2]

    result = bool(res_after_check_memory != res_before_check_memory)
    if not result:
        logging.error("Test Failed: Complete and compatible message before check memory: %s is "
                      "same as complete and compatible message after check memory: %s ",
                      res_before_check_memory, res_after_check_memory)
        return False

    logging.info("Complete and compatible message before check memory: %s is different from "
                 "complete and compatible message after check memory: %s ",
                 res_before_check_memory, res_after_check_memory)
    return True


def step_3(dut):
    """
    action: Download remaining software parts and check complete and compatibility
    expected_result: Downloaded software should be complete and compatible
    """
    result = True
    for swp in SSBL.get_df_filenames():
        result = result and SSBL.sw_part_download(dut, swp, stepno='3')

    if not result:
        logging.error("Test Failed: Unable to download remaining software parts")
        return False

    logging.info("Successfully downloaded remaining software parts")

    # Check complete and compatibility
    cc_result = SSBL.check_complete_compatible_routine(dut, stepno=3)
    if not cc_result:
        logging.error("Test Failed: Downloaded software is not complete and compatible")
        return False

    logging.info("Downloaded software is complete and compatible")
    return True


def step_4(dut):
    """
    action: ECU hard reset and verify default session
    expected_result: ECU should be in default session
    """
    # ECU reset
    dut.uds.ecu_reset_1101()

    # Verify active diagnostic session
    response = dut.uds.active_diag_session_f186()
    if response.data["details"]["mode"] == 1:
        logging.info("ECU is in default session as expected")
        return True

    logging.error("Test Failed: ECU is not in default session")
    return False


def run():
    """
    Check authenticity verification function
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=600)

        result_step = dut.step(step_1, purpose='Download and activate SBL')
        if result_step:
            result_step = dut.step(step_2, purpose='Verify complete and compatible messages are '
                                                   'different before and after check memory')
        if result_step:
            result_step = dut.step(step_3, purpose='Download remaining software parts and check '
                                                   'complete and compatibility')
        if result_step:
            result_step = dut.step(step_4, purpose='ECU hard reset and verify default session')

        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
