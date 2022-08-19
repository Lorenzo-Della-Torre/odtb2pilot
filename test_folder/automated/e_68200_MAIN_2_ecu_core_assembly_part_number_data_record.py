"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 68200
version: 2
title: ECU Core Assembly Part Number data record
purpose: >
    To enable readout of a part number that identifies the combination of the ECU hardware and any
    non-replaceable software (bootloaders and other fixed software).

description: >
    A data record with identifier as specified in the table below shall be implemented exactly as
    defined in Carcom - Global Master Reference Database

    Description	                                Identifier
    ---------------------------------------------------------
    ECU Core Assembly Part Number	            F12A
    ---------------------------------------------------------

    •	It shall be possible to read the data record by using the diagnostic service specified in
        Ref[LC : Volvo Car Corporation - UDS Services - Service 0x22 (ReadDataByIdentifier) Reqs].

    The identifier shall be implemented in the following sessions:
        •   Default session
        •   Programming session (which includes both primary and secondary bootloader)
        •   Extended Session

details: >
    Verify ECU response of DID 'F12A'(ECU Core Assembly Part Number) by ReadDataByIdentifier(0x22)
    service in default, programming and extended diagnostic session.
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_service22 import SupportService22

SE22 = SupportService22()


def req_read_data_by_id(dut: Dut, session):
    """
    Request ReadDataByIdentifier(0x22) and get the ECU response
    Args:
        dut(Dut): An instance of Dut
        session(str): Diagnostic session
    Returns:
        (bool): True on successfully verified positive response
    """
    response = dut.uds.read_data_by_id_22(bytes.fromhex('F12A'))
    if response.raw[4:6] == '62' and response.raw[6:10] == 'F12A':
        logging.info("Successfully read DID F12A in %s session with positive response %s",
                      session, response.raw)
        return True

    logging.error("Test Failed: Expected positive response 62 for DID F12A in %s session, "
                  "received %s", session, response.raw)
    return False


def step_1(dut: Dut):
    """
    action: Send ReadDataByIdentifier in default diagnostic session and verify ECU
            response of ReadDataByIdentifier request.
    expected_result: True when received positive response '62'
    """
    return req_read_data_by_id(dut, session='default')


def step_2(dut: Dut):
    """
    action: Send ReadDataByIdentifier in extended diagnostic session and verify ECU
            response of ReadDataByIdentifier request.
    expected_result: True when received positive response '62'
    """
    # Set to extended session
    dut.uds.set_mode(3)

    # Check active diagnostic session
    active_session = SE22.read_did_f186(dut, b'\x03')
    if active_session:
        result = req_read_data_by_id(dut, session='extended')
        if not result:
            return False
        return True

    logging.error("Test Failed: ECU is not in extended session")
    return False


def step_3(dut: Dut):
    """
    action: Send ReadDataByIdentifier in programming session and verify ECU response of
            ReadDataByIdentifier request.
    expected_result: True when received positive response '62'
    """
    # Set to programming session
    dut.uds.set_mode(2)

    # Check active diagnostic session
    active_session = SE22.read_did_f186(dut, b'\x02')
    if active_session:
        result = req_read_data_by_id(dut, session='programming')
        if not result:
            return False
        return True

    logging.error("Test Failed: ECU is not in programming session")
    return False


def run():
    """
    Verify ECU response of diagnostic read out DIDs by ReadDataByIdentifier(0x22) service in
    default, programming, and extended diagnostic session.
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=40)

        result_step = dut.step(step_1, purpose="Send ReadDataByIdentifier in default diagnostic"
                                               " session and verify ECU response of"
                                               " ReadDataByIdentifier request")
        if result_step:
            result_step = dut.step(step_2, purpose="Send ReadDataByIdentifier in extended"
                                                   " diagnostic session and verify ECU response"
                                                   " of ReadDataByIdentifier request")
        if result_step:
            result_step = dut.step(step_3, purpose="Send ReadDataByIdentifier in programming"
                                                   " session and verify ECU response of"
                                                   " ReadDataByIdentifier request")
        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
