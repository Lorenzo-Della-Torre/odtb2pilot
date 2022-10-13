"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 469462
version: 1
title: Authentication Data - Algorithm
purpose: >
    Define the algorithm to be used to calculate the Authentication Data.

description: >
    The "NIST Special Publication 800-38B Recommendation for Block Cipher Modes of Operation;
    The CMAC Mode for Authentication" shall by default be used to calculate the Authentication Data.
    The underlying block cipher shall be AES-128 (Advanced Encryption Standard FIPS PUB 197),
    where 128 bits is the minimum key length.
    Notes.
    (i) To reduce the required memory space, the CMAC might need to be truncated
    but is shall always be at least be 4 bytes (most significant bytes).
    (ii) Other methods like hash-based HMAC construction according to [FIPS Publ 198-1]
    as well as "Recommendation for Block Cipher Modes of Operation: Galois/Counter Mode (GCM) and
    GMAC, NIST Special Publication 800-38D" can be used upon agreement with Volvo or
    when explicitly required for a specific event type (based on data structure and
    key format defined by Volvo).GCM provides authenticated encryption.

details:
    Calculate authentication data using Crypto AES-128 algorithm and verify with security
    log authentication data.
    Steps-
        1. Read security log
        2. Exclude authentication data from security log
        3. Calculate CMAC and compare with security log authentication data
"""

import logging
from Crypto.Cipher import AES
from Crypto.Hash import CMAC
from hilding.dut import Dut
from hilding.dut import DutTestError


def calculate_cmac(dut, security_log):
    """
    Calculate message authentication data using crypto AES-128 algorithm
    Args:
        dut (Dut): An instance of Dut
        security_log (str): security log
    Returns:
        calculated_cmac (str): Calculated authentication data
    """
    # Get 128 bits auth key from config
    key_128 = bytes.fromhex(dut.conf.default_rig_config['security_log_auth_key'])
    cipher_obj = CMAC.new(key_128, ciphermod=AES)
    cipher_obj.update(bytes.fromhex(security_log))
    # Extract most significant 4 bytes of authentication data form cipher object
    calculated_cmac = cipher_obj.hexdigest()[:8].upper()

    return calculated_cmac


def step_1(dut: Dut):
    """
    action: Read security log in extended session
    expected_result: True when received positive response '62'
    """
    dut.uds.set_mode(3)

    response = dut.uds.read_data_by_id_22(bytes.fromhex('D046'))
    if response.raw[4:6] == '62':
        logging.info("Successfully read DID D046 with positive response %s", response.raw[4:6])
        return True, response

    logging.error("Test Failed: Expected positive response 62 for DID D046, received %s",
                   response.raw)
    return False, None


def step_2(dut: Dut, response):
    """
    action: Calculate and verify message authentication data
    expected_result: True when successfully verified MAC for the security log
    """
    # pylint: disable=unused-argument
    received_cmac = ''
    for response_item in response.data['details']['response_items']:
        if response_item['name'] == "Authentication Data":
            received_cmac = response_item['sub_payload']

    # Extracting header and message from security log(response.data['details']['item'][:-8])
    # to calculate CMAC
    security_log = response.data['details']['item'][:-8]
    calculated_cmac = calculate_cmac(dut, security_log)
    if received_cmac == calculated_cmac:
        logging.info("MAC verification successful for the security log")
        return True

    logging.error("Test Failed: Message authentication data is not identical, expected CMAC: %s,"
                  " calculated CMAC: %s", received_cmac, calculated_cmac)
    return False


def run():
    """
    Calculate message authentication data using Crypto AES-128 algorithm and verify with security
    log authentication data
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=30)
        result_step, security_log = dut.step(step_1, purpose='Read security log in extended'
                                                             ' session')
        if result_step:
            result_step = dut.step(step_2, security_log, purpose='Calculate and verify message'
                                                                 ' authentication data')
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
