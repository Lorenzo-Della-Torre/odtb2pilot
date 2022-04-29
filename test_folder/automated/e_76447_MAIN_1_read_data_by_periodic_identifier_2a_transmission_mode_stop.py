"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76447
version: 1
title: ReadDataByPeriodicIdentifier (2A) - transmissionMode slow (04)
purpose:
    Shall be possible to stop reading periodic identifiers without for example changing session
    since if a session change is done a lot of other functionality might reset as well.

description: >
    The ECU shall support the service readDataByPeriodicIdentifier with the data parameter
    transmissionMode set to stop in all sessions where the ECU supports the service
    readDataByPeriodicIdentifier.

details: >
    1. Checking response for ReadDataByPeriodicIdentifier(0x2A) in extendedDiagnosticSession with
       response code 0x6A.
    2. Verify transmission mode parameter slow in ReadDataByPeriodicIdentifier(0x2A) service.
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO

SC_CARCOM = SupportCARCOM()
SIO = SupportFileIO()


def compare_positive_response(response, periodic_did):
    """
    Compare ReadDataByPeriodicIdentifier(0x2A) positive response
    Args:
        response (str): ECU response code
        periodic_did (str): Periodic did
    Returns:
        (bool): True on Successfully verified positive response
    """
    result = False
    if response[2:4] == '6A':
        logging.info("Received %s for request ReadDataByPeriodicIdentifier(0x2A) in extended "
                     "session as expected", response[2:4])
        result = True
    else:
        logging.error("Test Failed: Expected positive response %s, received %s in extended "
                      "session", periodic_did, response)
        result = False

    return result


def request_read_data_periodic_identifier(dut: Dut, periodic_did):
    """
    Request ReadDataByPeriodicIdentifier(0x2A) with the data parameter transmissionMode set to
    stop and get the ECU response
    Args:
        dut(Dut): Dut instance
        periodic_did(str): Periodic identifier did
    Returns:
        response.raw (str): ECU response of ReadDataByPeriodicIdentifier request
    """

    payload = SC_CARCOM.can_m_send("ReadDataByPeriodicIdentifier", b'\x04' +
                                   bytes.fromhex(periodic_did), b'')
    response = dut.uds.generic_ecu_call(payload)

    return response.raw


def step_1(dut: Dut, periodic_did):
    """
    action: Set to extended mode and verify ReadDataByPeriodicIdentifier(0x2A) response
            with transmission mode parameter set to stop.
    expected_result: ECU should send positive response 0x6A
    """

    dut.uds.set_mode(3)

    # Initiate ReadDataByPeriodicIdentifier
    response = request_read_data_periodic_identifier(dut, periodic_did)

    result = compare_positive_response(response, periodic_did)

    return result


def run():
    """
    Verify transmissionMode parameter stop 0x04 in ReadDataByPeriodicIdentifier(0x2A) service
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    parameters_dict = {'periodic_did': ''}

    try:
        dut.precondition(timeout=60)
        # Read periodic did from yml file
        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameter not found")

        result = dut.step(step_1, parameters['periodic_did'], purpose='Verify '
                          'ReadDataByPeriodicIdentifier(0x2A) response in extended session '
                          ' with the transmissionMode parameter set to stop')

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
