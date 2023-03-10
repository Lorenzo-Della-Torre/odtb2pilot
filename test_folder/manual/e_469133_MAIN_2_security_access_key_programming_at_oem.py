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
from supportfunctions.support_sec_acc import SecAccessParam
from supportfunctions.support_sec_acc import SupportSecurityAccess
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_SBL import SupportSBL


SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
SIO = SupportFileIO()
SSA = SupportSecurityAccess()
SE22 = SupportService22()
SSBL = SupportSBL()


def activate_sbl(dut, sa_key):
    """
    Download and activate SBL
    Args:
        dut (Dut): Dut instance
        sa_key (str): security access key
    Returns:
        True when SBL is successfully downloaded and activated
    """

    # Load VBF files
    if not SSBL.get_vbf_files():
        logging.error("Test Failed: Unable to load VBF files")
        return False

    # SBL activation
    if not SSBL.sbl_activation(dut, sa_key):
        logging.error("Test Failed: Unable to activate SBL")
        return False

    # Get current ECU mode
    if not SE22.verify_sbl_session(dut):
        logging.error("Test Failed: Expected ECU to be in SBL session")
        return False

    return True

def security_access(dut: Dut, sa_level):
    """
    Unlock security access levels to ECU
    Args:
        dut (Dut): Dut instance
        sa_level (str): HEX security level
    Returns:
        Response (bool): True if ECU is unlocked with given security access level
    """

    # Request a seed from ECU
    SSA.set_keys(dut.conf.default_rig_config)
    sa_level_decimal = int(sa_level, 16) # set_level_key is using sa_level as decimal variable
    SSA.set_level_key(sa_level_decimal)
    payload = SSA.prepare_client_request_seed()
    response = dut.uds.generic_ecu_call(payload)

    # Calculate the key with the server seed
    server_seed = response.raw[4:]
    result = SSA.process_server_response_seed(bytearray.fromhex(server_seed))

    # Send key to unlock ECU
    payload = SSA.prepare_client_send_key()
    response = dut.uds.generic_ecu_call(payload)

    # Process response from ECU
    result = SSA.process_server_response_key(bytearray.fromhex(response.raw[6:(6+4)]))
    if result != 0:
        logging.error("Security access denied.")
        return False

    logging.info("ECU unlock with security access %s", sa_level)
    return True


def program_key(dut: Dut, did, sa_key):
    """
    Send a request to program the security access key
    Args:
        dut (Dut): Dut instance
        did (str): Security access DID
        sa_key (str): Security access key to write
    response
        response.raw (str): ECU response
    """

    # calculate crc16 checksum
    checksum = hex(SUTE.crc16(bytes.fromhex(sa_key)))

    # prepare request to send to the ECU
    message = bytes.fromhex(did + sa_key + checksum[2:])

    # send request and store response
    response = dut.uds.generic_ecu_call(SC_CARCOM.can_m_send("WriteDataByIdentifier",
                                                            message, b''))
    return response.raw

def step_1(dut: Dut, sa_levels_dids_extended):
    """
    action: Try to program security access key twice in extended session
    expected_result: True when successfully verified keys are by default one-time-programmed.
    """

    # Setting up key
    sa_key: SecAccessParam = dut.conf.default_rig_config
    sa_key2write = sa_key["auth_key"]+sa_key["proof_key"]

    for level, did in sa_levels_dids_extended.items():

        # set ECU to extended session
        dut.uds.set_mode(3)

        # unlock ECU security access
        if not security_access(dut, level):
            return False

        # program security access key a first time
        response = program_key(dut, did, sa_key2write)

        if response[2:4] != "6E":
            logging.error("Failed to write DID %s. received: %s", did, response)
            return False
        logging.info("DID %s successfully programmed", did)

       # attempt to program security access key a second time
        response = program_key(dut, did, sa_key2write)

        if response[2:8] != "7F2E22":
            logging.error("Expected request to fail because of condition not correct."
                          " Received: %s", response)
            return False
        logging.info("Unable to write DID %s a second time as expected", did)

        # reset ECU
        dut.uds.ecu_reset_1101()
        time.sleep(5)

    return True

def step_2(dut: Dut, sa_levels_dids_programming):
    """
    action: Try to program security access key twice in programming session SBL
    expected_result: True when successfully verified keys are by default one-time-programmed.
    """

    # Setting up key
    sa_key: SecAccessParam = dut.conf.default_rig_config
    sa_key2write = sa_key["auth_key"]+sa_key["proof_key"]

    for level, did in sa_levels_dids_programming.items():

        # set ECU to programming session
        dut.uds.set_mode(2)

        # unlock ECU security access
        if not security_access(dut, level):
            return False

        # Activate SBL with the security access key
        if not activate_sbl(dut, sa_key):
            logging.error("Unable to activate SBL")
            return False
        logging.info("SBL successfully activated")

        # program security access key a first time
        response = program_key(dut, did, sa_key2write)

        if response[2:4] != "6E":
            logging.error("Failed to write DID %s. received: %s", did, response)
            return False
        logging.info("DID %s successfully programmed", did)

       # attempt to program security access key a second time
        response = program_key(dut, did, sa_key2write)

        if response[2:8] != "7F2E22":
            logging.error("Expected request to fail because of condition not correct."
                          " Received: %s", response)
            return False
        logging.info("Unable to write DID %s a second time as expected", did)

        # reset ECU
        dut.uds.ecu_reset_1101()
        time.sleep(5)

    return True

def run():
    """
    Verify keys are by default one-time-programmable
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {"sa_levels_dids_programming" : {},
                       "sa_levels_dids_extended" : {}}
    try:
        dut.precondition(timeout=400)

        # Read yml parameters
        parameters = SIO.parameter_adopt_teststep(parameters_dict)

        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        # start test steps
        result_step = dut.step(step_1, parameters['sa_levels_dids_extended'],
                                purpose="try to program extended session security access keys "
                                "twice")
        result_step = result_step and dut.step(step_2, parameters['sa_levels_dids_programming'],
                                purpose="try to program programming session SBL security access "
                                "keys twice")
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
