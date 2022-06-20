"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 487892
version: 1
title: SecOC profile configuration - MAC truncation
purpose: >
    To ensure the MAC truncation is done properly.

description: >
    The MAC truncation is defined by the chosen SecOC profile configuration.
    For the ETH or CAN-FD PDUs, the default length of truncated MAC shall be 64-bit,
    i.e. SecOCAuthInfoTxLength = 64.
    For the CAN PDUs, the default length of truncated MAC shall be 32-bit,
    i.e. SecOCAuthInfoTxLength = 32.
    It is possible to choose different length for the truncated MAC depending on the available
    space in the PDU for the MAC and the acceptable security risk.
    The minimum length shall be 24-bit to ensure reasonable security level and FV shall be used
    in such case to limit the attack window.

details: >
    Verify calculated MAC and the ECU MAC are equal for ETH PDUs, CAN FD PDUs and CAN PDUs
    respectively.
"""

import logging
from Crypto.Hash import CMAC
from Crypto.Cipher import AES
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_secoc import SecOCmsgVerification

SIO = SupportFileIO()
SECOC_KEY_VERIFY = SecOCmsgVerification()


def calculate_authentication_data(dev_key, message):
    """
    Calculate message authentication data using Crypto AES-128-CMAC algorithm
    Args:
        dev_key(str): Development Key
        message(str): security access message
    Returns:
        calculated_cmac(str): Calculated authentication data
    """
    # Get 128 bits dev_key
    key_128 = bytes.fromhex(dev_key)
    cipher_obj = CMAC.new(key_128, ciphermod=AES)
    cipher_obj.update(bytes.fromhex(message))
    calculated_cmac = cipher_obj.hexdigest().upper()

    return calculated_cmac


def step_1(dut: Dut, parameters):
    """
    action: Calculate and verify CMAC for ETH PDUs, CAN FD PDUs and CAN PDUs
    expected_result: True on successfully verified CMAC for respective PDUs
    """
    # pylint: disable=unused-argument
    results = []
    signals = parameters['signals']
    for signal, signal_data in signals.items():
        response = SECOC_KEY_VERIFY.get_pdu({signal: signal_data}, parameters['bus_type'])

        if response == '':
            logging.error("Test Failed: Did not receive any response from ECU for signal %s",
                           signal)
            return False

        if parameters['bus_type'] == 'ETH' and parameters['bus_type'] == 'CAN_FD':
            # Extract 8 bytes for ECU CMAC
            ecu_cmac = response[-16:]
            calculated_cmac = calculate_authentication_data(parameters['dev_key'],\
                                                            str(response[:-16]))
        else:
            # Extract 4 bytes for ECU CMAC
            ecu_cmac = response[-8:]
            calculated_cmac = calculate_authentication_data(parameters['dev_key'],\
                                                            str(response[:-8]))

        if ecu_cmac == calculated_cmac:
            logging.info("CMAC verification successful")
            results.append(True)
        else:
            logging.error("Test Failed: CMAC verification failed expected %s, "
                        "calculated CMAC %s", ecu_cmac, calculated_cmac)
            results.append(False)

    if len(results) != 0 and all(results):
        logging.info("CMAC verification successful of all signals for %s PDUs",
                      parameters['bus_type'])
        return True

    logging.error("Test Failed: CMAC verification not successful for %s PDUs",
                   parameters['bus_type'])
    return False


def run():
    """
    Verify calculated MAC and the ECU MAC are equal for ETH PDUs, CAN FD PDUs and CAN PDUs
    respectively.
    """
    dut = Dut()
    start_time = dut.start()
    result = False

    parameters_dict = {'dev_key': '',
                       'signals': {},
                       'bus_type': ''}

    try:
        # Read parameters from yml file
        parameters = SIO.parameter_adopt_teststep(parameters_dict)

        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        dut.precondition(timeout=60)

        result = dut.step(step_1, parameters, purpose="Verify CMAC for ETH PDUs, CAN FD PDUs and"
                                                      " CAN PDUs")

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
