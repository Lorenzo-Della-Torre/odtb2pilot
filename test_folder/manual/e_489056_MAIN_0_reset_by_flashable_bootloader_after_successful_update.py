"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 489056
version: 0
title: Reset by flashable bootloader after successful update
purpose: >
    As the Flashable PBL may not be able to communicate with the tester, it needs to reset itself
    after the erase and copy process has finished in order to resume normal operations and enable
    communication to the tester.

description: >
    Reset shall be performed by flashable PBL itself after the successful PBL update.

details: >
    Verify ECU stays in programming session and is able to communicate with tester after
    flash PBL using software download.
    Steps -
    1. Flash PBL using software download.
    2. Verify ECU stays in programming session
    3. Verify ECU is able to communicate with tester
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_service22 import SupportService22

SSBL = SupportSBL()
SE22 = SupportService22()


def step_1(dut: Dut):
    """
    action: Change to programming session and flash PBL using software download.
    expected_result: ECU is able to flash PBL using software download.
    """
    # Change to programming session
    dut.uds.set_mode(2)

    # Load VBF files
    result = SSBL.get_vbf_files()
    if not result:
        logging.error("Test failed: Unable to load VBF files")
        return False


    # Flash PBL using software download.
    result = SSBL.sbl_activation(dut, sa_keys=dut.conf.default_rig_config)

    if result:
        logging.info("Flash PBL using software download successful")
        return True

    logging.error("Test failed: Flash PBL using software download failed")
    return False


def step_2(dut: Dut):
    """
    action: Verify ECU is in programming session and able to communicate with tester
    expected_result: ECU is in programming session and respond to Read DID request.
    """

    result = SE22.read_did_f186(dut, b'\x02')
    if not result:
        logging.error("Test failed: Expected ECU to be in programming session.")
        return False

    # Verify ECU communicates with tester by responding to Read DID request
    response = dut.uds.read_data_by_id_22(bytes.fromhex('F125'))
    if response.raw[2:4] =='62':
        return True

    logging.error("Test failed: Expected ECU to communicate after flash PBL"
                    " using software download.")
    return False


def run():
    """
    Verify ECU stays in programming session and is able to communicate with tester after
    flash PBL using software download.
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False
    try:
        dut.precondition(timeout=60)

        result_step = dut.step(step_1, purpose="Change to programming session and flash PBL"
                                                " using software download")

        if result_step:
            result_step = dut.step(step_2, purpose="Verify ECU is in programming session and able"
                                                " to communicate with tester")

        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)

if __name__ == '__main__':
    run()
