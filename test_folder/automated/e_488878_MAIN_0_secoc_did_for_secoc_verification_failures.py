"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 488878
version: 0
title: SecOC - DID for SecOC verification failures
purpose: >
    Define DID structure and parameters used to read out SecOC message verification failures and
    to log snapshot data for global SecOC failure DTC in ECU.

description: >
    The ECU shall report information related to SecOC verification failures for all supported
    signals protected by SecOC in the ECU. The information shall be accessible by
    readDataByIdentifier service using DID 0xD0CC - “Secure On-board Communication verification
    failures” as defined in the GMRDB. DID shall be supported in all diagnostic sessions except
    programming session and shall not be possible to write. DID shall not be protected by Security
    Access and same DID shall be used to configure snapshot data for global SecOC failure DTC
    defined in ECU.

    The response for reading DID D0CC shall be bit encoded and the bit value shall be set to one (1)
    if a signal has exceeded the SecOC failure count limit and zero (0) otherwise.

    Example:
    DID D0CC is 4 bytes long and both Signal 1 and Signal 3 have exceeded their limits respectively.
    The response shall be: 0b00000000000000000000000000000101
    DID 0xD0CC parameters are specific to ECU and shall be defined as per below structure for all
    the signals that are protected by SecOC in the ECU.

    Parameter name                              | Length (Bits) | Values
    Signal 1 SecOC failure count limit exceeded       1          0b0 - No
                                                                 0b1 - Yes
    Signal 2 SecOC failure count limit exceeded       1          0b0 - No
                                                                 0b1 - Yes
    Signal 3 SecOC failure count limit exceeded       1          0b0 - No
                                                                 0b1 - Yes
                      ......                       ......          ......
                      ......                       ......          ......
    Signal x SecOC failure count limit exceeded       1          0b0 - No
                                                                 0b1 - Yes

details: >
    Read did 'D0CC' and verify the failure count limit bit status for each SecOC protected signal.
"""

import logging
import odtb_conf
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_can import SupportCAN, CanParam

SIO = SupportFileIO()
SC = SupportCAN()


def subscribe_to_signal(parameters):
    """
    Request subscribe to signal
    """
    can_p_ex: CanParam = {
    "netstub" : SC.connect_to_signalbroker(odtb_conf.ODTB2_DUT, odtb_conf.ODTB2_PORT),
    "send" : parameters['send'],
    "receive" : parameters['receive'],
    "namespace" : SC.nspace_lookup("Front1CANCfg0")
    }
    SIO.parameter_adopt_teststep(can_p_ex)

    # Subscribe to signal
    SC.subscribe_signal(can_p_ex, 15)


def step_1(dut: Dut):
    """
    action: Verify the status of 'D0CC' for failure count limit
    expected_result: True when successfully verified the status of failure count limit for
                     all SecOC protected signal
    """
    # Read yml parameters
    parameters_dict = {'sec_oc_verification_failure_did': '',
                       'send': '',
                       'receive': '',
                       'signals':{}}
    parameters = SIO.parameter_adopt_teststep(parameters_dict)

    if not all(list(parameters.values())):
        logging.error("Test Failed: yml parameter not found")
        return False

    results = []
    bit_pos = 0
    byte_pos = 6

    did_response = dut.uds.read_data_by_id_22(bytes.fromhex \
                   (parameters['sec_oc_verification_failure_did']))

    # Extract message and calculate byte length
    message_length = int((len(did_response.raw[byte_pos:]))/2)

    # Iterate up to message length to verify failure count bit for set of SecOC signals
    # i.e. #n byte represents m bit signals, where n is message_length and m is 8 bit
    for _ in range(message_length):
        # Read did response for all SecOC protected signal
        for signal_name, sig_data in parameters['signals'].items():
            logging.info("Verifying failure count limit bit status of %s by reading the did 'D0CC'",
                          signal_name)

            # Subscribe to signal
            subscribe_to_signal(parameters)

            failure_count_len = int(sig_data['failure_count_byte'], 16)
            for count_value in range(failure_count_len):
                # Send faulty data of SecOC protected signal to ECU
                dut.uds.generic_ecu_call(bytes.fromhex(sig_data['data']))

                # Read did 'D0CC' to get the failure count limit status
                did_response = dut.uds.read_data_by_id_22(bytes.fromhex \
                               (parameters['sec_oc_verification_failure_did']))

                # Byte-4 to Byte-n  of did 'D0CC' gives failure count limit status
                failure_count_limit_status = bin(int(did_response.raw[byte_pos:byte_pos+2], 16))
                # Reverse bit string
                fail_count = failure_count_limit_status[2:][::-1]

                if count_value < (failure_count_len-1):
                    if fail_count[bit_pos:bit_pos+1] == '0':
                        logging.info("SecOC failure count limit bit is %s, and limit is not"
                                     " exceeded", fail_count[bit_pos:bit_pos+1])
                        results.append(True)
                    else:
                        logging.error("Test Failed: SecOC failure count limit is exceeded"
                                      " for %s and the bit value is %s", signal_name,
                                      fail_count[bit_pos:bit_pos+1])
                        results.append(False)
                else:
                    if fail_count[bit_pos:bit_pos+1] == '1':
                        logging.info("SecOC failure count limit bit is %s, and limit is exceeded",
                                    fail_count[bit_pos:bit_pos+1])
                        results.append(True)
                    else:
                        logging.error("Test Failed: SecOC failure count limit is not exceeded "
                                      " for %s and the bit value is %s", signal_name,
                                      fail_count[bit_pos:bit_pos+1])
                        results.append(False)

            # Unsubscribe to signal
            SC.unsubscribe_signal(signal_name)

            # Increase bit_pos value by 1 to select next signal
            bit_pos = bit_pos + 1

        # Increase byte_pos value by 2 to select next byte
        byte_pos = byte_pos + 2

    if all(results) and len(results) != 0:
        logging.info("Successfully verified the status of DID for all signals")
        return True

    logging.error("Test Failed: Failed to verify the status of DID for some signals")
    return False


def run():
    """
    Read did 'D0CC' and verify the failure count limit bit status for each SecOC protected signal
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    try:
        dut.precondition(timeout=60)

        result = dut.step(step_1, purpose="Verify the status of 'D0CC' for failure count "
                                          " limit")
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
