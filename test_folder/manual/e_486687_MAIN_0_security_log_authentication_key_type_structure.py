"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 486687
version: 0
title: Security Log Authentication key type structure
purpose: >
    Define the format and structure of the Security Log Authentication key, when programmed
    to the ECU server. The distribution of keys to e.g. diagnostic clients shall comply with
    other methods.

description: >
    For the default method defined in "REQPROD 369991 : Authentication Data - Algorithm",
    The Security Log Authentication key shall be represented in hexadecimal format when
    programmed using writeDataByIdentifier service 0x2E at OEM. DID number 0xD0C8, as defined
    in OEM database, shall be used for writing security log authentication key. The DID must
    not be possible to read.

    To ensure the integrity of the key, a checksum is appended to the key when programmed.
    The ECU must successfully verify the checksum prior to the keys are stored in non-volatile
    memory. The format of the key when programmed shall be the concatenation of one AES-128-bit
    long key followed by two bytes long CRC16-CCITT. The CRC16-CCITT shall have the initial value
    0xFFFF and using normal representation, i.e. the polynomial is 0x1021.

    There shall be different negative response codes to separate:
    Trying to program a security log authentication key a second time, when a valid key has already
    been written once (conditions not correct).
    The checksum check fails when the key is programmed (request out of range).
    Failed to write key inside ECU, E,g, Failed to write key inside hardware security module
    (generalProgrammingFailure).



details: >
    Verify Security Log Authentication key type structure with WriteDataByIdentifier request
    with Correct CRC to get conditions not correct or generalProgrammingFailure and incorrect
    CRC(0xFFFF) to get request out of range.
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_test_odtb2 import SupportTestODTB2

SC_CARCOM = SupportCARCOM()
SE27 = SupportService27()
SIO = SupportFileIO
SUTE = SupportTestODTB2()


def step_1(dut: Dut):
    """
    action: Verify WriteDataByIdentifier request with correct CRC to get conditions not correct
            or generalProgrammingFailure
    expected_result: True on receiving conditions not correct or generalProgrammingFailure
    """
    # Define did from yml file
    parameters_dict = { 'did': '',
                        'security_log_authentication_key_data_record':'',
                        'security_log_authentication_key_checksum':''
                    }
    parameters = SIO.parameter_adopt_teststep(parameters_dict)

    if not all(list(parameters.values())):
        logging.error("Test Failed: yml parameter not found")
        return False, None

    dut.uds.set_mode(2)
    # Security access to ECU
    security_access = SE27.activate_security_access_fixedkey(dut, dut.conf.default_rig_config,
                                                            step_no=272, purpose="SecurityAccess")
    if not security_access:
        logging.error("Test Failed: security access denied in extended session")
        return False, None

    result = False
    sa_key_32byte = parameters['security_log_authentication_key_data_record']
    crc = SUTE.crc16(bytearray(sa_key_32byte.encode('utf-8')))
    crc_hex = hex(crc)
    message = bytes.fromhex(parameters['did'] +
              parameters['security_log_authentication_key_data_record'] + crc_hex[2:])

    # 1st Request WriteDataByIdentifier
    response = dut.uds.generic_ecu_call(SC_CARCOM.can_m_send("WriteDataByIdentifier",
                                                             message, b''))
    if response[2:4] == '6E' and response[4:8] == parameters['did']:
        logging.info("Received Positive Response %s for request WriteDataByIdentifier "
                                                        , response[2:4])
        # 2nd Request WriteDataByIdentifier
        response = dut.uds.generic_ecu_call(SC_CARCOM.can_m_send("WriteDataByIdentifier",
                                                             message, b''))

        if response[2:4] == '7F' :
            if response[6:8] == '72' or response[6:8] == '22':
                logging.info("Received NRC %s for request WriteDataByIdentifier as expected "
                        "(General Programming Failure or Conditions Not Correct)", response[6:8])
                result = True

    return result, parameters


def step_2(dut: Dut, parameters):
    """
    action: Verify WriteDataByIdentifier request with incorrect CRC(0xFFFF) to get request
            out of range.
    expected_result: True on receiving request out of range
    """
    result = False
    crc = 'FFFF'
    crc_hex = hex(crc)
    message = bytes.fromhex(parameters['did'] +
              parameters['security_log_authentication_key_data_record'] + crc_hex[2:])

    response = dut.uds.generic_ecu_call(SC_CARCOM.can_m_send("WriteDataByIdentifier",
                                                             message, b''))

    if response.raw[2:4] == '7F' and response.raw[6:8] == '31':
        logging.info("Received NRC %s for request WriteDataByIdentifier as expected"
                     "(Request out of Range)", response[6:8])
        result = True

    return result


def run():
    """
    Verify Security Log Authentication key type structure
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False
    try:
        dut.precondition(timeout=60)

        result_step, parameters = dut.step(step_1, purpose=" Verify WriteDataByIdentifier with "
                                                           "correct CRC to get conditions not "
                                                           "correct or generalProgrammingFailure")

        if result_step:
            result_step = dut.step(step_2, parameters, purpose=" Verify WriteDataByIdentifier "
                                                              "request with incorrect CRC(0xFFFF) "
                                                              "to get request out of range ")

        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
