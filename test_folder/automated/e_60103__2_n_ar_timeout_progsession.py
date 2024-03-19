"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 60103
version: 2
title: N_Ar timeout in programming session
purpose: >
    From a system perspective it is important that both sender and receiver side times out
    roughly the same time. The timeout value shall be high enough to not be affected by
    situations like occasional high busloads and low enough to get a user friendly system if for
    example an ECU is not connected.

description: >
    N_Ar timeout value shall be 1000ms in programming session.

details: >
    Verify N_Ar timeout value is 1000ms
    Steps:
        1. Request EDA0 DID with FC delay greater than and less than 1000ms and verify response
           in PBL session
        2. Request EDA0 DID with FC delay greater than and less than 1000ms and verify response
           in SBL session
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_can import SupportCAN, CanTestExtra, CanPayload, CanMFParam
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_service22 import SupportService22

SE22 = SupportService22
SIO = SupportFileIO()
SC = SupportCAN()
SC_CARCOM = SupportCARCOM()
SUTE = SupportTestODTB2()
SSBL = SupportSBL()


def change_control_frame_parameters(dut, frame_control_delay):
    """
    Request change frame control delay
    Args:
        dut (Dut): An instance of Dut
        frame_control_delay (int): Frame control delay
    Returns: None
    """
    can_mf: CanMFParam = {"block_size": 0,
                          "separation_time": 0,
                          "frame_control_delay": frame_control_delay,
                          "frame_control_flag": 48,
                          "frame_control_auto": True}

    SC.change_mf_fc(dut["receive"], can_mf)


def request_fc_delay(dut, parameters, frame_control_delay):
    """
    Request EDA0 DID with FC delay < 1000ms and FC delay > 1000ms
    Args:
        dut (Dut): An instance of Dut
        parameters (dict): DID, number of frames
        frame_control_delay (int): Frame control delay
    Returns:
        (bool): True when ECU supports DID EDA0 with FC delay < 1000ms or FC delay > 1000ms
    """
    change_control_frame_parameters(dut, frame_control_delay)

    cpay: CanPayload = {"payload": SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                        bytes.fromhex(parameters['did']),
                                                        b""),
                        "extra": b''}

    etp: CanTestExtra = {"step_no": 102,
                         "purpose": '',
                         "timeout": 5,
                         "min_no_messages": -1,
                         "max_no_messages": -1}

    teststep_result = SUTE.teststep(dut, cpay, etp)
    if not teststep_result:
        logging.error("Test Failed: Expected positive response for a request ReadDataByIdentifier "
                      "to get MF reply but not received")
        return False

    # Verify whole message is received when frame control delay is less than 1000ms
    if frame_control_delay <= 1000:
        result = (len(SC.can_messages[dut["receive"]]) == 1)
        if result:
            logging.info("Whole message received as expected")
            return True

        logging.error("Test Failed: No request reply received. Received frames: %s",
                       len(SC.can_frames[dut["receive"]]))
        return False

    # Verify only first frame is received when frame control delay is greater than 1000ms
    result = (len(SC.can_frames[dut["receive"]]) == parameters['number_of_frames'])
    if result:
        logging.info("Only first frame received as expected. Received frames: %s",
                      len(SC.can_frames[dut["receive"]]))
        return True

    logging.error("Test Failed: Expected number of frames: %s, Received frames: %s",
                   parameters['number_of_frames'], len(SC.can_frames[dut["receive"]]))
    return False


def verify_n_ar_timeout(dut, parameters):
    """
    Verify N_Ar timeout value is 1000ms
    Args:
        dut (Dut): An instance of Dut
        parameters (dict): DID, number of frames
    Returns:
        (bool): True when successfully verified N_Ar timeout value
    """
    # Request EDA0 DID with FC delay < 1000ms
    result_fc_less_than_1000_ms = request_fc_delay(dut, parameters, frame_control_delay=950)
    if not result_fc_less_than_1000_ms:
        return False

    # Request EDA0 DID with FC delay > 1000ms
    result_fc_greater_than_1000_ms = request_fc_delay(dut, parameters, frame_control_delay=1050)
    if not result_fc_greater_than_1000_ms:
        return False

    # Set back frame control delay to default
    change_control_frame_parameters(dut, frame_control_delay=0)

    return True


def download_and_activate_sbl(dut):
    """
    Download and activation of SBL
    Args:
        dut (Dut): An instance of Dut
    Returns:
        (bool): True on SBL activation
    """
    # Loads the rig specific VBF files
    vbf_result = SSBL.get_vbf_files()
    if not vbf_result:
        logging.error("Test Failed: Unable to load VBF files")
        return False

    # Download and activate SBL
    sbl_result = SSBL.sbl_dl_activation(dut, sa_keys=dut.conf.default_rig_config)
    if not sbl_result:
        logging.error("Test Failed: SBL activation failed")
        return False

    logging.info("SBL activation successful")
    return True


def step_1(dut: Dut, parameters):
    """
    action: Request EDA0 DID with FC delay < 1000ms and FC delay > 1000ms in PBL session
    expected_result: All the frames related to the CAN reply from the ECU should be received for
                     FC delay < 1000 and only the first frame be received for FC delay > 1000 in
                     pbl
    """
    # Set to programming session
    dut.uds.set_mode(2)

    result = verify_n_ar_timeout(dut, parameters)
    if not result:
        return False

    # check active diagnostic sessiont
    response = dut.uds.active_diag_session_f186()
    if response.data["details"]["mode"] != 2:
        logging.error("Test Failed: ECU is not in programming session, received sessio n %s", response.data["details"]["mode"])
        return False

    logging.info("ECU is in programming session as expected")
    return True


def step_2(dut: Dut, parameters):
    """
    action: Request EDA0 DID with FC delay < 1000ms and FC delay > 1000ms in SBL session
    expected_result: All the frames related to the CAN reply from the ECU should be received for
                     FC delay < 1000 and only the first frame be received for FC delay > 1000 in
                     sbl
    """
    result_sbl = download_and_activate_sbl(dut)
    if not result_sbl:
        return False

    result = verify_n_ar_timeout(dut, parameters)
    if not result:
        return False

    # Verify positive response '62' and DID 'F122' is received in ECU response
    response = dut.uds.read_data_by_id_22(bytes.fromhex('EDA0'))
    pos = response.raw.find('F122')
    if response.raw[4:6] != '62' and pos == '-1':
        logging.error("Test Failed: Expected positive response '62' and DID 'F122' in response,"
                      " received %s", response.raw)
        return False

    logging.info("ECU is in SBL session as expected")
    return True


def run():
    """
    Verify N_Ar timeout value is 1000ms
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'did':'',
                       'number_of_frames':0}
    try:
        dut.precondition(timeout=100)

        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step = dut.step(step_1, parameters, purpose="Request EDA0 DID with FC delay <"
                               " 1000ms and FC delay > 1000ms in PBL session")
        '''if result_step:
            result_step = dut.step(step_2, parameters, purpose="Request EDA0 DID with FC delay <"
                                   " 1000ms and FC delay > 1000ms in SBL session")'''
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
