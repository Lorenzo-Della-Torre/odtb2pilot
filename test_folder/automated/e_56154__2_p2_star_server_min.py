"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 56154
version: 2
title: P2(star)Server_min
purpose: >
    P2*Server_min is specified differently for final response and pending response. For final
    response it shall be as short as possible to allow good timing performance. For pending
    response it must be a suitable value so that a server do not significantly increase bus
    load by consecutive pending responses.

description: >
    For a final response the minimum time for P2*Server in all sessions is 0ms.
    During the enhanced response timing, the minimum time between the transmission of consecutive
    negative messages (each with negative response code 0x78) shall be 0.3 * P2*Server_max, in
    order to avoid flooding the data link with unnecessary negative response messages.

details: >
    Calculate and verify NRC 78 response time is greater than or equal to
    0.3 * P2*Server_max(1500.0ms) in both programming and extended session.

    Steps:
        1. Download Software
        2. Use custom Flash erase function for ESS VBF and store list of NRC 78 response time
        3. Verify time difference of consecutive NRC 78 is greater than 0.3*P2*server_max(1500.0ms)
"""

import logging
import time
from os import listdir
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_sec_acc import SecAccessParam
from supportfunctions.support_service3e import SupportService3e
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_can import SupportCAN, CanParam, CanPayload, CanTestExtra
from supportfunctions.support_service31 import SupportService31
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_file_io import SupportFileIO

SS3E = SupportService3e()
SIO = SupportFileIO()
SUTE = SupportTestODTB2()
SSBL = SupportSBL()
SC = SupportCAN()
SE31 = SupportService31()
S_CARCOM = SupportCARCOM()
SE22 = SupportService22()


def send_message(can_p: CanParam, etp: CanTestExtra, cpay: CanPayload, wait_time):
    """
    Send CAN message to ECU.
    Args:
        can_p (class obj): CAN parameter
        etp (class obj): CAN TestExtra parameter
        cpay (class obj): CAN payload
        wait_time (float): waiting time
    Returns:
        None
    """
    wait_max = False
    if "wait_max" in etp:
        wait_max = etp["wait_max"]

    wait_start = time.time()
    # Clean CAN messages
    SC.clear_all_can_messages()
    SC.t_send_signal_can_mf(can_p, cpay, padding=True, padding_byte=0x00)

    # Compare max number of messages and update
    if (wait_max or (etp["max_no_messages"] == -1)):
        time.sleep(etp["timeout"])
        SC.update_can_messages(can_p)
    else:
        SC.update_can_messages(can_p)
        while((time.time()-wait_start <= etp["timeout"])
                and (len(SC.can_messages[can_p["receive"]]) < etp["max_no_messages"])):
            SC.clear_can_message(can_p["receive"])
            SC.update_can_messages(can_p)
            # Pause a bit to receive frames in background
            time.sleep(wait_time)


def flash(can_p: CanParam, cpay: CanPayload, etp: CanTestExtra, wait_time):
    """
    Generate NRC 78 by Routine Flash Erase and get response time.
    Args:
        can_p (class obj): CAN parameters
        etp (class obj): CAN TEST parameters
        cpay (class obj): CAN payload
        wait_time (float): waiting time
    Returns:
        nrc_78_response_time_list (list): response time when received NRC 78.
    """
    # Clean previous can frame
    SC.clear_old_cf_frames()

    clear_old_mess = True
    if "clear_old_mess" in etp:
        clear_old_mess = etp["clear_old_mess"]

    if clear_old_mess:
        logging.debug("Clear old messages")
        SC.clear_all_can_frames()
        SC.clear_all_can_messages()

    # Message to send
    send_message(can_p, etp, cpay, wait_time)
    nrc_78_response_time_list = []
    # Check for NRC 78 when received CAN message
    if SC.can_messages[can_p["receive"]]:
        while SUTE.check_7f78_response(SC.can_messages[can_p["receive"]]):
            # Store NRC 78 and time to response_and_time_list
            if SC.can_messages[can_p["receive"]][0][2][6:8] == '78':
                # Store response time of NRC 78 in nrc_78_response_time_list
                nrc_78_response_time_list.append(SC.can_messages[can_p["receive"]][0][0])
            # Remove first frame when buffer is full
            SC.remove_first_can_frame(can_p["receive"])
            # wait for next frame to be received
            wait_loop = 0
            max_7fxx78 = 10

            new_max_7fxx78 = SIO.parameter_adopt_teststep('max_7fxx78')
            if new_max_7fxx78 != '':
                max_7fxx78 = new_max_7fxx78
            # Wait for next message
            while (len(SC.can_frames[can_p['receive']]) == 0) and (wait_loop <= max_7fxx78):
                time.sleep(1)
                wait_loop += 1

            # Clear messages
            SC.clear_can_message(can_p["receive"])
            SC.update_can_messages(can_p)

    return nrc_78_response_time_list


def flash_erase(dut, vbf_header, wait_time):
    """
    Routine Flash Erase
    Args:
        dut (class obj): dut instance
        vbf_header (str): VBF file header
        wait_time (float): waiting time
    Returns:
        nrc_78_response_time_list (list): response time when received NRC 78.
    """
    for erase_el in vbf_header['erase']:
        # Read EDA0 DID
        result = SE22.read_did_eda0(dut)
        # Prepare payload
        cpay: CanPayload = {"payload" : S_CARCOM.can_m_send("RoutineControlRequestSID",\
                                        b'\xFF\x00' +\
                                        erase_el[0].to_bytes(4, byteorder='big') +\
                                        erase_el[1].to_bytes(4, byteorder='big'), b'\x01'),\
                            "extra" : ''
                            }
        etp: CanTestExtra = {"step_no": 230,\
                                "purpose" : "RC flash erase",\
                                "timeout" : 1,\
                                "min_no_messages" : -1,\
                                "max_no_messages" : -1
                            }
        # start flash erase, may take long to erase
        nrc_78_response_time_list = flash(dut, cpay, etp, wait_time)

        rc_response = False
        rc_loop = 0
        logging.info("SE31 RC Flash Erase wait max 30sec for flash erased")
        while (not rc_response) and (rc_loop < 30):
            SC.clear_can_message(dut["receive"])
            SC.update_can_messages(dut)

            if len(SC.can_messages[dut["receive"]]) > 0:
                for all_mess in SC.can_messages[dut["receive"]]:
                    # Check response 71
                    if all_mess[2].find('71') == 2:
                        logging.info(SC.can_messages[dut["receive"]])
                        #try to decode message
                        result = result and (
                            SUTE.pp_decode_routine_control_response(all_mess[2],\
                                'Type1,Completed'))
                        rc_response = True
                    # Log response based on NRC 7F
                    elif  all_mess[2].find('7F') == 2:
                        logging.info(SUTE.pp_decode_7f_response(all_mess[2]))
                    else:
                        logging.info(SC.can_messages[dut["receive"]])
            time.sleep(1)
            rc_loop += 1
        if rc_loop == 15:
            logging.info("SE31 RC FlashErase: No pos reply received in max time")
            result = False

    return nrc_78_response_time_list


def load_vbf_files(dut):
    """
    Loads the rig specific VBF files found in rigs/<default-rig-name>/VBFs
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
    """
    Downloads and activates SBL on the ECU using supportfunction from support_SBL
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


def download_ess(dut, wait_time):
    """
    Download the ESS file to the ECU
    Args:
        dut (Dut): An instance of Dut
        wait_time(float): wait time
    Returns:
        boolean: True if download software part was successful, otherwise False
        nrc_78_time_list: Response NRC 78 with time
    """
    result = SSBL.get_ess_filename()
    if result:
        vbf_header = SSBL.read_vbf_file(result)[1]
        SSBL.vbf_header_convert(vbf_header)

        # Erase Memory
        nrc_78_time_list = flash_erase(dut, vbf_header, wait_time)

        logging.info("~~~~~~~~ Download ESS started ~~~~~~~~")
        result = SSBL.sw_part_download(dut, result, purpose="Download ESS")
        if result and len(nrc_78_time_list) != 0:
            return result, nrc_78_time_list

    logging.error("Software download failed for ESS type VBF file or NRC 78 not received")
    return result, None


def download_application_and_data(dut):
    """
    Download the application to the ECU
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


