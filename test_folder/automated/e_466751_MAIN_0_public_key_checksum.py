"""

/*********************************************************************************/



Copyright © 2023 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 466751
version: 0
title: : Public Key Checksum data record
purpose: >
    To support diagnostic processes this information must be accessible in application,
    to not have to force the vehicle into programmingSession

description: >
    If the ECU is supporting the Software Authentication concept as defined in
    Ref[LC : General Software Authentication], where the key type is "RAW_KEY_TYPE_WITH_CHECKSUM",
    the ECU shall implement a data record as specified in the table below:

    ----------------------------------------------
    Description	                    Identifier
    ----------------------------------------------
    swAuth Public Key CheckSum	    D03A
    ----------------------------------------------

    It shall be possible to read the data record by using the diagnostic service specified in
    Ref[LC : Volvo Car Corporation - UDS Services - Service 0x22 (ReadDataByIdentifier) Reqs].
    The ECU shall implement the data record exactly as defined in Carcom Global Master Referenced
    Database (GMRDB).

    The ECU shall support the identifier in the following sessions:
    •   Default session
    •   Extended Session

details: >
    Verify public key checksum data record with ReadDataByIdentifier(0x22) service using
    DID 'D03A' and also verify it is supported in default and extended session.
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_service22 import SupportService22

SIO = SupportFileIO()
SE22 = SupportService22()


def request_read_data_by_id(dut, did_to_read, session):
    """
    Request ReadDataByIdentifier(0x22) service
    Args:
        dut (Dut): An instance of Dut
        did_to_read (str): DID 'D03A'
        session (str): Diagnostic session
    Returns:
        (bool): True when received positive response '62'
    """
    result = False
    response = dut.uds.read_data_by_id_22(bytes.fromhex(did_to_read))

    if response.raw[4:6] == '62' and response.raw[6:10] == did_to_read:
        logging.info("Received positive response %s for request ReadDataByIdentifier(0x22) "
                     "service in %s session", response.raw[4:6], session)
        result = True
    else:
        logging.error("Test Failed: Expected positive response '62' for request "
                      "ReadDataByIdentifier(0x22) service in %s session, received %s", session,
                      response.raw)
        result = False

    return result


def step_1(dut: Dut):
    """
    action: Set ECU to default session
    expected_result: ECU should be in default session
    """
    # Set to default session
    dut.uds.set_mode(1)

    # Verify active diagnostic session
    result = SE22.read_did_f186(dut, b'\x01')
    if result:
        logging.info("ECU is in default session as expected")
    else:
        logging.error("Test Failed: ECU is not in default session")

    return result


def step_2(dut: Dut, sw_auth_public_key_checksum):
    """
    action: Read DID 'swAuth Public Key CheckSum' in default session
    expected_result: ECU should send positive response '62' in default session
    """
    return request_read_data_by_id(dut, sw_auth_public_key_checksum, 'default')


def step_3(dut: Dut):
    """
    action: Set ECU to extended session
    expected_result: ECU should be in extended session
    """
    # Set to extended session
    dut.uds.set_mode(3)

    # Verify active diagnostic session
    result = SE22.read_did_f186(dut, b'\x03')
    if result:
        logging.info("ECU is in extended session as expected")
    else:
        logging.error("Test Failed: ECU is not in extended session")

    return result


def step_4(dut: Dut, sw_auth_public_key_checksum):
    """
    action: Read DID 'swAuth Public Key CheckSum' in extended session
    expected_result: ECU should send positive response '62' in extended session
    """
    return request_read_data_by_id(dut, sw_auth_public_key_checksum, 'extended')


def run():
    """
    Verify public key checksum data record with ReadDataByIdentifier(0x22) service using
    DID 'D03A' and also verify it is supported in default and extended session.
    """
    dut = Dut()

    start_time = dut.start()

    parameters_dict = {'sw_auth_public_key_checksum': ''}

    try:
        dut.precondition(timeout=90)

        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result = dut.step(step_1, purpose="Set ECU to default session")
        result = result and dut.step(step_2, parameters['sw_auth_public_key_checksum'],
                                     purpose="Read DID 'swAuth Public Key CheckSum' in default "
                                             "session")
        result = result and dut.step(step_3, purpose="Set ECU to extended session")
        result = result and dut.step(step_4, parameters['sw_auth_public_key_checksum'],
                                     purpose="Read DID 'swAuth Public Key CheckSum' in extended "
                                             "session")

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
