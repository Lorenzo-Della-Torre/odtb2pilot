"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 67865
version: 1
title: Dynamically defined periodic Data Identifiers in ascending order

purpose: >
    To simplify management of data identifiers in the Volvo Car Corporation tools

description: >
    If Dynamically defined periodic DataIdentifier data records are implemented they shall have
    data identifiers in the range as specified in the table below. The data records shall use the
    identifiers in ascending order starting from data identifier 0xF200 (i.e. if the ECU supports
    only one single dynamically defined periodicDataIdentifier then its value shall be 0xF200, if
    the ECU supports two dynamically defined periodicDataIdentifiers then the values shall be
    0xF200 and 0xF201, etc.)
    -------------------------------------------------------------------------
    Description	                                   |        Identifier range
    -------------------------------------------------------------------------
    Dynamically defined periodic Data Identifier   |        F200 - F240
    -------------------------------------------------------------------------

details: >
    Checking response of Dynamically defined periodic Data Identifiers in a sequence
    with response code 0x6A

"""

import logging
import time
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_can import SupportCAN

SC_CARCOM = SupportCARCOM()
SIO = SupportFileIO()
SC = SupportCAN()


def prepare_lookup_dids(start_did, end_did):
    """
    Prepare periodic DIDs list within specified range
    Args:
        start_did(str): Periodic DID start
        end_did(str): Periodic DID end
    Returns: periodic DIDs
    """
    current_did = start_did[2:]
    periodic_dids = current_did
    while current_did != end_did[2:]:
        did = int(current_did, 16) + 1
        current_did = format(did, '#04x')[2:].upper()
        periodic_dids = periodic_dids + current_did
    return periodic_dids


def verify_positive_response(dut, periodic_dids):
    """
    Dynamically defined periodic DataIdentifier(0x2A) positive response
    Args:
        dut (Dut): An instance of Dut
        periodic_dids(str): periodic dids
    Returns:
        (bool): True on Successfully verified positive periodic response
    """
    results = []
    dpos = 0
    for _ in range(int(len(periodic_dids)/2)):
        response = SC.can_messages[dut["receive"]][0][2]
        if response[4:6] == periodic_dids[dpos:dpos+2]:
            logging.info("Positive response %s received as expected",
                         periodic_dids[dpos:dpos+2])
            results.append(True)
        else:
            logging.error("Response received %s, expected %s", response[4:6],
                          periodic_dids[dpos:dpos+2])
            results.append(False)
        dpos = dpos+2
        time.sleep(12.5/1000)

    if all(results) and len(results) == int(len(periodic_dids)/2):
        logging.info("Dynamically defined periodic DIDs in sequence in "
                     "extended session as expected")
        return True

    logging.error("Dynamically defined periodic DIDs in sequence in "
                  "extended session as expected")
    return False


def request_read_data_periodic_identifier(dut: Dut, periodic_dids):
    """
    Request Dynamically defined periodic DataIdentifier(0x2A) and get the ECU response
    Args:
        dut(Dut): Dut instance
        periodic_dids(str): periodic dids
    """

    payload = SC_CARCOM.can_m_send("ReadDataByPeriodicIdentifier", b'\x01'+
                                   bytes.fromhex(periodic_dids), b'')

    response = dut.uds.generic_ecu_call(payload)
    return response.raw


def step_1(dut: Dut):
    """
    action: Set ECU to extended session and verify Dynamically defined periodic
    DataIdentifier(0x2A) positive response

    expected_result: ECU should send positive response
    """

    dut.uds.set_mode(3)
    # Read did from yml file
    parameters_dict = {'periodic_dids': {},
                       'slow_rate_max_time': 0}
    parameters = SIO.parameter_adopt_teststep(parameters_dict)

    if not all(list(parameters.values())):
        logging.error("Test Failed: yml parameter not found")
        return False

    periodic_dids = prepare_lookup_dids(parameters['periodic_dids']['start_did'],
                                        parameters['periodic_dids']['end_did'])

    # Initiate Dynamically defined periodic DataIdentifier
    response = request_read_data_periodic_identifier(dut, periodic_dids)
    if response[2:4] != '6A':
        logging.error("Test Failed: Initial response verification failed")
        return False

    result = verify_positive_response(dut, periodic_dids)
    # Stop dynamically defined periodic DID
    payload = SC_CARCOM.can_m_send("ReadDataByPeriodicIdentifier", b'\x04'
                                + bytes.fromhex(periodic_dids), b'')
    dut.uds.generic_ecu_call(payload)

    if result:
        logging.info("Successfully verified dynamically defined periodic DIDs in sequence")
        return True
    logging.error("Test Failed: Received unexpected response for one or more periodic DIDs")
    return False


def run():
    """
    Verify response of Dynamically defined periodic Data Identifiers in a sequence
    with response code 0x6A
    """
    dut = Dut()

    start_time = dut.start()
    result = False

    try:
        dut.precondition(timeout=60)
        result = dut.step(step_1, purpose='Verify Dynamically defined periodic '
                          'DataIdentifier(0x2A) response in extended session')

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
