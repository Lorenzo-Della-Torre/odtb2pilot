"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76171
version: 2
title: ReadDataByIdentifier (22) - multiple identifiers with one request
purpose: >
    The manufacturing and aftersales tool supports reading several DIDs simultaneously from one
    ECU. Since the time for each request will be to long, the ECU shall be able to package
    several data record in one response message

description: >
    The ECU shall support a minimum 10 dataIdentifiers, or as many dataIdentifiers as implemented,
    in one single ReadDataByIdentifier request in default and extended diagnostic session.
    The ECU is permitted to reject requests with multiple dataIdentifiers when the response is
    larger than 61 bytes. In programmingSession only one dataIdentifier needs to be supported.

details: >
    Verify ECU supports minimum 10 data identifiers in default and extended session
    and only one data identifier in programming session.
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_can import SupportCAN
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_file_io import SupportFileIO

SC_CARCOM = SupportCARCOM()
SUTE = SupportTestODTB2()
SC = SupportCAN()
SE22 = SupportService22()
SIO = SupportFileIO()


def did_count_find(dids_to_read, response):
    """
    Verify DIDs are present in ECU response
    Args:
        dids_to_read (list): DIDs
        response (str): ECU response
    Returns:
        (bool): True when all DIDs are present
    """
    results = []
    for did in dids_to_read:
        did_count = response.count(did)
        if did_count != 0:
            results.append(True)
        else:
            logging.error("%s DID not found in ECU response", did)
            results.append(False)

    if all(results) and len(results) != 0:
        logging.info("Successfully verified that all the DIDs are present in ECU response")
        return True

    logging.error("Test Failed: Some DIDs not present in ECU response")
    return False


def read_data_id_with_dids(dut:Dut, dids_to_read):
    """
    Verify ReadDataByIdentifier service 22 with multiple DIDs for positive response
    Args:
        dut (Dut): An instance of Dut
        dids_to_read (list): DIDs
    Returns:
        (bool): True on successfully verified positive response
    """
    if isinstance(dids_to_read, list):
        payload = ''.join(dids_to_read)
    else:
        payload = dids_to_read
    response = dut.uds.read_data_by_id_22(bytes.fromhex(payload))
    if response.raw[4:6] == '62':
        # Check if expected DID are contained in reply
        result = did_count_find(dids_to_read, response.raw)
        if not result:
            return False
        logging.info("Received positive response %s for request ReadDataByIdentifier",
                      response.raw[4:6])
        return True

    logging.error("Test Failed: Expected positive response, received %s", response)
    return False


def read_data_id_with_dids_negative_31(dut:Dut, dids_to_read):
    """
    Verify ReadDataByIdentifier service 22 with multiple DIDs for negative response
    Args:
        dut (Dut): An instance of Dut
        dids_to_read (list): DIDs
    Returns:
        (bool): True on successfully verified negative response
    """
    payload = ''.join(dids_to_read)
    response = dut.uds.read_data_by_id_22(bytes.fromhex(payload))
    if response.raw[2:4] == '7F' and response.raw[6:8] == '31' :
        logging.info("Received NRC %s for request ReadDataByIdentifier as expected",
                      response.raw[6:8])
        return True

    logging.error("Test Failed: Expected NRC '31', received %s", response.raw)
    return False


def read_data_id_with_dids_negative_13(dut:Dut, dids_to_read):
    """
    Verify ReadDataByIdentifier service 22 with multiple DIDs for negative response
    Args:
        dut (Dut): An instance of Dut
        dids_to_read (list): DIDs
    Returns:
        (bool): True on successfully verified negative response
    """
    payload = ''.join(dids_to_read)
    response = dut.uds.read_data_by_id_22(bytes.fromhex(payload))
    if response.raw[2:4] == '7F' and response.raw[6:8] == '13' :
        logging.info("Received NRC %s for request ReadDataByIdentifier as expected",
                      response.raw[6:8])
        return True

    logging.error("Test Failed: Expected NRC '13', received %s", response.raw)
    return False


