"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.


/*********************************************************************************/

reqprod: 68191
version: 2
title: Primary Bootloader Diagnostic Database Part Number
purpose: >
    To enable readout of a database key for the diagnostic database used by the ECU's primary
    bootloader SW.

description: >
    The data record Primary Bootloader Diagnostic Database Part Number with identifier as specified
    in the table below shall be implemented exactly as defined in Carcom - Global Master Reference
    Database (GMRDB).

    Description	                                                Identifier
    --------------------------------------------------------------------------
    Primary Bootloader Diagnostic Database Part Number	          F121
    --------------------------------------------------------------------------

    •   It shall be possible to read the data record by using the diagnostic service specified
        in Ref[LC : Volvo Car Corporation - UDS Services - Service 0x22 (ReadDataByIdentifier)
        Reqs].
    •   It is allowed to change the value of the data record one time in secondary bootloader by
        diagnostic service as specified in Ref[LC : VCC - UDS Services - Service 0x2E
        (WriteDataByIdentifier) Reqs].

    The ECU shall support the identifier in the following sessions:
    •   Programming session (which includes both primary and secondary bootloader)

details: >
    Verify and compare primary bootloader diagnostic database part number by reading DID 'F121'
    & from sddb file
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError


def step_1(dut: Dut):
    """
    action: Set to programming session and verify active diagnostic session
    expected_result: True when ECU is in programming session
    """
    # Set to programming session
    dut.uds.set_mode(2)

    # Check active diagnostic session
    response = dut.uds.active_diag_session_f186()
    if response.data["details"]["mode"] == 2:
        logging.info('ECU is in programming session as expected')
        return True

    logging.error('Test Failed: Not in programming session, received session %s',
                  response.data["details"]["mode"])
    return False


def step_2(dut: Dut):
    """
    action: Verify and compare primary bootloader diagnostic database part number by reading
            DID 'F121' & from sddb file
    expected_result: True when both primary bootloader diagnostic database part numbers are equal
    """
    # Read DID 'F121'(Primary Bootloader Diagnostic Database Part Number)
    response = dut.uds.read_data_by_id_22(bytes.fromhex('F121'))

    if response.raw[4:6] == '62':
        # Extract diagnostic database part number from response
        pbl_part_number = response.data['details']['F121_valid']

        # Extract DB Part Number for PBL
        sddb_file = dut.conf.rig.sddb_dids
        if 'pbl_diag_part_num' not in sddb_file.keys():
            logging.error('Test Failed: unable to find pbl_diag_part_num in sddb file')
            return False

        pbl_diag_part_num = sddb_file['pbl_diag_part_num']

        # Compare primary bootloader diagnostic database part numbers from data base and PBL
        pbl_part_number = pbl_part_number.replace(" ", "_")
        if pbl_part_number == pbl_diag_part_num:
            logging.info('Primary bootloader diagnostic database part numbers are equal')
            return True

        logging.error('Test Failed: Primary bootloader diagnostic database part numbers are '
                      'not equal')
        return False

    logging.error('Test Failed: Expected positive response 62, received %s', response.raw)
    return False


def run():
    """
    Verify and compare primary bootloader diagnostic database part number by reading DID 'F121'
    & from sddb file
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=30)

        result_step = dut.step(step_1, purpose='Set to programming session and verify active '
                                               'diagnostic session')
        if result_step:
            result_step = dut.step(step_2, purpose='Verify and compare primary bootloader '
                                                   'diagnostic database part number by reading '
                                                   'DID F121 & from sddb file')
        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
