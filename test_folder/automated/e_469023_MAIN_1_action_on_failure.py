"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 469023
version: 1
title: Action on failure
purpose: >
	Prevent any further operations after a Secure Boot verification failure.

description: >
    If the Secure Boot verification process for any reason fails, the system shall be halted. To
    avoid valuable information for an attacker, no further information shall be provided by the
    system. The exact cause, state or reason for boot failure must only be available for OEM
    approved developers using proper debug equipment that complies with the secure debug concept.

details: >
    Modify application VBF and verify ECU ends up in mode 2 (programming session) after restart
    as secure boot fails.
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
import hilding.flash as swdl
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_service31 import SupportService31

SSBL = SupportSBL()
SE31 = SupportService31()


def step_1(dut: Dut):
    """
    action: Software download
    expected_result: ECU should be in default session after successful software download
    """
    result = swdl.software_download(dut)
    if result:
        logging.info("Software download successful")
        return True

    logging.error("Test Failed: Software download failed")
    return False


def step_2(dut: Dut):
    """
    action: Download and activate SBL
    expected_result: SBL should be successfully activated
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


def step_3(dut: Dut):
    """
    action: Send routine control(erase memory) to erase one block of the application software
    expected_result: One block of the application software should be erased
    """
    # Read VBF files for application file
    _, vbf_header, _, _ = SSBL.read_vbf_file(SSBL.get_df_filenames()[0])
    SSBL.vbf_header_convert(vbf_header)

    # Verify programming preconditions
    result = SE31.routinecontrol_requestsid_flash_erase(dut, header=vbf_header)
    if not result:
        logging.error("Test Failed: Routine control(erase memory) unsuccessful")
        return False

    return True


def step_4(dut: Dut):
    """
    action: ECU hardreset and verify active diagnostic session
    expected_result: ECU should be in programming session after ECU hard reset
    """
    # ECU reset
    result = dut.uds.ecu_reset_1101()
    if not result:
        logging.error("Test Failed: ECU reset failed")
        return False

    # Verify active diagnostic session
    active_session = dut.uds.active_diag_session_f186()
    if active_session.data["details"]["mode"] == 2:
        logging.info("ECU is in programming session as expected")
        return True

    logging.error("Test Failed: ECU is not in programming session")
    return False


def step_5(dut: Dut):
    """
    action: Software download
    expected_result: ECU should be in default session after successful software download
    """
    result = swdl.software_download(dut)
    if result:
        logging.info("Software download successful")
        return True

    logging.error("Test Failed: Software download failed")
    return False


def run():
    """
    Modify application VBF and verify ECU ends up in mode 2 (programming session) after restart
    as secure boot fails.
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=1500)

        result_step = dut.step(step_1, purpose='Software download')
        if result_step:
            result_step = dut.step(step_2, purpose='Download and activate SBL')
        if result_step:
            result_step = dut.step(step_3, purpose='Send routine control(erase memory) to erase '
                                                   'one block of the application software')
        if result_step:
            result_step = dut.step(step_4, purpose='ECU hardreset')
        if result_step:
            result_step = dut.step(step_5, purpose='Software download')
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
