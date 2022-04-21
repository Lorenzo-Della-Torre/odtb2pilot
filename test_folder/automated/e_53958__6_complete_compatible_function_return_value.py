"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 53958
version: 6
title: CompleteCompatibleFunction() return value
purpose: >
    Definition of the bitcoded CompleteCompatibleFunction() return value. When the complete check
    is part of the bootloader, the bootloader might have limited knowledge of the relation between
    a logical block and actual sw part type (DATA, EXE).

description: >
    The return value from the CompleteCompatibleFunction() shall be 4 bytes long and bit coded
    and contain the type of failure and which software part(s) that has failed. If a failure
    has occurred the bit value is set to one (1), not effected bits are set to zero (0).
    This means the Complete and compatible function has “PASSED”, when complete and compatible
    function returns 0. The diagnostic database shall contain the actual return values for an ECU.

    Example.
    Bit (4) shall be set to "0" if the ECU doesn't supports a software part
    (e.g. the Car Configuration).

    Return values from CompleteCompatibleFunction()
    Bit number              Description

    Bit 6-31 (msb)	        User defined software parts(s). One bit per SW part which
                            is documented by each ECU respectively.
    Bit 5                   ECU Software Structure
    Bit 4	                Car Config, if applicable.
    Bit 3	                Signal Configuration
    Bit 2	                Executable
    Bit 1	                Compatible check
    Bit 0 (lsb)	            Complete check

details: >
    Software download request for VBF file types and verify which part of software
    download has failed.
    Steps-
        1. Download SBL and old relaese DATA vbf file and verify Compatible bit is 1
        2. Download SBL and ESS and verify Complete & EXE bit set to 1 and
           CompleteCompatibleFunction() response is 4 bytes long
        3. Download SBL and empty ESS and verify ESS bit set to 1
        4. Restore ECU
"""

import logging
import time
from os import listdir, path
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_service31 import SupportService31
from supportfunctions.support_can import SupportCAN
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_service3e import SupportService3e

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


def load_vbf_files(dut, parameters=None, old_vbf_data_flag=False):
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
    vbfs = listdir(dut.conf.rig.vbf_path)
    paths_to_vbfs = [str(dut.conf.rig.vbf_path) + "/" + x for x in vbfs]
    if old_vbf_data_flag:
        vbf_old_folder = parameters['old_rel_vbf_folder']
        if vbf_old_folder in listdir(dut.conf.rig.vbf_path):
            vbfs = listdir(str(dut.conf.rig.vbf_path)+ f"/{vbf_old_folder}")
            previous_rel_vbf_paths = [str(dut.conf.rig.vbf_path) + f"/{vbf_old_folder}/"
                                      + x for x in vbfs]
            paths_to_vbfs = filter_vbf_files(paths_to_vbfs, old_vbf_flag=False)
            paths_to_vbfs.extend(filter_vbf_files(previous_rel_vbf_paths, old_vbf_flag=True))
        else:
            logging.error("Previous release vbf directory or file not found in %s",
                          dut.conf.rig.vbf_path)
            return False

    if not paths_to_vbfs:
        logging.error("VBFs file not found, expected in %s ... aborting", paths_to_vbfs)
        return False

    result = SSBL.read_vbf_param(paths_to_vbfs)

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
        result = result and SSBL.sw_part_download(dut, vbf_file, purpose="Download EXE & DATA vbf")
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
    # Activate sbl
    sbl_result = SSBL.sbl_activation(dut, sa_keys=dut.conf.default_rig_config)

    logging.info("Software download (downloading and activating sbl) completed."
                 " Result: %s", sbl_result)

    if sbl_result is False:
        logging.error("Aborting software download due to problems when activating SBL")
        return False

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


def software_download_empty_ess(dut):
    """
    Software download(SWDL) for SBL and empty ESS VBFs file type
    Args:
        dut (Dut): An instance of Dut
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

    # Download empty ESS
    _, vbf_header, vbf_data, vbf_offset = SSBL.read_vbf_file(SSBL.get_ess_filename())
    vbf_data = b''
    #convert vbf header so values can be used directly
    SSBL.vbf_header_convert(vbf_header)

    # Erase Memory
    result = SSBL.flash_erase(dut, vbf_header, stepno=2)
    # Iteration to Download the Software by blocks
    result = result and SSBL.transfer_data_block(dut, vbf_header, vbf_data, vbf_offset)

    return result


def step_1(dut: Dut):
    """
    action: Download Software VBFs file type and previous release DATA VBF file
            and verify which part of downloaded software is Complete and Compatible

    expected_result: True when downloaded software is Complete(bit 0) and Compatible(bit 1)
    """
    # Read yml parameters
    parameters_dict = {'old_rel_vbf_folder': ''}
    parameters = SIO.parameter_adopt_teststep(parameters_dict)

    if not all(list(parameters.values())):
        logging.error("Test Failed: yml parameter not found")
        return False

    # Load vbfs files
    vbf_result = load_vbf_files(dut, parameters, old_vbf_data_flag=True)
    logging.info("Software download (loading vbfs) completed. Result: %s", vbf_result)

    if vbf_result is False:
        logging.error("Aborting software download due to problems when loading VBFs")
        return False

    result = software_download(dut, ess_flag=True, exe_data_flag=True)
    if result:
        SE31.routinecontrol_requestsid_complete_compatible(dut, stepno=101)
        message = SC.can_messages[dut["receive"]][0][2]
        pos = message.find('0205')
        value = "{:040b}".format(int(message[pos+6:pos+16], 16))

        # Verify Complete bit is set to 0 and Compatible bit set to 1
        if value[39] == '0' and value[38] == '1':
            logging.info("Complete bit %s and Compatible bit %s received", value[39], value[38])
            return True

        logging.error("Test failed:  Complete check bit is not 0 received: %s or Compatible "
                      "bit is not 1 received: %s", value[39], value[38])
        return False

    logging.error("Test Failed: Software download failed")
    return False


