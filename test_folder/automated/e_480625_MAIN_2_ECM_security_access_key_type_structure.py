"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 480625
version: 2
title: : Security Access key type structure
purpose: >
    Define the format and structure of the Security Access keys,
    when programmed to the ECU server for authentication method 0x0001.
    The distribution of keys to e.g. diagnostic clients shall comply
    with other methods.

description: >
    The Security Access key(s) shall be represented in hexadecimal format
    when programmed using writeDataByIdentifier service 0x2E at OEM. The
    specified DID numbers in the table "Security Access Levels definition"
    (REQPROD: 481795 - Security Access Levels) shall be used for writing
    security access keys for respective security access levels. The DID must
    not be possible to read.

    To ensure the integrity of the key, a checksum is appended to the key
    when programmed. The ECU must successfully verify the checksum prior to
    the keys are stored in non-volatile memory.

    The format of the key(s) when programmed shall be the concatenation of
    two AES-128 bits long keys followed by a two bytes long CRC16-CCIT. The
    CRC16-CCIT shall have the initial value 0xFFFF and using normal
    representation, i.e. the polynomial is 0x1021.

    There shall be different negative response codes to separate:
    •   Trying to program a security access key a second time, when a
        valid key has already been written once (conditions not correct)
    •   The checksum check fails when the key is programmed (request out of range).

    Message direction- Client --> Server
    Message Type- Diagnostic request writeDataByIdentifier

    Data byte | Description (all values are in hexadecimal) | Byte Value (Hex)
    --------------------------------------------------------------------------
    # 1          WriteDataByIdentifier Request SID               2E
    --------------------------------------------------------------------------
    # 2          Data Identifier - Security Access Key
                # 1 msb (high byte)          DID value for key
                for level 'xx'  Byte
    # 3          Data Identifier - Security Access Key for       to be programmed
                level 'xx'  Byte#2 lsb (low byte)
    --------------------------------------------------------------------------
    # 4          Security Access Proof-of-ownership Key          00-FF
                Data Record Byte#1 msb (high byte)
    # 19         Security Access Proof-of-ownership Key          00-FF
                Data Record Byte#16 lsb (low byte)
    --------------------------------------------------------------------------
    # 20        Security Access Encryption and
                Authentication Key Data Record Byte#1           00-FF
                msb (high byte)
    # 35        Security Access Encryption and
                Authentication Key Data Record Byte#16          00-FF
                lsb (low byte)
    # 36        Security Access key Checksum Byte#1             00-FF
                msb (high byte)	0x00=programmed
    # 37        Security Access key Checksum Byte#2             00-FF
                lsb (low byte)	0x00=programmed

    Notes;
        -   The actual Data Identifiers are specified in the OEM diagnostic database.There
            is one dedicated DID per security access level supported in the ECU.
        -   When key writing is done for common test objects (e.g. boxcars, rigs) it is
            recommended to use following key;0x55555555 55555555 55555555 55555555 55555555
            55555555 55555555 55555555 7D3F, i.e. CRC16 is 7D3F.

details: >
    Verifying if respective security access key are programmed for different access levels in all
    diagnostic sessions -
    Steps:
    • Verify NRC-13(incorrectMessageLengthOrInvalidFormat) for WriteDataByIdentifier with wrong
      structure and correct CRC in programming session

    • Verify NRC-13(incorrectMessageLengthOrInvalidFormat) for WriteDataByIdentifier with wrong
      structure and correct CRC in extended session

    • Verify NRC-31(requestOutOfRange) for WriteDataByIdentifier with correct structure and wrong
      CRC in programming session

    • Verify NRC-31(requestOutOfRange) for WriteDataByIdentifier with correct structure and wrong
      CRC in extended session

    • Verify DIDs is not readable with NRC-31(requestOutOfRange) response

        01 - Diagnostic services in programmingSession, e.g. software download (DID 0xF103)
        05 - Diagnostic services in extendedSession(DID 0xF10A)
        19 - Security Log (DID 0xF115)
        23 - Secure Debug (0xF112)
        27 - Secure On-board Communication (DID 0xF117)
