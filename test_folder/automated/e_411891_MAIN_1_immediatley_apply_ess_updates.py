"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 411891
version: 1
title: Immediately apply ESS update
purpose: >
    The ESS is downloaded as any other software parts. For example, an ECU reset cannot be added
    to the programming sequence every time an ESS is updated.

description: >
    The ESS updates must be applied immediately after being verified correctly, i.e. an
    initiation of the bootloader must not be required. This means that another software part
    (e.g. EXE) shall be possible to program next to the ESS without requiring an ECU reset.

details: >
    Verify another software download next to the ESS without requiring an ECU reset
"""


import logging
import hilding.flash as swdl
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_can import SupportCAN
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service11 import SupportService11
from supportfunctions.support_SBL import SupportSBL

SSBL = SupportSBL()
SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
SE11 = SupportService11()
SE22 = SupportService22()


def step_1(dut: Dut):
    """
    action: Download and activation of SBL
    expected_result: True on SBL activation
    """
    # Loads the rig specific VBF files
    vbf_result = swdl.load_vbf_files(dut)
    if not vbf_result:
        return False

    # Download and activate SBL on the ECU
    sbl_result = swdl.activate_sbl(dut)
    if not sbl_result:
        logging.error("Test Failed: SBL activation failed")
        return False

    logging.info("SBL activation successful")
    return True


def step_2(dut: Dut):
    """
    action: Download ESS software part
    expected_result: True on successful download
    """
    # Download the ESS file to the ECU
    ess_result = swdl.download_ess(dut)
    if not ess_result:
        logging.error("Test Failed: ESS Download failed")
        return False

    logging.info("ESS download successful")
    return True


def step_3(dut):
    """
    action: Verify active diagnostic session
    expected_result: True when ECU is in programming session
    """
    # Check programming session
    active_session = SE22.read_did_f186(dut, b'\x02')
    if not active_session:
        logging.error("Test Failed: ECU is not in programming session")
        return False

    logging.info("ECU is in programming session as expected")
    return True


def step_4(dut: Dut):
    """
    action: Download the application and data to the ECU
    expected_result: True on successful download
    """
    # Download the application and data to the ECU
    app_data_result = swdl.download_application_and_data(dut)
    if not app_data_result:
        logging.error("Test Failed: Application and data download failed")
        return False

    logging.info("Application and data download successful")
    return True


def step_5(dut: Dut):
    """
    action: Check complete & compatibility and do ECU hardreset
    expected_result: True when ECU is in default session
    """
    # Complete and Compatible check
    result = SSBL.check_complete_compatible_routine(dut, stepno=105)
    if not result:
        return False

    logging.info("Downloaded software is complete and compatible")

    # ECU reset
    result = SE11.ecu_hardreset_5sec_delay(dut, stepno=105)
    if not result:
        return False

    # Verify active diagnostic session
    result = SE22.read_did_f186(dut, dsession=b'\x01', stepno=105)
    if not result:
        logging.error("Test Failed: ECU is not in default session")
        return False

    logging.info("ECU is in default session as expected")
    return True


def run():
    """
    Verify another software download next to the ESS without requiring an ECU reset
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=600)

        result_step = dut.step(step_1, purpose='Download and activation of SBL')
        if result_step:
            result_step = dut.step(step_2, purpose='Download ESS software part')
        if result_step:
            result_step = dut.step(step_3, purpose='Verify active diagnostic session')
        if result_step:
            result_step = dut.step(step_4, purpose='Download the application and data to the ECU')
        if result_step:
            result_step = dut.step(step_5, purpose='Check complete & compatibility and do ECU '
                                                   'hardreset')
        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
