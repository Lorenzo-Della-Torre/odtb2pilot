/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



**********************************************************************************/


'''
project:  HVBM basetech MEPII
author:   jpiousmo (Jenefer Liban)
date:     2021-11-11
version:  1.0
reqprod:  68172
title:    Usage Mode data record
purpose: >
    To enable readout of the active Usage mode.

description: >
    If the ECU is a publisher or a subscriber on the
    usage mode signal, a data record with identifier as specified in
    the table below shall be implemented exactly as defined in
    Carcom - Global Master Reference Database.

details: >
    Read the DID 'DD0A' in both default and extended session
    and make sure that we get a positive response with the
    DID(DD0A) in the response.
'''

import sys
import logging

from hilding.dut import Dut
from hilding.dut import DutTestError

def step_1(dut: Dut):
    """
    action:
        Send ReadDataByIdentifier(0xDD0A) and verify that ECU
        replies with correct DID in default Session

    expected_result:
        Positive response with DID(DD0A) in the response
    """

    res = dut.uds.read_data_by_id_22(bytes.fromhex('DD0A'))
    logging.debug(res)
    if not 'DD0A' in res.raw:
        raise DutTestError(
            f"No valid response for DD0A by ecu in Default Session:\n{res}")

def step_2(dut: Dut):
    """
    action:
        Set ECU to Extended session.

    expected_result:
        ECU is in Extended session
    """
    dut.uds.set_mode(3)

def step_3(dut: Dut):
    """
    action:
        Send ReadDataByIdentifier(0xDD0A) and verify that
        ECU replies with correct DID in ext session.

    expected_result:
        Positive response with DID(DD0A) in the response

    """
    res = dut.uds.read_data_by_id_22(bytes.fromhex('DD0A'))
    logging.debug(res)
    if not 'DD0A' in res.raw:
        raise DutTestError(
            f"No valid response for DD0A by ecu in Ext Session:\n{res}")

def step_4(dut: Dut):
    """
    action:
        Verify that the ECU is still in Extended Session
        using DID 0xF186

    expected_result:
        The ECU is in Extended session.
    """
    res = dut.uds.active_diag_session_f186()
    logging.debug(res)
    if res.data['details']['mode'] != 3:
        raise DutTestError(
            f"ECU is not in Extended Session:\n{res}")

def run():
    """
    DD0A verification in  Default and Ext Session
    """
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

    dut = Dut()
    start_time = dut.start()

    result = False

    try:
        # Communication with ECU lasts 30 seconds.
        dut.precondition(timeout=30)

        # Send ReadDataByIdentifier(0xDD0A)
        dut.step(step_1, purpose="Read DID DD0A")

        # Change to Extended session
        dut.step(step_2, purpose="Set ECU to extended session")

        # Send ReadDataByIdentifier(0xDD0A)
        dut.step(step_3, purpose="Read DID DD0A in Ext Session")

        # Verify that the ECU is still in Ext Session
        dut.step(step_4, purpose="Verify that the ECU is in Ext Session")
        result = True

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)

if __name__ == '__main__':
    run()
