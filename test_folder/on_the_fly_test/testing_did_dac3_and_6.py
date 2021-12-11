"""
/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

"""
title:
    Testing did dac3 and dac6

purpose:
    Validate that the DAC3 and DAC6 DIDs are working as expected.

description:
    Validate that the DAC3 and DAC6 DIDs are working as expected.

details:
    Reading the DAC3 and DAC6 before and after a reset will help us determine if it works

"""

import logging

from hilding.dut import Dut
from hilding.dut import DutTestError


def pp_result(res):
    """
    Pretty prints the read_data_by_id_22 result.
    Writes the name and the scaled value
    """
    logging.info("-----------------------------------------------")
    logging.info("| %s", res.details.get('name'))
    logging.info("|----------------------------------------------")
    for resp_item in res.details.get('response_items'):
        logging.info("| %s: %s", resp_item.get('name'), resp_item.get('scaled_value'))
    logging.info("-----------------------------------------------")


def step_1(dut: Dut):
    """
    action:
        Read DID D034 (Counter for number of software resets)
    expected_result:
        To receive the counter value for number of software resets
    """
    res = dut.uds.read_data_by_id_22(bytes.fromhex('D034'))
    pp_result(res)


def step_2(dut: Dut):
    """
    action:
        Read DID DAC3 (SW Reset Type)
    expected_result:
        To receive the SW Reset Type
    """
    res = dut.uds.read_data_by_id_22(bytes.fromhex('DAC3'))
    pp_result(res)


def step_3(dut: Dut):
    """
    action:
        Read DID DAC6 (3 last SW Reset Types)
    expected_result:
        To receive the 3 last SW Reset Types
    """
    res = dut.uds.read_data_by_id_22(bytes.fromhex('DAC6'))
    pp_result(res)


def step_4(dut: Dut):
    """
    action:
        Make hardreset
    expected_result:
        Reset done
    """
    res = dut.uds.ecu_reset_1101()
    logging.info(res)


def step_5(dut: Dut):
    """
    action:
        Read DID D034 (Counter for number of software resets)
    expected_result:
        To receive the counter value for number of software resets
    """
    res = dut.uds.read_data_by_id_22(bytes.fromhex('D034'))
    pp_result(res)


def step_6(dut: Dut):
    """
    action:
        Read DID DAC3 (SW Reset Type)
    expected_result:
        To receive the SW Reset Type
    """
    res = dut.uds.read_data_by_id_22(bytes.fromhex('DAC3'))
    pp_result(res)


def step_7(dut: Dut):
    """
    action:
        Read DID DAC6 (3 last SW Reset Types)
    expected_result:
        To receive the 3 last SW Reset Types
    """
    res = dut.uds.read_data_by_id_22(bytes.fromhex('DAC6'))
    pp_result(res)


def run():
    """
    Run
    """
    dut = Dut()
    start_time = dut.start()

    result = False
    try:
        dut.precondition(timeout=60)
        dut.step(step_1, purpose="Service 22 - Read D034")
        dut.step(step_2, purpose="Service 22 - Read DAC3")
        dut.step(step_3, purpose="Service 22 - Read DAC6")
        dut.step(step_4, purpose="Service 11 - Do a hardreset")
        dut.step(step_5, purpose="Service 22 - Read D034")
        dut.step(step_6, purpose="Service 22 - Read DAC3")
        dut.step(step_7, purpose="Service 22 - Read DAC6")
        result = True
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)

if __name__ == '__main__':
    run()
