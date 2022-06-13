"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 60010
version: 0
title: : Separation time (STmin) non-programming session server side
purpose: >
    Define STmin for non-programming session server side. For more information see
    section Separation (STmin) parameter definition.

description: >
    Separation time (STmin) for server side when in non-programming session shall be maximum
    15ms.

details: >
    Verify separation time (STmin) for server side in default and extended diagnostic session
    are maximum 15ms
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_can import SupportCAN
from supportfunctions.support_carcom import SupportCARCOM

SE22 = SupportService22()
SC = SupportCAN()
SIO = SupportFileIO()
SC_CARCOM = SupportCARCOM()


def request_read_data_id(dut:Dut, multiframe_did):
    """
    Verify the ReadDataByIdentifier service 22 with respective DID
    Args:
        dut (Dut): An instance of Dut
        multiframe_did (str): Multiframe DID
    Returns:
        (bool): True when received positive response
    """
    response = dut.uds.read_data_by_id_22(bytes.fromhex(multiframe_did))

    if response.raw[4:6] == '62':
        logging.info("Received positive response 62 for request ReadDataByIdentifier")
        return True

    logging.error("Test Failed: Expected positive response, received %s", response)
    return False


def step_1(dut: Dut):
    """
    action: Send multiframe and verify server reply with CTS with correct separation time
            in default session
    expected_result: True on positive response
    """
    response = SE22.read_did_f186(dut, dsession=b'\x01')

    if not response:
        logging.error("ECU is not in default session")
        return False

    did_response = request_read_data_id(dut, 'DD02DD0ADD0C4947')
    if not did_response:
        logging.error("Test Failed: ECU unable to read DID DD02DD0ADD0C4947 in default session")
        return False

    logging.info("Control Frame from Server: %s", SC.can_cf_received[dut["receive"]][0][2])
    logging.info("Separation time is [ms]: %d",
                 int(SC.can_cf_received[dut["receive"]][0][2][4:6], 16))

    # Test if ST is less than 15 ms: get ST from saved Control Frame
    if int(SC.can_cf_received[dut["receive"]][0][2][4:6], 16) < 15:
        result_default = SE22.read_did_f186(dut, dsession=b'\x01')
        if not result_default:
            logging.error("ECU is not in default session")
            return False
        logging.info("Separation time is less than 15 ms as expected")
        return True

    logging.error("Test Failed: Separation time is bigger than 15 ms")
    return False


def step_2(dut: Dut):
    """
    action: Send multiframe and verify server reply with CTS with correct separation time
            in extended session
    expected_result: True on positive response
    """
    # Set to extended session
    dut.uds.set_mode(3)

    response = SE22.read_did_f186(dut, dsession=b'\x03')
    if not response:
        logging.error("ECU is not in extended session")
        return False

    did_response = request_read_data_id(dut, 'DD02DD0ADD0C4947')
    if not did_response:
        logging.error("Test Failed: ECU unable to read DID DD02DD0ADD0C4947 in extended session")
        return False

    logging.info("Control Frame from Server: %s", SC.can_cf_received[dut["receive"]][0][2])
    logging.info("Separation time is [ms]: %d",
                 int(SC.can_cf_received[dut["receive"]][0][2][4:6], 16))

    # Test if ST is less than 15 ms: get ST from saved Control Frame
    if int(SC.can_cf_received[dut["receive"]][0][2][4:6], 16) < 15:
        result_ext = SE22.read_did_f186(dut, dsession=b'\x03')
        if not result_ext:
            logging.error("ECU is not in Extended session")
            return False

        logging.info("Separation time is less than 15 ms as expected")
        # set to default session
        dut.uds.set_mode(1)
        return True

    logging.info("Test Failed: Separation time is bigger than 15 ms")
    return False


def run():
    """
    Verify separation time (STmin) for server side in default and extended diagnostic session
    is maximum 15ms
    """
    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=60)

        result_step = dut.step(step_1, purpose="Send multiframe and verify server reply with CTS "
                                               "with correct separation time in default session")

        if result_step:
            result_step = dut.step(step_2, purpose="Send multiframe and verify server reply with "
                                                   "CTS with correct separation time in extended"
                                                   " session")

        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
