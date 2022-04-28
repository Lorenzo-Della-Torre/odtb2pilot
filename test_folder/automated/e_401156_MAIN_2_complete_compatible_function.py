"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 401156
version: 2
title: CompleteCompatibleFunction()
purpose: >
    Define alternatives of how to perform the compatibility check, to not limit the ECU designer
    to use a specific method.

description: >
    The compatible check is either exclusively executed by the bootloader or via a call-out to a
    function placed in a downloaded software part (e.g. application). The bootloader must always
    verify that the compatible function applied is available and is complete, i.e. it has passed
    the complete check (resides in a verified memory location) and the existence is verified by
    e.g. some known start- and end-patterns prior to execution.

details: >
    Verify whether the ECU is able to detect the downloaded software is compatible or not.
    1. Verify downloaded software is complete & compatible
    2. Verify downloaded software is complete and not compatible with current release VBF
       files(SBL,ESS,EXE) and previous releases VBF file(DATA) and

"""
import logging
import time
from os import listdir, path
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_service3e import SupportService3e
from supportfunctions.support_file_io import SupportFileIO

SIO = SupportFileIO()
SSBL = SupportSBL()
SS3E = SupportService3e()


def filter_vbf_files(file_paths, vbf_data_flag):
    """
    Filter VBF file path based on VBF type
    Args:
        file_paths (list): VBF file paths
        vbf_data_flag(bool): True to get previous release DATA vbf file
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
            print(vbf_header)

            # Compare vbf header 'sw_part_type' with 'DATA' and get the file path
            if vbf_data_flag:
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


def load_vbf_files(dut, parameters=None, vbf_file_flag=False):
    """
    Loads the rig specific VBF files found in rigs/<default-rig-name>/VBFs or
    in vbf_old (previous release vbf files)

    Args:
        dut (Dut): An instance of Dut
        parameters(dict): previous release vbf directory name
        vbf_file_flag (bool): True to get previous release VBF paths
    Returns:
        boolean: True if vbfs were loaded successfully, otherwise False
    """
    logging.info("~~~~~~~~ Loading VBFs started ~~~~~~~~")
    vbfs = listdir(dut.conf.rig.vbf_path)
    paths_to_vbfs = [str(dut.conf.rig.vbf_path) + "/" + x for x in vbfs]
    if vbf_file_flag:
        vbf_old_folder = parameters['old_rel_vbf_folder']
        if vbf_old_folder in listdir(dut.conf.rig.vbf_path):
            vbfs = listdir(str(dut.conf.rig.vbf_path)+ f"/{vbf_old_folder}")
            previous_rel_vbf_paths = [str(dut.conf.rig.vbf_path) + f"/{vbf_old_folder}/"
                                      + x for x in vbfs]
            paths_to_vbfs = filter_vbf_files(paths_to_vbfs, vbf_data_flag=False)
            paths_to_vbfs.extend(filter_vbf_files(previous_rel_vbf_paths, vbf_data_flag=True))
        else:
            logging.error("Previous release vbf directory or file not found in %s",
                          dut.conf.rig.vbf_path)
            return False

    if not paths_to_vbfs:
        logging.error("VBFs file not found, expected in %s ... aborting", paths_to_vbfs)
        return False

    result = SSBL.read_vbf_param(paths_to_vbfs)

    return result


def download_application_and_data(dut):
    """Download the application to the ECU
    Args:
        dut (Dut): An instance of Dut
    Returns:
        boolean: True when software download is successful for application and data,
                 otherwise False
    """

    logging.info("~~~~~~~~ Download application and data started ~~~~~~~~")
    result = True
    purpose = "Download application and data"
    for vbf_file in SSBL.get_df_filenames():
        result = result and SSBL.sw_part_download(dut, vbf_file, purpose=purpose)

    return result


def software_download(dut: Dut, parameters, memory_verify=False):
    """
    Software download(SWDL) for SBL, ESS DATA and EXE VBF file type
    Args:
        dut (Dut): An instance of Dut
        parameters(dict): yml parameters
        memory_verify (bool): True to for checking memory verify
    Returns:
        (bool): True on successful software download
    """
    # Activate sbl
    sbl_result = SSBL.sbl_activation(dut, sa_keys=dut.conf.default_rig_config)

    logging.info("Software download (downloading and activating sbl) completed."
                 " Result: %s", sbl_result)

    if sbl_result is False:
        logging.error("Aborting software download due to problems when activating SBL")
        return False

    if memory_verify is True:
        result = vbf_start_length(dut, parameters)
        if result is False:
            logging.error("vbf_start_length is not equal")
            return False

    # Download ess (if needed)
    ess_result = SSBL.sw_part_download(dut, SSBL.get_ess_filename(), purpose="Download ESS")

    logging.info("Software download (downloading ess) completed. Result: %s", ess_result)

    if ess_result is False:
        logging.error("Aborting software download due to problems when downloading ESS")
        return False

    # Download application and data
    app_result = download_application_and_data(dut)

    logging.info("Software download (downloading application and data) completed."
                 " Result: %s", app_result)

    if app_result is False:
        logging.error("Aborting software download due to problems when downloading application")
        return False

    return True