def read_data_id_with_composite_dids(dut:Dut, dids_to_read, composite_did):
    """
    Verify ReadDataByIdentifier service 22 with multiple DIDs for positive response
    Args:
        dut (Dut): An instance of Dut
        dids_to_read (list): DIDs
        composite_did (list): Composite DIDs for respective DID
    Returns:
        (bool): True on successfully verified positive response
    """
    payload = ''.join(dids_to_read)
    response = dut.uds.read_data_by_id_22(bytes.fromhex(payload))
    if response.raw[4:6] == '62':
        # Check if expected DID are contained in reply
        result = did_count_find(composite_did, response.raw)
        if not result:
            return False
        logging.info("Received positive response %s for request ReadDataByIdentifier",
                      response.raw[4:6])
        return True

    logging.error("Test Failed: Expected positive response, received %s", response)
    return False


def check_active_session(dut:Dut, mode, session):
    """
    Verify active diagnostic session
    Args:
        dut (Dut): An instance of Dut
        mode (bytes): Diagnostic session in bytes
        session (str): Diagnostic session
    Returns:
        (bool): True on successfully verified active diagnostic session
    """
    # Read active diagnostic session
    active_session = SE22.read_did_f186(dut, mode)
    if not active_session:
        logging.error("Test Failed: ECU is not in %s session", session)
        return False
    return True


def step_1(dut: Dut, parameters):
    """
    action: Verify the ECU supports 10 dataIdentifiers as implemented,
            in one single ReadDataByIdentifier request in default session.
    expected_result: True when ECU supports 10 dataIdentifiers in default session.
    """
    # Request 2 DIDs in one request and verify if DIDs are included in response
    result_non_prog_dids = read_data_id_with_dids(dut, parameters['non_prog_dids'])
    if not result_non_prog_dids:
        return False

    # Request 10 DIDs in one request - those with shortest response
    result_max_dids_with_less_bytes_in_return = \
    read_data_id_with_dids(dut, parameters['max_dids_with_less_bytes_in_return'])
    if not result_max_dids_with_less_bytes_in_return:
        return False

    # Check default session
    def_session_result = check_active_session(dut, b'\x01', session='default')
    if not def_session_result:
        return False

    # Request 11 DIDs at once and check if error message received
    result_exceeded_max_dids = \
    read_data_id_with_dids_negative_13(dut, parameters['exceeded_max_dids'])
    if not result_exceeded_max_dids:
        return False

    # Request 10 DIDs in one request - those with most bytes in response
    result_max_dids_with_less_bytes_in_return = \
    read_data_id_with_dids(dut, parameters['max_dids_with_most_bytes_in_return'])

    # Verify if composite DIDs are included in response
    result_composite_did = result_max_dids_with_less_bytes_in_return and\
                           read_data_id_with_composite_dids(dut, 'EDA0',\
                           parameters['def_ext_composite_did_eda0'])
    if not result_composite_did:
        return False

    logging.info("ECU supports 10 dataIdentifiers as implemented, in one single"
                 " ReadDataByIdentifier request in default session")
    return True


