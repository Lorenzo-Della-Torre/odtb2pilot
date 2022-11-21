"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 60102
version: 1
title: N_As timeout in programming session
purpose: >
    From a system perspective it is important that both sender and receiver side times out roughly
    the same time. The timeout value shall be high enough to not be affected by situations like
    occasional high busloads and low enough to get a user friendly system if for example an ECU is
    not connected

description: >
    N_As timeout value shall be 1000ms in programming session

details: >
    Software download request in pbl and routine control request in sbl, with flow control delay
    more than timeout(>1000 ms) and less than timeout(<1000 ms)
"""

import time
import os
import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_can import SupportCAN, CanMFParam, CanPayload, CanTestExtra
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_service31 import SupportService31
from supportfunctions.support_service34 import SupportService34
from supportfunctions.support_SBL import SupportSBL

SIO = SupportFileIO()
SSBL = SupportSBL()
SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
SE27 = SupportService27()
SE31 = SupportService31()
SE34 = SupportService34()


def set_flow_control_delay(dut, delay):
    """
    Set flow control delay
    Args:
        dut (Dut): An instance of Dut
        delay (int): Flow control delay
    Returns: None
    """
    can_mf: CanMFParam = {"block_size": 0,
                         "separation_time": 0,
                         "frame_control_delay": delay,
                         "frame_control_flag": 48,
                         "frame_control_auto": False}
    SC.change_mf_fc(dut["send"], can_mf)


def get_vbf_params():
    """
    Extract vbf headers and vbf block from sbl type vbf file
    Args: None
    Returns:
        vbf_header (dict): Vbf header
        vbf_block (dict): Vbf block
    """
    SSBL.get_vbf_files()

    _, vbf_header, vbf_data, vbf_offset = SSBL.read_vbf_file(SSBL.get_sbl_filename())
    SSBL.vbf_header_convert(vbf_header)
    vbf_block = SSBL.block_data_extract(vbf_data, vbf_offset)[1]
    return vbf_header, vbf_block


def get_ess_params(ess_vbf_path):
    """
    Extract vbf headers from ess file
    Args:
        ess_vbf_path (str): Ess vbf file path
    Returns:
        vbf_header (dict): Vbf header
    """
    odtb_proj_param = os.environ.get('ODTBPROJPARAM')
    if odtb_proj_param is None:
        odtb_proj_param = '.'

    ess_vbf_invalid = odtb_proj_param + ess_vbf_path
    vbf_header = SSBL.read_vbf_file(ess_vbf_invalid)[1]
    SSBL.vbf_header_convert(vbf_header)

    return vbf_header


def read_did(dut, did):
    """
    Read DID 'EDA0' and find required DID in response for pbl/sbl
    Args:
        dut (Dut): An instance of Dut
        did (str): Did to check
    Returns:
        (bool): True when required DID is present in response
    """
    response = dut.uds.read_data_by_id_22(bytes.fromhex('EDA0'))
    start_pos = response.raw.find(did)
    if start_pos != -1 and response.raw[start_pos:start_pos+4] == did:
        return True

    return False


def request_download(dut, vbf_header, vbf_block):
    """
    Send software download as multi frame request, with a delay more than 1000 ms in pbl
    Args:
        dut (Dut): An instance of Dut
        vbf_header (dict): Vbf header
        vbf_block (dict): Vbf block
    Returns:
        (bool): True on successful software download
    """
    start_add = vbf_block['StartAddress'].to_bytes(4,'big')
    add_len = vbf_block['Length'].to_bytes(4,'big')

    cpay: CanPayload = {"payload": SC_CARCOM.can_m_send("RequestDownload",
                                   vbf_header["data_format_identifier"].to_bytes(1, 'big') +
                                   bytes.fromhex('44') + start_add + add_len, b''),
                        "extra": ''
                        }

    etp: CanTestExtra = {"step_no": 102,
                         "purpose": "Send multi frame request, delay in CF > 1000ms",
                         "timeout": 0.05,
                         "min_no_messages": -1,
                         "max_no_messages": -1
                         }

    result = SUTE.teststep(dut, cpay, etp)
    return result


def step_1(dut):
    """
    action: Security access in pbl
    expected_result: Security access should be granted in pbl
    """
    # Set ECU in programming session
    dut.uds.set_mode(2)

    # To avoid NRC-37
    time.sleep(5)

    # Security access in pbl
    result = SE27.activate_security_access_fixedkey(dut, sa_keys=dut.conf.default_rig_config)
    if not result:
        logging.error("Test Failed: Security access denied in pbl")
        return False

    logging.info("Security access granted in pbl")
    return True


def step_2(dut):
    """
    action: Software download request in pbl with flow control delay more than 1000ms
    expected_result: Software download request should be failed for flow control delay more
                     than 1000ms
    """
    # Extract vbf parameters
    vbf_header, vbf_block = get_vbf_params()
    if not bool(vbf_header) and not bool(vbf_block):
        logging.error("Test Failed: Vbf parameters are not found")
        return False

    # Software download request with delay more than 1000ms
    set_flow_control_delay(dut, delay=1050)
    result = request_download(dut, vbf_header, vbf_block)
    if result and len(SC.can_messages[dut["receive"]]) == 0:
        logging.info("Software download request is failed with flow control delay more than "
                      "1000ms as expected")
        return True

    logging.error("Test Failed: Software download request is successful with flow control delay "
                  "more than 1000ms")
    return False


def step_3(dut):
    """
    action: Software download request in pbl with flow control delay less than 1000ms
    expected_result: Successful software download for flow control delay less than 1000ms
    """
    # Extract vbf parameters
    vbf_header, vbf_block = get_vbf_params()
    if not bool(vbf_header) and not bool(vbf_block):
        logging.error("Test Failed: Vbf parameters are not found")
        return False

    # Software download request with delay less than 1000ms
    set_flow_control_delay(dut, delay=850)
    result = SE34.request_block_download(dut, vbf_header, vbf_block)[0]
    if not result:
        logging.error("Test Failed: Software download request failed for flow control "
                      "delay less than 1000ms")
        return False

    logging.info("Software download request is successful with flow control delay "
                  "less than 1000ms")
    return True


def step_4(dut, did):
    """
    action: Verify pbl is active and set flow control delay as default
    expected_result: ECU should be in pbl
    """
    # Read did EDA0 and check response
    result = read_did(dut, did)
    set_flow_control_delay(dut, delay=0)
    if result:
        return True

    logging.error("Test Failed: DID %s is not found in the response of DID EDA0", did)
    return False


def step_5(dut, ess_vbf_path):
    """
    action: SBL activation and routine control request with flow control delay more than 1000ms
    expected_result: Routine control request should be failed for delay more than 1000ms
    """
    # ECU reset
    dut.uds.ecu_reset_1101()

    SSBL.get_vbf_files()
    # SBL activation
    result = SSBL.sbl_activation(dut, sa_keys=dut.conf.default_rig_config)
    if not result:
        logging.error("Test Failed: SBL activation failed")
        return False

    # Extract vbf parameter
    vbf_header = get_ess_params(ess_vbf_path)
    if not bool(vbf_header):
        logging.error("Test Failed: Vbf parameters are not found")
        return False

    # Routine control request with delay more than 1000ms
    set_flow_control_delay(dut, delay=1050)
    SE31.routinecontrol_requestsid_flash_erase(dut, vbf_header)
    if len(SC.can_messages[dut["receive"]]) == 0:
        logging.info("Routine control request is failed for flow control delay more than "
                      "1000 ms as expected")
        return True, vbf_header

    logging.error("Test Failed: Routine control request is successful for flow control delay "
                  "more than 1000ms")
    return False, None


def step_6(dut, vbf_header, did):
    """
    action: Routine control request with flow control delay less than 1000ms and
            verify sbl is active
    expected_result: ECU should give NRC-31 for routine control request and sbl is active
    """
    # Routine control request with delay less than 1000ms
    set_flow_control_delay(dut, delay=850)
    SE31.routinecontrol_requestsid_flash_erase(dut, vbf_header)

    response = SC.can_messages[dut["receive"]][0][2]
    # Routine should give negative response as faulty ESS is used
    if response[2:8] != '7F3131':
        logging.error("Test Failed: Expected response of routine control request is NRC-31, but "
                      "received %s", response)
        return False

    # Read DID EDA0 and check response
    result = read_did(dut, did)
    if not result:
        logging.error("Test Failed: DID %s is not found in the response of DID EDA0", did)
        return False

    logging.info("Routine control request is successful for flow control delay less than "
                 "1000ms")
    return True


def step_7(dut, did):
    """
    action: Verify SBL session is still active after setting flow control delay as default
    expected_result: DID F122 should be present in response of DID EDA0
    """
    # Set delay to default
    set_flow_control_delay(dut, delay=0)

    # Read DID EDA0 and check response after default delay
    result = read_did(dut, did)
    if result:
        logging.info("SBL session is still active after setting delay as default")
        return True

    logging.error("Test Failed: DID %s is not found in response of DID EDA0 after default delay",
                  did)
    return False


def run():
    """
    Software download request in pbl and routine control request in sbl, with flow control delay
    more than timeout(>1000 ms) and less than timeout(<1000 ms)
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'response_did_pbl': '',
                       'response_did_sbl': '',
                       'ess_vbf_path': ''}
    try:
        dut.precondition(timeout=160)
        parameters = SIO.parameter_adopt_teststep(parameters_dict)

        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step = dut.step(step_1, purpose="Security access in pbl")
        if result_step:
            result_step = dut.step(step_2, purpose="Software download request in pbl with flow "
                                                   "control delay more than 1000ms")
        if result_step:
            result_step = dut.step(step_3, purpose="Software download request in pbl with flow "
                                                   "control delay less than 1000ms")
        if result_step:
            result_step = dut.step(step_4, parameters['response_did_pbl'], purpose="Verify pbl is "
                                   "active and set flow control delay as default")
        if result_step:
            result_step, vbf_header = dut.step(step_5, parameters['ess_vbf_path'], purpose="SBL "
                                               "activation and routine control request with flow "
                                               "control delay more than 1000ms")
        if result_step:
            result_step = dut.step(step_6, vbf_header, parameters['response_did_sbl'], purpose=
                                   "Routine control request with flow control delay less than "
                                   "1000ms and verify sbl is active")
        if result_step:
            result_step = dut.step(step_7, parameters['response_did_sbl'], purpose="Verify SBL "
                                   "session is still active after setting flow control delay as "
                                   "default")
        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
