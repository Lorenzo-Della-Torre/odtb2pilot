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
    •	Trying to program a security access key a second time, when a
        valid key has already been written once (conditions not correct)
    •	The checksum check fails when the key is programmed (request out of range).

    Message direction- Client --> Server
    Message Type- Diagnostic request writeDataByIdentifier

    Data byte | Description (all values are in hexadecimal) | Byte Value (Hex)
    --------------------------------------------------------------------------
    # 1          WriteDataByIdentifier Request SID               2E
    --------------------------------------------------------------------------
    # 2          Data Identifier – Security Access Key
                # 1 msb (high byte)          DID value for key
                for level ‘xx’  Byte
    # 3          Data Identifier – Security Access Key for       to be programmed
                level ‘xx’  Byte#2 lsb (low byte)
    --------------------------------------------------------------------------
    # 4          Security Access Proof-of-ownership Key          00-FF
                Data Record Byte#1 msb (high byte)
    # 19         Security Access Proof-of-ownership Key          00-FF
                Data Record Byte#16 lsb (low byte)
    --------------------------------------------------------------------------
    # 20      	Security Access Encryption and
                Authentication Key Data Record Byte#1           00-FF
                msb (high byte)
    # 35      	Security Access Encryption and
                Authentication Key Data Record Byte#16          00-FF
                lsb (low byte)
    # 36      	Security Access key Checksum Byte#1             00-FF
                msb (high byte)	0x00=programmed
    # 37      	Security Access key Checksum Byte#2             00-FF
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
    • Verify security access key are programmed for supported security access levels in programming
      session with wrong structure & valid CRC and get requestOutOfRange NRC (31) response.

    • Verify security access key are programmed for supported security access levels in extended
      session with wrong structure & valid CRC and get requestOutOfRange NRC (31) response.

    • Verify security access key are programmed for supported security access levels in programming
      session with valid structure & wrong CRC and get requestOutOfRange NRC (31) response.

    • Verify security access key are programmed for supported security access levels in extended
      session with valid structure & wrong CRC and get requestOutOfRange NRC (31) response.

    • Verify the DID is not readable with NRC (31) response

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
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_sec_acc import SupportSecurityAccess

SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
SIO = SupportFileIO()
SSBL = SupportSBL()
SE27 = SupportService27()
SSA = SupportSecurityAccess()


def write_data_by_identifier_with_wrong_crc(dut: Dut, did):
    """
    WriteDataByIdentifier with valid structure & wrong CRC.
    Args:
        dut (class object): Dut instance
        did (str): security access DID
        level (str): security access level
    Returns: response
    """
    sa_key_32byte = 'FF'*32
    wrong_crc_hex = 'FF'*2
    message = bytes.fromhex(did + sa_key_32byte + wrong_crc_hex)
    response = dut.uds.generic_ecu_call(SC_CARCOM.can_m_send("WriteDataByIdentifier",
                                                             message, b''))
    return response.raw


def write_data_by_identifier_with_wrong_structure(dut: Dut, did):
    """
    WriteDataByIdentifier with wrong structure & valid CRC.
    Args:
        dut (class object): Dut instance
        did (str): security access DID
    Returns: response
    """
    sa_key_32byte = 'FF'*32
    crc = SUTE.crc16(bytearray(sa_key_32byte.encode('utf-8')))
    crc_hex = hex(crc)
    wrong_structure_33byte = 'FF'*33
    message = bytes.fromhex(did + wrong_structure_33byte + crc_hex[2:])

    response = dut.uds.generic_ecu_call(SC_CARCOM.can_m_send("WriteDataByIdentifier",
                                                             message, b''))
    return response.raw


def read_yml_parameters(dut: Dut):
    """
    Read all the security access levels and DIDs.
    Args: dut (class object): Dut instance
    Returns: parameters(dict): yml parameters
    """
    # pylint: disable=unused-argument
    parameters = {"sa_levels_dids_programming" : {},
                "sa_levels_dids_extended" : {}}
    parameters = SIO.extract_parameter_yml("*", parameters)

    if parameters is None:
        logging.error("Security Access parameters Levels and DIDs not found")
        return None
    return parameters


