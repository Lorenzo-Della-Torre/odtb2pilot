"""
/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

"""
reqprod: 68230
version: 4
title:
    ECU Serial Number data record

purpose:
    To enable readout of the unique ECU serial number.

description: >
    Rationale:

    The serial number is a vital part for any process that requires
    traceability of mounted specific ECUs down to a vehicle individual. E.g. of
    such processes are the aftersales SWDL process and situations where
    vehicles are to be recalled due to warranty reasons. In case of recalls,
    the supplier must have designed and implemented the serial number in such a
    way that it is possible to trace which individual vehicles that are
    affected by using the serial number in combination with a hardware number.

    The combination of serial and core assembly part number must be unique even
    in the case where the delivered components are manufactured in different
    plants or production lines.

    Example of serial number format (length and coding)
    12345678 -> 12 34 56 78
    123456 -> 00 12 34 56

    Req:
    A data record with identifier as specified in the table below shall be
    implemented exactly as defined in Carcom - Global Master Reference
    Database. It shall be designed so that each individual ECU will have a
    unique serial number per ECU Core Assembly Part Number, independent of
    manufacturing plant/line. The combination of the serial and Core assembly
    part number shall support the possibility to identify individual ECUs.

    Description: ECU Serial number data record
    Identifier: F18C

    Read/write access:
     * It shall be possible to read the data record by using the diagnostic
       service specified in Ref[LC : Volvo Car Corporation - UDS Services -
       Service 0x22 (ReadDataByIdentifier) Reqs].
     * It shall not be possible to write to the data record using any
       diagnostic service after the supplier manufacturing process.

    Format and length:
    The data record shall have 8 digits for the serial number, all coded in
    BCD. The data record shall have a fixed length of 4 bytes, be right
    justified with any unused digit(s) filled with 0.

    Origin:
    The serial number shall be created in the supplier manufacturing process.

    Supported sessions:
    The identifier shall be implemented in the following sessions:
     * Default session
     * Programming session (which includes both primary and secondary bootloader)
     * Extended Session


details:
    Retrieve the ECU serial number in all sessions including primary and
    secondary bootloader

"""

import sys
import logging

from hilding.dut import Dut
from hilding.dut import DutTestError


def step_1(dut: Dut):
    """
    action:
        retrieve the ecu serial number with the did F18C

    expected_result:
        positive response containing the serial number
    """
    __call_f18c(dut)


def step_2(dut: Dut):
    """
    action:
        set the ecu in extended mode

    expected_result:
        positive response
    """
    dut.uds.set_mode(3)


def step_3(dut: Dut):
    """
    action:
        retrieve the ecu serial number with the did F18C

    expected_result:
        positive response containing the serial number
    """
    __call_f18c(dut)


def step_4(dut: Dut):
    """
    action:
        set the ecu in programming mode (pbl)

    expected_result:
        positive response
    """

    dut.uds.set_mode(2)


def step_5(dut: Dut):
    """
    action:
        retrieve the ecu serial number with the did F18C

    expected_result:
        positive response containing the serial number
    """
    __call_f18c(dut)


def step_6(dut: Dut):
    """
    action:
        set the ecu in programming mode (sbl)

    expected_result:
        positive response
    """
    dut.uds.enter_sbl()


def step_7(dut: Dut):
    """
    action:
        retrieve the ecu serial number with the did F18C

    expected_result:
        positive response containing the serial number
    """
    __call_f18c(dut)


def __call_f18c(dut: Dut):
    ecu_serial_number_f18c = bytes.fromhex('F18C')
    res = dut.uds.read_data_by_id_22(ecu_serial_number_f18c)
    if res.empty() or not res.data["did"] == "F18C":
        raise DutTestError("Could not retrieve ECU serial number")

    logging.info(res)

    item = res.details["item"]

    if len(item) != 8:
        raise DutTestError("ECU has incorrect length")

    size = res.details["size"]
    if size != 4:
        raise DutTestError(f"SDDB contains wrong ECU serial number "
                           f"length definition: {size}")

    return item


def run():
    """
    ECU Serial Number Data Record F18C
    """
    logging.basicConfig(
        format=' %(message)s', stream=sys.stdout, level=logging.DEBUG)

    dut = Dut()
    start_time = dut.start()

    result = False
    try:
        dut.precondition()
        step_1(dut)
        step_2(dut)
        step_3(dut)
        step_4(dut)
        step_5(dut)
        step_6(dut)
        step_7(dut)

        result = True
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)

if __name__ == '__main__':
    run()
