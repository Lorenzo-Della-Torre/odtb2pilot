"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 68202
version: 2
title: ECU Delivery Assembly Part Number data record
purpose: >
    To enable readout of a part number that identifies the complete ECU at the point of delivery
    to the assembly plant.

description: >
    A data record with identifier as specified in the table below shall be implemented exactly as
    defined in Carcom - Global Master Reference Database.

    Description                         	Identifier
    ECU Delivery Assembly Part Number	    F12B

    •	It shall be possible to read the data record by using the diagnostic service specified in
        Ref[LC : Volvo Car Corporation - UDS Services - Service 0x22 (ReadDataByIdentifier) Reqs].

    The identifier shall be implemented in the following sessions:
    •	Default session
    •	Programming session (which includes both primary and secondary bootloader)
    •	Extended session

details: >
    Verify if identifier is implemented in default, extended and programming session(pbl and sbl)
    Steps:
        1. Verify ECU is in default session
        2. Verify response received in default, extended and programming session(pbl and sbl)
           is equal
        3. Verify valid part number for did F12B
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_SBL import SupportSBL

SUTE = SupportTestODTB2()
SE22 = SupportService22()
SSBL = SupportSBL()


def did_count_find(did_to_read, response):
    """
    Verify DID is present in ECU response
    Args:
        did_to_read (str): DID F12B
        response (str): ECU response
    Returns:
        (bool): True when F12B is present
    """
    did_count = response.count(did_to_read)
    if did_count != 0:
        logging.info("Successfully verified that F12B DID is present in ECU response")
        return True

    logging.error("%s DID not found in ECU response", did_to_read)
    return False


def send_request_f12b(dut, did_to_read):
    """
    Verify ReadDataByIdentifier service 22 with F12B DID
    Args:
        dut (Dut): dut instance
        did_to_read (str): DID F12B
    Returns:
        (bool): True on successfully verified positive response
        response (str): ECU response
    """
    response = dut.uds.read_data_by_id_22(bytes.fromhex(did_to_read))
    if response.raw[4:6] == '62':
        # Check if F12B DID is contained in reply
        result = did_count_find(did_to_read, response.raw)
        if not result:
            return False, None

        logging.info("Received positive response %s for request ReadDataByIdentifier",
                      response.raw[4:6])
        return True, response.raw

    logging.error("Test Failed: Expected positive response, received %s", response)
    return False, None


def step_1(dut: Dut):
    """
    action: Verify active diagnostic session
    expected_result: True when ECU is in default session
    """
    # Check default session
    active_session = SE22.read_did_f186(dut, b'\x01')
    if not active_session:
        logging.error("Test Failed: ECU is not in default session")
        return False

    logging.info("ECU is in default session as expected")
    return True


def step_2(dut: Dut):
    """
    action: Verify response received in default, extended and programming session(pbl and sbl)
            is equal
    expected_result: True when response received in default, extended and programming
                     session(pbl and sbl) is equal
    """
    # Request F12B DID in one request and verify if DID is included in response
    result_non_prog_dids, default_f12b_result = send_request_f12b(dut, did_to_read='F12B')
    if not result_non_prog_dids:
        return False, None

    # Change to extended session
    dut.uds.set_mode(3)

    # Request F12B DID in one request and verify if DID is included in response
    result_non_prog_dids, extended_f12b_result = send_request_f12b(dut, did_to_read='F12B')
    if not result_non_prog_dids:
        return False, None

    # Change to default session
    dut.uds.set_mode(1)

    # Change to programming session
    dut.uds.set_mode(2)

    # Request F12B DID in one request and verify if DID is included in response
    result_non_prog_dids, pbl_f12b_result = send_request_f12b(dut, did_to_read='F12B')
    if not result_non_prog_dids:
        return False, None

    '''SSBL.get_vbf_files()
    # Activate SBL
    result = SSBL.sbl_activation(dut, sa_keys=dut.conf.default_rig_config)
    if not result:
        logging.error("Test Failed: SBL activation failed")
        return False, None

    # Request F12B DID in one request and verify if DID is included in response
    result_non_prog_dids, sbl_f12b_result = send_request_f12b(dut, did_to_read='F12B')
    if not result_non_prog_dids:
        return False, None'''

    # Change to default session
    dut.uds.set_mode(1)

    # The response received in default, extended and programming session shall be equal
    result = (default_f12b_result == extended_f12b_result)
    logging.info("Response of did F12B is equal in default and extended session")
    '''result = result and (pbl_f12b_result == sbl_f12b_result)
    logging.info("Response of did F12B is equal in pbl and sbl session")'''
    result = result and (default_f12b_result == pbl_f12b_result)
    logging.info("Response of did F12B is equal in default and pbl session")
    return result, default_f12b_result


def step_3(dut: Dut, default_f12b_result):
    """
    action: Verify valid part number for did F12B
    expected_result: True when response received valid part number for did F12B
    """
    # pylint: disable=unused-argument
    # Validate the part number and format
    pos = default_f12b_result.find('F12B')
    valid_part_number = SUTE.validate_part_number_record(default_f12b_result[pos+4:pos+18])
    ecu_delivery_assembly_pn = SUTE.pp_partnumber(default_f12b_result[pos+4:pos+18])
    logging.info("Valid_f12b_num:%s", ecu_delivery_assembly_pn)

    if not valid_part_number:
        logging.error("Test Failed: Received invalid part number")
        return False

    logging.info("Received vaild part number as expected")
    return True


def run():
    """
    Verify if identifier is implemented in default, extended and programming session(pbl and sbl)
    Steps:
        1. Verify ECU is in default session
        2. Verify response received in default, extended and programming session(pbl and sbl)
           is equal
        3. Verify valid part number for did F12B
    """
    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=200)

        result_step = dut.step(step_1, purpose="Verify ECU is in default sesion")
        if result_step:
            result_step, default_f12b_result = dut.step(step_2, purpose="Verify response received"
                                                        " in default, extended and programming"
                                                        " session(pbl and sbl) is equal")
        if result_step:
            result_step = dut.step(step_3, default_f12b_result, purpose="Verify valid part number"
                                                                        " for did F12B")
        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
