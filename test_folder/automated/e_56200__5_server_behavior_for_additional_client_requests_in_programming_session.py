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
    Send three consecutive flash erase requests just before downloading ESS software part using
    threading and verify that ECU should not give any response for the third flash erase request
    since request queue is full.
"""

import copy
import logging
import time
import threading
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_can import SupportCAN, CanPayload, CanTestExtra
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO

SIO = SupportFileIO()
SUTE = SupportTestODTB2()
SSBL = SupportSBL()
SC = SupportCAN()
SC_CARCOM = SupportCARCOM()
RESPONSE_LIST = []


def send_message(dut, etp: CanTestExtra, cpay: CanPayload, wait_time):
    """
    Send CAN message to ECU.
    Args:
        dut (Dut): An instance of Dut
        etp (class obj): CAN TestExtra parameter
        cpay (class obj): CAN payload
        wait_time (float): Waiting time
    Returns:
        None
    """
    wait_max = False
    if "wait_max" in etp:
        wait_max = etp["wait_max"]

    wait_start = time.time()
    # Clean CAN messages
    SC.clear_all_can_messages()
    SC.t_send_signal_can_mf(dut, cpay, padding=True, padding_byte=0x00)

    # Compare max number of messages and update
    if (wait_max or (etp["max_no_messages"] == -1)):
        time.sleep(etp["timeout"])
        SC.update_can_messages(dut)
    else:
        SC.update_can_messages(dut)
        while((time.time()-wait_start <= etp["timeout"])
                and (len(SC.can_messages[dut["receive"]]) < etp["max_no_messages"])):
            SC.clear_can_message(dut["receive"])
            SC.update_can_messages(dut)
            # Pause a bit to receive frames in background
            time.sleep(wait_time)


def flash(dut, cpay: CanPayload, etp: CanTestExtra, wait_time, lock):
    """
    Generate NRC 78 followed by positive response and return corresponding positive response time
    Args:
        dut (Dut): An instance of Dut
        etp (class obj): CAN test parameters
        cpay (class obj): CAN payload
        wait_time (float): Waiting time
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
    send_message(dut, etp, cpay, wait_time)

    # Check for NRC 78 when received CAN message
    if SC.can_messages[dut["receive"]]:
        while SUTE.check_7f78_response(SC.can_messages[dut["receive"]]):
            response_78 = SC.can_messages[dut["receive"]][0][2]
            RESPONSE_LIST.append(copy.deepcopy(response_78))
            # Remove first frame when buffer is full
            SC.remove_first_can_frame(dut["receive"])
            # Wait for next frame to be received
            wait_loop = 0
            max_7fxx78 = 10

            new_max_7fxx78 = SIO.parameter_adopt_teststep('max_7fxx78')
            if new_max_7fxx78 != '':
                max_7fxx78 = new_max_7fxx78
            # Wait for next message
            while (len(SC.can_frames[dut['receive']]) == 0) and (wait_loop <= max_7fxx78):
                time.sleep(1)
                wait_loop += 1

            # Clear messages
            SC.clear_can_message(dut["receive"])
            SC.update_can_messages(dut)
    lock.release()
    try:
        positive_response = SC.can_messages[dut["receive"]][0][2]
    except IndexError:
        positive_response = None

    RESPONSE_LIST.append(copy.deepcopy(positive_response))


