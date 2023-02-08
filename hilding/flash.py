"""
ECU software download

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""
from os import listdir
from os import path
from os import sep
import logging
import traceback
import time

from hilding.dut import Dut

from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_sec_acc import SecAccessParam

SSBL = SupportSBL()

def load_vbf_files(dut, pbl_vbf=False):
    """Loads the rig specific VBF files found in rigs/<default-rig-name>/VBFs

    Args:
        dut (Dut): An instance of Dut

    Returns:
        boolean: True if vbfs were loaded successfully, otherwise False
    """
    logging.info("~~~~~~~~ Loading VBFs started ~~~~~~~~")
    location = dut.conf.rig.vbf_path
    if pbl_vbf:
        location = dut.conf.rig.pbl_vbf_path
    vbfs = listdir(location)
    paths_to_vbfs = [str(location) + sep + x for x in vbfs if path.isfile(str(location)+ sep + x)]

    if not paths_to_vbfs:
        logging.error("VBFs not found, expected in %s ... aborting", location)
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
    result = SSBL.sbl_activation(dut,
                                 sa_keys)

    return result

def download_ess(dut):
    """Download the ESS file to the ECU

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

def software_download(dut, param="Software download"):
    """The function that handles all the sub-steps when performing software download.
    This function will keep track of the progress and give error indications if a step fails

    Args:
        dut (Dut): An instance of Dut

    Returns:
        boolean: Result of software download
    """
    for operation in param:

        step = 1

        # Define vbfs location and total steps of the operation
        if operation == "PBL update":
            pbl_vbf = True
            total_steps = 4
        else:
            pbl_vbf = False
            total_steps = 5

        # Load vbfs
        vbf_result = load_vbf_files(dut, pbl_vbf)

        logging.info("~~~~~~ Step %s/%s of software download (loading vbfs) done."
        " Result: %s\n\n", step, total_steps, vbf_result)
        step += 1

        if vbf_result is False:
            logging.error("Aborting %s due to problems when loading VBFs",operation)
            return False

        # Activate sbl
        sbl_result = activate_sbl(dut)

        logging.info("~~~~~~ Step %s/%s of software download (downloading and activating sbl) done."
        " Result: %s\n\n", step, total_steps, sbl_result)
        step += 1

        if sbl_result is False:
            logging.error("Aborting %s due to problems when activating SBL",operation)
            return False

        # Download ess (if needed)
        ess_result = download_ess(dut)

        logging.info("~~~~~~ Step %s/%s of software download (downloading ess) done. \
        Result: %s\n\n", step, total_steps, ess_result)
        step += 1

        if ess_result is False:
            logging.error("Aborting %s due to problems when downloading ESS", operation)
            return False

        # Download application and data
        app_result = download_application_and_data(dut)

        logging.info("~~~~~~ Step %s/%s of software download (downloading application and data) \
        done."
        " Result: %s\n\n", step, total_steps, app_result)
        step += 1

        if app_result is False:
            logging.error("Aborting %s due to problems when downloading application", operation)
            return False

        # Check Complete And Compatible
        if operation == "Software download":
            check_result = check_complete_and_compatible(dut)

            logging.info("~~~~~~ Step %s/%s of software download (Check Complete And Compatible) \
            done."
            " Result: %s\n\n", step, total_steps, check_result)

            if check_result is False:
                logging.error("Aborting %s due to problems when checking C & C",operation)
                return False

        # Check that the ECU ends up in expected mode
        dut.uds.ecu_reset_1101()
        time.sleep(5)
        uds_response = dut.uds.active_diag_session_f186()
        mode = uds_response.data['details'].get('mode')
        if (operation=="PBL update" and mode==2) or (operation=="Software download" and mode==1):
            logging.info("ECU ends up in mode %s as expected mode.",mode)
            correct_mode = True
        else:
            correct_mode = False
            logging.error("%s complete "
            "but ECU did not end up in expected mode, current mode is: %s",operation, mode)

    return correct_mode



def flash(operation):
    """Flashes the ECU with VBF files found in the rigs folder.
    If the script is executed on a remote computer the remote computers VBF files will be used.
    If executed locally on a hilding the VBF files on that hilding will be used.
    """
    dut = Dut()
    start_time = dut.start()

    result = False
    try:
        dut.precondition(timeout=1800)

        if operation == "PBL update":
            logging.info("----       Starting PBL update      ----")
            param = ["PBL update"]

        elif operation == "Software download":
            logging.info("----   Starting software download   ----")
            param = ["Software download"]

        elif operation == "PBL update and software download":
            logging.info("----       Starting PBL update      ----")
            param = ["PBL update","Software download"]

        purpose_text = "Perform " + operation
        result = dut.step(software_download, param, purpose=purpose_text)

    except: # pylint: disable=bare-except
        error = traceback.format_exc()
        logging.error("Software download failed: %s", error)

    finally:
        dut.postcondition(start_time, result)
