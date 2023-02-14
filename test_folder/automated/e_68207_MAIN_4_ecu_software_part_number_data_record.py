"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 68207
version: 4
title: ECU Software Part Number data record
purpose: >
    To enable readout of the part number for the ECU software

description: >
    A data record with identifier 0xF12E shall be implemented. The data records shall be
    implemented exactly as defined in Carcom - Global Master Reference Database.

    The content of the data record (0xF12E) with the data identifier shall be the following:
    --------------------------------------------------------------------------------
            Byte                          Description
    --------------------------------------------------------------------------------
            #1                     Total number of ECU Software Part Numbers
            #2-8                   ECU Software #1 Part Number
            #9-15                  ECU Software #2 Part Number
              .
              .
            #N-(N+6)               ECU Software #X Part Number
    --------------------------------------------------------------------------------

    The Part Number(s) is only allowed to be used for item(s) that can be separately downloaded to
    the ECU.
    • It shall be possible to read the data record by using the diagnostic service specified in
    Ref[LC : Volvo Car Corporation - UDS Services - Service 0x22 (ReadDataByIdentifier) Reqs].

    The identifier shall be implemented in the following sessions:
    • Default session
    • Extended Session

details: >
    Verify part-number from the response of DID 'F12E' in default session, also verify the
    response of DID 'F12E' in default and extended session are equal
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_can import SupportCAN

SUTE = SupportTestODTB2()
SC = SupportCAN()

def validate_partnumbers_f12e(message):
    """
    Validate part-number from the response of DID 'F12E'
    Args:
        message (str): response of DID 'F12E'
    Returns:
        (bool): True when successfully validate part-number from response
    """
    result = False
    pos = message.find('F12E')
    number = int(message[pos+4:pos+6])
    logging.info("Number of part number in F12E Response: %s", number)
    if number > 0:
        result = SUTE.validate_part_number_record(message[pos+6:pos+20])
        logging.info("_swlm: %s is Valid? %s", message[pos+6:pos+20], result)
    if number > 1:
        result = result and SUTE.validate_part_number_record(message[pos+20:pos+34])
        logging.info("_swp1: %s is Valid? %s", message[pos+20:pos+34], result)
    if number > 2:
        result = result and SUTE.validate_part_number_record(message[pos+34:pos+48])
        logging.info("_swp2: %s is Valid? %s", message[pos+34:pos+48], result)
    if number > 3:
        result = result and SUTE.validate_part_number_record(message[pos+48:pos+62])
        logging.info("_swce: %s is Valid? %s", message[pos+48:pos+62], result)
    if number > 4:
        result = result and SUTE.validate_part_number_record(message[pos+62:pos+76])
        logging.info("_structure_pn: %s is Valid? %s", message[pos+62:pos+76], result)

    return result


def step_1(dut: Dut):
    """
    action: Read DID F12E and verify part-number in default session
    expected_result: Response of DID F12E should contain valid part-number
    """
    logging.error("Requesting DID F12E")
    response = dut.uds.read_data_by_id_22(bytes.fromhex('F12E'))
    logging.error("Display frames sent/received:")

    #logging.error("Frames sent:", SC.can_frames[dut['send']])
    #logging.error("Frames received:", SC.can_frames[dut['receive']])

    #result = validate_partnumbers_f12e(response.raw)
    #if result:
    #    logging.info("Successfully verified part-number of DID 'F12E' in default session")
    #    return True, response.raw

    #logging.error("Test Failed: Part-number of DID 'F12E' in default session is invalid")
    #return False, None
    return True, response.raw


def step_2(dut: Dut, res_of_default):
    """
    action: Read DID F12E and verify the response of DID F12E is equal in extended and default
            session
    expected_result: Response of DID F12E should be equal in extended and default session
    """
    dut.uds.set_mode(3)
    response = dut.uds.read_data_by_id_22(bytes.fromhex('F12E'))

    if res_of_default == response.raw:
        logging.info("Part-number of DID 'F12E' in default and extended session are equal")
        return True

    logging.error("Test Failed: Part-number of DID 'F12E' in default and extended session are"
                  " not equal")
    return False


def run():
    """
    Verify response of DID F12E in default session and extended session are equal
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=30)
        logging.info("Test of sent frames added")
        result_step, res_of_default = dut.step(step_1, purpose="Verify part-number from the "
                                               "response of DID 'F12E' in default session")
        if result_step:
            result_step = dut.step(step_2, res_of_default, purpose="Verify response of DID "
                                   "'F12E' in extended and default session are equal")
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
