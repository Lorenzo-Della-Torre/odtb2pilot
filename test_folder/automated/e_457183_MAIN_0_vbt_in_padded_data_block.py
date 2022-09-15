"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 457183
version: 0
title: Verification Block Table in a padded data block
purpose: >
    To clarify how to manage the verification block table when there is a need to align that
    data block to a specific length, e.g. to match the start and/or end of a data block to the
    boundary of a flash sector (for an addressed based ECU). This requirement is valid for the
    data block containing the VBT, i.e. for all other data blocks the padding will be treated
    as any other data when generating the VBT.

description: >
    If there is a must to align and pad the data blocks to some specific size, the padded data
    must have the value of erased memory, i.e. it will be included in the ECU "blank" check.
    Note: The verification_block_start, verification_block_length and verification_block_root_hash
    shall be generated using the "raw" unprocessed data in the verification block table prior to
    any padding is applied to this specific data block.

details: >
    Implicitly tested script
    Tested implicitly by REQPROD 400425 because software download has covered in
    programming of Logical Blocks
"""
import logging
import sys
from e_400425_MAIN_2_programming_of_logical_blocks import run

logging.basicConfig(format=' %(message)s',stream=sys.stdout, level=logging.INFO)


if __name__ == '__main__':
    run()
