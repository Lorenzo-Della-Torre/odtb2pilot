"""
/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

"""
title:   Secondary Bootloader Software Version Number data record
reqprod: 129845
version: 1
purpose:
    To enable readout of the version number of the Secondary Bootloader SW
description: >

    A data record with identifier as specified in the table below shall be
    implemented exactly as defined in Carcom - Global Master Reference Database
    (GMRDB).

    Description: Secondary Bootloader Software Version Number data record
    Identifier: F124

     * It shall be possible to read the data record by using the diagnostic
       service specified in Ref[LC : Volvo Car Corporation - UDS Services -
       Service 0x22 (ReadDataByIdentifier) Reqs].

     * The identifier shall be BCD encoded, right justified and all unused
       digit shall be filled with 0.

    The ECU shall support the identifier in the following sessions:

     * Programming session (which includes secondary bootloader).

details:
    Verifying the format of Software Version Number data record
"""

import sys
import logging

from hilding.dut import Dut
from hilding.dut import DutTestError
from hilding.uds import IoVmsDid

def step_1(dut: Dut):
    """
    action:
        set ecu to programming mode (pbl)

    expected_result: >
        ECU: empty response

    comment: mode 2 should be set
    """
    dut.uds.set_mode(2)


def step_2(dut: Dut):
    """
    action:
        set the ecu in programming mode (sbl)

    expected_result:
        positive response
    """
    dut.uds.enter_sbl()


def step_3(dut: Dut):
    """
    action:
        retrieve sbl software part number
    expected_result:
        sbl software part numbers should be valid
    comment:
        validate call to the F124 did
    """
    res = dut.uds.read_data_by_id_22(IoVmsDid.sbl_software_part_num_f124)
    logging.info(res)
    if not 'F124_valid' in res.details:
        raise DutTestError(
            f"No valid F124 record returned by ecu:\n{res}")


def run():
    """
    Secondary Bootloader Software Version Number data record
    """
    logging.basicConfig(
        format=' %(message)s', stream=sys.stdout, level=logging.INFO)

    dut = Dut()
    start_time = dut.start()

    result = False
    try:
        dut.precondition(timeout=800)
        dut.step(step_1, purpose="set mode 2")
        dut.step(step_2, purpose="enter sbl")
        dut.step(step_3, purpose="test F124")
        result = True
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)

if __name__ == '__main__':
    run()
