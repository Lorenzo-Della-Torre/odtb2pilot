"""
Testscript ODTB2 MEPII
project:  BECM basetech MEPII
author:   DHJELM (Daniel Hjelm)
date:     2020-11-23
version:  3
reqprod:  60103

title:

    Handling of DLC on Classic CAN ; 3

purpose:

    Define how the recipient to react upon DLCs received
    on Classic CAN.


description:

    USDT request frames with a DLC not equal to eight (8) for Classic CAN shall
    be considered invalidly formatted and be ignored by the recipient.

details:

    This requirement is tested by sending a DD00 request first with proper
    padding and hence the DLC record should be set correctly to 8 bytes and
    then one request without padding. DD00 requests are short and without
    padding will not extend to the required 8 bytes of the USDT frame, hence it
    should be rejected.

"""

import os
import sys
import logging

from supportfunctions.support_dut import Dut
from supportfunctions.support_dut import DutTestError
from supportfunctions.support_uds import global_timestamp
from supportfunctions.support_uds import UdsEmptyResponse

def step_1(dut):
    """
    Attempt to get the global timestamp
    """
    data = dut.uds.read_data_by_identifier(global_timestamp)
    if not data:
        raise DutTestError("No global_timestamp data received")

    assert 'DD00' in data

def step_2(dut):
    """
    Attempt to get the global timestamp with DLC set to 7 bytes
    """
    platform = os.getenv("ODTBPROJ")
    if platform == "MEP2_SPA1":
        dut.reconfigure_broker(
            "BO_ 1845 Vcu1ToBecmFront1DiagReqFrame: 8 VCU1",
            "BO_ 1845 Vcu1ToBecmFront1DiagReqFrame: 7 VCU1",
        )

    if platform == "MEP2_SPA2":
        dut.reconfigure_broker(
            "BO_ 1875 HvbmdpToHvbmUdsDiagRequestFrame : 8 HVBMdp",
            "BO_ 1875 HvbmdpToHvbmUdsDiagRequestFrame : 7 HVBMdp"
        )

    try:
        dut.uds.read_data_by_identifier(global_timestamp)
    except UdsEmptyResponse:
        logging.info("Received an empty response as expected when using 7 byte frame")

    dut.reconfigure_broker()

    # we need to run the precondition again to get the ECU to respond properly again.
    dut.precondition()

def run():
    """
    Handling of DLC on classic CAN

    Note that this test requires the beamy signal broker
    """
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

    dut = Dut()

    start_time = dut.start()

    result = False

    try:
        dut.precondition()

        # step1:
        # action: Get time data from DTC snapshoot with a 8 byte long frame
        # result: We should be able to retrieve a timestamp from the response
        step_1(dut)

        # step2:
        # action: Get time data from DTC snapshoot with a 7 byte long frame
        # result: Any attempts with a DLC that is not 8 byte long should fail
        step_2(dut)

        result = True
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
