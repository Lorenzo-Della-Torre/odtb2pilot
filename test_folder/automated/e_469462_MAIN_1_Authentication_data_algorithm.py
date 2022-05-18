"""
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
from hilding.dut import DutTestError
from hilding.dut import Dut
from hilding.conf import Conf

CNF = Conf()


def calculate_cmac(security_log):
    """
    Calculate message authentication data using Crypto AES-128 algorithm
    Args:
        security_log(str): security log
    Returns:
        calculated_cmac(Str): Calculated authentication data
    """
    # Get 128 bits auth_key from config
    key_128 = bytes.fromhex(CNF.default_rig_config['security_log_auth_key'])
    cipher_obj = CMAC.new(key_128, ciphermod=AES)
    cipher_obj.update(bytes.fromhex(security_log))
    # Extract most significant 4 bytes of authentication data form cipher_object
    calculated_cmac = cipher_obj.hexdigest()[:8].upper()

    return calculated_cmac


def step_1(dut: Dut):
    """
    action: Set ECU to extended session and read security log
    expected_result: Positive response with security log
    """
    dut.uds.set_mode(3)
    response = dut.uds.read_data_by_id_22(bytes.fromhex('D046'))
    if response is not None:
        return True, response
    logging.error("Test Failed: Invalid response or DID not readable")
    return False, None


def step_2(dut: Dut, response):
    """
    action: Calculate and verify message authentication data
    expected_result: Positive response
    """
    # pylint: disable=unused-argument
    received_cmac = ''
    for response_item in response.data['details']['response_items']:
        if response_item['name'] == "Authentication Data":
            received_cmac = response_item['sub_payload']

    # Extracting header and message from security log(response.data['details']['item'][:-8])
    # to calculate CMAC
    security_log = response.data['details']['item'][:-8]
    calculated_cmac = calculate_cmac(security_log)
    if received_cmac == calculated_cmac:
        logging.info("MAC verification successful for the security log.")
        return True
    message = "Message authentication data is not identical, expected CMAC: {} " \
              "calculated CMAC: {}".format(received_cmac, calculated_cmac)
    logging.error(message)
    return False


def run():
    """
    Calculated message authentication data using Crypto AES-128 algorithm and verify
    with security log authentication data
    """
    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False
    try:
        dut.precondition()
        result_step, security_log = dut.step(step_1, purpose="Set ECU to extended session "
                                             "and read security log")
        if result_step:
            result_step = dut.step(step_2, security_log,
                                   purpose="Calculate and verify message authentication data")
        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
