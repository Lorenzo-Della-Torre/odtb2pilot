"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 53838
version: 1
title: PBL can only write data to volatile memory
purpose: >
    Due to security and integrity purpose shall the PBL not be able to write or erase data in the
    non-volatile memory.

description: >
    The primary bootloader shall only be capable of writing data to the volatile memory. Erasure
    or writing to non-volatile memory is not allowed.

details: >
    Verify request block download is rejected for ESS file in PBL.
"""

import time
import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_service34 import SupportService34

SSBL = SupportSBL()
SE27 = SupportService27()
SE34 = SupportService34()


def step_1(dut: Dut):
    """
    action: Security access in programming session
    expected_result: Security access should be successful in programming session
    """
    # Set ECU in programming session
    dut.uds.set_mode(2)

    # Sleep time to avoid NRC37
    time.sleep(5)

    result = SE27.activate_security_access_fixedkey(dut, sa_keys=dut.conf.default_rig_config)
    if result:
        logging.info("Security access is successful in PBL")
        return True

    logging.error("Test Failed: Security access denied in PBL")
    return False


def step_2(dut: Dut):
    """
    action: Verify request block download(service 34) is rejected for ESS file
    expected_result: True when request block download rejected
    """
    # Extract vbf header and vbf block from ESS file
    SSBL.get_vbf_files()
    _, vbf_header, data, data_start = SSBL.read_vbf_file(SSBL.get_ess_filename())
    vbf_block = SSBL.block_data_extract(data, data_start)[1]
    SSBL.vbf_header_convert(vbf_header)

    # Request block download
    result = SE34.request_block_download(dut, vbf_header, vbf_block)[0]
    if not result:
        logging.info("Request block download is failed as expected")
        return True

    logging.error("Test Failed: Request block download should be failed")
    return False


def step_3(dut: Dut):
    """
    action: ECU hard reset and verify active diagnostic session
    expected_result: ECU should be in default session after ECU hard reset
    """
    # ECU hard reset
    dut.uds.ecu_reset_1101()

    # Verify active diagnostic session
    response = dut.uds.active_diag_session_f186()
    if response.data["details"]["mode"] == 1:
        logging.info("ECU is in default session as expected")
        return True

    logging.error("Test Failed: Expected ECU to be in default session, but it is in mode %s",
                  response.data["details"]["mode"])
    return False


def run():
    """
    Verify request block download is rejected for ESS file in PBL.
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=60)

        result_step = dut.step(step_1, purpose="Security access in programming session")
        if result_step:
            result_step = dut.step(step_2, purpose="Verify request block download(service 34) is "
                                                   "rejected for ESS file")
        if result_step:
            result_step = dut.step(step_3, purpose="Verify ECU is in default session")
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
