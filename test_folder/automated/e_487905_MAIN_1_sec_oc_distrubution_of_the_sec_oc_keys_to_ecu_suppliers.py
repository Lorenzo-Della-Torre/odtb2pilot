"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 487905
version: 1
title: SecOC - Distribution of the SecOC keys to ECU suppliers
purpose: >
    The OEM must be in control of the key applied and for separation of keys used during
    development and production

description: >
    The SecOC keys shall be provided by the OEM, i.e. the ECU supplier must not choose these.
    This is applicable for key(s) used during both development and production. Unless others are
    agreed, the initial SecOC key plain text data records shall have all bytes set to "0xFF" when
    parts are delivered to OEM.
    Note. The keys, initial keys, for ECUs intended for "production" shall be implemented at latest
    prior to "vehicle prototype build" unless others are agreed for the project. This is the latest
    milestone to change initial keys.

details: >
    Verify initial SecOC key plain text data records shall have all bytes set to "0xFF"
"""

import logging
from Cryptodome.Cipher import AES
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_secoc import SecOCmsgVerification

SIO = SupportFileIO()
SECOC_KEY_VERIFY = SecOCmsgVerification()


def step_1(dut: Dut):
    """
    action: Verify initial SecOC key plain text data records shall have all bytes set to "0xFF"
    expected_result: Return True on successful comparison of all decrypted data with message
    """
    # pylint: disable=unused-argument
    # Extract yml parameters
    parameters_dict = {'signals':{},
                       'secoc_initial_key':''}
    parameters = SIO.parameter_adopt_teststep(parameters_dict)
    if not all(list(parameters.values())):
        logging.error("Test Failed: yml parameter not found")
        return False

    results = []
    for signal, message in parameters['signals'].items():
        response = SECOC_KEY_VERIFY.get_secoc_message(signal)

        secoc_initial_key = bytes.fromhex(parameters['secoc_initial_key'])

        cipher = AES.new(secoc_initial_key, AES.MODE_CTR)
        nonce = cipher.nonce
        # Decryption using response
        cipher = AES.new(secoc_initial_key, AES.MODE_CTR, nonce = nonce)
        decrypted_data_record = cipher.decrypt(response)

        logging.info("DECRYPTED DATA RECORD %s",  decrypted_data_record.decode('ascii'))

        # Compare decrypted response with message
        if decrypted_data_record == message:
            logging.info("Initial key %s is present for %s signal", decrypted_data_record, signal)
            results.append(True)
        else:
            logging.error("Test Failed: Expected initial key, received %s for %s signal ",
                        decrypted_data_record, signal)
            results.append(False)

    if len(results) != 0 and all(results):
        logging.info("Initial SecOC key plain text data records of all bytes are set to 0xFF")
        return True

    logging.error("Test Failed: Initial SecOC key plain text data records of all bytes are not "
                  "set to 0xFF")
    return False


def run():
    """
    Verify initial SecOC key plain text data records shall have all bytes set to "0xFF"
    """
    dut = Dut()
    start_time = dut.start()
    result = False

    try:
        dut.precondition(timeout=30)

        result = dut.step(step_1, purpose=" Verify value of initial SecOC key plain text data for"
                          " all the signals")
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
