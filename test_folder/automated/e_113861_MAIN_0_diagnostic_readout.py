"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 113861
version: 0
title: Diagnostic Read out #1 to #4 data record
purpose: >
    To support quality tracking of the ECU.

description: >
    A data record(s) with identifiers as specified in the table below may be implemented. The data
    record(s) intended for quality tracking of the ECU is defined by the implementer. The data
    record(s) shall only consist of other record data than the record data read by the generic
    standard read out sequence.

    Description	                                Identifier
    ---------------------------------------------------------
    Diagnostic Read out #1 to #4	            EDC0 - EDC3
    ---------------------------------------------------------

    •	It shall be possible to read the data record by using the diagnostic service specified in
        Ref[LC : Volvo Car Corporation - UDS Services - Service 0x22 (ReadDataByIdentifier) Reqs].

    The identifier shall be implemented in the following sessions:
        •	Default session
        •	Extended Session

details: >
    Verify ECU response of DID 'EDC0' and 'EDC1' by ReadDataByIdentifier(0x22) service in default
    and extended diagnostic session.
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_file_io import SupportFileIO

SIO = SupportFileIO


def req_read_data_by_id(dut: Dut, diag_read_out_did, session):
    """
    Request ReadDataByIdentifier(0x22) and get the ECU response
    Args:
        dut (Dut): An instance of Dut
        diag_read_out_did (str): Diagnostic read out did
        session (str): Diagnostic session
    Returns:
        (bool): True on successfully verified positive response
    """
    response = dut.uds.read_data_by_id_22(bytes.fromhex(diag_read_out_did))

    if response.raw[4:6] == '62':
        logging.info("Successfully read DID %s in %s diagnostic session with positive "
                     "response %s", diag_read_out_did, session, response.raw[4:6])
        return True

    logging.error("Test Failed: Expected positive response 62 for DID %s in %s diagnostic "
                  "session, received %s", diag_read_out_did, session, response.raw)
    return False


def step_1(dut: Dut, diag_read_out_dids):
    """
    action: Send ReadDataByIdentifier in default diagnostic session and verify ECU
            response of ReadDataByIdentifier request.
    expected_result: ECU should send positive response '62'
    """
    results = []

    for diag_read_out_did in diag_read_out_dids:
        results.append(req_read_data_by_id(dut, diag_read_out_did, session='default'))

    if all(results) and len(results) != 0:
        logging.info("Successfully read all the DIDs in default diagnostic session")
        return True

    logging.error("Test Failed: Failed to read some DIDs in default diagnostic session")
    return False


def step_2(dut: Dut, diag_read_out_dids):
    """
    action: Send ReadDataByIdentifier in extended diagnostic session and verify ECU
            response of ReadDataByIdentifier request.
    expected_result: ECU should send positive response '62'
    """
    results = []

    # Set to extended session
    dut.uds.set_mode(3)

    for diag_read_out_did in diag_read_out_dids:
        results.append(req_read_data_by_id(dut, diag_read_out_did, session='extended'))

    if all(results) and len(results) != 0:
        logging.info("Successfully read all the DIDs in extended diagnostic session")
        return True

    logging.error("Test Failed: Failed to read some DIDs in extended diagnostic session")
    return False


def run():
    """
    Verify ECU response of diagnostic read out DIDs by ReadDataByIdentifier(0x22) service in
    default and extended diagnostic session.
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'diag_read_out_dids': ''}
    try:
        dut.precondition(timeout=60)
        # Read yml parameters
        parameters = SIO.parameter_adopt_teststep(parameters_dict)

        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step = dut.step(step_1, parameters['diag_read_out_dids'], purpose="Send"
                               " ReadDataByIdentifier in default diagnostic session and verify ECU"
                               " response of ReadDataByIdentifier request")
        if result_step:
            result_step = dut.step(step_2, parameters['diag_read_out_dids'], purpose="Send"
                                   " ReadDataByIdentifier in extended diagnostic session and verify"
                                   " ECU response of ReadDataByIdentifier request")
        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
