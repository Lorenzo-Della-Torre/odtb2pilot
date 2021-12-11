"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

"""
reqprod: 68214
version: 1
title: Part number data records coding
purpose: N/A
description: >
    Part number data records used by Volvo Car Corporation shall have 8 digits
    for part number + 3 characters (version suffix).

        * The part number digits shall be coded in BCD and the 3 characters
          shall be coded in ASCII.
        * The data record shall have a fixed length of 7 bytes and be right
          justified with any unused digit(s) filled with 0.
        * If version suffix contains one character, there shall be two space
          characters between the part number digits and the version suffix.
        * If version suffix contains two characters, there shall be one space
          character between the part number digits and the version suffix.

    This requirement applies to all data records with the following
    identifiers:

        - Application Diagnostic Database Part number: F120
        - PBL Diagnostic Database Part number: F121
        - SBL Diagnostic Database Part number: F122
        - PBL Software Part Number: F125
        - ECU Core Assembly Part Number: F12A
        - ECU Delivery Assembly Part Number: F12B
        - ECU Software Structure Part Number: F12C
        - ECU Software Part Number: F12E

details:
    We extract F120, F12A, F12B, F12E in default mode,
    F121, F125, F12C in PBL, and F122 in SBL
"""

import sys
import logging

from hilding.dut import Dut
from hilding.dut import DutTestError
from hilding.uds import IoVmsDid


def step_1(dut: Dut):
    """
    action:
        Test default mode dids

    expected_result: >
        All returned part numbers should be valid
    """
    dids = [
        IoVmsDid.app_diag_part_num_f120,
        IoVmsDid.ecu_core_assembly_part_num_f12a,
        IoVmsDid.ecu_delivery_assembly_part_num_f12b,
        IoVmsDid.ecu_software_part_number_f12e
    ]
    validate_dids(dut, dids)

def step_2(dut: Dut):
    """
    action:
        Set ecu to programming mode (pbl)

    expected_result: >
        ECU: Empty response

    comment: Mode 2 should be set
    """
    dut.uds.set_mode(2)

def step_3(dut: Dut):
    """
    action:
        Test programming mode dids (pdl)

    expected_result: >
        All returned part numbers should be valid

    """
    dids = [
        IoVmsDid.pbl_diag_part_num_f121,
        IoVmsDid.pbl_software_part_num_f125,
        IoVmsDid.ecu_software_structure_part_number_f12c,
    ]
    validate_dids(dut, dids)

def step_4(dut: Dut):
    """
    action:
        Set ecu to programming mode (sbl)

    expected_result: >
        ECU: Empty response

    comment: Mode 2 should be set and in sbl mode
    """
    dut.uds.enter_sbl()

def step_5(dut: Dut):
    """
    action:
        Test programming mode dids (sdl)

    expected_result: >
        All returned part numbers should be valid

    """
    dids = [
        IoVmsDid.sbl_diag_part_num_f122
    ]
    validate_dids(dut, dids)


def validate_dids(dut, dids):
    """ validate a list of dids """
    for did in dids:
        res = dut.uds.read_data_by_id_22(did)
        logging.info(res)
        if not did.hex().upper()+'_valid' in res.data['details']:
            raise DutTestError(
                "No valid {} returned by ecu".format(
                    res.data['details']['name']))


def run():
    """
    Part number data records coding
    """
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

    dut = Dut()
    start_time = dut.start()

    result = False
    try:
        dut.precondition(timeout=800)
        dut.step(step_1)
        dut.step(step_2)
        dut.step(step_3)
        dut.step(step_4)
        dut.step(step_5)
        result = True
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
