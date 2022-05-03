"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 68189
version: 2
title: Application Diagnostic Database Part Number data record
purpose: >
    To enable readout of a database key for the diagnostic database used by the ECU application SW.

description: >
    A data record with identifier as specified in the table below shall be implemented exactly as
    defined in Carcom - Global Master Reference Database.

    Description	                                    Identifier
    ----------------------------------------------------------
    Application Diagnostic Database Part Number	    F120
    ----------------------------------------------------------

    •	It shall be possible to read the data record by using the diagnostic service specified in
        Ref[LC : Volvo Car Corporation - UDS Services - Service 0x22 (ReadDataByIdentifier) Reqs].

    The identifier shall be implemented in the following sessions:
        •	Default session
        •	Extended Session

details: >
    Verify ECU response of DID 'F120'(Application Diagnostic Database Part Number) by
    ReadDataByIdentifier(0x22) service in default and extended diagnostic session.
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError


def step_1(dut: Dut):
    """
    action: Send ReadDataByIdentifier(0xF120) in default diagnostic session and verify that
            ECU replies with correct DID
    expected_result: ECU should send positive response '62'
    """
    response = dut.uds.read_data_by_id_22(bytes.fromhex('F120'))

    if response.raw[4:6] == '62':
        logging.info("Successfully read DID 'F120' in default diagnostic session with positive "
                     "response %s", response.raw[4:6])
        return True

    logging.error("Test Failed: Expected positive response 62 for DID 'F120' in default "
                  "diagnostic session , received %s", response.raw)
    return False


def step_2(dut: Dut):
    """
    action: Send ReadDataByIdentifier(0xF120) in extended diagnostic session and verify that
            ECU replies with correct DID
    expected_result: ECU should send positive response '62'
    """
    # Set to extended session
    dut.uds.set_mode(3)

    response = dut.uds.read_data_by_id_22(bytes.fromhex('F120'))

    if response.raw[4:6] == '62':
        logging.info("Successfully read DID 'F120' in extended diagnostic session with positive "
                     "response %s", response.raw[4:6])
        return True

    logging.error("Test Failed: Expected positive response 62 for DID 'F120' in extended "
                  "diagnostic session , received %s", response.raw)
    return False


def run():
    """
    Verify ECU response of DID 'F120'(Application Diagnostic Database Part Number) by
    ReadDataByIdentifier(0x22) service in default and extended diagnostic session.
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=30)

        result_step = dut.step(step_1, purpose="Send ReadDataByIdentifier(0xF120) in default "
                                       "diagnostic session and verify that ECU replies with "
                                       "correct DID")
        if result_step:
            result_step = dut.step(step_2, purpose="Send ReadDataByIdentifier(0xF120) in extended"
                                           " diagnostic session and verify that ECU replies with"
                                           " correct DID")
        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
