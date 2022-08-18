"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 52235
version: 2
title: RequestDownload Service on Classic CAN
purpose: >
    To define the size of transfer data blocks.

description: >
    The maxNumberOfBlockLenght shall be dimensioned to be as big as possible.
    The maxNumberOfBlockLenght on CAN Classic shall be between 2048 to 4095 bytes.

details: >
    Verify minimum maxNumberOfBlockLenght is between 2048 to 4095 bytes
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_service31 import SupportService31
from supportfunctions.support_service34 import SupportService34

SSBL = SupportSBL()
SE27 = SupportService27()
SE31 = SupportService31()
SE34 = SupportService34()


def step_1(dut: Dut):
    """
    action: Verify minimum maxNumberOfBlockLenght is between 2048 to 4095 bytes
    expected_result: True when maxNumberOfBlockLenght is between 2048 to 4095 bytes
    """
    # Loads the rig specific VBF files
    vbf_result = SSBL.get_vbf_files()
    if not vbf_result:
        logging.error("Test Failed: Unable to load VBF files")
        return False

    # Verify programming preconditions
    routinecontrol_result = SE31.routinecontrol_requestsid_prog_precond(dut)
    if not routinecontrol_result:
        logging.error("Test Failed: Programming preconditions are not fulfilled")
        return False

    # Set to programming session
    dut.uds.set_mode(2)

    # Security access
    sa_result = SE27.activate_security_access_fixedkey(dut, sa_keys=dut.conf.default_rig_config)
    if not sa_result:
        logging.error("Test Failed: Security access denied in programming session")
        return False

    # Read VBF files for SBL file (1st logical block)
    _, vbf_header, data, data_start = SSBL.read_vbf_file(SSBL.get_sbl_filename())

    # Extract data for the 1st data block from SBL
    block_by = SSBL.block_data_extract(data, data_start)[1]

    # Get maxNumberOfBlockLenght from request download service
    SSBL.vbf_header_convert(vbf_header)
    nbl = SE34.request_block_download(dut, vbf_header, block_by)[1]

    # Verify min maxNumberOfBlockLenght is between 2048 to 4095 bytes
    if 2048 < nbl < 4095:
        logging.info("maxNumberOfBlockLenght is between 2048 to 4095 bytes as expected")
        return True

    logging.error("Test Failed: Expected maxNumberOfBlockLenght between 2048 to 4095 bytes,"
                  " received %s", nbl)
    return False


def step_2(dut: Dut):
    """
    action: ECU hardreset
    expected_result: True when ECU is in default session
    """
    # ECU reset
    result = dut.uds.ecu_reset_1101()
    if not result:
        logging.error("Test Failed: ECU reset failed")
        return False

    # Verify active diagnostic session
    active_session = dut.uds.active_diag_session_f186()
    if active_session.data["details"]["mode"] == 1:
        logging.info("ECU is in default session as expected")
        return True

    logging.error("Test Failed: ECU is not in default session")
    return False


def run():
    """
    Verify minimum maxNumberOfBlockLenght is between 2048 to 4095 bytes
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=40)

        result_step = dut.step(step_1, purpose='Verify minimum maxNumberOfBlockLenght is between'
                                               ' 2048 to 4095 bytes')
        if result_step:
            result_step = dut.step(step_2, purpose='ECU hardreset')
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
