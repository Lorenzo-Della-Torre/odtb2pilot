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
    service 0x27 with level 0x27. The information in DID shall contain failure counters of length
    8-bit each for all SecOC signals configured in ECU. The 8-bit fail counter value indicates
    number of times a signal has failed final verification with SecOC.
    Each fail count value shall be reset to zero on every ECU startup. Upon reaching maximum value
    0xFF, fail count value shall be frozen to maximum value (0xFF) and shall not overflow or reset
    until next ECU startup or power cycle.

details: >
    Verify status of fail count value of signal, on failure overflow and ECU startup
    Steps:
    1. Read SecOC verification failure for signals using readDataByIdentifier service
    2. Perform ECU reset and verify fail count value is reset to zero for each signal
    3. verify fail count value does not overflow beyond maximum value (0xFF) for each signal
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from hilding.conf import Conf
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_can import SupportCAN

SC = SupportCAN()
CNF = Conf()
SE27 = SupportService27()
SIO = SupportFileIO


def step_1(dut: Dut):
    """
    action: Verify fail count value does not overflow after reaching maximum value (0xFF)
    expected_result: True on successfully verified fail count value of signals
    """

    parameters_dict = {'did': '',
                       'signal1_pos': ''
                       }
    parameters = SIO.parameter_adopt_teststep(parameters_dict)
    if not all(list(parameters.values())):
        logging.error("Test Failed: yml parameter not found")
        return False, None
    # Change to extended session
    dut.uds.set_mode(3)
    result = SE27.activate_security_access_fixedkey(dut, sa_keys=CNF.default_rig_config,
                                                    step_no=1, purpose="SecurityAccess")
    if result:
        logging.info("Security access Successful")
    logging.error("Test Failed: Security access denied")
    return False

    # Create a payload with SecOC failure counters DID to send to ECU
    response = dut.uds.read_data_by_id_22(bytes.fromhex(parameters['did']))
    result = []

    # verify positive response on did request
    if response.raw[0:2] == '62':
        # find total number of signals in SecOC DID response
        signal_cnt = int(len(response.raw[parameters['signal1_pos']:]) / 2)
        # verify failure count value for each signal from Signal- 1 to Signal n
        for signal_no in range(signal_cnt):
            if response.raw[parameters['signal1_pos']:parameters['signal1_pos'] + 2] > '00' and\
                    response.raw[parameters['signal1_pos']:parameters['signal1_pos'] + 2] <= 'FF':
                # perform ECU reset and verify failure count value is reset to zero
                dut.uds.ecu_reset_1101()
                response = dut.uds.read_data_by_id_22(bytes.fromhex(parameters['did']))
                if response.raw[0:2] == '62':
                    if response.raw[parameters['signal1_pos']:parameters['signal1_pos']: + 2] == '00':
                        logging.info("Fail count value for Signal-%s is reset to 0", signal_no+1)
                        result.append(True)
                    else:
                        result.append(False)
            if response.raw[parameters['signal1_pos']:parameters['signal1_pos'] + 2] > 'FF':
                logging.error("Fail count value exceed maximum limit (0xFF) for Signal number-%s",\
                              signal_no+1)
            parameters['signal1_pos'] += 2

    if all(result):
        logging.info("Fail count value for all signals reset to 0 after ECU reset")
        return True
    logging.error("Test Failed: fail count value not reset to 0 after ECU reset or exceeds maximum"
                  " limit (0xFF)")
    return False


def run():
    """
    Verify status of fail count value for all signals, on ECU reset and failure overflow
    """

    dut = Dut()
    start_time = dut.start()
    result = False
    try:
        dut.precondition(timeout=60)

        result = dut.step(step_1, purpose='Verify status of signal fail count value on '
                                           'maximum value and ECU reset in extended session')
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)

if __name__ == '__main__':
    run()