def vbf_start_length(dut:Dut, parameters):
    """
    Retrieving Start Address and Length from ESS vbf file
    Args:
        dut (Dut): An instance of Dut
        parameters: yml parameters
    Returns:
        (dict): verification_block_start, verification_block_length
    """
    # pylint: disable=unused-argument
    vbf_header = SSBL.read_vbf_file(SSBL.get_ess_filename())[1]
    if  vbf_header['verification_block_start'] == parameters['start_address'] and \
        vbf_header['verification_block_length'] == parameters['length']:
        logging.info("ESS VBF's Start Address and Length Equal to yml start and length")
        return True
    logging.error("ESS VBF's Start Address and Length Not Equal to yml start and length")
    return False


def step_1(dut: Dut):
    """
    action: Download Software for SBL, ESS, DATA & EXE VBFs file type and verify the
            downloaded software is complete and compatible

    expected_result: True when downloaded software is Complete&Compatible
    """
    # Read yml parameters
    parameters_dict = {'start_address': '',
                       'length': ''}
    parameters = SIO.parameter_adopt_teststep(parameters_dict)

    if not all(list(parameters.values())):
        logging.error("Test Failed: yml parameter not found")
        return False

    dut.uds.set_mode(1)
    # Wait for 10 second to expire security access delay timer and start software download
    time.sleep(10)

    # Load vbfs
    vbf_result = load_vbf_files(dut, parameters=None, vbf_file_flag=False)
    logging.info("Software download (loading vbfs) completed. Result: %s", vbf_result)

    if vbf_result is False:
        logging.error("Aborting software download due to problems when loading VBFs")
        return False

    # Memory_verify flag True to Verify Memory address of ESS VBF File
    result = software_download(dut, parameters, memory_verify=True)
    if result:
        response = SSBL.check_complete_compatible_routine(dut, stepno=1)
        complete_compatible_list = response.split(",")
        if complete_compatible_list[0] == 'Complete' and \
            complete_compatible_list[1].strip() == 'Compatible':
            return True

        logging.error("Test Failed: Complete & Compatible check failed, expected Complete,"
                      " and Compatible received %s", response)
        return False
    logging.error("Test Failed: Software Download failed")
    return False


def step_2(dut: Dut):
    """
    action: Download Software for SBL, ESS & EXE VBF file type and previous release DATA
            VBF file and verify the downloaded software is Complete and Not Compatible

    expected_result: True when downloaded software is Complete and Not Compatible
    """

    # Read yml parameters
    parameters_dict = {'old_rel_vbf_folder': ''}
    parameters = SIO.parameter_adopt_teststep(parameters_dict)

    if not all(list(parameters.values())):
        logging.error("Test Failed: yml parameter not found")
        return False

    # Load vbfs
    vbf_result = load_vbf_files(dut, parameters, vbf_file_flag=True)
    logging.info("Software download (loading vbfs) completed. Result: %s", vbf_result)

    if vbf_result is False:
        logging.error("Aborting software download due to problems when loading VBFs")
        return False

    # Memory_verify flag False to skip Verify Memory address of ESS VBF File
    result = software_download(dut, parameters=None,memory_verify = False)
    if result:
        response = SSBL.check_complete_compatible_routine(dut, stepno=2)
        complete_compatible_list = response.split(",")
        if complete_compatible_list[0] == 'Complete' and \
            complete_compatible_list[1].strip() == 'Not Compatible':
            logging.info("Complete & Not Compatible check successful with latest release VBF"
                         "file and previous release configuration file")
            return True

        logging.error("Test Failed: Complete & Compatible check failed, expected Complete "
                      "and Not Compatible, received %s", response)
        return False
    logging.error("Test Failed: Software Download failed")
    return False


def run():
    """
    Verifying current downloaded software is compatible or not
    """
    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False
    try:
        dut.precondition(timeout=1800)
        result_step = dut.step(step_1, purpose='Verify current Downloaded Software '
                               'is Complete & Compatible with latest VBF releases')

        # Commented as Not Compatible check can not perform with old release VBF files
        # if result_step:
        #     result_step = dut.step(step_2, purpose='Verify current Downloaded Software is '
        #                            'Complete and Not Compatible with previous VBF releases')

        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
