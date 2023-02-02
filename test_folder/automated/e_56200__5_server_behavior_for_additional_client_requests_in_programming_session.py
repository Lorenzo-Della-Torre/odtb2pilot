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
    Send flash erase requests first and then send multiple request of DID 'F186' in queue just
    before downloading ESS software part and verify that ECU should not give any response for last
    DID request since request queue is full.
"""

import time
import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_can import SupportCAN, CanPayload
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO

SIO = SupportFileIO()
SUTE = SupportTestODTB2()
SSBL = SupportSBL()
SC = SupportCAN()
SC_CARCOM = SupportCARCOM()


def flash_erase(dut, vbf_header):
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

        SC.t_send_signal_can_mf(dut, cpay, padding=True, padding_byte=0x00)


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


def step_2(dut: Dut, num_of_request):
    """
    action: Send flash erase requests and multiple DID request in queue just before downloading
            ESS software part
    expected_result: True when ESS software download successful after multi-thread request
    """
    result = SSBL.get_ess_filename()
    if result:
        vbf_header = SSBL.read_vbf_file(result)[1]
        SSBL.vbf_header_convert(vbf_header)

        # Request erase memory with three consecutive flash erase requests
        flash_erase(dut, vbf_header)

        cpay: CanPayload = {"payload": SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                        bytes.fromhex('F186'),
                                                        b""),
                            "extra": b''}

        for _ in range(num_of_request):
            SC.clear_all_can_frames()
            # Send queued request
            SC.t_send_signal_can_mf(dut, cpay, True, 0x00)
            time.sleep(13)
            SC.update_can_messages(dut)

        logging.info("CAN Messages : %s", SC.can_messages[dut['receive']])
        # Number of response received while sending multiple request in queue. Ignore first message
        # as it's coming from "check_memory" of "SBL_download"
        num_of_res_received = len(SC.can_messages[dut['receive']][1:])

        result = SSBL.sw_part_download(dut, result, purpose="Download ESS")
        if result:
            return True, num_of_res_received

    logging.error("Test Failed: ESS software download failed")
    return False, None


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


def step_4(dut: Dut, num_of_res_received, num_of_request):
    """
    action: Verify number of response received is equal to (total number of request-1)
    expected_result: Number of response received should be equal to (total number of request-1)
    """
    # pylint: disable=unused-argument
    expected_num_of_response = (num_of_request-1)
    if (num_of_res_received is not None) and (num_of_res_received == expected_num_of_response):
        logging.info("Last request is ignored as expected when the receive queue is full")
        return True

    logging.error("Test Failed: Expected number of response is %s, but received %s",
                  expected_num_of_response, num_of_res_received)
    return False


def run():
    """
    Send flash erase requests first and then send multiple request of DID 'F186' in queue just
    before downloading ESS software part and verify that ECU should not give any response for last
    DID request since request queue is full.
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'num_of_request': 0}

    try:
        dut.precondition(timeout=900)

        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameter not found")

        result_step = dut.step(step_1, purpose="SBL activation")
        if result_step:
            result_step, num_of_res_received = dut.step(step_2, parameters['num_of_request'],
                                                        purpose="Send multiple request in queue "
                                                        "downloading ESS software part")
        if result_step:
            result_step = dut.step(step_3, purpose="Download remaining software part")
        if result_step:
            result_step = dut.step(step_4, num_of_res_received, parameters['num_of_request'],
                                  purpose="Verify ECU should ignore the third consecutive request")
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
