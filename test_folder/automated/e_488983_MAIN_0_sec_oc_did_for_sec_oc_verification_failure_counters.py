"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 488983
version: 0
title: : SecOC - DID for SecOC verification failure counters
purpose: >
    Define DID structure and parameters used to read out SecOC message verification failure
    counters from ECU

description: >
    The ECU shall report failure counters of SecOC verification failures for all supported signals
    protected by SecOC in the ECU. The information shall be accessible by readDataByIdentifier
    service using DID 0xD0CD - “SecOC verification failure counters” as defined in the GMRDB. DID
    shall be supported in extended diagnostic session and shall be protected by Security Access
    service 0x27 with level 0x27.

    The information in DID shall contain failure counters of length 8-bit each for all SecOC
    signals configured in ECU. The 8-bit fail counter value indicates number of times a signal
    has failed final verification with SecOC.

    Each fail count value shall be reset to zero on every ECU startup. Upon reaching maximum value
    0xFF, fail count value shall be frozen to maximum value (0xFF) and shall not overflow or reset
    until next ECU startup or power cycle.

details: >
    Verify status of failure count value of SecOC signal, on failure overflow and ECU startup
    Steps:
        1. Read SecOC verification failure count value for signals using readDataByIdentifier
           service
        2. Perform ECU reset and verify failure count value is reset to zero for each signal
        3. Verify failure count value does not overflow beyond maximum value (0xFF) for each signal
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_file_io import SupportFileIO

SE27 = SupportService27()
SIO = SupportFileIO


def request_read_data_by_identifier(dut: Dut, parameters):
    """
    Request ReadDataByIdentifier(0x22) and get the ECU response
    Args:
        dut (Dut): An instance of Dut
        parameters (dict): sec_oc_did, position

    Returns: ECU response of ReadDataByIdentifier request and signal count value
    """
    sec_oc_did = parameters['sec_oc_did']

    # Read did 'D0CD' to get SecOC failure count value for supported SecOC signals
    did_response = dut.uds.read_data_by_id_22(bytes.fromhex(sec_oc_did))

    # Find total number of signals in did response
    sig_count = int(len(did_response.raw[parameters['position']:])/2)

    # Verify positive response on did request
    if did_response.raw[2:4] == '62':
        logging.info("Successfully read DID: %s with positive response %s", sec_oc_did,
                     did_response.raw[2:4])
        return did_response.raw, sig_count

    logging.error("Expected positive response 62 for DID: %s, received %s", sec_oc_did,
                  did_response.raw)
    return None, None


def step_1(dut: Dut):
    """
    action: Security access to ECU in extended session
    expected_result: Security access successful and ECU is in extended session
    """
    # Change to extended session
    dut.uds.set_mode(3)

    sa_result = SE27.activate_security_access_fixedkey(dut, sa_keys=dut.conf.default_rig_config,
                                                            step_no=272, purpose="SecurityAccess")
    if sa_result:
        logging.info("Security access Successful in extended session")
        return True

    logging.error("Test Failed: Security access denied in extended session")
    return False


def step_2(dut: Dut, parameters):
    """
    action: Verify SecOC failure count value within the range '00' to 'FF'
    expected_result: True when SecOC failure count value is within the range '00' to 'FF'
    """
    results = []
    sig_pos = 0

    did_response, sig_count = request_read_data_by_identifier(dut, parameters)

    # Verify failure count value for each signal from signal-1 to Signal-n
    for index in range(sig_count):
        # Conversion of hexadecimal data into integer
        signal = int(did_response[parameters['position']+sig_pos:parameters['position']+sig_pos+2],
                     16)
        # Verifying signal is within range '00' to 'FF'
        if signal >= 0:
            if signal <= 255:
                logging.info("SecOC failure count %s is within the range '00' to 'FF' for "
                             "Signal-%s", hex(signal).upper()[2:], index)
                results.append(True)
        else:
            logging.error("SecOC failure count %s is not within the range '00' to 'FF' "
                          "for Signal-%s", hex(signal).upper()[2:], index)
            results.append(False)

        sig_pos = sig_pos + 2

    if all(results) and len(results) != 0:
        logging.info("Successfully verified that the SecOC failure count is within the range"
                     " '00' to 'FF'")
        return True

    logging.error("Test Failed: SecOC failure count is not within the range '00' to 'FF'")
    return False


def step_3(dut: Dut, parameters):
    """
    action: Verify SecOC failure count for all signals after ecu reset
    expected_result: True when SecOC failure count set to '0x00'
    """
    # ECU reset
    dut.uds.ecu_reset_1101()

    results = []
    sig_pos = 0

    did_response, sig_count = request_read_data_by_identifier(dut, parameters)

    for index in range(sig_count):
        # Conversion of hexadecimal data into integer
        signal = int(did_response[parameters['position']+sig_pos:parameters['position']+sig_pos+2],
                     16)
        if signal == 0:
            logging.info("SecOC failure count of Signal-%s is %s as expected", index,
                          hex(signal).upper()[2:])
            results.append(True)
        else:
            logging.error("SecOC failure count of Signal-%s is %s, and it is not reset to '00'",
                          index, hex(signal).upper()[2:])
            results.append(False)

        sig_pos = sig_pos + 2

    if all(results) and len(results) != 0:
        logging.info("Successfully verified the SecOC failure count after ecu reset")
        return True

    logging.error("Test Failed: SecOC failure count after ecu reset is not reset to '00'")
    return False


def step_4(dut: Dut, parameters):
    """
    action: Verify SecOC failure count does not overflow after reaching maximum value '0xFF'
    expected_result: True when received failure count value in the range '00' to 'FF'
    """
    results = []
    sig_pos = 0

    did_response, sig_count = request_read_data_by_identifier(dut, parameters)

    for index in range(sig_count):
        # Conversion of hexadecimal data into integer
        signal = int(did_response[parameters['position']+sig_pos:parameters['position']+sig_pos+2],
                     16)
        # Verifying signal is within range '00' to 'FF'
        if signal <= 255:
            logging.info("SecOC failure count %s is within the limit '00' to 'FF' for Signal-%s",
                         hex(signal).upper()[2:], index)
            results.append(True)
        else:
            logging.error("SecOC failure count %s exceeds maximum limit '0xFF' for Signal-%s",
                          hex(signal).upper()[2:], index)
            results.append(False)

            sig_pos = sig_pos + 2

    if all(results) and len(results) != 0:
        logging.info("Successfully verified the SecOC failure count does not overflow")
        return True

    logging.error("Test Failed: SecOC failure count value exceeds maximum limit '0xFF'")
    return False


def run():
    """
    Verify status of failure count value for all SecOC signals, on ECU reset and failure overflow
    """
    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False
    parameters_dict = {'sec_oc_did': '',
                       'position': 0}

    try:
        dut.precondition(timeout=60)
        parameters = SIO.parameter_adopt_teststep(parameters_dict)

        if not all(list(parameters.values())):
            raise DutTestError("yml parameter not found")

        result_step = dut.step(step_1, purpose="Security access to ECU in extended session")

        if result_step:
            result_step = dut.step(step_2, parameters, purpose= "Verify SecOC failure count "
                                    "within the range '00' to 'FF'")
        if result_step:
            result_step = dut.step(step_3, parameters, purpose= "Verify SecOC failure count "
                                   "for all signals after ecu reset")
        if result_step:
            result_step = dut.step(step_4, parameters, purpose= "Verify SecOC failure count "
                                   "does not overflow after reaching maximum value '0xFF'")
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)

if __name__ == '__main__':
    run()
