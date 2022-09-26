"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 68197
version: 1
title: Autosar BSW cluster versions
purpose:
    To enable readout of the specific version of the (VCC) AUTOSAR cluster(s) implemented
    in the ECU.

description:
    If the ECU contains any AUTOSAR Basic Software cluster a data record with identifier as
    specified in the table below shall be implemented exactly as defined in
    Carcom - Global Master Reference Database.

    -------------------------------------------
    Description	                    Identifier
    -------------------------------------------
    Autosar BSW cluster version     F126
    -------------------------------------------
    •   It shall be possible to read the data record by using the diagnostic service specified in
        Ref[LC : Volvo Car Corporation - UDS Services - Service 0x22 (ReadDataByIdentifier) Reqs].

    The identifier shall be implemented in the following sessions:
    •   Default session
    •   Extended Session

details:
    Read DID F126 and verify the autosar BSW cluster version data record also verify that
    the data record in same in default and extended session.
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError


def request_read_data_by_id(dut, session):
    """
    Request ReadDataByIdentifier(0x22)
    Args:
        dut (Dut): An instance of Dut
        session (str): Diagnostic session
    Returns:
        (bool): True when received positive response '62'
        response.raw (str): ECU response
    """
    response = dut.uds.read_data_by_id_22(bytes.fromhex('F126'))
    if response.raw[4:6] == '62' and response.raw[6:10] == 'F126':
        logging.info("Received positive response '62' for request ReadDataByIdentifier in "
                     "%s session as expected", session)
        return True, response.raw

    logging.error("Test Failed: Expected positive response '62' for request ReadDataByIdentifier "
                  "in %s session, received %s", session, response.raw)
    return False, None


def verify_active_diag_session(dut, mode, session):
    """
    Request ReadDataByIdentifier(0x22)
    Args:
        dut (Dut): An instance of Dut
        mode (int): Diagnostic mode
        session (str): Diagnostic session
    Returns:
        (bool): True when ECU is in expected diagnostic session
    """
    response = dut.uds.active_diag_session_f186()
    if response.data["details"]["mode"] == mode:
        logging.info("ECU is in %s session as expected", session)
        return True

    logging.error("Test Failed: ECU is not in %s session", session)
    return False


def step_1(dut: Dut):
    """
    action: Read DID 'F126' and verify the autosar BSW cluster version data record in default
            session
    expected_result: Autosar BSW cluster version data record should match and message length
                     should equal to 51 bytes.
    """
    session_result = verify_active_diag_session(dut, mode=1, session='default')
    if not session_result:
        return False, None

    did_result, response_default = request_read_data_by_id(dut, session='default')
    if not did_result:
        return False, None

    logging.info("Data record with autosar BSW cluster version in default session %s",
                  response_default)

    # Verify the autosar BSW cluster version data record
    pos = response_default.find('F126')
    result = pos > 0
    message_length = int((len(response_default) - pos - 4)/2)
    result = result and message_length == 51
    if result:
        logging.info("Received valid autosar BSW cluster version data record and size of the "
                     "data is %s bytes", message_length)
        return True, response_default

    logging.info("Test Failed: Received invalid autosar BSW cluster version data record and size "
                 "of the data is %s bytes", message_length)
    return False, None


def step_2(dut: Dut, response_default):
    """
    action: Read DID 'F126' and compare autosar BSW cluster version data record
    expected_result: Autosar BSW cluster version data record should same in default
                     and extended session.
    """
    # Set to extended session
    dut.uds.set_mode(3)

    session_result = verify_active_diag_session(dut, mode=3, session='extended')
    if not session_result:
        return False

    did_result, response_extended = request_read_data_by_id(dut, session='extended')
    if not did_result:
        return False

    logging.info("Data record with autosar BSW cluster version in extended session %s",
                  response_extended)

    # Compare autosar BSW cluster version data record
    result = bool(response_default == response_extended)
    if result:
        logging.info("Autosar BSW cluster version data record are same in both default and "
                     "extended session")
        return True

    logging.error("Test Failed: Autosar BSW cluster version data record are not same in both "
                  "default and extended session")
    return False


def run():
    """
    Read DID F126 and verify the autosar BSW cluster version data record and also verify
    that the data record in same in default and extended session
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(40)
        result_step, default_f126_result = dut.step(step_1, purpose='Read DID F126 and verify '
                                                    'the autosar BSW cluster version data record '
                                                    'in default session')
        if result_step:
            result_step = dut.step(step_2, default_f126_result, purpose='Read DID F126 and compare'
                                                        ' autosar BSW cluster version data record')
        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
