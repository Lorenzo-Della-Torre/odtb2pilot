"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 481875
version: 0
title: >
    Random number generator validation

purpose: >
    Ensure that the Random Number Generator output fulfills entropy test.

description: >
    The output from the random number generator shall be tested with the tool Dieharder.
    When tested, no test shall fail independent of ECU mode (like after a reboot).

    Links to Dieharder:
    https://www.phy.duke.edu/~rgb/General/dieharder.php


details: >
    Test to verify the randomness of the random numbers generated by the ECU.
    1. Enter into programming session.
    2. Collect 100 samples of server random number from the ECU in a text file.
    3. Call Die harder tool to verify the randomness of the numbers.

    Please use the below command to install dieharder tool in Rasbperry pi.
    "sudo apt-get install dieharder"
"""
import os
import logging
import time
from Crypto.Util import Counter
from Crypto.Cipher import AES
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_sec_acc import SupportSecurityAccess
from supportfunctions.support_file_io import SupportFileIO

SSA = SupportSecurityAccess()
SIO = SupportFileIO()

def decrypt_data(dut: Dut, init_vector, encrypted_data):
    """
    Decrypt encrypted data using Crypto AES-CTR algorithm
    Args:
        dut(Dut): An instance of Dut
        init_vector(str): initialization vector
        encrypted_data(str): Encrypted data record
    Returns:
        decrypted_data(Str): Decrypted data record
    """
    # Get 128 bits auth_key from config
    key_128 = bytes.fromhex(dut.conf.default_rig_config['auth_key'])
    counter = Counter.new(128,
                          initial_value=int.from_bytes(bytes.fromhex(init_vector),
                          byteorder='big'), little_endian=False)
    cipher_dec_obj = AES.new(key_128, AES.MODE_CTR, counter=counter)
    decrypted_data = cipher_dec_obj.decrypt(bytes.fromhex(encrypted_data))
    return decrypted_data.hex().upper()


def get_server_decrypted_data(dut: Dut, res_seed_message):
    """
    Decrypt server response seed data record
    Args:
        dut(Dut): An instance of Dut
        req_seed_message(str): server response seed message
    Returns:
        dec_server_data(Str): Decrypted server data
    """
    # Extract iv from the response seed message.
    res_seed_iv = res_seed_message[8:40]

    # Extract encrypted data record from the response seed message.
    enc_server_data = res_seed_message[40:104]

    # Decrypt the ecnrypted data record from ECU.
    dec_server_data = decrypt_data(dut, res_seed_iv, enc_server_data)

    # Extract first 16 bytes of data record to get server random number.
    server_random_number = dec_server_data[0:32]
    logging.info("Received server random number: %s", server_random_number)

    # Return server random number as an integer.
    return int(server_random_number,16)

def request_seed(dut: Dut, sa_level):
    """
    Request seed using ClientRequestSeed message.
    Args:
        dut(Dut): An instance of Dut
        sa_level(int): Security access level
    Returns:
        server_res_seed: Server Response Seed message from ECU.
    """

    SSA.set_keys(dut.conf.default_rig_config)
    SSA.set_level_key(sa_level)
    payload = SSA.prepare_client_request_seed()

    # Send Client Request Seed message.
    response = dut.uds.generic_ecu_call(payload)

    # Extract server response seed from raw message.
    server_res_seed = response.raw[4:]
    logging.info("ECU response: %s", server_res_seed)
    SSA.process_server_response_seed(bytearray.fromhex(server_res_seed))

    return server_res_seed

def step_1(dut: Dut):
    """
    action: Enter into Programming session.

    expected_result: ECU is in programming session.
    """
    dut.uds.set_mode(2)
    return True

def step_2(dut: Dut):
    """
    action: Collect and save 100 samples of server random numbers from the ECU.
            This is achevied by decrypting the encrypted data record from ServerResponseSeed
            message from the ECU.

    expected_result: The ECU sends ServerResponseSeed messages and the random numbers are saved
                     in a text file.
    """

    # Define the pretext of the random number list file.
    file_txt = "#==============================================\n# generator Park       seed = 1\n"
    file_txt = file_txt + "#==============================================\ntype: d\ncount: 100\n"
    file_txt = file_txt + "numbit: 128"

    # Create a file to save the list of random numbers.
    file = open("random.txt",'w',encoding='utf-8')
    # Write the pretext to the file.
    file.write(file_txt)
    # To avoid NRC37
    time.sleep(5)

    for _ in range(100):
        # Get ServerResponseSeed by sending ClientRequestSeed message.
        server_res_seed = request_seed(dut, 1)

        if len(server_res_seed) < 20:
            logging.info("Received NRC from the ECU for Request seed message")
            return False
        # Decrypt the data record and extract the server random number.
        decrypted_random_number = get_server_decrypted_data(dut, server_res_seed)

        # Write the decrypted server random number in the file.
        file.write('\n')
        file.write(str(decrypted_random_number))

        time.sleep(2)

    file.close()
    return True

def step_3(dut: Dut):
    """
    action: Call dieharder tool and verify the randomness of the collected random number samples.

    expected_result: The dieharder tool should return "Passed" for the random number list.
    """
    # pylint: disable=unused-argument

    # The parameters means the following.
    # -a ----> All tests in dieharder suite
    # -g ----> The value 202 means that the file is of ASCII format.
    # -f ----> To provide the file name
    cmd = "dieharder -a -f random.txt"

    logging.info("+======================================================================+")
    logging.info("*****************Randomness Test by die harder tool*********************")
    logging.info("+======================================================================+")

    # Call the dieharder tool externally by passing the random number list as an argument.
    if os.system(cmd):
        return True

    logging.info("Die harder tool returns an error. "
                    "  Please check the input file and other parameters.")
    return False

def run():
    """
    Test to verify the randomness of the random numbers generated by the ECU.
    """
    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=1000)

        result_step = dut.step(step_1, purpose="Enter into programming session")

        result_step = result_step and dut.step(step_2, purpose="Collect and save 100 samples of"
                                                            " server random numbers from the ECU")

        result_step = result_step and dut.step(step_3, purpose="Verify the randomness of the "
                                                        "random numbers by using die harder tool")

        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
