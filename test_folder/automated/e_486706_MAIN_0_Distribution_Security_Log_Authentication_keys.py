"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



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
    ECU supplier. The keys, initial keys, for ECUs intented for "production" shall be implemented at
    latest prior to "vehicle prototype build" unless others are agreed for the project. This is the
    latest milestone to change initial keys.

details:
    Reading the status from (D0C7) as the checksum cannot be read.
    Expect Positive response when the key programed status is 1.
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError


def step_1(dut: Dut):
    """
    action: Send ECU to programming session and read DID D0C7
    expected_result: Positive response with the key programed status is 1
    """
    dut.uds.set_mode(2)
    res = dut.uds.read_data_by_id_22(b'\xd0\xc7')
    return res.data["details"]["response_items"][0]['scaled_value'] == 1


def run():
    """ Supporting functional requests """
    dut = Dut()
    start_time = dut.start()
    result = False

    try:
        dut.precondition()
        result = dut.step(
            step_1, purpose='Reading DID D0C7 for checking key programed status')
    except DutTestError as error:
        logging.error("Test failed: %s", error)

    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
