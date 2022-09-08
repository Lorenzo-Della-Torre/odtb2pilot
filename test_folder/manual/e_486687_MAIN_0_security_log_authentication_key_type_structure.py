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
    Verify security log authentication key type structure with WriteDataByIdentifier request
    with correct CRC to get NRC 22(conditionsNotCorrect) or NRC 72(generalProgrammingFailure) and
    incorrect CRC(0xFFFF) to get NRC 31(requestOutOfRange).
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
SIO = SupportFileIO()
SUTE = SupportTestODTB2()


def step_1(dut):
    """
    action: Security access in programming session
    expected_result: True when security access successful in programming session
    """
    dut.uds.set_mode(2)
    result = SE27.activate_security_access_fixedkey(dut, sa_keys=dut.conf.default_rig_config)
    if not result:
        logging.error("Test Failed: Security access denied in programming session")
        return False

    return True


def step_2(dut, parameters):
    """
    action: Verify WriteDataByIdentifier request with correct CRC
    expected_result: True when received 7F and NRC 22(conditionsNotCorrect) or 7F and NRC 72
                     (generalProgrammingFailure)
    """
    sec_key = parameters['sec_key']
    crc = SUTE.crc16(bytearray(sec_key.encode('utf-8')))
    crc_hex = hex(crc)
    message = bytes.fromhex(parameters['did'] + sec_key + crc_hex[2:])
    payload = SC_CARCOM.can_m_send("WriteDataByIdentifier", message, b'')

    # 1st Request WriteDataByIdentifier
    response = dut.uds.generic_ecu_call(payload)
    if response.raw[2:4] != '6E' and response.raw[4:8] != parameters['did']:
        logging.error("Test Failed: Expected positive response, but received %s", response.raw)
        return False

    # 2nd Request WriteDataByIdentifier
    response = dut.uds.generic_ecu_call(payload)
    if response.raw[2:4] != '7F':
        if response.raw[6:8] != '72' or response.raw[6:8] != '22':
            logging.error("Test Failed: Expected 7F and NRC 22(conditionsNotCorrect) or 7F and "
                          "NRC 72 (generalProgrammingFailure), but received %s", response.raw)
            return False

    logging.info("WriteDataByIdentifier request with correct CRC is successful")
    return True


def step_3(dut, parameters):
    """
    action: Verify WriteDataByIdentifier request with incorrect CRC(0xFFFF)
    expected_result: True when received 7F and NRC 31(requestOutOfRange)
    """
    crc = 'FFFF'.encode('utf-8')
    crc_hex = crc.hex()
    message = bytes.fromhex(parameters['did'] + parameters['sec_key'] + crc_hex[2:])
    payload = SC_CARCOM.can_m_send("WriteDataByIdentifier", message, b'')

    response = dut.uds.generic_ecu_call(payload)
    if response.raw[2:4] == '7F' and response.raw[6:8] == '31':
        logging.info("Received 7F and NRC 31 for request WriteDataByIdentifier as expected")
        return True

    logging.error("Test Failed: Expected 7F and NRC 31, but received %s", response.raw)
    return False


def run():
    """
    Verify security log authentication key type structure
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'did': '',
                       'sec_key': ''}

    try:
        dut.precondition(timeout=60)

        parameters = SIO.parameter_adopt_teststep(parameters_dict)

        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step = dut.step(step_1, purpose="Security access in programming session")
        if result_step:
            result_step = dut.step(step_2, parameters, purpose="Verify WriteDataByIdentifier "
                                                               "request with correct CRC")
        if result_step:
            result_step = dut.step(step_3, parameters, purpose="Verify WriteDataByIdentifier "
                                                               "request with incorrect CRC")
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
