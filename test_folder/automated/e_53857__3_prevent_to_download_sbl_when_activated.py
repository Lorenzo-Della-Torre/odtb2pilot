"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 53857
version: 3
title: Prevent the possibility to download the SBL when already activated
purpose: >
    To avoid overwriting the SBL.

description: >
    After download and activation of the SBL in the volatile memory it shall not be possible
    to make a new SBL download to volatile memory, the ECU shall reject to execute the request
    with an NRC. Before a new SBL download to the volatile memory can be performed a hard reset
    of the ECU is required.
    Before the SBL activation request is received a new download of the SBL shall be possible to
    perform.

details: >
    Verify it shall not be possible to make a new SBL download to volatile memory
    Steps:
    1. Request SBL download
    2. Request download of the 1st data block (SBL)
    3. Request ECU hard reset
"""

import time
import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_can import SupportCAN
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_sec_acc import SupportSecurityAccess
from supportfunctions.support_service11 import SupportService11
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_service31 import SupportService31
from supportfunctions.support_service34 import SupportService34

SC = SupportCAN()
SE11 = SupportService11()
SE22 = SupportService22()
SE27 = SupportService27()
SE31 = SupportService31()
SE34 = SupportService34()
SSBL = SupportSBL()
SSA = SupportSecurityAccess()


def sbl_download_activation(dut, stepno):
    """
    SBL download and activation
    Args:
        dut (Dut): dut instance
        stepno (int): step number
    Returns:
        (bool): True on successful SBL download and activation
    """
    # SBL download
    result, vbf_sbl_header = SSBL.sbl_download(dut, SSBL.get_sbl_filename(), stepno)
    if not result:
        logging.error("Test Failed: SBL download failed")
        return False

    # Activate SBL
    result = SSBL.activate_sbl(dut, vbf_sbl_header, stepno)
    if not result:
        logging.error("Test Failed: SBL activation failed")
        return False

    return True


def step_1(dut: Dut):
    """
    action: Request SBL download
    expected_result: True when successfully downloaded SBL
    """
    # Verify programming preconditions
    result = SE31.routinecontrol_requestsid_prog_precond(dut, stepno=1)
    if not result:
        logging.error("Test Failed: Routine control request failed")
        return False

    # Set ECU to programming session
    dut.uds.set_mode(2)

    # Verify programming session
    result = SE22.read_did_f186(dut, dsession=b'\x02')
    if not result:
        logging.error("Test Failed: Expected ECU to be in programming session")
        return False

    # Sleep time to avoid NRC37
    time.sleep(5)
    # Security access to ECU
    result = SE27.activate_security_access_fixedkey(dut, sa_keys=dut.conf.default_rig_config,
                                                    step_no=272, purpose="SecurityAccess")
    if not result:
        logging.error("Test Failed: Security access denied")
        return False

    # SBL download
    SSBL.get_vbf_files()
    result = SSBL.sbl_download(dut, SSBL.get_sbl_filename(), stepno=1)[0]
    if result:
        logging.info("Successfully downloaded SBL")
        return True

    logging.error("Test Failed: SBL download failed")
    return False


def step_2(dut: Dut):
    """
    action: Request download of the 1st data block (SBL)
    expected_result: True when received NRC-31(requestOutOfRange)
    """
    # Download and activate SBL
    result = sbl_download_activation(dut, stepno=1)
    if not result:
        return False

    # Read VBF files for SBL
    _, vbf_header, data, data_start = SSBL.read_vbf_file(SSBL.get_sbl_filename())

    # Extract data for the 1st data block from SBL
    block_by = SSBL.block_data_extract(data, data_start)[1]

    # Verify request download the 1st data block (SBL) is rejected
    SSBL.vbf_header_convert(vbf_header)
    result = SE34.request_block_download(dut, vbf_header, block_by, stepno=340)[0]
    response = SC.can_messages[dut["receive"]][0][2]
    if result:
        logging.error("Expected NRC-31(requestOutOfRange), received %s", response)
        return False

    logging.info("Received NRC-%s(requestOutOfRange) as expected", response[6:8])
    return True


def step_3(dut: Dut):
    """
    action: Request ECU hard reset
    expected_result: True when ECU is in default session
    """
    # ECU hard reset
    ecu_response = SE11.ecu_hardreset_5sec_delay(dut, stepno=3)
    if not ecu_response:
        return False

    # Activate SBL
    result = SSBL.sbl_activation(dut, dut.conf.default_rig_config)
    if not result:
        logging.error("Test Failed: SBL activation failed")
        return False

    # ECU hard reset
    ecu_response = dut.uds.ecu_reset_1101()
    if ecu_response.raw[2:4] != '51':
        logging.error("ECU reset not successful, expected '51', received %s", ecu_response.raw)
        return False

    # Verify ECU in default session
    result = SE22.read_did_f186(dut, b'\x01')
    if result:
        logging.info("ECU is in default session")
        return True

    logging.error("Test Failed: ECU not in default session")
    return False


def run():
    """
    Verify it shall not be possible to make a new SBL download to volatile memory
    """
    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=160)

        result_step = dut.step(step_1, purpose="Request SBL download")

        if result_step:
            result_step = dut.step(step_2, purpose="Request download of the 1st data block (SBL)")
        if result_step:
            result_step = dut.step(step_3, purpose="Request ECU hard reset")

        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
