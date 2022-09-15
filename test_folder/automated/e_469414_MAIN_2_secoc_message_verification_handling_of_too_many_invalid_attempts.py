"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 469414
version: 2
title: SecOC message verification handling of too many invalid attempts
purpose: >
    To reduce the risk of a successful guessing attacks, by restricting the number of times
    the verification process can return verification failures for a given key when truncated
    authentication codes are applied. This is e.g. recommended by NIST Special Publication 800-38B
    The probability of a successful guessing attack is higher if an attacker can guess unlimited
    of times when (i) truncated authentication codes are used or (ii) there is no limitation in
    terms of reducing the time window of acceptable time stamped messages
    (i.e. no freshness value used)


description: >
    This requirement is mandatory when either (i) SecOCAuthInfoTxLength < 32 bits OR
    (ii) no freshness value is used (SecOCFreshnessValueLength = 0).

    If the ECU at application layer detects, by the final verification result provided by the
    SecOC data protection mechanism, that too many corrupt data values are received from
    transmitting ECU, the receiving ECU shall take failsafe actions and reduce the possibility
    that an attacker guesses a valid message. Final verification results mean that intermediate
    results due to e.g. freshness retry mechanism checks shall not be considered.

    If too many final SecOC verification failures are reported within a period, the ECU shall
    apply a delay timer. When the delay timer is active, the receiving ECU shall consider all
    SecOC verification results as “not successful” for the signal(s) that the delay timer is
    applied for. It must always be ensured that a delay is acceptable for the application and
    that failsafe actions can be ensured.
    The default, design time configurable, parameters per signal shall be:
    • SECOC_DELAY_TIMER = 5 seconds (0 means no delay timer)
    • SECOC_INVALID_ATTEMPTS <= 0.2 x SECOC_INVALID_TIME_WINDOW / Expected Message Rate
    • SECOC_INVALID_TIME_WINDOW = 10 seconds

    The SECOC_INVALID_ATTEMPTS are the number of failed verifications that shall be reached within
    one active time window defined by SECOC_INVALID_TIME_WINDOW. If the counter for failed
    attempts are reached within SECOC_INVALID_TIME_WINDOW seconds, the delay timer shall be active
    for SECOC_DELAY_TIMER seconds. The counter for failed attempts and timer for invalid attempts
    shall be reset when
    (i) the active delay timer expires OR
    (ii) the active timer, where number of failed verifications are counted, reaches
    SECOC_INVALID_TIME_WINDOW but conditions for activating the delay timer are not fulfilled.
    To avoid that the delay timer is activated at reset/start when e.g. the time is not yet
    synchronized, or ECU internal modules are not yet initialized, the ECU shall implement special
    handling during start-up time or tune the configurable parameters accordingly.

    Example 1 - SECOC_INVALID_ATTEMPTS = 10.
    (1) A signal with SecOC final verification failure is received. The timer where number of
    failed final verifications are counted is started
    (until timer reaches SECOC_INVALID_TIME_WINDOW)
    (2) The counter for invalid attempts is incremented per every final verification failure
    for a signal.
    (3) IF the counter reaches SECOC_INVALID_ATTEMPTS and timer started in
    (1) is less than or equal to SECOC_INVALID_TIME_WINDOW, a delay timer shall be started and
    active for SECOC_DELAY_TIMER.
    (4) When the delay timer is active, the application shall consider all received signals as
    having failed verification status.
    (5) The delay timer expires. The counter for failed attempts is reset.

    Example 2 - SECOC_INVALID_ATTEMPTS default value.
    Assumption: More than 80% of messages are always verified as successful in all conditions.
    Scheduled message rate for a periodic message is 50 ms.
    SECOC_INVALID_ATTEMPTS = 0.20 x 10 / 0.050 = 40.

details: >
    Verify handling of too many invalid attempts by SecOC message verification.