def verify_wrong_structure_response(response, level, did):
    """
    Verify response NRC 13 when incorrect structure
    Args:
        response(str): response
        level(str): Security access level
        did(str): DID
    Returns: True on successful verification
    """
    if response is None:
        logging.error("Test Failed: Invalid or empty response")
        return False

    # NRC 13 Incorrect Message Length Or Invalid Format
    if response[6:8] == '13':
        return True

    msg = "Response expected 13 but received: {} for Security level: {} and DID: {}".format(
        response[6:8], level, did)
    logging.error(msg)
    return False


def verify_wrong_crc_response(response, level, did):
    """
    Verify response NRC 31 when incorrect checksum
    Args:
        response(str): response
        level(str): Security access level
        did(str): DID
    Returns: True on successful verification
    """
    if response is None:
        logging.error("Test Failed: Invalid or empty response")
        return False

    # NRC 31 requestOutOfRange
    if response[6:8] == '31':
        return True

    msg = "Response expected 31 but received: {} for Security level: {} and DID: {}".format(
        response[6:8], level, did)
    logging.error(msg)
    return False

def security_access(dut: Dut, level):
    """
    security access to ECU for request seed
    Args:
        dut(class object): dut instance
        level(str): Security access level
    Returns: ECU response seed
    """
    # Set security access key and level
    SSA.set_keys(dut.conf.default_rig_config)
    SSA.set_level_key(int(level, 16))

    # Prepare client request seed
    client_req_seed = SSA.prepare_client_request_seed()
    response = dut.uds.generic_ecu_call(client_req_seed)

    # Truncate initial 2 bytes from response to process server response seed
    server_res_seed = response.raw[4:]
    result = SSA.process_server_response_seed(
        bytearray.fromhex(server_res_seed))

    # Prepare client request seed
    client_resp_key = SSA.prepare_client_send_key()
    response = dut.uds.generic_ecu_call(client_resp_key)

    # Check serverResponseSeed is successful or not
    if result == 0 and '67' in response.raw:
        logging.info("Security unlock successful")
        return True
    logging.error("Security unlock failed")
    return False


def step_1(dut: Dut):
    """
    action:
        Set ECU to programming session and Send WriteDataByIdentifier for supported security
        access levels i.e. 01 and 19 with invalid structure & valid CRC and confirm that
        service 2E responds with Incorrect Message Length Or Invalid Format NRC '13'.
    expected_result: Negative response
    """
    result = []
    parameters = read_yml_parameters(dut)
    if parameters is None:
        logging.error("Test Failed: yml parameters not found")
        return False

    # Sleep time to avoid NRC37
    time.sleep(5)
    dut.uds.set_mode(2)

    SSBL.get_vbf_files()

    SSBL.sbl_activation(dut, dut.conf.default_rig_config, stepno=200,\
                                            purpose="DL and activate SBL")

    for level, did in parameters['sa_levels_dids_programming'].items():
        response = write_data_by_identifier_with_wrong_structure(dut, did)
        result.append(verify_wrong_structure_response(response, level, did))

    if all(result) and len(result) == len(parameters['sa_levels_dids_programming']):
        return True
    logging.error("Test Failed: Invalid response")
    return False


def step_2(dut: Dut):
    """
    action:
        Set ECU to Extended session and Send WriteDataByIdentifier for supported security access
        levels i.e. 05, 19, 23 and 27 with invalid structure & valid CRC and confirm that service
        2E responds with Incorrect Message Length Or Invalid Format NRC '13'.
    expected_result: Negative response
    """
    result = []
    parameters = read_yml_parameters(dut)
    dut.uds.set_mode(1)
    dut.uds.set_mode(3)
    if parameters is None:
        logging.error("Test Failed: yml parameters not found")
        return False

    for level, did in parameters['sa_levels_dids_extended'].items():
        response = write_data_by_identifier_with_wrong_structure(dut, did)
        result.append(verify_wrong_structure_response(response, level, did))

    if all(result) and len(result) == len(parameters['sa_levels_dids_extended']):
        return True
    logging.error("Test Failed: Invalid response")
    return False


