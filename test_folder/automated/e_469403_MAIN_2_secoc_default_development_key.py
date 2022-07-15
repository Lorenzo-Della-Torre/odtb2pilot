"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 469403
version: 2
title: SecOC - Default Development Key
purpose: >
    To simplify the process during test & development, but also to ensure that the security
    mechanism is always on (processes and system behavior validation purposes).

description: >
    During test and development, unless others are agreed, following default development key shall
    be programmed to the ECU at OEM:
    “0x0F0E0D0C 0B0A0908 07060504 03020100”

    Note: When programming default development key in ECU for first time, initial key (provisioned
    by supplier as all bytes set to 0xFF) will be used as old key in DID request to write new
    default development key.

details: >
    Verify program default development key to the ECU at OEM is:
    “0x0F0E0D0C 0B0A0908 07060504 03020100”
"""

import logging
from Crypto.Util import Counter
from Crypto.Cipher import AES
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_secoc import SecOCmsgVerification

SIO = SupportFileIO()
SECOCVERIFY = SecOCmsgVerification()


def step_1(dut: Dut):
    """
    action: Verify default development key(“0x0F0E0D0C 0B0A0908 07060504 03020100”) is
            programmed to the ECU at OEM
    expected_result: True when retrieved correct decrypted data using development key
    """
    # pylint: disable=unused-argument
    # Read yml parameters
    parameters_dict = {'sec_oc_iv': '',
                       'sec_oc_new_key': '',
                       'compare_value': '',
                       'signal': ''}

    parameters = SIO.parameter_adopt_teststep(parameters_dict)

    if not all(list(parameters.values())):
        logging.error("Test Failed: yml parameter not found")
        return False

    encrypted_data_record = SECOCVERIFY.get_secoc_message(parameters['signal'])

    # Cipher key
    key_128 = bytes.fromhex(parameters['sec_oc_new_key'])

    # Counter
    counter = Counter.new(128,
                        initial_value=int.from_bytes(bytes.fromhex(parameters['sec_oc_iv']),
                        byteorder='big'), little_endian=False)

    # Decryption
    cipher_dec_obj = AES.new(key_128, AES.MODE_CTR, counter=counter)
    decrypted_data = cipher_dec_obj.decrypt(bytes.fromhex(encrypted_data_record))

    # Compare decrypted_data and compare_value
    if decrypted_data.hex().upper()[32:] == parameters['compare_value']:
        logging.info("Decrypted data received in the response is as expected")
        return True
    logging.error("Test Failed: Received incorrect decrypted data")
    return False


def run():
    """
    Verify default development key(“0x0F0E0D0C 0B0A0908 07060504 03020100”) is programmed to
    the ECU at OEM
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    try:
        dut.precondition(timeout=30)

        result = dut.step(step_1, purpose="Verify default development key is programmed "
                          "to the ECU at OEM")
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
