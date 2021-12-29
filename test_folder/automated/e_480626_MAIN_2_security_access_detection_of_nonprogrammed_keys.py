"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 480626
version: 2
title: : Security Access - detection of non-programmed production keys
purpose: >
    To identify when the initial security access key(s) are still present
    in the ECU, in case of failure when confidential production keys for
    some reasons havent been programmed.

description: >
    The ECU shall report the current status of security access key(s), i.e.
    status indicating if the key has been written according to the requirement
    "Security Access Key programming at OEM" . The information shall be
    accessibleby readDataByIdentifier service using DID “Security Access Key Status”
    DID 0xD09B as defined in the Global Master Reference Database.

    The read only DID shall be possible to read in all sessions
    and it shall not be protected by security access.
    Status “OK, programmed” means that all required security
    access keys per that level are successfully programmed.

    Message direction:	Client <= Server
    Message Type:	Diagnostic response readDataByIdentifier DID Security Access Key Status

    Data byte | Description (all values are in hexadecimal) | Byte Value (Hex)
    --------------------------------------------------------------------------
    #1          Positive Response read request                  62
    #2          DID Security Access Key Status Byte#1 (MSB)     D0
    #3          DID Security Access Key Status Byte#2 (LSB)	    9B
    #4          Number of supported Security Access Levels	    0x00-0xFF
    #5          First supported security access level	        0x00-0xFF,
                                                                odd numbers (security_access_type
                                                                for request seed)
    #6      	Status first supported security access level	0x00=programmed
                                                                0x01=not programmed
    …	 	    …
    #n	        i:th supported security access level	        0x00-0xFF, odd numbers
    #n+1	    Status of i:th supported security               0x00, 0x01
    #           access level

    The read only DID shall be possible to read in all sessions and
    it shall not be protected by security access.
    Status “OK, programmed” means that all required security access
    keys per that level are successfully programmed.

    Note.
    If it is agreed by OEM that some key is one-time-programmable at supplier,
    0x00 shall be reported.

details: >
    Verifying if respective security access key are programmed for different access levels in all
    3 diagnostic sessions.
        01 -Diagnostic services in programmingSession, e.g. software download ( DID 0xF103)
        05 - Diagnostic services in extendedSession(DID 0xF10A)
        19 - Security Log ( DID 0xF115)
        23 - Secure Debug (0xF112)
        27 - Secure On-board Communication ( DID 0xF117)
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError


def verify_levels(response, supported_keys):
    """
     Verifies security access levels are programmed for respective session
    Args:
        response (dict): dut instance
        supported_keys (dict): security access levels supported in respective session
    Returns:
        bool: True if respective security access key are programmed in
        respective sessions
    """
    true_counter = 0
    return_verify = False
    try:
        if response['sid'] == "62" and response['did'] == "D09B":
            payload = response['details']['item']
            for index in range(2, len(payload)-2, 4):
                security_level = payload[index:index+2]
                programmed_status = int(payload[index+2:index+4], 16)
                if security_level in supported_keys.keys() and \
                    programmed_status == 0:
                    true_counter += 1
                elif programmed_status != 0:
                    msg = "Security level key: {} - Not Programmed".format(
                        supported_keys[security_level])
                    logging.info(msg)
            return_verify = true_counter == len(supported_keys.keys())
        else:
            return_verify = False
    except KeyError:
        logging.error(
            "Test Failed: Key Error Occurred, DID and/or SID are not present in response from ECU")
        return_verify = False
    return return_verify


def step_1(dut: Dut):
    """
    action:
        set mode to Default session and Send ReadDataByIdentifier(0xD09B)

    expected_result: Positive response
    """
    # Since default session doesn't support any keys
    supported_keys = {}
    dut.uds.set_mode(1)
    response = dut.uds.read_data_by_id_22(bytes.fromhex('D09B'))
    if response.raw[6:8] == '31':
        logging.error("Test Failed: Unable to read DID - D09B, received NRC31")
        return False
    return verify_levels(response.data, supported_keys)


def step_2(dut: Dut):
    """
    action:
        set mode to Extended session and Send ReadDataByIdentifier(0xD09B)

    expected_result: Positive response
    """
    supported_keys = {
        '05': "Extended session",
        '19': "Security Log",
        '23': "Secure Debug",
        '27': "Secure On-board Communication"
    }
    dut.uds.set_mode(3)
    response = dut.uds.read_data_by_id_22(bytes.fromhex('D09B'))
    if response.raw[6:8] == '31':
        logging.error("Test Failed: Unable to read DID - D09B, received NRC31")
        return False
    return verify_levels(response.data, supported_keys)


def step_3(dut: Dut):
    """
    action:
        set mode to Programming session and Send ReadDataByIdentifier(0xD09B)

    expected_result: Positive response
    """
    supported_keys = {
        '01': "Programming Session",
        '19': "Security Log"
    }
    dut.uds.set_mode(2)
    response = dut.uds.read_data_by_id_22(bytes.fromhex('D09B'))
    if response.raw[6:8] == '31':
        logging.error("Test Failed: Unable to read DID - D09B, received NRC31")
        return False
    return verify_levels(response.data, supported_keys)


def run():
    """
    0xD09B verification in all sessions
    """
    dut = Dut()
    start_time = dut.start()
    result = False
    try:
        # Communication with ECU lasts 30 seconds.
        dut.precondition(timeout=30)
        # Send ReadDataByIdentifier(0xD09B) in default session
        result = dut.step(step_1, purpose="0xD09B in Default Session")

        # Send ReadDataByIdentifier(0xD09B) in Extended session
        result = dut.step(step_2, purpose="0xD09B in Extended Session")

        # Send ReadDataByIdentifier(0xD09B) in Programming session
        result = dut.step(
            step_3, purpose="0xD09B in Programming Session")

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
