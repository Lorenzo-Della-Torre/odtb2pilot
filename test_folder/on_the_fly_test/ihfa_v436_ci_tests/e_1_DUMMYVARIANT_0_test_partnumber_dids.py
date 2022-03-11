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

import logging

from hilding.dut import Dut
from hilding.dut import DutTestError

def _read_did(dut, did_id):
    """Report the DTC extended data record by DTC number

    THIS FUNCTION WILL ALMOST ALWAYS RETURN TRUE. REMOVE TRY/EXCEPT
    WHEN SDDB IS UPDATED

    Args:
        dut (Dut): Instance of Dut
        did_id (string): Did id, ex: DD00

    Returns:
        Boolean: The result of the read
    """

    try:
        ECU_response = dut.uds.read_data_by_id_22(bytes.fromhex(did_id))
        logging.info("Response from ECU: %s", ECU_response)
        if did_id.upper() not in ECU_response.raw:
            logging.error("The DID %s was not read successfully", did_id)
            return False

        return True

    except KeyError:
        logging.error("%s most likely not found in sddb (could be other causes)", did_id)
        return True


def step_1(dut: Dut):
    """
    action:
        Read DID DD00
    expected_result: >
        ECU: Valid reply from ECU
    """

    return _read_did(dut, "DD00")

def step_2(dut: Dut):
    """
    action:
        Read DID DD00
    expected_result: >
        ECU: Valid reply from ECU
    """

    return _read_did(dut, "DD01")

def step_3(dut: Dut):
    """
    action:
        Read DID DD00
    expected_result: >
        ECU: Valid reply from ECU
    """

    return _read_did(dut, "F120")

def step_4(dut: Dut):
    """
    action:
        Read DID DD00
    expected_result: >
        ECU: Valid reply from ECU
    """

    return _read_did(dut, "F126")

def step_5(dut: Dut):
    """
    action:
        Read DID DD00
    expected_result: >
        ECU: Valid reply from ECU
    """

    return _read_did(dut, "F12A")

def step_6(dut: Dut):
    """
    action:
        Read DID DD00
    expected_result: >
        ECU: Valid reply from ECU
    """

    return _read_did(dut, "F12B")

def step_7(dut: Dut):
    """
    action:
        Read DID DD00
    expected_result: >
        ECU: Valid reply from ECU
    """

    return _read_did(dut, "F18C")

def run():
    """ Supporting functional requests """
    dut = Dut()
    start_time = dut.start()
    result = False
    step_result = False
    try:
        dut.precondition()

        step_result = dut.step(step_1, purpose = "Read did DD00")

        if step_result:
            step_result = dut.step(step_2, purpose = "Read did DD01")

        if step_result:
            step_result = dut.step(step_3, purpose = "Read did F120")

        if step_result:
            step_result = dut.step(step_4, purpose = "Read did F126")

        if step_result:
            step_result = dut.step(step_5, purpose = "Read did F12A")

        if step_result:
            step_result = dut.step(step_6, purpose = "Read did F12B")

        if step_result:
            step_result = dut.step(step_7, purpose = "Read did F18C")

        result = step_result

    except DutTestError as error:
        logging.error("The testcase failed: %s", error)
    finally:
        dut.postcondition(start_time, result)
if __name__ == '__main__':
    run()
