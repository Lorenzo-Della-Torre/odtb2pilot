/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



**********************************************************************************/


"""
reqprod:
    76499
title:
    ReadDTCInformation (19)
purpose:
    Read DTC information
description:
    The ECU shall support the service ReadDTCInformation. The ECU shall implement the service
    accordingly:

    Supported sessions:
    The ECU shall support Service ReadDTCInformation in:
    •	defaultSession
    •	extendedDiagnosticSession
    Response time:
    Maximum response time for the service readDTCInformation (0x19) is 500 ms.

    Effect on the ECU normal operation:
    The service ReadDTCInformation (0x19) shall not affect the ECU’s ability to execute
    non-diagnostic tasks.

    Entry conditions:
    The ECU shall not implement entry conditions for service readDTCInformation (0x19).

    Security access:
    The ECU shall not protect service ReadDTCInformation by using the service securityAccess (0x27).
details:
    Requesting DTC information, expecting the requested DTC in response. Measuring time to make
    sure it is less than maximum allowed.
    Doing the same in extended session.
    Requesting DTC information in programming session, expecting the error 'serviceNotSupported'.
"""

import logging

from hilding.dut import Dut
from hilding.dut import DutTestError

# The DTC we use
DTC = '0B4A00'

def step_sup(dut: Dut):
    """
    action:
        Verify ReadDTCInfoExtDataRecordByDTCNumber reply positively
    expected_result:
        -
    """
    res = dut.uds.dtc_extended_1906(bytes.fromhex(DTC))
    logging.info(res)
    if res.data.get('dtc') != DTC:
        raise DutTestError('Incorrect DTC ID in response')

    max_resp_time = 500
    network_latency = 30
    if dut.uds.milliseconds_since_request() > max_resp_time + network_latency:
        # Took too long to receive response from the server.
        raise DutTestError("Failed: Service took too long to respond.")


def step_not_sup(dut: Dut):
    """
    action:
        Verify ReadDTCInfoExtDataRecordByDTCNumber reply positively
    expected_result:
        -
    """
    res = dut.uds.dtc_extended_1906(bytes.fromhex(DTC))
    logging.info(res)

    if res.data.get('nrc_name') != 'serviceNotSupported':
        raise DutTestError('Did not recieve the expected serviceNotSupported')


def run():
    """
    Run - Call other functions from here
    """
    dut = Dut()
    start_time = dut.start()

    result = True
    try:
        dut.precondition(timeout=30)
        dut.step(step_sup,
                 purpose="Verify ReadDTCInfoExtDataRecordByDTCNumber reply positively")

        # Change to extended session
        dut.uds.set_mode(3)

        dut.step(step_sup,
                 purpose="Verify ReadDTCInfoExtDataRecordByDTCNumber reply positively in"\
                 " ext session")

        # Change to programming session
        dut.uds.set_mode(2)

        dut.step(step_not_sup,
                 purpose="Verify ReadDTCInfoExtDataRecordByDTCNumber reply with"\
                 " serviceNotSupported in programming session")

    except DutTestError as error:
        logging.error("Test failed: %s", error)
        result = False
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
