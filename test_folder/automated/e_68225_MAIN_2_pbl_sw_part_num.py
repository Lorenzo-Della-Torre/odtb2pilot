"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 68225
version: 2
title: Primary Bootloader Software Part Number data record
purpose: >
    To enable readout of the part number of the Primary Bootloader SW

description: >
    A data record with identifier as specified in the table below shall be implemented exactly as
    defined in Carcom - Global Master Reference Database (GMRDB).
    --------------------------------------------------------------------------------------------
                Description	                                       Identifier
    --------------------------------------------------------------------------------------------
    Primary Bootloader Software Part Number data record	              F125
    --------------------------------------------------------------------------------------------

    •	It shall be possible to read the data record by using the diagnostic service specified in
        Ref[LC : Volvo Car Corporation - UDS Services - Service 0x22 (ReadDataByIdentifier) Reqs].

    •	It is allowed to change the value of the data record one time in secondary bootloader by
        diagnostic service as specified in Ref[LC : VCC - UDS Services - Service 0x2E
        (WriteDataByIdentifier) Reqs].

    The ECU shall support the identifier in the following sessions:
    •	Programming session (which includes both primary and secondary bootloader)

details: >
    Read the data record(F125) in PBL and SBL and compare both part numbers.
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from hilding.flash import load_vbf_files, activate_sbl
from supportfunctions.support_test_odtb2 import SupportTestODTB2

SUTE = SupportTestODTB2()


def read_data_by_identifier(dut):
    """
    Request readDataByIdentifier(0x22) with DID 'F125'
    Args:
        dut(Dut): Dut instance
    Returns:
        pbl_part_num(str): Part number
    """
    response = dut.uds.read_data_by_id_22(bytes.fromhex('F125'))
    part_num = response.raw[10:]

    # Verify positive response
    if response.raw[4:6] == '62' and response.raw[6:10] == 'F125':
        # Validate the format of part number
        if SUTE.validate_part_number_record(part_num):
            logging.info("Successfully validate part number")
            return part_num

    logging.error("Unable to get valid part number")
    return None


def step_1(dut):
    """
    action: Read the data record(F125) in PBL and SBL and compare both part numbers.
    expected_result: True when both part numbers are equal.
    """
    # Set ECU in programming mode
    dut.uds.set_mode(2)
    part_num_from_pbl = read_data_by_identifier(dut)

    if not load_vbf_files(dut):
        return False
    # SBL activation
    if not activate_sbl(dut):
        return False

    part_num_from_sbl = read_data_by_identifier(dut)

    # Compare part numbers from pbl and sbl
    if part_num_from_pbl == part_num_from_sbl:
        logging.info("Part numbers are equal")
        return True

    logging.error("Test Failed: Part numbers are not equal")
    return False


def run():
    """
    Read the data record(F125) in PBL and SBL and compare both part numbers.
    """
    dut = Dut()
    start_time = dut.start()
    result = False

    try:
        dut.precondition(timeout=60)
        result = dut.step(step_1, purpose="Read the data record in PBL and SBL and compare "
                                          "both part numbers")
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
