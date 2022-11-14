"""
/*********************************************************************************/


Copyright © 2022 Volvo Car Corporation. All rights reserved.


NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 469133
version: 2
title: Security Access key programming at OEM

purpose: >
    Define how to program (update) the security access key(s).

description: >
    The ECU shall be equipped with initial security access key(s) per supported security access
    level when provided to OEM, where the actual keys for production vehicle are programmed using
    the writeDataByIdentifier service. The key(s) shall by default be one-time-programmable with no
    possibility to return to previous key, i.e. the ECU key programing function shall be disabled.
    The belonging security access level must be unlocked in order to perform the write-once
    operation.

    If some use-case requires support for multiple key updates, it shall be documented as an
    approved deviation.

    Example-
    ECU Security access level YY is unlocked
    The key for level YY is programmed, using writeDataByIdentifier
    ECU validates the DID, format, checksum and stores the key if no previously key has been
    programmed.

details: >
    Verify if keys are by default one-time-programmable
    Steps:
    1. Unlock security access level for programming and extended diagnostic session and DIDs
    2. Program the key for respective levels using writeDataByIdentifier and
       verify positive response
    3. Reprogram the key for respective levels using writeDataByIdentifier and
       verify negative response
"""

import time
import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_sec_acc import SupportSecurityAccess
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO

SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
SIO = SupportFileIO()
SSA = SupportSecurityAccess()


def security_access(dut: Dut, sa_level):
    """
    Unlock security access levels to ECU
    Args:
        dut (Dut): Dut instance
        level (str): security level
    Returns:
        Response (str): Can response
    """
    SSA.set_keys(dut.conf.default_rig_config)
    SSA.set_level_key(int(sa_level))
    payload = SSA.prepare_client_request_seed()

    response = dut.uds.generic_ecu_call(payload)
    # Prepare server response seed
    server_res_seed = response.raw[4:]
    result = SSA.process_server_response_seed(bytearray.fromhex(server_res_seed))

    payload = SSA.prepare_client_send_key()
    client_send_key = payload.hex().upper()

    response = dut.uds.generic_ecu_call(payload)

    # Process server response key
    result = SSA.process_server_response_key(bytearray.fromhex(response.raw[6:(6+4)]))
    if result != 0:
        logging.error("Security access not successful")
        return None

    return client_send_key


def prepare_message(dut: Dut, did):
    """
    Prepare the message to program the key for respective levels using writeDataByIdentifier
    with payload & CRC.
    Args:
        dut (Dut): Dut instance
        did (str): Security access DID
    response
        response.raw (str): ECU response
    """
    sa_key_32byte = 'FF'*32
    crc = SUTE.crc16(bytearray(sa_key_32byte.encode('utf-8')))
    crc_hex = hex(crc)

    message = bytes.fromhex(did + sa_key_32byte + crc_hex[2:])

    response = dut.uds.generic_ecu_call(SC_CARCOM.can_m_send("WriteDataByIdentifier",
                                                            message, b''))
    return response.raw


def write_data_by_identifier_positive_response(dut: Dut, did, level):
    """
    Program the key for respective levels using writeDataByIdentifier with payload & CRC.
    Args:
        dut (Dut): Dut instance
        did (str): Security access DID
        level (str): Security level
    Returns:
        (bool): True when received positive response
    """
    response = prepare_message(dut, did)

    # Extract and validate positive response
    if response[6:8] == '6E':
        logging.info("Received positive response %s as expected", response)
        logging.info("Successfully verified the key is one-time-programmed for"
                     " security level %s and did %s", level, did)
        return True

    logging.error("Test Failed: Expected 6E, received %s", response)
    return False


def write_data_by_identifier_negative_response(dut: Dut, did, level):
    """
    Reprogram the key for respective levels using writeDataByIdentifier with payload & CRC.
    Args:
        dut (Dut): Dut instance
        did (str): Security access DID
        level (str): Security level
    Returns:
        (bool): True when received negative response
    """
    response = prepare_message(dut, did)

    # Extract and validate negative response
    if response[6:8] == '7F':
        logging.info("Received negative response %s as expected", response)
        logging.info("Successfully verified the key is by default one-time-programmed for"
                     " security level %s and did %s", level, did)
        return True

    logging.error("Test Failed: Expected 7F, received %s", response)
    return False


def verify_results(results, session):
    """
    Verify the response of writeDataByIdentifier for all security access levels
    Args:
        results (list): List of boolean based on ECU response
        session (str): Diagnostic session
    Returns:
        (bool): True when all results are true
    """
    if all(results) and len(results) != 0:
        logging.info("Key is by default one-time-programmed for all security access level in"
                     " %s session", session)
        return True

    logging.error("Test Failed: Key is not one-time-programmed for respective security access"
                  " level in %s session", session)
    return False


def step_1(dut: Dut, sa_levels_dids_programming):
    """
    action: Set ECU to programming session and send WriteDataByIdentifier for supported security
            access levels i.e. 01 and 19 to verify keys are by default one-time-programmed.
    expected_result: True when successfully verified keys are by default one-time-programmed.
    """
    results = []

    # Set ECU in programming session
    dut.uds.set_mode(2)

    # Sleep time to avoid NRC37
    time.sleep(5)

    # Validate response for all security levels
    for level, did in sa_levels_dids_programming.items():
        response = security_access(dut, level)
        if response is not None:
            results.append(write_data_by_identifier_positive_response(dut, did, level))
            results.append(write_data_by_identifier_negative_response(dut, did, level))
        else:
            logging.error("Test Failed: Security access denied for level %s", level)
            results.append(False)

    result = verify_results(results, session='programming')
    return result


def step_2(dut: Dut, sa_levels_dids_extended):
    """
    action: Set ECU to Extended session and send WriteDataByIdentifier for supported security access
            levels i.e. 05, 19, 23 to verify keys are by default one-time-programmed.
    expected_result: True when successfully verified keys are by default one-time-programmed.
    """
    results = []

    # Set ECU in extended session
    dut.uds.set_mode(1)
    dut.uds.set_mode(3)

    # Validate response for all security levels
    for level, did in sa_levels_dids_extended.items():
        response = security_access(dut, level)
        if response is not None:
            results.append(write_data_by_identifier_positive_response(dut, did, level))
            results.append(write_data_by_identifier_negative_response(dut, did, level))
        else:
            logging.error("Test Failed: Security access denied for level %s", level)
            results.append(False)

    result = verify_results(results, session='extended')
    return result


def run():
    """
    Verify if keys are by default one-time-programmable
    Steps:
    1. Unlock security access level for programming and extended diagnostic session and DIDs
    2. Program the key for respective levels using writeDataByIdentifier and
       verify positive response
    3. Reprogram the key for respective levels using writeDataByIdentifier and
       verify negative response
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {"sa_levels_dids_programming" : {},
                       "sa_levels_dids_extended" : {}}
    try:
        dut.precondition(timeout=60)
        # Read yml parameters
        parameters = SIO.parameter_adopt_teststep(parameters_dict)

        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step = dut.step(step_1, parameters['sa_levels_dids_programming'], purpose="Verify"
                               "  key is by default one-time-programmed for respective security"
                               " access level in programming session")
        if result_step:
            result_step = dut.step(step_2, parameters['sa_levels_dids_extended'], purpose="Verify"
                                   " key is by default one-time-programmed for respective security"
                                   " access level in extended session")

        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
