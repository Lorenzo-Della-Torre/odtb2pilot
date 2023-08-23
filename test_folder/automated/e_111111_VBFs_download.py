"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 405051
version: 1
title: CompleteCompatibleFunction - error handling
purpose: >
    Define a error handling strategy, where a restricted approach is applied meaning that the
    application must not be started unless it is proven to be valid.

description: >
    In case of an unexpected fault during the CompleteCompatibleFunction() that prevents the
    function to be completed and the root cause cannot be derived to a specific software part,
    the ECU shall be considered as not complete (or not compatible respectively, dependent of
    the check that was not completed). This shall be indicated in the response to the
    routineIdentifier (Check Complete & Compatible) request. If the bootloader cannot identify
    which part that failed the verification, the bit for the Executable shall be set.

details: >
    Software download request for VBF file types and verify which part of software
    download has failed.
    Steps-
        1. Download SBL and old relaese DATA vbf file and verify Compatible bit is 1
        2. Download SBL and ESS and verify Complete & EXE bit set to 1
        3. Download SBL and empty ESS and verify ESS bit set to 1
        4. Restore ECU
"""

import logging
import time
from os import listdir, path
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_can import CanParam
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_service31 import SupportService31
from supportfunctions.support_can import SupportCAN
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_service3e import SupportService3e
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_service10 import SupportService10
from supportfunctions.support_service11 import SupportService11

SE11 = SupportService11()
SE10 = SupportService10()
SE22 = SupportService22()
SE27 = SupportService27()
SS3E = SupportService3e()
SIO = SupportFileIO()
SSBL = SupportSBL()
SE31 = SupportService31()
SC = SupportCAN()


def filter_vbf_files(file_paths, old_vbf_flag):
    """
    Filter VBF file path based on VBF type
    Args:
        file_paths (list): VBF file paths
        old_vbf_flag(bool): True to get previous release DATA vbf file
    Returns:
        vbf_path_list (list): filtered VBF paths
    """
    vbf_path_list = []
    if len(file_paths) > 0:
        # Iterate through all the files
        for vbf_file_path in file_paths:
            # Read vbf file
            if path.isdir(vbf_file_path):
                continue
            vbf_header = SSBL.read_vbf_file(vbf_file_path)[1]
            vbf_header = dict(vbf_header)

            # Compare vbf header 'sw_part_type' with 'DATA' and get the file path
            if old_vbf_flag:
                if vbf_header['sw_part_type'] == 'DATA':
                    vbf_path_list.append(vbf_file_path)
            else:
                if vbf_header['sw_part_type'] != 'DATA':
                    vbf_path_list.append(vbf_file_path)

        if len(vbf_path_list) > 0:
            return vbf_path_list

        logging.error("Unable to extract VBF files")
        return None

    logging.error("No VBF file found in %s", file_paths)
    return None

def cr8_paths_to_vbfs(dut):
    """
    """
    vbfs = listdir(str(dut.conf.rig.vbf_path)+ "/vbf_list_ecm")
    #paths_to_vbfs = [str(dut.conf.rig.vbf_path) + "/" + x for x in vbfs]
    #vbfs = listdir("C:/tmp")
    vbfs.sort()
    paths_to_vbfs=[]
    for i in range(0, len(vbfs)-1, 2):
        paths_to_vbfs.append([ str(dut.conf.rig.vbf_path) + "/vbf_list_ecm" + "/" + vbfs[i],str(dut.conf.rig.vbf_path)+ "/vbf_list_ecm" + "/" +  vbfs[i+1]])
    logging.info("the path list is %s", paths_to_vbfs)

    if not paths_to_vbfs:
        logging.error("VBFs file not found, expected in %s ... aborting", paths_to_vbfs)
        return False
    return paths_to_vbfs   


def load_vbf_files(path_to_vbfs):
    """
    Loads the rig specific VBF files found in rigs/<default-rig-name>/VBFs or
    in vbf_old (previous release vbf files)

    Args:
        dut (Dut): An instance of Dut
        parameters(dict): previous release vbf directory name
        old_vbf_data_flag (bool): True to get previous release VBF paths
    Returns:
        boolean: True if vbfs were loaded successfully, otherwise False
    """
    logging.info("~~~~~~~~ Loading VBFs started ~~~~~~~~")

    result = SSBL.read_vbf_param(path_to_vbfs)

    return result


def download_application_data(dut):
    """
    Download data and EXE VBFs type to the ECU
    Args:
        dut (Dut): An instance of Dut
    Returns:
        boolean: True when software download is successful, otherwise False
    """

    logging.info("~~~~~~~~ Download software started ~~~~~~~~")
    result = True
    for vbf_file in SSBL.get_df_filenames():
        result = result and SSBL.sw_part_download_no_check(dut, vbf_file)
    if result:
        logging.info("Software download successful")
        return True

    logging.error("Software download failed")
    return False


def software_download(dut:Dut, ess_flag=False, exe_data_flag=False):
    """
    Software download(SWDL) for SBL, ESS DATA and EXE VBF file type
    Args:
        dut (Dut): An instance of Dut
        ess_flag(bool): True to download ESS vbf type
        exe_data_flag(bool): True to download application
    Returns:
        (bool): True on successful software download
    """
    '''# Activate sbl
    sbl_result = SSBL.sbl_activation(dut, sa_keys=dut.conf.default_rig_config)

    logging.info("Software download (downloading and activating sbl) completed."
                 " Result: %s", sbl_result)

    if sbl_result is False:
        logging.error("Aborting software download due to problems when activating SBL")
        return False'''
    SE10.diagnostic_session_control_mode2(dut)
    time.sleep(1)
    ecu_mode = SE22.get_ecu_mode(dut)
    if ecu_mode == 'PBL':
        # Security Access Request SID
        SE27.activate_security_access_fixedkey(dut, sa_keys=dut.conf.default_rig_config)
    else:
        SE10.diagnostic_session_control_mode2(dut)
        time.sleep(1)
        ecu_mode = SE22.get_ecu_mode(dut)
        if ecu_mode == 'PBL':
            # Security Access Request SID
            SE27.acrivate_security_aaccess_fixedkey(dut, sa_keys=dut.conf.default_rig_config)

    # Download ess (if needed)
    if ess_flag:
        ess_result = SSBL.sw_part_download(dut, SSBL.get_ess_filename(), purpose="Download ESS")

        logging.info("Software download (downloading ess) completed. Result: %s", ess_result)

        if ess_result is False:
            logging.error("Aborting software download due to problems when downloading ESS")
            return False

    # Download application and data when exe_data_flag is True
    if exe_data_flag:
        # When data_flag is True download only data otherwise both
        app_result = download_application_data(dut)
        logging.info("Software download (downloading application and data) completed."
                    " Result: %s", app_result)

        if app_result is False:
            logging.error("Aborting software download due to problems when downloading "
                          "application")
            return False

    return True

def step_1(dut: Dut):
    """
    action: Download Software VBFs file type and previous release DATA VBF file
            and verify which part of downloaded software is Complete and Compatible

    expected_result: True when downloaded software is Complete(bit 0) and Compatible(bit 1)
    """

    '''# Read yml parameters
    parameters_dict = {'old_rel_vbf_folder': ''}
    parameters = SIO.parameter_adopt_teststep(parameters_dict)

    if not all(list(parameters.values())):
        logging.error("Test Failed: yml parameter not found")
        return False'''

    # Load vbfs files
    paths = cr8_paths_to_vbfs(dut)
    for path in paths:
        vbf_result = load_vbf_files(path)
        logging.info("Software download (loading vbfs) completed. Result: %s", vbf_result)

        if vbf_result is False:
            logging.error("Aborting software download due to problems when loading VBFs")
            return False

        result = software_download(dut, ess_flag=False, exe_data_flag=True)
        if not result:

            logging.error("Test Failed: Software download failed")
            return False
        check_result = SSBL.check_complete_compatible_routine(dut, stepno=104)
        if not check_result:

            #SE31.routinecontrol_requestsid_complete_compatible(dut, stepno=101)
            #message = SC.can_messages[dut["receive"]][0][2]
            #pos = message.find('0205')
            #value = "{:040b}".format(int(message[pos+6:pos+16], 16))

            # Verify Complete bit is set to 0 and Compatible bit set to 1
            #if value[39] == '0' and value[38] == '0':
                #logging.info("Complete bit %s and Compatible bit %s received", value[39], value[38])
                

            logging.error("Test failed:  Complete check bit is not 0 received: %s or Compatible "
                          "bit is not 0 received: %s", value[39], value[38])
            return False
         
        SE11.ecu_hardreset(dut)
        time.sleep(1)
        SE22.read_did_cal_id(dut)
        SE22.read_did_cvn(dut)
        SE22.read_did_engine_platform(dut)
        SE22.read_did_appl_dbpn(dut)

    return True

def run():
    """
    Software download request for VBF file types and verify which part of software
    download is failed.
    """
    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False
    try:
        dut.precondition(timeout=98000)

        result_step = dut.step(step_1, purpose='Software download request for VBF files types '
                               'and DATA(old vbf) and verify Compatible bit is set to 1')

        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