"""

import logging
import time
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


def check_delay_timer(parameters, sig_data, sec_oc_invalid_count, time_window):
    """
    Verify the status of delay timer
    Args:
        parameters (dict): sec_oc_auth_info_tx_length, sec_oc_freshness_value_length,
                           sec_oc_invalid_time_window, sec_oc_delay_timer,
                           sec_oc_verification_failure_did, signals
        sig_data (dict): failure_count_byte, data, expected_message_rate
        sec_oc_invalid_count(int): Counter for sec oc invalid counts
        time_window (int): 0.2*sec_oc_invalid_time_window
    Return:
        (bool): True when
    """
    sec_oc_invalid_attempts = time_window/sig_data['expected_message_rate']
    if sec_oc_invalid_count != sec_oc_invalid_attempts:
        logging.error("Delay timer not activated")
        return False
    logging.info("Delay timer activated")

    time.sleep(parameters['sec_oc_delay_timer'])
    if sec_oc_invalid_count != 0:
        logging.error("Test Failed: Delay timer not expired")
        return False
    logging.info("Delay timer is expired")
    return True


def verify_did_status(dut: Dut, parameters):
    """
    Verify the status of 'D0CC' for failure count limit
    Args:
        dut (class obj): Dut instance
        parameters (dict): sec_oc_auth_info_tx_length, sec_oc_freshness_value_length,
                           sec_oc_invalid_time_window, expected_message_rate, sec_oc_delay_timer,
                           sec_oc_verification_failure_did, signals
    Return:
        (bool): True when successfully verified the status of failure count limit for
                all SecOC protected signal
        sec_oc_invalid_attempts (int): Counter for invalid attempts
    """
    results = []
    bit_pos = 0
    byte_pos = 6
    sec_oc_invalid_count = 0
    time_window = 0.2 * parameters['sec_oc_invalid_time_window']

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
                    sec_oc_invalid_count = sec_oc_invalid_count + 1
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

        delay_timer_result = check_delay_timer(parameters, sig_data, sec_oc_invalid_count,\
                                               time_window)
        if not delay_timer_result:
            return False

    # Increase byte_pos value by 2 to select next byte
    byte_pos = byte_pos + 2

    if all(results) and len(results) != 0:
        logging.info("Successfully verified the status of DID for all signals")
        return True, sec_oc_invalid_count

    logging.error("Test Failed: Failed to verify the status of DID for some signals")
    return False, None


def step_1(dut: Dut, parameters):
    """
    action: Verify handling of too many invalid attempts by SecOC message verification
    expected_result: Return true when delay timer is expired
    """
    # Set extended session
    dut.uds.set_mode(3)

    byte_pos = 6

    # Read did 'D0CC' to get the message length
    did_response = dut.uds.read_data_by_id_22(bytes.fromhex \
                   (parameters['sec_oc_verification_failure_did']))

    # Extract message and calculate byte length
    message_length = int((len(did_response.raw[byte_pos:]))/2)

    for _ in range(message_length):
        initial_time = time.time()
        while time.time() - initial_time >= parameters['sec_oc_invalid_time_window']:
            # Iterate up to message length to verify failure count bit for set of SecOC signals
            # i.e. #n byte represents m bit signals, where n is message_length and m is 8 bit
            verify_did_status(dut, parameters)

        elapsed_time = time.time() - initial_time
        if elapsed_time >= parameters['sec_oc_invalid_time_window']:
            logging.info("Delay timer activated")
            return True


def run():
    """
    Verify handling of too many invalid attempts by SecOC message verification.
    """
    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'sec_oc_invalid_time_window': 10.0,
                       'sec_oc_delay_timer': 0,
                       'sec_oc_verification_failure_did': '',
                       'send': '',
                       'receive': '',
                       'signals': {}}
    try:
        dut.precondition(timeout=150)
        # Read yml parameters
        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step = dut.step(step_1, parameters, purpose="Verify handling of too many invalid"
                                                           " attempts by SecOC message"
                                                           " verification")
        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
