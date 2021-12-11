"""
/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

"""
reqprod: 469461
version: 1
title: Authentication data Inputs
purpose:
    Define the input data to be part of the actual Authentication Data calculation.

description:
    The Authentication Data shall be calculated using
    all stored SecurityEvents and the SecurityEventHeader
    (Authentication Data itself excluded) as input data.
    A single Authentication Data is calculated per event type
    The Authentication Data shall always be appended next to the last
    event record for an event type, big endian.

details:
    Read with one of the Security log event DID D046 and
    Store the response Total number of successful events and Authentication Data
    Create an Event; Security Access ProgrammingSession
    Send ECU back to Default session to check DID D046
    Check the Event has been logged in D046 DID and
    Compare with previously saved response
    Total number of successful events and Authentication Data
    Total number of successful events will be incremented by 1
    Authentication Data will be different as the previously saved Data
"""
import logging
import time
import inspect
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_sec_acc import SecAccessParam
from hilding.dut import Dut
from hilding.dut import DutTestError

SIO = SupportFileIO()
SE27 = SupportService27()


def step_1(dut: Dut):
    """
    action: Read Security log event DID D046
    expected_result: Positive responce with the event data
    """
    res = dut.uds.read_data_by_id_22(b'\xd0\x46')
    for response_item in res.data['details']['response_items']:
        if response_item['name'] == "Total number of successful events":
            total_succ_events = response_item['sub_payload']
        if response_item['name'] == "Authentication Data":
            cmac = response_item['sub_payload']
    if res.raw[4:6] == '62':
        return True, total_succ_events, cmac
    return False, None, None


def step_2(dut: Dut):
    """
    action: Set ECU to Programmin Session
    expected_result: Positive response
    """
    dut.uds.set_mode(2)
    res = dut.uds.active_diag_session_f186()
    if res.data['sid'] == '62' and res.data['details']['mode'] == 2:
        return True
    return False


def step_3(dut: Dut):
    """
    action: Security Access to ECU
    expected_result: Positive response
    """
    sa_keys: SecAccessParam = {
        "SecAcc_Gen": 'Gen2',
        "fixed_key": '0102030405',
        "auth_key": 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF',
        "proof_key": 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), sa_keys)
    result = SE27.activate_security_access_fixedkey(
        dut, sa_keys, step_no=3, purpose='Security Access')
    return result


def step_4(dut: Dut, total_succ_events, cmac):
    """
    action: Set ECU to Default session and
            Read Security log event DID D046
    expected_result: Authentication Datas are different
                     Total number of successful events is incremented by 1
    """
    dut.uds.set_mode()
    time.sleep(2)
    res = dut.uds.read_data_by_id_22(b'\xd0\x46')
    for response_item in res.data['details']['response_items']:
        if response_item['name'] == "Total number of successful events":
            total_succ_events_latest = response_item['sub_payload']
        if response_item['name'] == "Authentication Data":
            cmac_latest = response_item['sub_payload']

    if cmac != cmac_latest and int(total_succ_events_latest, 16) == int(total_succ_events, 16) + 1:
        return True
    return False


def run():
    """ Supporting functional requests """
    dut = Dut()
    start_time = dut.start()
    result = False

    try:
        dut.precondition()
        result1, total_succ_events, cmac = dut.step(
            step_1, purpose='Read DID D046')
        result2 = dut.step(step_2, purpose='ECU into programming session')
        result3 = dut.step(step_3, purpose='Security Access')
        result4 = dut.step(step_4, total_succ_events, cmac,
                           purpose='ECU to Default session and Read and compare DID D046')
        result = result1 and result2 and result3 and result4

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