"""

import logging
import time
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_sec_acc import SupportSecurityAccess

SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
SIO = SupportFileIO()
SSBL = SupportSBL()
SSA = SupportSecurityAccess()


def write_data_by_identifier_with_wrong_crc(dut: Dut, level, did):
    """
    WriteDataByIdentifier with valid structure & wrong CRC.
    Args:
        dut (Dut): An instance of Dut
        level (str): Security level
        did (str): Security access DID
    Returns:
        (bool): True when received NRC-31(requestOutOfRange)
    """
    sa_key_32byte = 'FF'*32
    wrong_crc_hex = 'FF'*2
    message = bytes.fromhex(did + sa_key_32byte + wrong_crc_hex)
    response = dut.uds.generic_ecu_call(SC_CARCOM.can_m_send("WriteDataByIdentifier",
                                                             message, b''))
    if response.raw[6:8] == '31':
        logging.info("Received NRC-31(requestOutOfRange) as expected")
        return True

    logging.error("Test Failed: Expected NRC-31, received %s for Security level %s and DID %s",
                   response.raw, level, did)
    return False


def write_data_by_identifier_with_wrong_structure(dut: Dut, level, did):
    """
    WriteDataByIdentifier with wrong structure & valid CRC.
    Args:
        dut (Dut): An instance of Dut
        level (str): Security level
        did (str): Security access DID
    Returns:
        (bool): True when received NRC-13(incorrectMessageLengthOrInvalidFormat)
    """
    sa_key_32byte = 'FF'*32
    crc = SUTE.crc16(bytearray(sa_key_32byte.encode('utf-8')))
    crc_hex = hex(crc)
    wrong_structure_33byte = 'FF'*33
    message = bytes.fromhex(did + wrong_structure_33byte + crc_hex[2:])

    response = dut.uds.generic_ecu_call(SC_CARCOM.can_m_send("WriteDataByIdentifier",
                                        message, b''))
    if response.raw[6:8] == '13':
        logging.info("Received NRC-13(incorrectMessageLengthOrInvalidFormat) as expected")
        return True

    logging.error("Test Failed: Expected NRC-13, received %s for Security level %s and DID %s",
                   response.raw, level, did)
    return False


def security_access(dut: Dut, level):
    """
    security access to ECU for request seed
    Args:
        dut (Dut): An instance of Dut
        level(str): Security access level
    Returns:
        (bool): True when security access successful
    """
    # Set security access key and level
    SSA.set_keys(dut.conf.default_rig_config)
    SSA.set_level_key(int(level, 16))

    # Prepare client request seed
    client_req_seed = SSA.prepare_client_request_seed()
    response = dut.uds.generic_ecu_call(client_req_seed)

    # Truncate initial 2 bytes from response to process server response seed
    server_res_seed = response.raw[4:]
    result = SSA.process_server_response_seed(bytearray.fromhex(server_res_seed))

    # Prepare client request seed
    client_resp_key = SSA.prepare_client_send_key()
    response = dut.uds.generic_ecu_call(client_resp_key)

    # Check serverResponseSeed is successful or not
    if result == 0 and '67' in response.raw:
        logging.info("Security access successful for level %s", level)
        return True

    logging.error("Security access denied for level %s", level)
    return False


def read_security_did(dut: Dut, level, did):
    """
    Read security DIDs
    Args:
        dut (Dut): An instance of Dut
        level (str): Security level
        did (str): Security access DID
    Returns:
        (bool): True when received NRC-31(requestOutOfRange)
    """
    response = dut.uds.read_data_by_id_22(bytes.fromhex(did))
    if response.raw[6:8] == '31':
        logging.info("Received NRC-31(requestOutOfRange) for level %s of read did %s", level, did)
        return True

    logging.error("Test Failed: Expected NRC-31, received %s for level %s and did %s ",
                   response.raw, level, did)
    return False


def step_1(dut: Dut, parameters):
    """
    action: WriteDataByIdentifier with wrong structure but correct CRC for all supported security
            level in programming session
    expected_result: True when received NRC-13(incorrectMessageLengthOrInvalidFormat) for all
                     supported security level
    """
    results = []
    # Set ECU is in programming session
    # Sleep time to avoid NRC37
    time.sleep(5)
    dut.uds.set_mode(2)

    '''SSBL.get_vbf_files()
    result = SSBL.sbl_activation(dut, sa_keys=dut.conf.default_rig_config)
    if not result:
        logging.error("Test Failed: SBL activation failed")
        return False'''

    for level, did in parameters['sa_levels_dids_programming'].items():
        result = write_data_by_identifier_with_wrong_structure(dut, level, did)
        results.append(result)

    if all(results) and len(results) == len(parameters['sa_levels_dids_programming']):
        logging.info("Received NRC-13 for incorrect structure in programming session as expected")
        return True

    logging.error("Test Failed: NRC-13 is not received for incorrect structure in programming "
                  "session")
    return False


def step_2(dut: Dut, parameters):
    """
    action: WriteDataByIdentifier with wrong structure but correct CRC for all supported security
            level in extended session
    expected_result: True when received NRC-13(incorrectMessageLengthOrInvalidFormat) for all
                     supported security level
    """
    results = []
    # Set ECU is in extended session
    dut.uds.set_mode(1)
    dut.uds.set_mode(3)

    for level, did in parameters['sa_levels_dids_extended'].items():
        result = write_data_by_identifier_with_wrong_structure(dut, level, did)
        results.append(result)

    if all(results) and len(results) == len(parameters['sa_levels_dids_extended']):
        logging.info("Received NRC-13 for incorrect structure in extended session as expected")
        return True

    logging.error("Test Failed: NRC-13 is not received for incorrect structure in extended "
                  "session")
    return False


def step_3(dut: Dut, parameters):
    """
    action: WriteDataByIdentifier with correct structure but wrong CRC for all supported security
            level in programming session
    expected_result: True when received NRC-31(requestOutOfRange) for all supported security level
    """
    results = []
    # Set ECU is in programming session
    dut.uds.set_mode(2)

    '''SSBL.get_vbf_files()
    result = SSBL.sbl_activation(dut, sa_keys=dut.conf.default_rig_config)
    if not result:
        logging.error("Test Failed: SBL activation failed")
        return False'''

    for level, did in parameters['sa_levels_dids_programming'].items():
        result = write_data_by_identifier_with_wrong_crc(dut, level, did)
        results.append(result)

    if all(results) and len(results) == len(parameters['sa_levels_dids_programming']):
        logging.info("Received NRC-31 for incorrect CRC in programming session as expected")
        return True

    logging.error("Test Failed: NRC-31 is not received for incorrect CRC in programming session")
    return False


def step_4(dut: Dut, parameters):
    """
    action: WriteDataByIdentifier with correct structure but wrong CRC for all supported security
            level in extended session
    expected_result: True when received NRC-31(requestOutOfRange) for all supported security level
    """
    results = []
    # Set ECU is in extended session
    dut.uds.set_mode(1)
    dut.uds.set_mode(3)

    time.sleep(5)

    for level, did in parameters['sa_levels_dids_extended'].items():
        security_access(dut, level)
        result = write_data_by_identifier_with_wrong_crc(dut, level, did)
        results.append(result)

    if all(results) and len(results) == len(parameters['sa_levels_dids_extended']):
        logging.info("Received NRC-31 for incorrect CRC in extended session as expected")
        return True

    logging.error("Test Failed: NRC-31 is not received for incorrect CRC in extended session")
    return False


def step_5(dut: Dut, parameters):
    """
    action: Verify negative response for read security did in extended session
    expected_result: True when received NRC-31(requestOutOfRange)
    """
    results = []

    for level, did in parameters['sa_levels_dids_extended'].items():
        result = read_security_did(dut, level, did)
        results.append(result)

    if len(results) != 0 and all(results):
        logging.info("received NRC-31 for all DID in extended session as expected")
        return True

    logging.error("Test Failed: NRC-31 is not received for all DID in extended session")
    return False


def step_6(dut: Dut, parameters):
    """
    action: Verify negative response for read security did in programming session
    expected_result: True when received NRC-31(requestOutOfRange)
    """
    results = []
    dut.uds.set_mode(2)

    for level, did in parameters['sa_levels_dids_programming'].items():
        result = read_security_did(dut, level, did)
        results.append(result)

    if len(results) != 0 and all(results):
        logging.info("received NRC-31 for all DID in programming session as expected")
        return True

    logging.error("Test Failed: NRC-31 is not received for all DID in programming session")
    return False


def run():
    """
    Verify respective security access key are programmed for different security access levels in
    all diagnostic sessions and also verify negative response for read security DIDs
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {"sa_levels_dids_programming" : {},
                       "sa_levels_dids_extended" : {}}
    try:
        dut.precondition(timeout=200)

        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step = dut.step(step_1, parameters, purpose="Verify response of "
                               "WriteDataByIdentifier with wrong structure but correct CRC in "
                               "programming session")
        if result_step:
            result_step = dut.step(step_2, parameters, purpose="Verify response of "
                                   "WriteDataByIdentifier with wrong structure but correct CRC in "
                                   "extended session")
        if result_step:
            result_step = dut.step(step_3, parameters, purpose="Verify response of "
                                   "WriteDataByIdentifier with correct structure but wrong CRC in "
                                   "programming session")
        if result_step:
            result_step = dut.step(step_4, parameters, purpose="Verify response of "
                                   "WriteDataByIdentifier with correct structure but wrong CRC in "
                                   "extended session")
        if result_step:
            result_step = dut.step(step_5, parameters, purpose="Verify negative response for read "
                                   "security DIDs in extended session")
        if result_step:
            result_step = dut.step(step_6, parameters, purpose="Verify negative response for read "
                                   "security did in programming session")
            result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
