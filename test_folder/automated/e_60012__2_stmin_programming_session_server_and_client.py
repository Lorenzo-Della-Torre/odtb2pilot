"""

/*********************************************************************************/



Copyright © 2023 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 60012
version: 2
title: : Separation time (STmin) programming session server and client
purpose: >
    Define STmin for programming session and client. For more information see section Separation
    (STmin) parameter definition.

description: >
    Separation time (STmin) for programming session shall be maximum 0ms for server and Client.

details: >
    Verify separation time (STmin) for server side in PBL and SBL session are maximum 0ms
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_can import SupportCAN
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_service22 import SupportService22

SC = SupportCAN()
SSBL = SupportSBL()
SE22 = SupportService22()


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


def read_did_and_verify(dut, did_to_read):
    """
    Verify ReadDataByIdentifier(0x22) service with programming DID
    Args:
        dut (Dut): An instance of Dut
        did_to_read (str): Programming DID
    Returns:
        (bool): True when received NRC-31(requestOutOfRange)
    """
    # Padding the payload with 0x00 till the size becomes payload_length
    payload = SC.fill_payload(bytes.fromhex(did_to_read), fill_value=0)
    response = dut.uds.read_data_by_id_22(payload, b'')

    if response.raw[2:4] == '7F' and response.raw[6:8] == '13':
        logging.info("Received NRC-%s for request ReadDataByIdentifier as expected",
                      response.raw[6:8])
        return True

    logging.error("Test Failed: Expected NRC-31(requestOutOfRange), received %s", response)
    return False


def step_1(dut: Dut):
    """
    action: Send multi-frame and verify server reply with CTS with correct separation time
            in PBL session
    expected_result: True when separation time is 0ms
    """
    # Set to programming session
    dut.uds.set_mode(2)

    # Verify PBL session
    if SE22.get_ecu_mode(dut) != 'PBL':
        logging.error("Expected ECU to be in PBL session, received %s", SE22.get_ecu_mode(dut))
        return False
    logging.info("ECU is in %s session as expected", SE22.get_ecu_mode(dut))

    did_response = read_did_and_verify(dut, did_to_read='F121')
    if not did_response:
        logging.error("Test Failed: ECU unable to read DID 'F121' in PBL session")
        return False

    logging.info("Control Frame from Server: %s", SC.can_cf_received[dut["receive"]][0][2])
    logging.info("Separation time is [ms]: %d",
                 int(SC.can_cf_received[dut["receive"]][0][2][4:6], 16))

    # Test if separation time is maximum 0ms: get separation time from saved control frame
    if int(SC.can_cf_received[dut["receive"]][0][2][4:6], 16) == 0:
        result = True
        # Verify that ECU is still in PBL
        if SE22.get_ecu_mode(dut) != 'PBL':
            logging.error("Test Failed: ECU is not in PBL session")
            result = False
        else:
            logging.info("Separation time is 0 ms as expected")
    else:
        logging.error("Test Failed: Separation time is greater than 0 ms")
        result = False
    return result


def step_2(dut: Dut):
    """
    action: Send multi-frame and verify server reply with CTS with correct separation time
            in SBL session
    expected_result: True when separation time is 0ms
    """
    result = download_and_activate_sbl(dut)
    if not result:
        return False

    # Verify SBL session
    if SE22.get_ecu_mode(dut) != 'SBL':
        logging.error("Expected ECU to be in SBL session, received %s", SE22.get_ecu_mode(dut))
        return False
    logging.info("ECU is in %s session as expected", SE22.get_ecu_mode(dut))

    did_response = read_did_and_verify(dut, did_to_read='F122')
    if not did_response:
        logging.error("Test Failed: ECU unable to read DID 'F122' in SBL session")
        return False

    logging.info("Control Frame from Server: %s", SC.can_cf_received[dut["receive"]][0][2])
    logging.info("Separation time is [ms]: %d",
                 int(SC.can_cf_received[dut["receive"]][0][2][4:6], 16))

    # Test if separation time is maximum 0ms: get separation time from saved control frame
    if int(SC.can_cf_received[dut["receive"]][0][2][4:6], 16) == 0:
        result = True
        # Verify that ECU is still in SBL
        if SE22.get_ecu_mode(dut) != 'SBL':
            logging.error("Test Failed: ECU is not in SBL session")
            result = False
        else:
            logging.info("Separation time is 0 ms as expected")
    else:
        logging.error("Test Failed: Separation time is greater than 0 ms")
        result = False
    return result


def run():
    """
    Verify separation time (STmin) for server side in PBL and SBL session are maximum 0ms
    """
    dut = Dut()

    start_time = dut.start()
    result = True

    try:
        dut.precondition(timeout=100)

        result = dut.step(step_1, purpose="Send multi-frame and verify server reply with CTS "
                                          "with correct separation time in PBL session")
        result = result and dut.step(step_2, purpose="Send multi-frame and verify server reply "
                                                     "with CTS with correct separation time in "
                                                     " SBL session")

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
