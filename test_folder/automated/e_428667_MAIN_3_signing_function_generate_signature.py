"""
/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 428667
version: 3
title: Signing function - Generate signature
purpose: >
    Define the input data to the signing function.

description: >
    The data to be signed is defined by the verification_block_start and verification_block_length
    identifiers. These start address, length and data of the addressed data block shall be used
    as inputs when generating the hash value. The signing entity has two possibilities:

    (1) always calculate the hash value over the verification block table and ensure that the
        content of the table is correct. This is the preferred option.
    (2) use the already calculated hash value (verification_block_root_hash).

details: >
    Verify Software Authentication (CheckMemory routine) with proper and manipulated
    vbf software signature.
    Steps:
        1. Enter into programming session and security access to ECU
        2. Verify Software Authentication (CheckMemory routine) with proper vbf software signature
        3. Verify Software Authentication (CheckMemory routine) with manipulated vbf software
           signature
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_service31 import SupportService31

SSBL = SupportSBL()
SE27 = SupportService27()
SE31 = SupportService31()


def step_1(dut: Dut):
    """
    action: Enter into programming session and security access to ECU

    expected_result: ECU is in programming session and security access successful.
    """
    # Change to programming session
    dut.uds.set_mode(2)

    # Security access to ECU
    result = SE27.activate_security_access_fixedkey(dut, sa_keys=dut.conf.default_rig_config,
                                                    step_no=272, purpose="SecurityAccess")
    if result:
        logging.info("Security access granted")
        return True

    logging.error("Test failed: Security access denied")
    return False


def step_2(dut: Dut):
    """
    action: Verify Software Authentication (CheckMemory routine)
            with proper vbf software signature

    expected_result: Check memory should pass for manipulated vbf software signature
    """
    result = SSBL.get_vbf_files()
    if not result:
        logging.error("Test failed: Unable to load VBF files")
        return False

    _, vbf_header, vbf_data, vbf_offset = SSBL.read_vbf_file(SSBL.get_sbl_filename())
    SSBL.vbf_header_convert(vbf_header)

    result = SSBL.transfer_data_block(dut, vbf_header, vbf_data, vbf_offset)
    if not result:
        logging.error("Test failed: Transfer data failed")
        return False

    check_memory_bool = SE31.check_memory(dut, vbf_header, stepno=2)
    if check_memory_bool:
        logging.info("CRC passed as expected for proper sw_signature_dev")
        return True

    logging.error("Test failed: CRC should pass for proper sw_signature_dev")
    return False


def step_3(dut: Dut):
    """
    action: Verifying Software Authentication (CheckMemory routine)
            with manipulated vbf software signature

    expected_result: Check memory should fail for manipulated vbf software signature
    """

    _, vbf_header, vbf_data, vbf_offset = SSBL.read_vbf_file(SSBL.get_sbl_filename())
    logging.info("Original sw_signature_dev:% s", vbf_header["sw_signature_dev"])

    # Manipulating sw_signature_dev present in VBF header
    vbf_header["sw_signature_dev"] = vbf_header["sw_signature_dev"][:2] +\
        len(vbf_header["sw_signature_dev"][2:])*"F"
    logging.info("Manipulated sw_signature_dev: %s", vbf_header["sw_signature_dev"])

    SSBL.vbf_header_convert(vbf_header)

    result = SSBL.transfer_data_block(dut, vbf_header, vbf_data, vbf_offset)
    if not result:
        logging.error("Test failed: Transfer data failed")
        return False

    check_memory_bool = SE31.check_memory(dut, vbf_header, stepno=3)
    if not check_memory_bool:
        logging.info("CRC failed as expected for manipulated sw_signature_dev")
        return True

    logging.error("Test failed: Expected crc to fail fail for manipulated sw_signature_dev")
    return False


def run():
    """
    Verify Software Authentication (CheckMemory routine) with proper and manipulated
    vbf software signature
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False
    try:
        dut.precondition(timeout=120)

        result_step = dut.step(step_1, purpose="Security Access to ECU.")

        if result_step:
            result_step = dut.step(step_2, purpose="Verify check memory with valid"
                                    " vbf software signature")

        if result_step:
            result_step = dut.step(step_3, purpose="Verify check memory with manipulated"
                                    " vbf software signature")

        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