def flash_erase(dut, vbf_header, wait_time):
    """
    Send three consecutive routine flash erase
    Args:
        dut (Dut): An instance of Dut
        vbf_header (dict): VBF file header
        wait_time (float): Waiting time
    Returns:
        None
    """
    for erase_el in vbf_header['erase']:

        # Prepare payload
        cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("RoutineControlRequestSID",
                                        b'\xFF\x00' + erase_el[0].to_bytes(4, byteorder='big') +
                                        erase_el[1].to_bytes(4, byteorder='big'), b'\x01'),
                            "extra" : ''}

        etp: CanTestExtra = {"step_no": 230,
                             "purpose" : "RC flash erase",
                             "timeout" : 1,
                             "min_no_messages" : -1,
                             "max_no_messages" : -1}

        # Start flash erase, may take long to erase
        lock = threading.Lock()
        flash_thread_1 = threading.Thread(target=flash, args=(dut, cpay, etp, wait_time, lock))
        flash_thread_2 = threading.Thread(target=flash, args=(dut, cpay, etp, wait_time, lock))
        flash_thread_3 = threading.Thread(target=flash, args=(dut, cpay, etp, wait_time, lock))
        # Starting flash thread 1
        flash_thread_1.start()
        # Starting flash thread 2
        flash_thread_2.start()
        # Starting flash thread 3
        flash_thread_3.start()

        # Wait until flash thread 1 is completely executed
        flash_thread_1.join()
        # Wait until flash thread 2 is completely executed
        flash_thread_2.join()
        # Wait until flash thread 3 is completely executed
        flash_thread_3.join()


def step_1(dut: Dut):
    """
    action: SBL activation
    expected_result: True when SBl activation successful
    """
    # Set to programming session
    dut.uds.set_mode(2)

    # Load vbfs
    vbf_result = SSBL.get_vbf_files()
    if not vbf_result:
        logging.error("Test Failed: Unable to load vbf files")
        return False

    # Sleep time to avoid NRC-37
    time.sleep(5)

    # Activate sbl
    sbl_result = SSBL.sbl_activation(dut, sa_keys=dut.conf.default_rig_config)
    if not sbl_result:
        logging.error("Test Failed: SBL activation failed")
        return False

    logging.info("SBL activation successful")
    return True


def step_2(dut: Dut, wait_time):
    """
    action: Send three consecutive flash erase requests just before downloading ESS software part
            using threading
    expected_result: True when ESS software download successful after multi-thread request
    """
    result = SSBL.get_ess_filename()
    if result:
        vbf_header = SSBL.read_vbf_file(result)[1]
        SSBL.vbf_header_convert(vbf_header)

        # Request erase memory with three consecutive flash erase requests
        flash_erase(dut, vbf_header, wait_time)
        result = SSBL.sw_part_download(dut, result, purpose="Download ESS")
        if result:
            return True

    logging.error("Test Failed: ESS software download failed")
    return result


def step_3(dut: Dut):
    """
    action: Download remaining software part
    expected_result: True when remaining software part download successful
    """
    result = True
    for vbf_file in SSBL.get_df_filenames():
        result = result and SSBL.sw_part_download(dut, vbf_file, purpose="Download application"\
                                                                         " and data")

    return result


def step_4(dut: Dut):
    """
    action: Verify ECU response of three consecutive flash erase requests
    expected_result: ECU should not give any response in third request
    """
    # pylint: disable=unused-argument
    # pylint: disable=global-statement
    global RESPONSE_LIST
    last_response = RESPONSE_LIST[-1]

    if last_response is None :
        logging.info("Last request is ignored as expected when the receive queue is full")
        return True

    logging.error("Test Failed: Expected empty response of last request, received"
                  " response %s", last_response)
    return False


def run():
    """
    Send three consecutive flash erase requests just before downloading ESS software part using
    threading and verify empty response is received for the third flash erase request since request
    queue is full.
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'wait_time': 0}

    try:
        dut.precondition(timeout=900)

        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step = dut.step(step_1, purpose="SBL activation")
        if result_step:
            result_step = dut.step(step_2, parameters, purpose="Send three consecutive flash erase"
                                   " requests just before downloading ESS software part using "
                                   "threading")
        if result_step:
            result_step = dut.step(step_3, purpose="Download remaining software part")
        if result_step:
            result_step = dut.step(step_4, purpose="Verify ECU should ignore the third consecutive"
                                                   " request")
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
