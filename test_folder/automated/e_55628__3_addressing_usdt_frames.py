"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 55628
version: 3
title: Addressing USDT frames
purpose: >
    Define which CAN IDs an ECU shall listen on

description: >
    The ECU shall implement USDT Diagnostic CAN IDs. The USDT Diagnostic CAN IDs shall originate
    from Volvo Car Corporation.

    Each ECU shall support a total of three (3) USDT Diagnostic CAN IDs:
        • Physically addressed requests (ECU Diagnostic Reception ID).
        • Functionally addressed requests (ECU Diagnostic Reception ID).
        • Physically and functionally addressed responses or (ECU Diagnostic Transmission ID).

details: >
    Verify response of ReadDataByIdentifier(0x22) from 'physically & functionally addressed
    response(0x653)' message, using 'physically addressed request signal(0x753)' and 'functionally
    addressed request signal(0x7FF)' as send message.
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_can import SupportCAN, CanParam, CanTestExtra, CanPayload
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM

SC = SupportCAN()
S_CARCOM = SupportCARCOM()
SUTE = SupportTestODTB2()


def step_1(dut: Dut):
    """
    action: Verify response of ReadDataByIdentifier(0x22) using 'physically addressed request
            (0x753)' as send message
    expected_result: Non-empty response from 'physically & functionally addressed response
                     (0x653)' message
    """
    dut.uds.read_data_by_id_22(bytes.fromhex('F186'))
    response = SC.can_messages[dut["receive"]][0][2]

    if response is not None:
        logging.info("Received non-empty response from 'physically & functionally addressed "
                     "response (0x653)' message as expected")
        return True

    logging.error("Test Failed: Received empty response for ReadDataByIdentifier(0x22) using "
                  "'physically addressed request signal(0x753)'")
    return False


def step_2(dut: Dut):
    """
    action: Verify response of ReadDataByIdentifier(0x22) using 'functionally addressed request
            (0x7FF)' as send message
    expected_result: Non-empty response from 'physically & functionally addressed response(0x653)'
                     message
    """
    etp: CanTestExtra = {'step_no': 102,
                         'purpose': "",
                         'timeout': 1,
                         'min_no_messages': -1,
                         'max_no_messages': -1}

    cpay: CanPayload = {"payload" : S_CARCOM.can_m_send("ReadDataByIdentifier",
                                    bytes.fromhex('F186'),
                                    b''),
                        "extra" : ''}

    can_p_ex: CanParam = {"netstub": dut.network_stub,
                          "send": dut.conf.rig.signal_tester_present,
                          "receive": dut.conf.rig.signal_receive,
                          "namespace": dut.namespace,
                          "protocol": dut.protocol,
                          "framelength_max": dut.framelength_max}

    result = SUTE.teststep(can_p_ex, cpay, etp)
    if not result:
        logging.error("Test Failed: Expected positive response for a request ReadDataByIdentifier "
                      "to get MF reply but not received")
        return False

    response = SC.can_messages[can_p_ex["receive"]][0][2]

    if response is not None:
        logging.info("Received non-empty response from 'physically & functionally addressed "
                     "response (0x653)' message as expected")
        return True

    logging.error("Test Failed: Received empty response for ReadDataByIdentifier(0x22) using "
                  "'functionally addressed request signal(0x7FF)'")
    return False


def run():
    """
    Verify response of ReadDataByIdentifier(0x22) from 'physically & functionally addressed
    response(0x653)' message, using 'physically addressed request signal(0x753)' and 'functionally
    addressed request signal(0x7FF)' as send message.
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=30)

        result_step = dut.step(step_1, purpose="Verify response of ReadDataByIdentifier(0x22) "
                               "using 'physically addressed request(0x753)' as send message")
        if result_step:
            result_step = dut.step(step_2, purpose="Verify response of ReadDataByIdentifier(0x22) "
                                   "using 'functionally addressed request(0x7FF)' as send message")
        result = result_step

    except DutTestError as error:
        logging.error("The testcase failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
