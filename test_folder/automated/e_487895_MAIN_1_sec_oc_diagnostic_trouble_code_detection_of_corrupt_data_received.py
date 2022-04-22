"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 487895
version: 1
title: SecOC Diagnostic Trouble Code - Detection of corrupt data received
purpose: >
    To handle the situation where there may be a customer complaint and a symptom associated
    with the ECU generating the DTC but the root cause is located on another ECU which may or
    may not be exhibiting any symptoms.

description: >
    If the ECU at application layer detects, by the verification result provided by the SecOC data
    protection mechanism, that a data value received from other ECU is corrupted and where this
    eventually causes the receiving ECU to take failsafe actions that causes customer symptoms
    (reconfiguration with reduced functionality, driver notification etc.) this shall be identified
    with a corresponding DTC. A data value is corrupt if the final SecOC verification is
    not successful. The same DTC is to be set for a tested signal independent of type of SecOC
    verification failure reported to the application layer (verification failure, freshness or
    authentication code failure).

    The monitor shall be implemented as follows:
    • Test Run Criteria (TRC):
        o The DTC test for detection of corrupt data received from other ECU by SecOC shall run
          each time updated data, for which a test is implemented, is received from another ECU.
          The DTC shall be set when the number of SecOC verification failures for any signal
          exceeds its configurable limit for setting the DTC.
        o The ECU shall have a common base DTC 0xD0C5 for all signals protected by SecOC in a ECU.
        o The DTC shall use Failure Type Byte (FTB) 0x68.
        o The ECU supporting SecOC shall implement a mandatory global DTC snapshot data record that
          shall include the following data identifier record, as defined in Global Master Reference
          Database (GMRDB).
            • 0xD0CC - Secure On-board Communication verification failures

    Example.
    An ECU has two SecOC protected signals, sent in two separate PDUs.
    The failure limits for both signals are 100.
    At ECU reset/start, the current failure counters are reset for both signals.
    If 100 (0x64) final SecOC verification failures are detected for Signal 2 and 72 (0x48) for
    Signal 1, the DTC shall be set with following snapshot data record:

    Parameter name                                  Length(Bits)          Values

    Signal 1 SecOC failure count limit exceeded         1               "No" - 0b0
    Signal 2 SecOC failure count limit exceeded         1               "Yes" - 0b1

details: >
    Verify the status of DTC 0xD0C568 when the failure count limit is exceeded for all of the
    SecOC protected signals.
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_carcom import SupportCARCOM

SIO = SupportFileIO()
SC_CARCOM = SupportCARCOM()


def verify_dtc_status(dut: Dut, parameters, byte_pos):
    """
    Verify ECU response of did 'D0CC' and read dtc snapshot for each SecOC protected signal
    Args:
        dut (Dut): An instance of Dut
        parameters (dict): secoc_verification_failure_did, dtc_did,
                           failure_type_byte, mask, signals
        byte_pos(int): byte position of failure count limit status
    Returns:
        result_dict (dict): signal, dtc_response.raw
    """
    result_dict = {}
    bit_pos = 0

    # Read dtc snapshot for all SecOC protected signal
    for signal_name, sig_data in parameters['signals'].items():
        logging.info("Verifying failure count limit bit status of %s by reading the did 'D0CC'",
                      signal_name)

        result = False
        for _ in range(int(sig_data['failure_count_byte'], 16)):
            # Send faulty data of SecOC protected signal to ECU
            dut.uds.generic_ecu_call(bytes.fromhex(sig_data['data']))

            # Read did 'D0CC' to get the failure count limit status
            did_response = dut.uds.read_data_by_id_22(bytes.fromhex(
                           parameters['secoc_verification_failure_did']))

            # Byte-4 to Byte-n  of did 'D0CC' gives failure count limit status
            failure_count_limit_status = bin(int(did_response.raw[byte_pos:byte_pos+2], 16))
            # Reverse bit string
            failure_count = failure_count_limit_status[2:][::-1]

            if failure_count[bit_pos] == '0':
                logging.info("SecOC failure count limit bit is %s, and limit is not exceeded",
                             failure_count[bit_pos])

            if failure_count[bit_pos] == '1':
                logging.info("SecOC failure count limit bit is %s, and limit is exceeded",
                             failure_count[bit_pos])
                result = True

        # Increase bit_pos value by 1 to select next signal
        bit_pos = bit_pos + 1

        if result:
            # Read DTC 0xD0C568 if failure count limit exceeds configurable limit
            dtc_snapshot = SC_CARCOM.can_m_send("ReadDTCInfoSnapshotRecordByDTCNumber",
                                                bytes.fromhex(parameters['dtc_did']+
                                                parameters['failure_type_byte']),
                                                bytes.fromhex(parameters['mask']))
            dtc_response = dut.uds.generic_ecu_call(dtc_snapshot)
            result_dict[signal_name] = dtc_response.raw
        else:
            logging.error("SecOC failure count limit is not exceeded for %s", signal_name)

    if len(result_dict) == len(parameters['signals']):
        return result_dict

    logging.error("Did received DTC snapshot response for one or all of the SecOC signals")
    return None


def step_1(dut: Dut):
    """
    action: Verify the status of DTC 0xD0C568 for all of the SecOC protected signals
    expected_result: True when successfully verified the status of DTC for all SecOC signals
    """
    # Read yml parameters
    parameters_dict = {'secoc_verification_failure_did': '',
                       'dtc_did': '',
                       'failure_type_byte': '',
                       'mask': '',
                       'signals':{}}
    parameters = SIO.parameter_adopt_teststep(parameters_dict)

    if not all(list(parameters.values())):
        logging.error("Test Failed: yml parameter not found")
        return False

    did_response = dut.uds.read_data_by_id_22(bytes.fromhex(
                    parameters['secoc_verification_failure_did']))
    results = []
    byte_pos = 6
    # Extract message and calculate byte length
    message_length = int((len(did_response.raw[byte_pos:]))/2)

    for _ in range(message_length):
        response_dict = verify_dtc_status(dut, parameters, byte_pos)
        byte_pos = byte_pos + 2

        for signal_name, dtc_response in response_dict.items():
            if dtc_response[4:6] != '59':
                logging.error("Test Failed: Invalid response or DTC snapshot not readable")
                return False

            pos = dtc_response.find(parameters['dtc_did'])
            if dtc_response[pos:pos+2] == parameters['dtc_did']:
                logging.info("DTC has triggered for %s as expected, response received %s",
                             signal_name, dtc_response[pos:pos+2])
                results.append(True)

            logging.error("Test Failed: Expected DTC to be triggered for %s, response received %s",
                          signal_name, dtc_response[pos:pos+2])
            results.append(False)

    if all(results) and len(results) != 0:
        logging.info("Successfully verified the status of DTC for all signals")
        return True

    logging.error("Test Failed: Failed to verify the status of DTC for some signals")
    return False


def run():
    """
    Verify the status of DTC 0xD0C568 when the failure count limit is exceeded for all of the
    SecOC protected signals.
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    try:
        dut.precondition(timeout=120)

        result= dut.step(step_1, purpose="Verify the status of DTC 0xD0C568 for all of the "
                         "SecOC protected signals")

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
