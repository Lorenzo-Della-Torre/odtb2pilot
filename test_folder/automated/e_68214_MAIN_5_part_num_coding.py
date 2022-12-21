"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

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
    Verify part numbers of DIDs are valid in default, PBL and SBL
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_file_io import SupportFileIO

SIO = SupportFileIO()


def verify_part_number(dut, dids, session):
    """
    verify part number
    Args:
        dut (Dut): An instance of Dut
        dids (list): List of DIDs
        session (str): Diagnostic session
    Returns:
        (bool) : True when part number of all DIDs are valid
    """
    for did in dids:
        response = dut.uds.read_data_by_id_22(bytes.fromhex(did))
        if response.raw[4:6] == '62':
            if not did.upper()+'_valid' in response.data['details']:
                logging.error("Test Failed: No valid %s returned by ecu for did: %s ",
                               response.data['details']['name'], did)
                return False

            logging.info("%s is valid for did %s", response.data['details']['name'], did)

        else:
            logging.error("Test Failed: Expected positive response, received %s for DID %s",
                          response.raw, did)
            return False

    logging.info("Part numbers are valid for all DIDs in %s session", session)
    return True


def step_1(dut: Dut, parameters):
    """
    action: Verify part number of DIDs in default session
    expected_result: Part numbers should be valid for all DIDs
    """
    return verify_part_number(dut, parameters, session='default')


def step_2(dut: Dut, parameters):
    """
    action: Verify part number of DIDs in PBL
    expected_result: Part numbers should be valid for all DIDs
    """
    # Set to programming session
    dut.uds.set_mode(2)

    return verify_part_number(dut, parameters, session='PBL')


def step_3(dut: Dut, parameters):
    """
    action: Verify part_number of DIDs in SBL
    expected_result: Part numbers should be valid for all DIDs
    """
    # Activate SBL
    dut.uds.enter_sbl()

    return verify_part_number(dut, parameters, session='SBL')


def run():
    """
    Verify part numbers of DIDs are valid in default, PBL and SBL
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    parameters_dict = {'default_dids' : [],
                       'pbl_dids' : [],
                       'sbl_dids' : []}

    try:
        dut.precondition(timeout=120)

        parameters = SIO.parameter_adopt_teststep(parameters_dict)
        if not all(list(parameters.values())):
            raise DutTestError("yml parameters not found")

        result_step = dut.step(step_1, parameters['default_dids'], purpose="Verify part number of "
                                                                         "DIDs in default session")
        if result_step:
            result_step = dut.step(step_2, parameters['pbl_dids'], purpose="Verify part number of "
                                                                           "DIDs in PBL")
        if result_step:
            result_step = dut.step(step_3, parameters['sbl_dids'], purpose="Verify part number of "
                                                                           "DIDs in SBL")
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
