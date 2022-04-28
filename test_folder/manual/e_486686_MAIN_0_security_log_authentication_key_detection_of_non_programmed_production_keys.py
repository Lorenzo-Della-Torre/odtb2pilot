"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 486686
version: 0
title: Security Log Authentication Key - detection of non-programmed production keys
purpose: >
    To identify when the initial Security Log Authentication key is still present in the ECU,
    in case of failure when confidential production key for some reasons haven't been programmed

description: >
    The ECU shall report the current write status of Secure Log Authentication key, i.e. status
    indicating if the key has been written according to the requirement "REQPROD 486685 : Security
    Log Authentication key programming at OEM". The information shall be accessible by
    readDataByIdentifier service using DID “Security Log Authentication Key Write Status” DID
    0xD0C7 as defined in the Global Master Reference Database

    The read only DID shall be possible to read in all sessions and it shall not be protected by
    security access. Status “programmed” means Security Log Authentication key is successfully
    programmed.

    Note.
    If it is agreed by OEM that some key is one-time-programmable at supplier, 0x00 shall be
    reported.

details: >
    Verify current write status of Secure Log Authentication key
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_file_io import SupportFileIO

SE22 = SupportService22()
SIO = SupportFileIO()


def step_1(dut: Dut):
    """
    action: Read did 'D0C7' (Secure log authentication - key write status)
    expected_result: Successfully read did 'D0C7' and Secure log authentication - key write status
    """
    # Read yml parameters
    parameters_dict = {'did': ''}
    parameters = SIO.parameter_adopt_teststep(parameters_dict)

    if not all(list(parameters.values())):
        logging.error("Test Failed: yml parameter not found")
        return False

    # Read did 'D0C7'(Secure log authentication - key write status)
    response = dut.uds.read_data_by_id_22(bytes.fromhex(parameters['did']))

    # Compare positive response
    if response.raw[2:4] == '62':
        logging.info("Successfully read DID: %s with positive response %s ",
                     parameters['did'], response.raw[2:4])
        if response.raw[8:10] == '00':
            logging.info("Secure log authentication key(Programmed) %s received",
                          response.raw[8:10])
            return True

        logging.error("Test Failed: Expected Secure log authentication key(Programmed), "
                           "received %s ", response.raw[8:10])
        return False

    logging.error("Test Failed: Expected positive response 62 for DID: %s, received %s",
                  parameters['did'], response.raw)
    return False


def run():
    """
    Read did 'D0C7' and Verify secure log authentication key is programmed or not programmed.
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    try:
        dut.precondition(timeout=30)

        result = dut.step(step_1, purpose="Read did 'D0C7' (Security Log Authentication "
                                               "Key Write Status) and verify "
                                               "positive response and write status of key ")
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
