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

"""

import sys
import logging

from supportfunctions.support_dut import Dut
from supportfunctions.support_dut import DutTestError
from supportfunctions.support_uds import complete_ecu_part_number_eda0
from supportfunctions.support_uds import ecu_software_structure_part_number_f12c


def step_1(dut):
    """
    action:

        Get the complete ecu part numbers from another did to have something to
        compare it with
    """
    eda0_response = dut.uds.read_data_by_id_22(
        complete_ecu_part_number_eda0)

    if eda0_response.empty() or not hasattr(
            eda0_response, "ecu_sw_struct_part_num"):
        raise DutTestError("Could not retrieve complete ecu part number")
    return eda0_response


def step_2(dut):
    """
    action: Set ecu to programming mode/session
    """
    dut.uds.set_mode(2)


def step_3(dut, eda0_response):
    """
    action:

        Make sure that the ecu software structure part number that we get with
        F12C matches with what we get from EDA0

    """
    f12c_response = dut.uds.read_data_by_id_22(
        ecu_software_structure_part_number_f12c)

    if f12c_response.empty() or not hasattr(
            f12c_response, "ecu_sw_struct_part_num"):
        raise DutTestError("No software structure part number received")

    assert f12c_response.ecu_sw_struct_part_num == \
        eda0_response.ecu_sw_struct_part_num, \
        "ecu software structure part numbers does not match: " + \
        "\neda0: %s\nf12c: %s" % (
            f12c_response.ecu_sw_struct_part_num,
            eda0_response.ecu_sw_struct_part_num)


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

        eda0_response = step_1(dut)
        step_2(dut)
        step_3(dut, eda0_response)

        result = True
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)

if __name__ == '__main__':
    run()