def step_3(dut: Dut):
    """
    action:
        Set ECU to programming session and Send WriteDataByIdentifier for supported security access
        levels i.e. 01 and 19 with valid structure & wrong CRC and confirm that service 2E responds
        with requestOutOfRange NRC '31'.
    expected_result: Negative response
    """
    result = []
    parameters = read_yml_parameters(dut)
    if parameters is None:
        logging.error("Test Failed: yml parameters not found")
        return False

    dut.uds.set_mode(2)

    SSBL.get_vbf_files()

    SSBL.sbl_activation(dut, dut.conf.default_rig_config, stepno=200,\
                                            purpose="DL and activate SBL")

    for level, did in parameters['sa_levels_dids_programming'].items():
        response = write_data_by_identifier_with_wrong_crc(dut, did)
        result.append(verify_wrong_crc_response(response, level, did))

    if all(result) and len(result) == len(parameters['sa_levels_dids_programming']):
        return True
    logging.error("Test Failed: Invalid response")
    return False


def step_4(dut: Dut):
    """
    action:
        Set ECU to Extended session and Send WriteDataByIdentifier for supported security access
        levels i.e. 05, 19, 23 and 27 with valid structure & wrong CRC and confirm that service
        2E responds with requestOutOfRange NRC '31'.
    expected_result: Negative response
    """
    result = []
    parameters = read_yml_parameters(dut)
    dut.uds.set_mode(1)
    dut.uds.set_mode(3)

    time.sleep(5)

    if parameters is None:
        logging.error("Test Failed: yml parameters not found")
        return False

    for level, did in parameters['sa_levels_dids_extended'].items():
        security_access(dut, level)
        response = write_data_by_identifier_with_wrong_crc(dut, did)
        result.append(verify_wrong_crc_response(response, level, did))

    if all(result) and len(result) == len(parameters['sa_levels_dids_extended']):
        return True
    logging.error("Test Failed: Invalid response")
    return False


def step_5(dut: Dut):
    """
    action: Verify the DIDs are not be possible to read in extended session
    expected_result: Negative response with NRC 31
    """
    result = []
    parameters = read_yml_parameters(dut)
    if parameters is None:
        logging.error("Test Failed: yml parameters not found")
        return False
    for _, did in parameters['sa_levels_dids_extended'].items():
        response = dut.uds.read_data_by_id_22(bytes.fromhex(did))
        if response is not None:
            # NRC 31 requestOutOfRange
            if response.raw[6:8] == '31':
                result.append(True)
            else:
                msg = "Invalid DID: {} response".format(did)
                logging.error(msg)
    if len(result) != 0 and all(result):
        return True
    logging.error("Test Failed: Invalid response")
    return False


def step_6(dut: Dut):
    """
    action: Verify the DIDs are not be possible to read in programming session
    expected_result: Negative response with NRC 31
    """
    result = []
    dut.uds.set_mode(2)
    parameters = read_yml_parameters(dut)
    if parameters is None:
        logging.error("Test Failed: yml parameters not found")
        return False
    for _, did in parameters['sa_levels_dids_programming'].items():
        response = dut.uds.read_data_by_id_22(bytes.fromhex(did))
        if response is not None:
            # NRC 31 requestOutOfRange
            if response.raw[6:8] == '31':
                result.append(True)
            else:
                msg = "Invalid DID: {} response".format(did)
                logging.error(msg)
    if len(result) != 0 and all(result):
        return True
    logging.error("Test Failed: Invalid response")
    return False


def run():
    """
    Verifying if respective security access key are programmed
    for different access levels in all diagnostic sessions.
    It also check the DIDs are not readable
    """
    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False
    try:
        dut.precondition(timeout=200)
        result_step = dut.step(step_1,
                               purpose="Program security access invalid structure and valid"
                               "CRC in programming mode with supported security access levels")
        if result_step:
            result_step = dut.step(step_2,
                                   purpose="Program security access invalid structure and valid "
                                   "CRC in extended mode with security supported access levels")
        if result_step:
            result_step = dut.step(step_3,
                                   purpose="Program security access key and wrong CRC in "
                                   "programming mode with supported security access levels")
        if result_step:
            result_step = dut.step(step_4,
                                   purpose="Program security access key and wrong CRC in "
                                   "extended mode with supported security access levels")
        if result_step:
            result_step = dut.step(step_5, purpose="Verify DIDs are not readable in "
                                   "extended session")
        if result_step:
            result_step = dut.step(step_6, purpose="Verify DIDs are not readable in "
                                   "programming session")

            result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
