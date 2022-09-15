"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 486706
version: 0
title: Distribution of the Security Log Authentication keys to ECU suppliers
purpose:
    The OEM must be in control of the key applied and for separation of keys
    used during development and production

description:
    The security log authentication key shall be provided by the OEM,
    i.e. the ECU supplier must not choose these.
    This is applicable for key(s) used during both development and production.
    Unless others are agreed, the initial key value shall be "0x000102030405060708090A0B0C0D0E0F"
    for which CRC16-CCITT checksum will be 0x3B37.
    Note.
    Development keys are by default generated in Global Master Reference Database and exported to
    ECU supplier. The keys, initial keys, for ECUs intended for "production" shall be implemented at
    latest prior to "vehicle prototype build" unless others are agreed for the project. This is the
    latest milestone to change initial keys.

details:
    Reading DID D0C7 for checking key programmed status as the checksum cannot be read.
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError


def step_1(dut: Dut):
    """
    action: Send ECU to programming session and read DID 'D0C7'
    expected_result: True when the key programmed status is 1
    """
    # Set to programming session
    dut.uds.set_mode(2)
    response = dut.uds.read_data_by_id_22(bytes.fromhex('D0C7'))

    key_programmed_status = response.data["details"]["response_items"][0]['scaled_value']
    if key_programmed_status == 1:
        logging.info("key programed status is %s as expected", key_programmed_status)
        return True

    logging.error("Test Failed: Expected key programed status is 1 but received %s",
                  key_programmed_status)
    return False


def run():
    """
    Reading DID D0C7 for checking key programed status as the checksum cannot be read
    """
    dut = Dut()

    start_time = dut.start()
    result = False

    try:
        dut.precondition(timeout=30)
        result = dut.step(step_1, purpose='Send ECU to programming session and read DID D0C7')
    except DutTestError as error:
        logging.error("Test failed: %s", error)

    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
