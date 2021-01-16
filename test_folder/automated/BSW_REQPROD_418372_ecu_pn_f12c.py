"""
reqprod: 418372
version: 2
title:
    ECU Software Structure Part Number data record

purpose:
    To enable readout of the part number of the ECU Software Structure.

description: >
    If the ECU supports the Software Authentication concept where each data
    file is signed and verified individually as defined in Ref[*LC : General
    Software Authentication*], a data record shall be implemented as specified
    in the table below.

    ECU Software Structure Part Number: F12C

    It shall be possible to read the data record by using the diagnostic
    service specified in Ref[*LC : Volvo Car Corporation - UDS Services -
    Service 0x22 (ReadDataByIdentifier) Reqs*].  The ECU shall implement the
    data record exactly as defined in *Carcom - Global Master Referenced
    Database (GMRDB)*.

    The ECU shall support the identifier in the following sessions:
     - Programming session (which includes both primary and secondary bootloader)

details: >
    A ECU software part number should look like something like this: 32263666 AA.
    This test ensures that the format is correct and if possible corresponds to
    the same ecu software part number that can be extracted with eda0.

"""

import re
import sys
import logging

from supportfunctions.support_dut import Dut
from supportfunctions.support_dut import DutTestError
from supportfunctions.support_dut import get_platform
from supportfunctions.support_uds import complete_ecu_part_number_eda0
from supportfunctions.support_uds import ecu_software_structure_part_number_f12c


def step_1(dut):
    """
    action:
        Get the complete ecu part numbers from another did to have something to
        compare it with

    expected_result: >
        ECU: Positive response

    comment:
        All the part numbers should be returned
    """
    eda0_response = dut.uds.read_data_by_id_22(
        complete_ecu_part_number_eda0)

    if eda0_response.empty() or not hasattr(
            eda0_response, "ecu_sw_struct_part_num"):
        raise DutTestError("Could not retrieve complete ecu part number")
    return eda0_response


def step_2(dut):
    """
    action:
        Set ecu to programming mode/session

    expected_result: >
        ECU: Empty response

    comment: Mode 2 should be set
    """
    dut.uds.set_mode(2)


def step_3(dut, eda0_response):
    """
    action:
        Test that the format of the software part number is correct. That is
        consist of 8 consecutive numbers, followed by a space, and followed by
        two letters.

    expected_result:
        The format should be correct

    comment: >
        spa1: also test if the software part number from eda0 matches with the
        one we get from f12c
    """
    f12c_response = dut.uds.read_data_by_id_22(
        ecu_software_structure_part_number_f12c)

    if f12c_response.empty() or not hasattr(
            f12c_response, "ecu_sw_struct_part_num"):
        raise DutTestError("No software structure part number received")

    sw_pn = f12c_response.ecu_sw_struct_part_num
    assert re.match(r'^\d{8} [A-Z]{2}$', sw_pn), sw_pn

    if get_platform() == "spa1":
        assert sw_pn == eda0_response.ecu_sw_struct_part_num, \
            "ecu software structure part numbers does not match: " + \
            "\neda0: %s\nf12c: %s" % (
                sw_pn, eda0_response.ecu_sw_struct_part_num)


def run():
    """
    ECU Software Structure Part Number data record
    """
    logging.basicConfig(
        format=' %(message)s', stream=sys.stdout, level=logging.DEBUG)

    dut = Dut()
    start_time = dut.start()
    result = False

    try:
        dut.precondition()

        eda0_response = dut.step(step_1, purpose="get eda0")
        dut.step(step_2, purpose="set programming mode")
        dut.step(step_3, eda0_response, purpose="get f12c and compare values")

        result = True
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)

if __name__ == '__main__':
    run()