def step_2(dut: Dut, parameters):
    """
    action: Verify the ECU supports 10 dataIdentifiers as implemented,
            in one single ReadDataByIdentifier request in extended session.
    expected_result: True when ECU supports 10 dataIdentifiers in extended session.
    """
    # Change to extended session
    dut.uds.set_mode(3)

    # Check extended session
    ext_session_result = check_active_session(dut, b'\x03', session='extended')

    # Request 2 DIDs in one request and verify if DIDs are included in response
    result_non_prog_dids = ext_session_result and \
    read_data_id_with_dids(dut, parameters['non_prog_dids'])
    if not result_non_prog_dids:
        return False

    # Request 10 DIDs in one request - those with shortest response
    result_max_dids_with_less_bytes_in_return = \
    read_data_id_with_dids(dut, parameters['max_dids_with_less_bytes_in_return'])
    if not result_max_dids_with_less_bytes_in_return:
        return False

    # Request 11 DIDs at once and check if error message received
    result_exceeded_max_dids = \
    read_data_id_with_dids_negative_13(dut, parameters['exceeded_max_dids'])
    if not result_exceeded_max_dids:
        return False

    # Request 10 DIDs in one request - those with most bytes in response
    result_max_dids_with_most_bytes_in_return = \
    read_data_id_with_dids(dut, parameters['max_dids_with_most_bytes_in_return'])

    # Verify if composite DIDs are included in response
    result_composite_did = result_max_dids_with_most_bytes_in_return and \
                           read_data_id_with_composite_dids(dut, 'EDA0',\
                           parameters['def_ext_composite_did_eda0'])
    if not result_composite_did:
        return False

    # Check extended session
    ext_session_result = check_active_session(dut, b'\x03', session='extended')
    if not ext_session_result:
        return False

    logging.info("ECU supports 10 dataIdentifiers as implemented, in one single"
                 " ReadDataByIdentifier request in extended session")
    return True


def step_3(dut: Dut, parameters):
    """
    action: Verify in programmingSession only one dataIdentifier is supported
    expected_result: True when ECU rejects requests with multiple dataIdentifier
    """
    # Change to programming session
    dut.uds.set_mode(2)

    # Check programming session
    prog_session_result = check_active_session(dut, b'\x02', session='programming')

    # Send single request using did 'F121' and verify if DIDs are included in response
    result_single_did = prog_session_result and\
                        read_data_id_with_dids(dut, parameters['prog_dids'][0])
    if not result_single_did:
        return False

    # Send single request using did 'F12A' and verify if DIDs are included in response
    result_single_did_again = read_data_id_with_dids(dut, parameters['prog_dids'][1])
    if not result_single_did_again:
        return False

    # Request 2 DIDs - 'F121' and 'F12A'
    result_non_prog_dids = read_data_id_with_dids_negative_31(dut, parameters['prog_dids'])
    if not result_non_prog_dids:
        return False

    # Send request containing composite DID and verify if DIDs are included in response
    result_eda0_did = read_data_id_with_dids(dut, 'EDA0')

    # Verify if composite DIDs are included in reply
    result_composite_did = result_eda0_did and\
                         read_data_id_with_composite_dids(dut, 'EDA0',\
                         parameters['composite_did_eda0'])
    if not result_composite_did:
        return False

    # Check programming session
    prog_session_result = check_active_session(dut, b'\x02', session='programming')

    # Change to default session
    dut.uds.set_mode(1)

    # Check default session
    def_session_result = prog_session_result and\
                         check_active_session(dut, b'\x01', session='default')
    if not def_session_result:
        return False

    logging.info("Only one data identifier is supported in programming session")
    return True


def run():
    """
    Verify ECU supports minimum 10 data identifiers in default and extended session
    and only one data identifier in programming session.
    """
    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'composite_did_eda0': '',
                       'def_ext_composite_did_eda0': '',
                       'prog_dids': '',
                       'non_prog_dids':'',
                       'max_dids_with_less_bytes_in_return':'',
                       'exceeded_max_dids':'',
                       'max_dids_with_most_bytes_in_return':''}

    try:
        dut.precondition(timeout=70)
        parameters = SIO.parameter_adopt_teststep(parameters_dict)

        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step = dut.step(step_1, parameters, purpose="Verify the ECU supports 10"
                               " dataIdentifiers as implemented, in one single"
                               " ReadDataByIdentifier request in default session")
        if result_step:
            result_step = dut.step(step_2, parameters, purpose="Verify the ECU supports 10"
                                   " dataIdentifiers as implemented, in one single"
                                   " ReadDataByIdentifier request in extended session")
        if result_step:
            result_step = dut.step(step_3, parameters, purpose="Verify in programming session"
                                   " only one dataIdentifier is supported")
        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