def check_time_diff(nrc_78_response_time_list, p2_star_server_max):
    """
    Verify timing difference of NRC 78
    Args:
        nrc_78_response_time_list (list): response time when received NRC 78.
        p2_star_server_max: maximum response time
    Returns:
       (bool): True when time difference of two consecutive NRC 78 is greater then
                0.3 * p2_star_server_max.
    """
    if len(nrc_78_response_time_list) < 2:
        logging.error("Time difference cannot be calculated as two consecutive NRC 78 response"
                        " not received")
        return False

    time_diff = nrc_78_response_time_list[1] - nrc_78_response_time_list[0]
    if time_diff >= 0.3 * p2_star_server_max:
        logging.info("Two consecutive NRC 78 response time %sms is more than"
                     " 0.3 * P2*Server_max(%sms) as expected", time_diff, 0.3 * p2_star_server_max)
        return True

    logging.error("Two consecutive NRC 78 response time %sms is less than"
                  " 0.3 * P2*Server_max(%sms)", time_diff, 0.3 * p2_star_server_max)
    return False


def software_download(dut, wait_time, stepno):
    """
    Perform software download for all VBFs file type and verify ECU land up in default session.
    Args:
        dut (Dut): An instance of Dut
        wait_time(float): wait time
        stepno(int): Test step number

    Returns:
        boolean: True on successful software download
    """

    # Load vbfs
    vbf_result = load_vbf_files(dut)

    logging.info("Software download (loading vbfs) completed. Result: %s", vbf_result)

    if vbf_result is False:
        logging.error("Aborting software download due to problems when loading VBFs")
        return False, None

    # Activate sbl
    sbl_result = activate_sbl(dut)

    logging.info("Software download (downloading and activating sbl) completed."
                 " Result: %s", sbl_result)

    if sbl_result is False:
        logging.error("Aborting software download due to problems when activating SBL")
        return False, None

    # Download ess
    ess_result, nrc_78_time_list = download_ess(dut, wait_time)

    logging.info("Software download (downloading ess) completed. Result: %s", ess_result)

    if ess_result is False:
        logging.error("Aborting software download due to problems when downloading ESS "
                      "or NRC 78 not received")
        return False, None

    # Download application and data
    app_result = download_application_and_data(dut)

    logging.info("Software download (downloading application and data) done."
                 " Result: %s", app_result)

    if app_result is False:
        logging.error("Aborting software download due to problems when downloading application")
        return False, None

    # Check Complete and Compatible
    check_result = SSBL.check_complete_compatible_routine(dut, stepno)

    logging.info("Software download (Check Complete and Compatible) completed."
                 " Result: %s", check_result)

    if check_result is False:
        logging.error("Aborting software download due to problems when checking C & C")
        return False, None

    # Check that the ECU ends up in mode 1 (default session)
    dut.uds.set_mode(1)
    time.sleep(10)
    uds_response = dut.uds.active_diag_session_f186()
    mode = uds_response.data['details'].get('mode')
    correct_mode = True
    if mode != 1:
        logging.error("Software download complete but ECU did not end up "
                      "in mode 1 (default session), current mode is: %s", mode)
        correct_mode = False

    return correct_mode, nrc_78_time_list


