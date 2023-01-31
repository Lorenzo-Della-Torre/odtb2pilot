"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 53935
version: 1
title: Validation of ECU Software(s)
purpose: >
    To prevent start of incomplete or incompatible software(s)

description: >
    The bootloader shall at every start check if the ECU software(s) is complete and compatible
    before starting execution of the application

details: >
    Download ECU software(s) and check complete and compatibility
"""

import time
import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_can import SupportCAN
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service3e import SupportService3e

SIO = SupportFileIO()
SC = SupportCAN()
SSBL = SupportSBL()
SE22 = SupportService22()
SE3E = SupportService3e()


def step_1(dut: Dut):
    """
    action: Load of ECU firmware partially
    expected_result: True when ECU firmware is partially loaded
    """
    SSBL.get_vbf_files()
    result = SSBL.sbl_activation(dut, sa_keys=dut.conf.default_rig_config)
    if not result:
        logging.error("Test Failed: SBL activation is failed")
        return False

    result = SSBL.sw_part_download(dut, SSBL.get_ess_filename())
    if not result:
        logging.error("Test Failed: ESS software part download is failed")
        return False

    logging.info("Successfully downloaded ESS software part after activation of SBL")
    return True


def step_2(dut: Dut):
    """
    action: Verify complete and compatibility checked at startup before execution of application
    expected_result: True when downloaded software is not complete, compatible
    """
    result = SSBL.check_complete_compatible_routine(dut, stepno=101)
    response = SC.can_messages[dut["receive"]][0][2]
    result = result and (SSBL.pp_decode_routine_complete_compatible
                        (response) == 'Not Complete, Compatible')
    if not result:
        logging.error("Test Failed: Expected not complete, compatible, received %s", response)
        return False

    logging.info("Downloaded software is not complete, compatible as expected")
    return True


def step_3(dut: Dut):
    """
    action: Restart ECU and Verify PBL
    expected_result: True when ECu is in PBL
    """
    # Stop sending tester present
    SE3E.stop_periodic_tp_zero_suppress_prmib()

    time.sleep(6)

    # Start periodic tester present
    SE3E.start_periodic_tp_zero_suppress_prmib(dut,
                                               SIO.extract_parameter_yml("precondition","tp_name"),
                                               periodic=1.02)

    # Verify ECU is still in mode prog session
    result =  SE22.verify_pbl_session(dut)
    if not result:
        logging.error("Test Failed: ECU is not in PBL")
        return False

    logging.info("ECU is in PBL as expected")
    return True


def step_4(dut: Dut):
    """
    action: Restore ECU firmware to complete and compatible
    expected_result: True when ECU firmware is complete and compatible
    """
    result = SSBL.sbl_activation(dut, sa_keys=dut.conf.default_rig_config)
    if not result:
        logging.error("Test Failed: SBL activation failed")
        return False

    logging.info("Successfully activate SBL")

    result = SSBL.sw_part_download(dut, SSBL.get_ess_filename())
    for swp in SSBL.get_df_filenames():
        result = result and SSBL.sw_part_download(dut, swp, stepno=112)

    if not result:
        logging.error("Test Failed: Unable to restore ECU firmware")
        return False

    logging.info("Successfully restore ECU firmware")
    return True


def step_5(dut):
    """
    action: Verify complete and compatibility is done at startup
    expected_result: True when C&C is done and ECU is in default session
    """
    result = SSBL.check_complete_compatible_routine(dut, stepno=102)
    response = SC.can_messages[dut["receive"]][0][2]
    result = result and (SSBL.pp_decode_routine_complete_compatible
                        (response) == 'Complete, Compatible')
    if not result:
        logging.error("Test Failed: Expected complete, compatible, received %s", response)
        return False

    logging.info("Downloaded software is complete, compatible as expected")

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
    Download ECU software(s) and check complete and compatibility
    """
    dut = Dut()

    start_time = dut.start()
    result = False

    try:
        dut.precondition(timeout=900)

        result = dut.step(step_1, purpose="Load of ECU firmware partially")
        result = result and dut.step(step_2, purpose="Verify complete and compatibility checked "
                                                     "at startup before execution of application")
        result = result and dut.step(step_3, purpose="Restart ECU and Verify PBL")
        result = dut.step(step_4, purpose="Restore ECU firmware to complete and compatible") and \
                 result
        result = result and dut.step(step_5, purpose="Verify complete and compatibility is done "
                                                     "at startup")

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
