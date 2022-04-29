"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76446
version: 2
title: ReadDataByPeriodicIdentifier (2A) - transmissionMode fast (03)
purpose: >
    Define the transmissionMode fast

description: >
    The ECU may support the service readDataByPeriodicIdentifier with the data parameter
    transmissionMode set to fast in all sessions where the ECU supports the service
    readDataByPeriodicIdentifier. The implementer defines the value of the transmission rate
    in the transmissionMode fast. The transmissionMode fast is allowed to be defined as "as fast
    as possible" i.e. must not be fixed, it may change over time (e.g. be CPU load dependent).

details: >
    1. Checking response for ReadDataByPeriodicIdentifier(0x2A) in extendedDiagnosticSession with
    response code 0x6A
    2. Verify transmissionMode fast rate (0x03) in ReadDataByPeriodicIdentifier(0x2A) service.
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


def verify_positive_response(dut, parameters, periodic_dids):
    """
    Verify ReadDataByPeriodicIdentifier(0x2A) positive response 0x6A
    Args:
        dut(Dut): Dut instance
        parameters (dict): initial_response_time, fast_rate_max_time
        periodic_dids (str): periodic did
    Returns:
        (bool): True on successfully verified positive response
    """
    results = []
    # Initial waiting time 25ms + interval positive response
    time.sleep(parameters['initial_response_time']/1000)
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
        time.sleep(parameters['fast_rate_max_time']/1000)

    if all(results) and len(results) == int(len(periodic_dids)/2):
        logging.info("Received positive response for periodic DIDs in extended session"
                     " as expected")
        return True

    logging.error("Unable to receive positive response for periodic DIDs in extended session")
    return False


def request_read_data_periodic_identifier(dut: Dut, periodic_dids):
    """
    Request ReadDataByPeriodicIdentifier(0x2A) with transmission mode fast rate 0x03 and
    get the ECU response
    Args:
        dut(Dut): Dut instance
        periodic_dids(str): Periodic identifier dids
    """
    # Request periodic did with transmissionMode fast rate
    payload = SC_CARCOM.can_m_send("ReadDataByPeriodicIdentifier", b'\x03' +
                                    bytes.fromhex(periodic_dids), b'')
    dut.uds.generic_ecu_call(payload)


def step_1(dut: Dut, parameters):
    """
    action: Set to extended mode and verify ReadDataByPeriodicIdentifier(0x2A) response
            with transmissionMode fast rate 0x03
    expected_result: ECU should send positive response 0x6A within fast rate(25ms)
    """
    dut.uds.set_mode(3)

    # Initiate ReadDataByPeriodicIdentifier
    request_read_data_periodic_identifier(dut, parameters['periodic_dids'])

    result = verify_positive_response(dut, parameters, parameters['periodic_dids'])

    # Stop dynamically defined periodic DID
    payload = SC_CARCOM.can_m_send("ReadDataByPeriodicIdentifier", b'\x04'
                                   + bytes.fromhex(parameters['periodic_dids']), b'')
    dut.uds.generic_ecu_call(payload)

    if result:
        logging.info("Successfully verified positive response for periodic DIDs in "
                     "extended session with transmissionMode fast 0x03")
        return True
    logging.error("Test Failed: Received unexpected response for one or more periodic DIDs")
    return False


def run():
    """
    Verify ReadDataByPeriodicIdentifier(0x2A) response with transmissionMode fast rate 0x03 and
    time interval 25ms
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    parameters_dict = {'periodic_dids': '',
                       'initial_response_time': 0,
                       'fast_rate_max_time': 0}

    try:
        dut.precondition(timeout=60)
        # Read periodic did from yml file
        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameter not found")

        result = dut.step(step_1, parameters, purpose='Verify '
                                              'ReadDataByPeriodicIdentifier(0x2A) response '
                                              'with transmissionMode fast in extended session')
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
