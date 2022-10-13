"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 404694
version: 2
title: Verification Block Root Hash
purpose: >
    Define how to calculate the verification block root hash,
    carrying the information of unprocessed data that is required to support
    use cases of having processing methods not necessarily known to the Trust Centre.

description: >
    The verification_block_root_hash must be calculated on the "raw" unprocessed data in
    the verification block table prior to any padding, encryption/compression/delta encoding
    methods have been applied to the VBT data block. The verification block root hash shall be
    calculated as Hash(startAddress||length||Verification Block Table data),
    where || represents the concatenation.
    The order shall be according to Figure - Verification Block Root Hash calculation.
    The start address (verification_block_start) and length (verification_block_length) are
    included to ensure the placement of the verification block and shall always be
    32 bits long each.The (root) hash function shall be the same as used when
    calculating the hash value of the data blocks defined in
    the verification block table REQPROD 404696.

    The root hash value shall be added by the software supplier to the header of the software part.

    Example 1.
    All values are in hexadecimal. SHA-256 is used as hash function.
    Hash(startAddress||length||Verification Block Table data)=
    Hash(00 05 FF 00 00 00 00 54 00 00 00 02 00 00 F0 00 00 00 00 88 B7 07 24 15 45 A3 46 26 5A AB
    1F FB 32 FF 64 B5 5B F8 F8 DC 1B 56 A4 6E F3 3C E3 D1 5D B1 1D 33 00 00 F1 00 00 00 00 10 5A 2C
    FE 8A B9 35 91 85 25 D4 4F D6 FD 87 C7 0F C8 3B 4F 29 D1 A7 27 67 2E 1B 48 F3 80 47 3F C1) =
    9B B4 E0 92 1C 4B 84 1C 31 C3 CB 3F DD 15 D0 B9 E8 ED 70 5E D3 C2 52 DC C9 2A D5 06 E0 5E 2B AE.

    Start Address: 0005FF00
    Length: 00000054
    Data: 00 00 00 02 00 00 F0 00 00 00 00 88 B7 07 24 15 45 A3 46 26 5A AB 1F FB 32 FF 64 B5 5B
    F8 F8 DC 1B 56 A4 6E F3 3C E3 D1 5D B1 1D 33 00 00 F1 00 00 00 00 10 5A 2C FE 8A B9 35 91 85
    25 D4 4F D6 FD 87 C7 0F C8 3B 4F 29 D1 A7 27 67 2E 1B 48 F3 80 47 3F C1

    Example 2.
    The length of the data block for a verification block table is 44 bytes long, prior to any
    padding or processing method is applied. All data blocks shall be aligned to a multiple of
    8 bytes. Hence, the VBT data block is padded to 48 bytes, but verification_block_length is
    still 44 (0x2C). It is this length that is used when calculating the
    verification_block_root_hash.

    Note; Be aware of the differences of how to manage the padding of data and start/length
    information for data blocks that are defined in the verification block table versus the
    data block containing the VBT.

details: >
    Read VBF, calculating root hash by concatenating start, length & verification block table
    data and comparing the calculated root hash value with value present in vbf header.
"""

import logging
import hashlib
from glob import glob
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_lzma import LzmaEncoder

LZMA = LzmaEncoder()
SSBL = SupportSBL()


def extract_vbt(vbf_data, vbf_offset):
    """
    Extracting vbf data block from vbf parameters
    Args:
        vbf_data (str): VBF data block
        vbf_offset (int): VBF offset
    Returns:
        data_block (str): VBT data in hex
    """
    data_block = ''
    # To extract VBT data, we need to extract last block of VBF file
    # So we are iterating through the loop and extracting every block
    # and in the last iteration of the loop, we receive VBT data block.
    while True:
        vbf_offset, vbf_block, vbf_block_data = SSBL.block_data_extract(vbf_data, vbf_offset)
        if vbf_block['StartAddress'] == 0:
            logging.debug("No more blocks")
            break
        data_block = LZMA.decode_barray(vbf_block_data)

    return data_block.hex()


def extract_vbf_params(vbf_path):
    """
    Extracting vbf parameters from vbf file
    Args:
        vbf_path (dict): VBF file path
    Returns:
        vbf_params (dict): VBF parameters with file name
    """
    vbf_params = {'vbf_data': '',
                  'vbf_root_hash': '',
                  'file_name': ''}

    _, vbf_header, vbf_data, vbf_offset = SSBL.read_vbf_file(vbf_path)
    vbt = extract_vbt(vbf_data, vbf_offset)

    vbf_params["vbf_root_hash"] = vbf_header['verification_block_root_hash']
    # Used [2:] to remove '0x' from the hex string
    vbf_params["vbf_data"] = (vbf_header["verification_block_start"][2:] +
                              vbf_header["verification_block_length"][2:] + vbt)
    vbf_params["file_name"] = vbf_path.split('/')[-1]

    return vbf_params


def compare_root_hash(vbf_params_list):
    """
    Compare root hash values, calculated from vbf data with the values present in vbf header
    Args:
        vbf_params_list (list): VBF parameters
    Returns:
        (bool): True when hash values in vbf header are equal with calculated hash value
    """
    check_list = []

    for vbf_params in vbf_params_list:
        result = False
        calculated_hash = hashlib.sha256(bytes.fromhex(vbf_params["vbf_data"]))
        calculated_hash_hex = calculated_hash.hexdigest().upper()
        vbf_root_hash = vbf_params["vbf_root_hash"][2:]

        if calculated_hash_hex == vbf_root_hash:
            result = True

        check_list.append(result)

    if len(check_list) != 0 and all(check_list):
        return True

    return False


def step_1(dut: Dut):
    """
    action: Calculate root hash from vbf data and compare with the value present in vbf header
    expected_result: True when both calculated and value present in vbf header are equal
    """
    rig_vbf_path = dut.conf.rig.vbf_path
    vbf_paths = glob(str(rig_vbf_path) + "/*.vbf")

    if len(vbf_paths) == 0:
        logging.error("Test Failed: No vbf file found in path: %s", rig_vbf_path)
        return False

    vbf_params_list = list(map(extract_vbf_params, vbf_paths))
    result = compare_root_hash(vbf_params_list)
    if result:
        logging.info("Calculated root hash value and the root hash value present in vbf are equal")
        return True

    logging.error("Test Failed: Calculated root hash value and the root hash value present in vbf "
                  "header are not equal")
    return False


def run():
    """
    Extracting verification block start, verification block length, VBT data.
    Calculating hash(SHA256) and comparing with verification block root hash.
    """
    dut = Dut()

    start_time = dut.start()
    result = False

    try:
        dut.precondition(timeout=30)

        result = dut.step(step_1, purpose="Calculate root hash from vbf data and compare with the "
                                          "value present in vbf header")

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
