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
import logging
import traceback
import inspect

from supportfunctions.support_service31 import SupportService31
from supportfunctions.support_SBL import SupportSBL
from hilding.dut import Dut
from hilding.dut import DutTestError
from hilding.uds import EicDid

from supportfunctions.support_can import SupportCAN, CanParam, PerParam
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_sec_acc import SupportSecurityAccess, SecAccessParam
from supportfunctions.support_file_io import SupportFileIO

from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_service11 import SupportService11
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service3e import SupportService3e

SIO = SupportFileIO
SC = SupportCAN()
SUTE = SupportTestODTB2()
SSBL = SupportSBL()
SSA = SupportSecurityAccess()

PREC = SupportPrecondition()
SE11 = SupportService11()
SE22 = SupportService22()
SE3E = SupportService3e()

def load_vbf_files(dut):
    logging.info("~~~~~~~~ Loading VBFs started ~~~~~~~~")
    vbfs = listdir(dut.conf.rig.vbf_path)

    paths_to_vbfs = [str(dut.conf.rig.vbf_path) + "/" + x for x in vbfs]

    if not paths_to_vbfs:
        logging.error("VBFs not found, expected in %s ... aborting", dut.conf.rig.vbf_path)
        return False

    result = SSBL.read_vbf_param(paths_to_vbfs)

    return result

def activate_sbl(dut):
    logging.info("~~~~~~~~ Activate SBL started ~~~~~~~~")

    # Setting up keys
    sa_keys: SecAccessParam = {
        "SecAcc_Gen": 'Gen1',
        "fixed_key": '0102030405',
        "auth_key": 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF',
        "proof_key": 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'
    }

    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), sa_keys)

    # Activate SBL
    result = SSBL.sbl_activation(dut,
                                 sa_keys)

    return result

def download_ess(dut):

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

    logging.info("~~~~~~~~ Download application and data started ~~~~~~~~")
    result = True
    purpose = "Download application and data"
    for vbf_file in SSBL.get_df_filenames():
        # if needed: actiate DID EDA0 to check which mode ecu is in:
        #result = result and SE22.read_did_eda0(can_p)
        result = result and SSBL.sw_part_download(dut, vbf_file, purpose=purpose)
    return result

def check_and_complete(dut):
    logging.info("~~~~~~~~ Check Complete And Compatible started ~~~~~~~~")

    return SSBL.check_complete_compatible_routine(dut)

def software_download(dut):

    # Load vbfs
    vbf_result = load_vbf_files(dut)

    logging.info("~~~~~~ Step 1/5 of software download (loading vbfs) done. \
     Result: %s", vbf_result)

    if vbf_result is False:
        logging.error("Aborting software download")
        return

    # Activate sbl
    sbl_result = activate_sbl(dut)

    logging.info("Step 2/5 of software download (downloading and activating sbl) done. \
     Result: %s", sbl_result)

    if sbl_result is False:
        logging.error("Aborting software download")
        return

    # Download ess (if needed)
    ess_result = download_ess(dut)

    logging.info("Step 3/5 of software download (downloading ess) done. \
     Result: %s", ess_result)

    if ess_result is False:
        logging.error("Aborting software download")
        return

    # Download application and data
    app_result = download_application_and_data(dut)

    logging.info("Step 4/5 of software download (downloading application and data) done. \
     Result: %s", app_result)

    if app_result is False:
        logging.error("Aborting software download")
        return

    # Check Complete And Compatible
    check_result = download_application_and_data(dut)

    logging.info("Step 5/5 of software download (Check Complete And Compatible) done. \
     Result: %s", check_result)

    if check_result is False:
        logging.error("Aborting software download")
        return



def flash():
    """ flash the ecu """
    dut = Dut()
    start_time = dut.start()
    result = False
    try:
        dut.precondition(timeout=3600)
        dut.step(software_download, purpose="Perform software download")
        result = True
    except: # pylint: disable=bare-except
        error = traceback.format_exc()
        logging.error("Software download failed: %s", error)
    finally:
        dut.postcondition(start_time, result)
