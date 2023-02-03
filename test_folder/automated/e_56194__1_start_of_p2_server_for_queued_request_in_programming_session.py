"""

/*********************************************************************************/



Copyright © 2023 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 56194
version: 1
title: Start of P2Server for queued request in programming session
purpose: >
    To reduce latency when the server shall start process the queued request.

description: >
    In programming session, the server shall start the P2Server timer for the queued request once
    the final response (indicated via Server T_Data.con) of the previous request is transmitted.

    If the queued request is not completely received at the server when the final response of the
    previous request is transmitted (e.g. the message is halted or a large queued request is
    received) shall the server start the P2Server timer when the complete queued message is
    received (indicated via Server T_Data.ind).

details: >
    Verify P2Server timer has started for the queued request once the final response of the previous
    request is transmitted in programming session.
"""

import logging
import time
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_service3e import SupportService3e
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_can import SupportCAN, CanPayload
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO

SS3E = SupportService3e()
SIO = SupportFileIO()
SSBL = SupportSBL()
SC = SupportCAN()
SC_CARCOM = SupportCARCOM()


def flash_erase(dut, header):
    """
    Routine Flash Erase
    Args:
        dut (Dut): An instance of Dut
        header (dict): VBF file header
    Returns:
        None
    """
    for erase_el in header['erase']:
        cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("RoutineControlRequestSID",
                                            b'\xFF\x00' +\
                                            erase_el[0].to_bytes(4, byteorder='big') +\
                                            erase_el[1].to_bytes(4, byteorder='big'), b'\x01'),
                            "extra" : ''}

        SC.t_send_signal_can_mf(dut, cpay, True, 0x00)


def download_ess(dut):
    """
    Download the ESS file to the ECU
    Args:
        dut (Dut): An instance of Dut
    Returns:
        boolean: True if download software part was successful, otherwise False
        can_frames_sent (list): Sent can frame list
        can_frames_received (list): Received can frame list
    """
    result = SSBL.get_ess_filename()
    if result:
        vbf_header = SSBL.read_vbf_file(result)[1]
        SSBL.vbf_header_convert(vbf_header)

        # Request flash erase
        flash_erase(dut, vbf_header)

        SC.update_can_messages(dut)

        cpay: CanPayload = {"payload": SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                        bytes.fromhex('F186'),
                                                        b""),
                            "extra": b''}

        # Send queued request
        SC.t_send_signal_can_mf(dut, cpay, True, 0x00)

        # Adding sleep timer to wait for all the frames to receive.
        time.sleep(20)
        can_frames_sent = SC.can_frames[dut['send']]
        can_frames_received = SC.can_frames[dut['receive']]
        logging.info("CAN frames sent %s", can_frames_sent)
        logging.info("CAN frames received %s", can_frames_received)

        result = SSBL.sw_part_download(dut, result, stepno='', purpose="Download ESS")
        time.sleep(5)
        if result:
            return True, can_frames_sent, can_frames_received

    logging.error("Test Failed: ESS software download failed")
    return result, None, None


def download_application_and_data(dut):
    """
    Download the application and data to the ECU
    Args:
        dut (Dut): An instance of Dut
    Returns:
       result (bool): True when download is successful, otherwise False
    """
    logging.info("Download application and data started")
    result = True
    purpose = "Download application and data"
    for vbf_file in SSBL.get_df_filenames():
        result = result and SSBL.sw_part_download(dut, vbf_file, purpose=purpose)

    return result


def software_download(dut, stepno):
    """
    Perform software download in a sequence(SBL, ESS, APP and DATA)
    Args:
        dut (Dut): An instance of Dut
        stepno (int): Test step number
    Returns:
        correct_mode (bool): True on successful software download
        can_frames_sent (list): Sent can frame list
        can_frames_received (list): Received can frame list
    """
    # Loads the rig specific VBF files
    vbf_result = SSBL.get_vbf_files()
    if not vbf_result:
        logging.error("Test Failed: VBF files are not found")
        return False, None, None

    # Activate SBL
    sbl_result = SSBL.sbl_activation(dut, sa_keys=dut.conf.default_rig_config)
    if not sbl_result:
        logging.error("Test Failed: SBL activation failed")
        return False, None, None

    # Download ESS
    ess_result, can_frames_sent, can_frames_received = download_ess(dut)
    if not ess_result:
        logging.error("Test Failed: ESS download failed or consecutive positive response "
                      "not received")
        return False, None, None

    # Download Application and Data
    app_result = download_application_and_data(dut)
    if not app_result:
        logging.error("Test Failed: Application and Data download failed")
        return False, None, None

    # Check Complete and Compatible
    check_complete_compatible = SSBL.check_complete_compatible_routine(dut, stepno)
    if not check_complete_compatible:
        logging.error("Test Failed: Complete and Compatible check failed")
        return False, None, None

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

    return correct_mode, can_frames_sent, can_frames_received


def step_1(dut: Dut, parameters):
    """
    action: Verify P2Server timer is started for the queued request once the final response
            of the previous request is transmitted in programming session
    expected_result: P2Server timer of the queued request should be started once the
            response of the previous request is sent.
    """
    # Set to programming session
    dut.uds.set_mode(2)

    # Sleep time to avoid NRC-37
    time.sleep(5)

    # Download software in a sequence and get consecutive positive response
    result, can_frames_sent, can_frames_received = software_download(dut, stepno=1)
    if not result:
        logging.error("Test Failed: Software download failed")
        return False

    # capturing the frames of the first response and queued response.
    second_positive_reponse_time = can_frames_received[-1][0]
    first_positive_reponse_time = can_frames_received[-2][0]
    time_difference = (second_positive_reponse_time - first_positive_reponse_time) * 1000

    # Test fails if the time difference is greater than p2 servermax.
    if time_difference > parameters['p2_server_max']:
        logging.error("Test Failed: Expected both positive response to be received within"
                      " p2ServerMax(25ms), but received within %sms", time_difference)
        return False

    logging.info("Time difference between the first response and the queued response"
                " received within p2ServerMax(25ms) %sms as expected", time_difference)

    # capturing the frame of the queued request.
    second_request_time = can_frames_sent[-1][0]
    request_response_diff = (second_positive_reponse_time - second_request_time) * 1000

    # This condition makes sure that the second request is really queued or not and the ECU
    # starts the timer only after the reception of the previous response.
    if request_response_diff > parameters['p2_server_max']:
        logging.info("Time difference between queued response and queued request: %sms "
                     "is greater than p2ServerMax(25ms) as expected", request_response_diff)
        return True

    logging.error("Test Failed: Time difference between queued response and queued request: %sms "
                  "is less than p2ServerMax(25ms) proves that the queueing is not achieved",
                  request_response_diff)
    return False


def run():
    """
    Verify P2Server timer is started for the queued request once the final response of the
    previous request is transmitted in programming session.
    """
    dut = Dut()

    start_time = dut.start()
    result = False

    parameters_dict = {'p2_server_max': 0}
    try:
        dut.precondition(timeout=900)

        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameter not found")

        result = dut.step(step_1, parameters, purpose='Verify P2Server timer is started in '
                                                      'programming mode')

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