def step_2(dut:Dut):
    """
    action: Software download request for VBF file types (SBL, ESS). Verify which part of software
            download has failed and CompleteCompatibleFunction() response shall be 4 bytes long
    expected_result: True when Complete check bit & EXE bit set to 1 and
                     CompleteCompatibleFunction() response is 4 bytes long
    """
    # Set default session
    dut.uds.set_mode(1)
    time.sleep(10)

    # Load vbfs file
    vbf_result = load_vbf_files(dut, parameters=None, old_vbf_data_flag=False)
    logging.info("Software download (loading vbfs) completed. Result: %s", vbf_result)

    if vbf_result is False:
        logging.error("Aborting software download due to problems when loading VBFs")
        return False

    # Software Download with SBL and ESS
    result = software_download(dut, ess_flag=True, exe_data_flag=False)
    if not result:
        logging.error("Test failed: SBL or ESS VBFs type Software Download failed")
        return False

    SE31.routinecontrol_requestsid_complete_compatible(dut, stepno=102)
    message = SC.can_messages[dut["receive"]][0][2]
    pos = message.find('0205')
    value = "{:040b}".format(int(message[pos+6:pos+16], 16))

    # Verify CompleteCompatibleFunction() response length 4 bytes, Complete check and EXE bit 1
    if len(message[14:]) == 8 and value[39] == '1' and value[37] == '1':
        logging.info("CompleteCompatibleFunction() response length 4 bytes, Complete check bit %s"
                     "and EXE bit %s received", value[39], value[37])
        return True

    logging.error("Test failed: CompleteCompatibleFunction() response length not 4 bytes or"
                  "Complete check bit is not 1 received: %s or EXE bit is not 1 received: %s",
                  value[39], value[37])
    return False


def step_3(dut: Dut):
    """
    action: Software download request for SBL and empty ESS VBFs file types. Verify ESS download
            has failed.
    expected_result: True when ESS bit set to 1
    """
    # Set default session
    dut.uds.set_mode(1)
    time.sleep(10)

    # Load vbfs file
    vbf_result = load_vbf_files(dut, parameters=None, old_vbf_data_flag=False)
    logging.info("Software download (loading vbfs) completed. Result: %s", vbf_result)

    if vbf_result is False:
        logging.error("Aborting software download due to problems when loading VBFs")
        return False

    # Software Download with SBL and empty ESS
    result = software_download_empty_ess(dut)
    if not result:
        logging.error("Test failed: Unexpected result of empty ESS software download")
        return False

    SE31.routinecontrol_requestsid_complete_compatible(dut, stepno=103)
    message = SC.can_messages[dut["receive"]][0][2]
    pos = message.find('0205')
    value = "{:040b}".format(int(message[pos+6:pos+16], 16))

    # Compare ESS bit set to 1
    if value[34] == '1':
        logging.info("ESS bit set %s as expected", value[34])
        return True

    logging.error("Test failed: ESS (ECU Software Structure) bit is not set to 1, Received "
                  "%s", value[34])
    return False


def step_4(dut: Dut):
    """
    action: Restore ECU

    expected_result: ECU should send positive response on successful software download
    """
    # Set default session
    dut.uds.set_mode(1)
    time.sleep(10)

    # Load vbfs file
    vbf_result = load_vbf_files(dut, parameters=None, old_vbf_data_flag=False)
    logging.info("Software download (loading vbfs) completed. Result: %s", vbf_result)

    if vbf_result is False:
        logging.error("Aborting software download due to problems when loading VBFs")
        return False

    result = software_download(dut, ess_flag=True, exe_data_flag=True)

    # Check Complete And Compatible
    check_result = SSBL.check_complete_compatible_routine(dut, stepno=104)

    logging.info("software download (Check Complete And Compatible) done."
                 " Result: %s\n\n", check_result)

    if check_result is False:
        logging.error("Aborting software download due to problems when checking C & C")
        return False

    SS3E.stop_periodic_tp_zero_suppress_prmib()

    time.sleep(10)
    uds_response = dut.uds.active_diag_session_f186()
    mode = uds_response.data['details'].get('mode')
    correct_mode = True
    if mode != 1:
        logging.error("Software download complete "
        "but ECU did not end up in mode 1 (default session), current mode is: %s", mode)
        correct_mode = False

    return result and correct_mode


def run():
    """
    Software download request for VBF file types and verify which part of software
    download is failed. Also verify CompleteCompatibleFunction() response length is 4 bytes
    """
    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=1800)
        result_step = dut.step(step_1, purpose='Software download request for VBF files types '
                               'and DATA(old vbf) and verify Compatible bit is set to 1')
        if result_step:
            result_step = dut.step(step_2, purpose='Software download request for VBF file types '
                                'SBL, ESS and verify Complete & EXE bit set to 1'
                                ' and CompleteCompatibleFunction() response length is 4 bytes')
        if result_step:
            result_step = dut.step(step_3, purpose='Software download request for VBF file types'
                                  ' SBL, empty ESS and verify ESS bit set to 1')
        if result_step:
            result_step = dut.step(step_4, purpose='Restore ECU')

        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
