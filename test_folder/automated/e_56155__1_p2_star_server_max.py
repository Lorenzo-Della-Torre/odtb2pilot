"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 56155
version: 1
title: : P2(star)Server_max
purpose: >
    P2*Server_max is the maximum time for the server to start with the response message
    after the transmission of a negative response 0x78 (enhanced response timing).

description: >
    The maximum time for P2*Server in all sessions is 5000 ms.

details: >
    Verify time difference between latest NRC 78 and positive response is less than or equal
    to P2(star)Server_max(5000ms)
    Steps:
        1. Download software
        2. Use custom flash erase function for ESS VBF and store NRC 78 followed by positive
           response
        3. Verify time difference of NRC 78 followed by positive response within p2*server_max
"""

import copy
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
        wait_time(float): waiting time
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
        # Compare CanTestExtra time is less than send request elapsed time
        # and number of can message is less than maximum number of can message
        while((time.time()-wait_start <= etp["timeout"])
                and (len(SC.can_messages[can_p["receive"]]) < etp["max_no_messages"])):
            SC.clear_can_message(can_p["receive"])
            SC.update_can_messages(can_p)
            time.sleep(wait_time)


def flash(can_p: CanParam, cpay: CanPayload, etp: CanTestExtra, wait_time):
    """
    Generate NRC 78 followed by positive response and get corresponding response code & time
    Args:
        can_p (class obj): CAN parameters
        etp (class obj): CAN TEST parameters
        cpay (class obj): CAN payload
        wait_time(float): waiting time
    Returns:
        response_and_time_list (list): Response code and time of NRC 78 followed
                                       by positive response.
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
    response_and_time_list = []
    response_and_time = {'response': '',
                         'time': 0 }
    # Check for NRC 78 when received CAN message
    if SC.can_messages[can_p["receive"]]:
        while SUTE.check_7f78_response(SC.can_messages[can_p["receive"]]):
            # Store NRC 78 and time to response_and_time_list
            response_and_time['response'] = SC.can_messages[can_p["receive"]][0][2][6:8]
            response_and_time['time'] = SC.can_messages[can_p["receive"]][0][0]
            response_and_time_list.append(copy.deepcopy(response_and_time))
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

    # Store positive response and time to response_and_time_list
    response_and_time['response'] = SC.can_messages[can_p["receive"]][0][2][6:8]
    response_and_time['time'] = SC.can_messages[can_p["receive"]][0][0]
    response_and_time_list.append(response_and_time)
    return response_and_time_list


def flash_erase(dut, vbf_header, wait_time):
    """
    Routine Flash Erase
    Args:
        dut (class obj): dut instance
        vbf_header (str): VBF file header
        wait_time(float): waiting time
    Returns:
        response_and_time_list (list): Response code and time of NRC 78 followed
                                       by positive response.
    """
    # Erase memory blocks
    for erase_el in vbf_header['erase']:
        # Read EDAO DID
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
        response_and_time_list = flash(dut, cpay, etp, wait_time)

        rc_response = False
        rc_loop = 0
        logging.info("SE31 RC Flash Erase wait max 30sec for flash erased")
        # Wait for 30 seconds for flash to be erased
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

    return response_and_time_list


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


def check_time_diff(response_and_time_list, p2_star_server_max):
    """
    Verify time difference between latest NRC 78 and positive response
    Args:
        response_and_time_list (list): Response code and time of NRC 78 followed
                                       by positive response.
        p2_star_server_max(int): p2 star server maximum time
    Returns:
       (bool): True when time difference of two consecutive response (NRC 78 followed by
               positive response) is less than P2*Server_max
    """
    if len(response_and_time_list) < 2:
        logging.error("Time difference can not be calculated as expected two consecutive response"
                      " NRC 78 followed by positive response")
        return False

    # Iterate list and calculate elapsed time
    for res_index in range(len(response_and_time_list)-1):
        logging.info("Response time: %s of response %s",
                    response_and_time_list[res_index]['time'],
                    response_and_time_list[res_index]['response'])
        # Extract NRC 78 followed by positive response
        if response_and_time_list[res_index]['response'] == '78' and \
            response_and_time_list[res_index+1]['response'] != '78':
            # Calculate elapsed time between NRC 78 followed by positive response
            time_elapsed = (response_and_time_list[res_index+1]['time'] - \
                                response_and_time_list[res_index]['time'])*1000

    # Compare elapsed time is within p2_star_server_max
    if time_elapsed >= 0:
        if time_elapsed <= p2_star_server_max:
            logging.info("Elapsed time %sms is less than P2*Server_max"
                         "(%sms) as expected", time_elapsed, p2_star_server_max)
            return True

    logging.error("Invalid response or elapsed time %sms is greater than P2*Server_max"
                  "(%sms)", time_elapsed, p2_star_server_max)
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

    logging.info("~~~~~~ Software download (loading vbfs) completed. Result: %s", vbf_result)

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
    # Wait for 10 second
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
    action: Calculate and verify the ECU response time between NRC 78 followed by positive
            response is less than or equal to P2*Server_max in programming session.
    expected_result: True on successful verification of ECU respone time within P2*Server_max,
                     otherwise False
    """
    dut.uds.set_mode(2)

    parameters_dict = {'p2_star_server_max': 0,
                       'wait_time': 0}
    parameters = SIO.parameter_adopt_teststep(parameters_dict)
    if not all(list(parameters.values())):
        logging.error("Test Failed: yml parameter not found")
        return False, None

    result, nrc_78_time_list = software_download(dut, parameters['wait_time'], stepno=1)

    # NRC 78 followed by positive response is less than or equal to P2*Server_max
    p2_star_result = result and check_time_diff(nrc_78_time_list, parameters['p2_star_server_max'])

    if p2_star_result:
        logging.info("ECU response time is less than or equal to P2*Server_max")
        return True, parameters

    logging.error("Test Failed: ECU response time is greater than P2*Server_max "
                  "in programming session")
    return False, None


def step_2(dut: Dut, parameters):
    """
    action: Calculate and verify the ECU response time between NRC 78 followed by positive
            response is less than or equal to P2*Server_max in extended session.
    expected_result: True on successful verification of ECU respone time within P2*Server_max,
                     otherwise False
    """
    dut.uds.set_mode(1)
    dut.uds.set_mode(3)

    # Download software in a sequence and get nrc 78 followed by positive
    # response with response time
    result, nrc_78_time_list = software_download(dut, parameters['wait_time'], stepno=2)

    # NRC 78 followed by positive response is less than or equal to P2*Server_max
    p2_star_result = result and check_time_diff(nrc_78_time_list, parameters['p2_star_server_max'])

    if p2_star_result:
        logging.info("ECU response time is less than or equal to P2*Server_max")
        return True

    logging.error("Test Failed: ECU response time is greater than P2*Server_max "
                    "in extended session")

    return False


def run():
    """
    Verify time difference between NRC 78 and positive response is less than or equal
    to P2(star)Server_max(5000ms)
    """
    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False
    try:
        dut.precondition(timeout=1800)

        result_step, parameters = dut.step(step_1, purpose='Calculate and verify time difference '
                            'between NRC 78 and positive response in programming session')

        if result_step:
            result_step = dut.step(step_2, parameters, purpose='Calculate and verify time'
                        'difference between NRC 78 and positive response in extended session')

        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
