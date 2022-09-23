"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 56200
version: 5
title: Server behavior for additional client requests in programming session
purpose: >
    If the server is processing a request and receives a request that is supposed to be
    placed in the receive queue and the receive queue is full, a predictable behavior is required.

description: >
    In programming session, if the server is processing a request and it receives a request that is
    supposed to be placed in the receive queue and the receive queue is full; the request just
    received shall be ignored.

    Note: This requirement applies regardless of the actual size of the receive queue.
    Example assuming minimum 1 queued request is required; If the server is processing a first
    request and queues a second request, and then a third request appears, the third request shall
    be ignored unless it can be queued as well.

details: >
    Verify empty response is received for request sent when request queue is full.
"""

import copy
import logging
import time
import threading
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_service3e import SupportService3e
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_can import SupportCAN, CanPayload, CanTestExtra
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
RESPONSE_LIST = []


def send_message(can_p, etp: CanTestExtra, cpay: CanPayload, wait_time):
    """
    Send CAN message to ECU.
    Args:
        can_p (Dut): Dut instance
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


def flash(can_p, cpay: CanPayload, etp: CanTestExtra, wait_time, lock):
    """
    Generate NRC 78 followed by positive response and return corresponding positive response time
    Args:
        can_p (Dut): Dut instance
        etp (class obj): CAN TEST parameters
        cpay (class obj): CAN payload
        wait_time (float): waiting time
        lock (class obj): Threading lock object
    Returns:
        None
    """
    # pylint: disable=global-statement
    global RESPONSE_LIST
    lock.acquire()

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
    # Check for NRC 78 when received CAN message
    if SC.can_messages[can_p["receive"]]:
        while SUTE.check_7f78_response(SC.can_messages[can_p["receive"]]):
            response_78 = SC.can_messages[can_p["receive"]][0][2]
            RESPONSE_LIST.append(copy.deepcopy(response_78))
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
    lock.release()
    try:
        positive_response = SC.can_messages[can_p["receive"]][0][2]
    except IndexError:
        positive_response = None

    RESPONSE_LIST.append(copy.deepcopy(positive_response))


def flash_erase(dut, vbf_header, wait_time):
    """
    Routine Flash Erase
    Args:
        dut (Dut): An instance of Dut
        vbf_header (dict): VBF file header
        wait_time (float): waiting time
    Returns:
        None
    """
    for erase_el in vbf_header['erase']:
        # DID result of EDA0
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
        lock = threading.Lock()
        flash_thread_1 = threading.Thread(target=flash, args=(dut, cpay, etp, wait_time, lock))
        flash_thread_2 = threading.Thread(target=flash, args=(dut, cpay, etp, wait_time, lock))
        flash_thread_3 = threading.Thread(target=flash, args=(dut, cpay, etp, wait_time, lock))
        # starting flash thread 1
        flash_thread_1.start()
        # starting flash thread 2
        flash_thread_2.start()
        # starting flash thread 3
        flash_thread_3.start()

        # wait until flash thread 1 is completely executed
        flash_thread_1.join()
        # wait until flash thread 2 is completely executed
        flash_thread_2.join()
        # wait until flash thread 3 is completely executed
        flash_thread_3.join()

        rc_response = False
        rc_loop = 0
        logging.info("SE31 RC Flash Erase wait max 30sec for flash erased")
        while (not rc_response) and (rc_loop < 30):
            SC.clear_can_message(dut["receive"])
            SC.update_can_messages(dut)
            # Check CAN message is greater than 0
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
            rc_loop += 1


def download_ess(dut, wait_time):
    """
    Download the ESS file to the ECU
    Args:
        dut (Dut): An instance of Dut
        wait_time(float): wait time
    Returns:
        boolean: True if download software part was successful, otherwise False
    """
    result = SSBL.get_ess_filename()
    if result:
        vbf_header = SSBL.read_vbf_file(result)[1]
        SSBL.vbf_header_convert(vbf_header)

        # Erase Memory
        flash_erase(dut, vbf_header, wait_time)
        result = SSBL.sw_part_download(dut, result, purpose="Download ESS")
        if result:
            return True

    logging.error("ESS software download failed")
    return result


def download_application_and_data(dut):
    """
    Download the application to the ECU
    Args:
        dut (Dut): An instance of Dut
    Returns:
        boolean: True of download was successful, otherwise False
    """
    logging.info("Download application and data started")
    result = True
    purpose = "Download application and data"
    for vbf_file in SSBL.get_df_filenames():
        result = result and SSBL.sw_part_download(dut, vbf_file, purpose=purpose)

    return result


def verify_ignored_request():
    """
    Verify the request is ignored when the receive queue is full
    Args:
        None
    Returns:
       (bool): True when request is ignored
    """
    # pylint: disable=global-statement
    global RESPONSE_LIST
    last_response = RESPONSE_LIST[-1]

    if last_response == '' or last_response is None :
        logging.info("Last request is ignored as expected when the receive queue is full")
        return True

    logging.error("Test failed: Expected empty response of last request, received"
                  " response %s", last_response)
    return False


def software_download(dut, wait_time, stepno):
    """
    Perform software download in a sequence(SBL, ESS, APP and DATA)
    Args:
        dut (Dut): An instance of Dut
        wait_time(float): wait time
        stepno(int): Test step number
    Returns:
        boolean: True on successful software download
    """
    # Load vbfs
    vbf_result = SSBL.get_vbf_files()
    if vbf_result is False:
        logging.error("Aborting software download due to problems when loading VBFs")
        return False

    # Activate sbl
    sbl_result = SSBL.sbl_activation(dut, sa_keys=dut.conf.default_rig_config)
    if sbl_result is False:
        logging.error("Aborting software download due to problems when activating SBL")
        return False

    # Download ess
    ess_result = download_ess(dut, wait_time)
    if ess_result is False:
        logging.error("Aborting software download due to problems when downloading ESS "
                      "or consecutive positive response not received")
        return False

    # Download application and data
    app_result = download_application_and_data(dut)
    if app_result is False:
        logging.error("Aborting software download due to problems when downloading application")
        return False

    # Check Complete and Compatible
    check_complete_compatible = SSBL.check_complete_compatible_routine(dut, stepno)
    if check_complete_compatible is False:
        logging.error("Aborting software download due to problems when checking C & C")
        return False

    # Check that the ECU ends up in mode 1 (default session)
    SS3E.stop_periodic_tp_zero_suppress_prmib()
    time.sleep(10)
    uds_response = dut.uds.active_diag_session_f186()
    mode = uds_response.data['details'].get('mode')
    correct_mode = True
    if mode != 1:
        logging.error("Software download complete but ECU did not end up "
                      "in default session, current mode is: %s", mode)
        correct_mode = False

    return correct_mode


def step_1(dut: Dut, parameters):
    """
    action: Verify empty response is received for request sent when request queue is full.
    expected_result: True when request is ignored
    """
    dut.uds.set_mode(2)
    # Download software in a sequence and get consecutive positive response
    result = software_download(dut, parameters['wait_time'], stepno=1)
    if not result:
        logging.error("Test failed: Software Download failed")
        return False

    # Verify request is ignored when queue is full
    return verify_ignored_request()


def run():
    """
    Verify empty response is received for request sent when request queue is full
    """
    dut = Dut()
    start_time = dut.start()
    result = False

    parameters_dict = {'wait_time': 0}
    try:
        dut.precondition(timeout=900)

        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result = dut.step(step_1, parameters, purpose="Verify empty response is received for"
                                            " request sent when request queue is full")
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