def step_1(dut: Dut):
    """
    action: Calculate and verify NRC 78 response time is greater than or equal to
            0.3 * P2*Server_max(1500.0ms) in programming session.
    expected_result: NRC 78 response time is greater than 0.3 * P2*Server_max(1500.0ms)
    """
    # Sleep time to avoid NRC37
    time.sleep(5)

    dut.uds.set_mode(2)
    # Read yml parameters
    parameters_dict = {'p2_star_server_max': 0,
                       'wait_time': 0}
    parameters = SIO.parameter_adopt_teststep(parameters_dict)
    if not all(list(parameters.values())):
        logging.error("Test Failed: yml parameter not found")
        return False, None

    # Download software in a sequence and get consecutive nrc 78 response time
    result, nrc_78_response_time_list = software_download(dut, parameters['wait_time'], stepno=1)
    if not result:
        logging.error("Test failed: Software Download failed")
        return False, None
    # NRC 78 response time is greater than or equal to 0.3 * P2*Server_max(1500.0ms)
    p2_star_result = check_time_diff(nrc_78_response_time_list, parameters['p2_star_server_max'])
    if p2_star_result:
        return True, parameters

    logging.error("Test failed: ECU response time is less than 0.3 * P2*Server_max(%sms)"
                  " or NRC 78 not received in programming session",
                   0.3*parameters['p2_star_server_max'])
    return False, None


def step_2(dut: Dut, parameters):
    """
    action: Calculate and verify NRC 78 response time is greater than or equal to
            0.3 * P2*Server_max(1500.0ms) in extended session.
    expected_result: NRC 78 response time is greater than 0.3 * P2*Server_max(1500.0ms)
    """
    dut.uds.set_mode(1)
    dut.uds.set_mode(3)
    # Download software in a sequence and get consecutive nrc 78 response time
    result, nrc_78_response_time_list = software_download(dut, parameters['wait_time'], stepno=2)
    if not result:
        logging.error("Test failed: Software Download failed")
        return False
    # NRC 78 response time is greater than or equal to 0.3 * P2*Server_max(1500.0ms)
    p2_star_result = check_time_diff(nrc_78_response_time_list, parameters['p2_star_server_max'])
    if p2_star_result:
        return True

    logging.error("Test failed: ECU response time is less than 0.3 * P2*Server_max(%sms)"
                  " or NRC 78 not received in extended session.",
                    0.3*parameters['p2_star_server_max'])
    return False


def run():
    """
    Calculate and verify NRC 78 response time is greater than or equal to
    0.3 * P2*Server_max(1500.0ms) in both programming and extended session.
    """
    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False
    try:
        dut.precondition(timeout=1800)

        result_step, parameters = dut.step(step_1, purpose='Calculate and verify NRC 78 response'
                                            ' time is greater than 0.3 * P2*Server_max(1500.0ms)'
                                            ' in programming session.')

        if result_step:
            result_step = dut.step(step_2, parameters, purpose='Calculate and verify NRC 78 '
                                            'response time is greater than '
                                            '0.3 * P2*Server_max(1500.0ms) in extended session.')

        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
