"""
/*********************************************************************************/
Copyright © 2021 Volvo Car Corporation. All rights reserved.
NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.
/*********************************************************************************/
reqprod: 404693
version: 3
title: Verification Block Table Header Identifiers
purpose: >
    Define the required header identifiers required to
    support the applied signing method.
description: >
    The header section of the delivered software part
    must contain the following identifier with respect
    to the verification block table, when a verification
    block table is constructed according to the format in
    "REQPROD 398360 Format of the Verification Block Table".
    Alternative 1 - verification block header identifiers (default configuration)
    verification_block_root_hash: The hash value of the unprocessed verification block table.
    verification_block_start: The start address of the unprocessed verification block table.
    verification_block_length: The length of the unprocessed verification block table.
    Upon Volvo approval, the header section can exclude the verification_block_start and
    verification_block_length identifiers
    Alternative 2 - verification block header identifiers
    verification_block_root_hash
    This might be applied for ECUs where existing installation and verification mechanisms,
    using e.g. ECU specific manifests, are to be reused in the ECU to ensure authenticity
    that is not possible to realize using the Volvo verification block table format
details: >
    Read VBF File and check if following keys are present
    in Vbf Header:
        1.verification_block_start
        2.verification_block_length
        3.verification_block_root_hash
"""

import logging
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_SBL import SupportSBL

SSBL = SupportSBL()


def step_1(dut: Dut):
    """
    action: Reading VBF Headers from Vbf Files
    expected_result: Verifying the presence of Vbf Table Header Identifiers
                     (verification_block_start,verification_block_length,
                     verification_block_root_hash)
    """
    rig = dut.conf.rig
    # Reading all vbf file paths
    vbf_files = [str(f.resolve()) for f in rig.vbf_path.glob("*.vbf")]
    if len(vbf_files) == 0:
        msg = "Test Failed: No VBF file found in path- {}".format(rig.vbf_path)
        logging.error(msg)
        return False
    check_files = []
    # Reading vbf headers of all files and checking Vbf Table Header Identifiers
    for file in vbf_files:
        try:
            vbf_header = SSBL.read_vbf_file(file)[1]
            logging.info('verification_block_start :%s',
                         vbf_header["verification_block_start"])
            logging.info('verification_block_length :%s',
                         vbf_header["verification_block_length"])
            logging.info('verification_block_root_hash :%s',
                         vbf_header["verification_block_root_hash"])
            # Append True if header identifiers exist in the file
            check_files.append(bool(vbf_header["verification_block_start"] and
                                    vbf_header["verification_block_length"] and
                                    vbf_header["verification_block_root_hash"]))
        except KeyError as keyerror:
            msg = "Test Failed: {} not found in the VBF file {}".format(
                keyerror.args[0], file)
            logging.error(msg)
            return False
    result = (len(check_files) != 0) and all(check_files)
    return result


def run():
    """
    Verification of Vbf Header if verification_block_start,
    verification_block_length,verification_block_root_hash are present.
    """

    dut = Dut()

    start_time = dut.start()
    result = False
    try:
        # Communication with ECU lasts 60 seconds.
        dut.precondition(timeout=60)

        # Reading of VBF files and check vbf table header identifier
        result = dut.step(step_1, purpose='Read the vbf file and verify all the \
                    block header identifiers')

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
