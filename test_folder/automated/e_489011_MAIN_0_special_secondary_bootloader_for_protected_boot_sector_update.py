"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 489011
version: 0
title: Special secondary bootloader for protected boot sector update
purpose: >
    Primary Bootloader update using special secondary bootloader(SSBL)

description: >
    The memory area of PBL with protected bootsectors shall be able to erase and update using
    Special Secondary bootloaders.

details: >
    Verify ECU stays in programming session after PBL is flashed using software download.
    Steps:
        1. Flash PBL using software download.
        2. Verify ECU stays in programming session.
        3. Re-flash the software.
"""

import time
import logging
from os import listdir
from hilding.dut import Dut
from hilding.dut import DutTestError
import hilding.flash as swdl
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_service27 import SupportService27

SSBL = SupportSBL()
SE27 = SupportService27()


def load_vbf_files(dut):
    """
    Loads the rig specific VBF files
    Args:
        dut (Dut): An instance of Dut
    Returns:
        (bool): True if vbfs were loaded successfully
    """
    logging.info("~~~~~~~~ Loading VBFs started ~~~~~~~~")

    rigs = dut.conf.rig.vbf_path
    pbl_vbf = listdir(rigs.joinpath('PBL_VBF'))
    pbl_vbf_path = [str(rigs.joinpath('PBL_VBF')) + "/" + x for x in pbl_vbf]

    vbf_path_dict = {}
    if len(pbl_vbf_path) > 0:
        # Iterate through all the files
        for vbf_file_path in pbl_vbf_path:
            # Read vbf file
            vbf_header = SSBL.read_vbf_file(vbf_file_path)[1]
            vbf_header = dict(vbf_header)

            if vbf_header['sw_part_type'] == 'SBL':
                vbf_path_dict['SBL'] = vbf_file_path
            elif vbf_header['sw_part_type'] == 'ESS':
                vbf_path_dict['ESS'] = vbf_file_path
            elif vbf_header['sw_part_type'] == 'EXE':
                vbf_path_dict['EXE'] = vbf_file_path

        if len(vbf_path_dict) > 0:
            return vbf_path_dict

        logging.error("Unable to extract VBF files")
        return None

    logging.error("No VBF file found in %s", pbl_vbf_path)
    return None


def activate_sbl(dut, vbf_path_sbl):
    """
    Downloads and activates SBL
    Args:
        dut (Dut): An instance of Dut
        vbf_path_sbl (str): SBL file path
    Returns:
        (bool): True if SBL is activated successfully
    """
    logging.info("~~~~~~~~ Activate SBL started ~~~~~~~~")

    # Set to programming session
    dut.uds.set_mode(2)

    # Sleep time to avoid NRC37
    time.sleep(5)

    result = SE27.activate_security_access_fixedkey(dut, sa_keys=dut.conf.default_rig_config)

    # SBL download
    if result:
        tresult, vbf_sbl_header = SSBL.sbl_download(dut, vbf_path_sbl)
        result = result and tresult

    # Activate SBL
    result = result and SSBL.activate_sbl(dut, vbf_sbl_header, stepno=101)

    return result


def download_ess(dut, vbf_path_ess):
    """
    Download the ESS file to the ECU
    Args:
        dut (Dut): An instance of Dut
        vbf_path_ess (str): ESS file path
    Returns:
        (bool): True if download software part was successful
    """
    logging.info("~~~~~~~~ Download ESS started ~~~~~~~~")
    return SSBL.sw_part_download(dut, vbf_path_ess, purpose="Download ESS")


def download_application(dut, vbf_path_exe):
    """
    Download the application to the ECU
    Args:
        dut (Dut): An instance of Dut
        vbf_path_exe (str): EXE file path
    Returns:
        (bool): True if download was successful
    """
    logging.info("~~~~~~~~ Download application started ~~~~~~~~")
    return SSBL.sw_part_download(dut, vbf_path_exe, purpose="Download application")


def software_download(dut):
    """
    The function that handles all the sub-steps when performing software download.
    This function will keep track of the progress and give error indications if a step fails
    Args:
        dut (Dut): An instance of Dut
    Returns:
        (bool): Result of software download
    """
    # Load vbfs
    vbf_path_dict = load_vbf_files(dut)
    if vbf_path_dict is None:
        logging.error("Aborting software download due to problems when loading VBFs")
        return False

    logging.info("Loading vbfs done, Result: %s", vbf_path_dict)

    # Activate sbl
    sbl_result = activate_sbl(dut, vbf_path_dict['SBL'])
    if sbl_result is False:
        logging.error("Aborting software download due to problems when activating SBL")
        return False

    logging.info("Downloading and activating sbl done, Result: %s", sbl_result)

    # Download ess
    ess_result = download_ess(dut, vbf_path_dict['ESS'])
    if ess_result is False:
        logging.error("Aborting software download due to problems when downloading ESS")
        return False

    logging.info("Downloading ess done, Result: %s", ess_result)

    # Download application
    app_result = download_application(dut, vbf_path_dict['EXE'])
    if app_result is False:
        logging.error("Aborting software download due to problems when downloading application")
        return False

    logging.info("Downloading application done, Result: %s", app_result)
    return True


def step_1(dut: Dut):
    """
    action: Software Download
    expected_result: PBL should be flashed successfully
    """
    result = software_download(dut)
    if result:
        logging.info("Software download successful")
        return True

    logging.error("Test Failed: Software download failed")
    return False


def step_2(dut: Dut):
    """
    action: Verify ECU is in programming session
    expected_result: ECU should be in programming session after flashing PBL
    """
    # Verify active diagnostic session
    active_session = dut.uds.active_diag_session_f186()
    if active_session.data["details"]["mode"] == 2:
        logging.info("ECU is in programming session as expected")
        return True

    logging.error("Test Failed: ECU is not in programming session")
    return False


def step_3(dut: Dut):
    """
    action: ECU hardreset and download software
    expected_result: ECU should be in default session after successful software download
    """
    # ECU hardreset
    dut.uds.ecu_reset_1101()

    # Set to programming session
    dut.uds.set_mode(2)
    time.sleep(5)

    result = swdl.software_download(dut)
    if result:
        logging.info("Software download successful")
        return True

    logging.error("Test Failed: Software download failed")
    return False


def run():
    """
    Verify ECU stays in programming session after PBL is flashed using software download
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False
    try:
        dut.precondition(timeout=900)

        result_step = dut.step(step_1, purpose="Change to programming session and flash PBL"
                                               " using software download")
        if result_step:
            result_step = dut.step(step_2, purpose="Verify ECU is in programming session")
        if result_step:
            result_step = dut.step(step_3, purpose='ECU hardreset and download software')
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)

if __name__ == '__main__':
    run()
