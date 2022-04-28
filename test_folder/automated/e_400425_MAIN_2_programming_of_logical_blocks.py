"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 400425
version: 2
title: Programming of Logical Blocks
purpose: >
    Define properties for a logical block, that are required for the ECU to be able to manage each
    logical block independently but also to simplify the signing process at the trust centre.

description: >
    Each logical block shall be possible to sign separately, i.e. each logical block must be
    possible to erase, program and verify independently in the ECU.

details: >
    All logical blocks of a VBF are signed separately.
"""

import logging
import time
from os import listdir
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_sec_acc import SecAccessParam
from supportfunctions.support_service3e import SupportService3e

SSBL = SupportSBL()
SS3E = SupportService3e()


def load_vbf_files(dut):
    """Loads the rig specific VBF files found in rigs/<default-rig-name>/VBFs

    Args:
        dut (Dut): An instance of Dut

    Returns:
        boolean: True if vbfs were loaded successfully, otherwise False
    """
    logging.info("~~~~~~~~ Loading VBFs started ~~~~~~~~")
    vbfs = listdir(dut.conf.rig.vbf_path)

    paths_to_vbfs = [str(dut.conf.rig.vbf_path) + "/" + x for x in vbfs]

    if not paths_to_vbfs:
        logging.error("VBFs not found, expected in %s ... aborting", dut.conf.rig.vbf_path)
        return False

    result = SSBL.read_vbf_param(paths_to_vbfs)

    return result


def activate_sbl(dut):
    """Downloads and activates SBL on the ECU using supportfunction from support_SBL

    Args:
        dut (Dut): An instance of Dut

    Returns:
        boolean: Result from support_SBL.sbl_activation.
        Should be True if sbl is activated successfully,
        otherwise False
    """
    logging.info("~~~~~~~~ Activate SBL started ~~~~~~~~")

    # Setting up keys
    sa_keys: SecAccessParam = dut.conf.default_rig_config

    # Activate SBL
    result = SSBL.sbl_activation(dut, sa_keys)

    return result


def download_ess(dut):
    """
    Download the ESS file to the ECU

    Args:
        dut (Dut): An instance of Dut

    Returns:
        boolean: True if download software part was successful, otherwise False
    """

    if SSBL.get_ess_filename():
        logging.info("~~~~~~~~ Download ESS started ~~~~~~~~")

        purpose = "Download ESS"
        result = SSBL.sw_part_download(dut, SSBL.get_ess_filename(),
                                       purpose=purpose)

    else:
        result = True
        logging.info("ESS file not needed for this project, skipping...")

    return result


def download_application_and_data(dut):
    """Download the application to the ECU

    Args:
        dut (Dut): An instance of Dut

    Returns:
        boolean: True of download was successful, otherwise False
    """

    logging.info("~~~~~~~~ Download application and data started ~~~~~~~~")
    result = True
    purpose = "Download application and data"
    for vbf_file in SSBL.get_df_filenames():
        result = result and SSBL.sw_part_download(dut, vbf_file, purpose=purpose)

    return result


def check_complete_and_compatible(dut):
    """Run complete and compatible routine

    Args:
        dut (Dut): Instance of Dut

    Returns:
        boolean: Result of complete and compatible
    """
    logging.info("~~~~~~~~ Check Complete And Compatible started ~~~~~~~~")

    return SSBL.check_complete_compatible_routine(dut, stepno=1)


def software_download(dut):
    """The function that handles all the sub-steps when performing software download.
    This function will keep track of the progress and give error indications if a step fails

    Args:
        dut (Dut): An instance of Dut

    Returns:
        boolean: Result of software download
    """

    # Load vbfs
    vbf_result = load_vbf_files(dut)

    logging.info("~~~~~~ Step 1/5 of software download (loading vbfs) done."
    " Result: %s", vbf_result)

    if vbf_result is False:
        logging.error("Aborting software download due to problems when loading VBFs")
        return False

    # Activate sbl
    sbl_result = activate_sbl(dut)

    logging.info("Step 2/5 of software download (downloading and activating sbl) done."
    " Result: %s", sbl_result)

    if sbl_result is False:
        logging.error("Aborting software download due to problems when activating SBL")
        return False

    # Download ess (if needed)
    ess_result = download_ess(dut)

    logging.info("Step 3/5 of software download (downloading ess) done. \
     Result: %s", ess_result)

    if ess_result is False:
        logging.error("Aborting software download due to problems when downloading ESS")
        return False

    # Download application and data
    app_result = download_application_and_data(dut)

    logging.info("Step 4/5 of software download (downloading application and data) done."
    " Result: %s", app_result)

    if app_result is False:
        logging.error("Aborting software download due to problems when downloading application")
        return False

    # Check Complete And Compatible
    check_result = check_complete_and_compatible(dut)

    logging.info("Step 5/5 of software download (Check Complete And Compatible) done."
    " Result: %s", check_result)

    if check_result is False:
        logging.error("Aborting software download due to problems when checking C & C")
        return False

    # Check that the ECU ends up in mode 1 (default session)
    SS3E.stop_periodic_tp_zero_suppress_prmib()
    time.sleep(10)
    uds_response = dut.uds.active_diag_session_f186()
    mode = uds_response.data['details'].get('mode')
    correct_mode = True
    if mode != 1:
        logging.error("Software download complete "
        "but ECU did not end up in mode 1 (default session), current mode is: %s", mode)
        correct_mode = False

    return correct_mode


def step_1(dut: Dut):
    """
    action: Software Download

    expected_result: True on successful download
    """
    result = software_download(dut)

    if result:
        logging.info("Software download successful")
        return True

    logging.error("Test Failed: Software download failed")
    return False


def run():
    """
    All logical blocks of a VBF are signed separately.
    """
    dut = Dut()
    start_time = dut.start()
    result = False

    try:
        dut.precondition(timeout=800)
        result = dut.step(step_1, purpose='Verify current Software is Downloaded'
                                            ' and signed separately.')

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
