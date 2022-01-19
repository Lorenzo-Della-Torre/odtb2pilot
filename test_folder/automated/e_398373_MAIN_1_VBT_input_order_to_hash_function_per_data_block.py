"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 398373
version: 1
title: Verification Block Table - Input order to Hash function per data block
purpose: >
    Define the input order to the hash function per data block.
    If the order is changed, the output from the hash function will be changed also.
    The start address and length of a data block are NOT input to the hash function.
    The placement of a data block is ensured by explicitly defining the start address
    and length per corresponding data block: start address, length, hash (data block)

description: >
    The hash value for each data block in the verification block table shall be
    calculated as Hash(Data), i.e. the start address and length are excluded.
    The data to be hashed starts with the data at the start address.

details: >
    Extracting and calculating the Hash value for each block and comparing
    it with calculated hash present in Verification block table data.
    Steps-
        1. Read and extract all VBF data blocks and verification block
           table(VBT) data from vbf file.
        2. Calculate vbf block hashes.
        3. Filtering hashes from Verification Block Table data(VBT) data.
        4. Compare calculated vbf block data hashes with extracted block hashes
           from Verification Block Table(VBT) data.
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
HASH_SIZE = 64
HASH_INIT_POS = 8

def extract_vbf_blocks(vbf_path):
    """
    Reading vbf file and extracting all the data blocks
    Storing all data blocks in a list
    Preparing block_data_dict with VBT data, VBF block data list and filename
    Args:
        vbf_path (dict): VBF file path
    Returns:
        block_data_dict (dict): dictionary of data blocks
    """
    block_data_dict = {
        'vbt_data': '',
        'vbf_block_data_list': [],
        'file_name': ''
    }
    _, vbf_header, vbf_data, vbf_offset = SSBL.read_vbf_file(vbf_path)
    SSBL.vbf_header_convert(vbf_header)
    # Extracting all the block data from vbf file
    while True:
        vbf_offset, vbf_block, vbf_block_data = SSBL.block_data_extract(
            vbf_data, vbf_offset)
        if vbf_block['StartAddress'] == 0:
            # Terminate the loop if no more blocks are present
            break
        data = LZMA.decode_barray(vbf_block_data).hex()
        block_data_dict["vbf_block_data_list"].append(data)
    # Last block is Verification Block Table Data so removed it from vbf_block_data_list
    # and assigned to vbt_data in block_data_dict dictionary
    block_data_dict["vbt_data"] = block_data_dict["vbf_block_data_list"].pop()
    block_data_dict["file_name"] = vbf_path.split('/')[-1]
    return block_data_dict


def calculate_vbf_data_hashes(vbf_block_data_list):
    """
    Calculating hash of all the VBF block data and storing in
    calculated_block_data_hash_list.
    Args:
        vbf_block_data_list (list): list of VBF block data

    Returns:
        calculated_block_data_hash_list (list) : list of SHA-256 hash of respective block data
    """
    calculated_block_data_hash_list = []
    for vbf_block in vbf_block_data_list:
        calculated_block_data_hash_list.append(hashlib.sha256(bytes.fromhex(
            vbf_block)).hexdigest().upper())
    return calculated_block_data_hash_list


def extract_vbt_hashes(vbt_data):
    """
    Extracting calculated VBF data block hash from VBF Block Table
    and storing in extracted_block_data_hash_list.
    Args:
        vbt_data (str): Verification block table data

    Returns:
        extracted_block_data_hash_list (list): list of SHA-256 hash extracted from
            Verification block table data
    """
    index = 1
    byte_index = 8
    extracted_block_data_hash_list = []
    while byte_index < len(vbt_data):
        if index % 3 != 0:
            # Ignore start-address and block-length from VBT Data
            byte_index += HASH_INIT_POS
        else:
            # Extract and Append hash from VBT data
            extracted_hash = vbt_data[byte_index:byte_index+HASH_SIZE]
            extracted_block_data_hash_list.append(extracted_hash.upper())
            byte_index += HASH_SIZE
        index += 1
    return extracted_block_data_hash_list


def compare_hashes(extracted_block_data_hash_list, calculated_block_data_hash_list, file_name):
    """
    Comparing extracted hash from Verification block table with calculated VBF data block hash
    Args:
        extracted_block_data_hash_list (list): list of extracted hashes
            from Verification Block Table data
        calculated_block_data_hash_list (list): list of hashes from respective VBF block data
        file_name (str): VBF filename
    Returns:
        bool: True
    """

    if len(extracted_block_data_hash_list) != len(calculated_block_data_hash_list):
        logging.error("Test failed: Extracted hashes list length and calculated hashes"\
                      " list length is not matched")
        return False

    result = []

    for extracted_block_data, calculated_block_data in zip(extracted_block_data_hash_list,
                                                           calculated_block_data_hash_list):
        if extracted_block_data == calculated_block_data:
            result.append(True)
        else:
            msg = "Test failed: VBT hash '{}' and Block Data hash '{}'" \
                " did not match in file {}".format(extracted_block_data,
                                                    calculated_block_data, file_name)
            logging.error(msg)
            result.append(False)

    if len(result) != 0:
        return all(result)
    logging.error(
        "Test Failed: All extracted_block_data and calculated_block_data hash did not match.")
    return False


def step_1(dut: Dut):
    """
    action: Extracting all data blocks and verification block table data from vbf file

    expected_result: Positive Response with list of dictionaries containing verification
                    block table data and list of vbf block data of all vbf files
    """
    rig_vbf_path = dut.conf.rig.vbf_path
    vbf_paths = glob(str(rig_vbf_path) + "/*.vbf")

    if len(vbf_paths) == 0:
        msg = "No vbf file found in path: {}".format(rig_vbf_path)
        logging.error(msg)
        return False, None

    # vbf_data_list will contain a list of dictionaries containing Verification Block Table data,
    # list of vbf data block and filename
    vbf_data_list = []
    for vbf_path in vbf_paths:
        vbf_data_list.append(extract_vbf_blocks(vbf_path))

    if len(vbf_data_list) != 0:
        return True, vbf_data_list
    logging.error("Test failed: Unable to extract Block data")
    return False, None


def step_2(dut: Dut, vbt_data_dict):
    """
    action: Calculating vbf block hash and extracting hashes from Verification Block Table data

    expected_result: Positive Response with list of dictionaries of calculated hashes
                    from vbf block data and extracted from Verification Block Table data
    """
    # pylint: disable=unused-argument
    vbf_hash_list = []
    vbf_hashes = {
        'vbt_data_hashes': None,
        'vbf_block_hashes': None,
        'file_name': ''
    }
    for element in vbt_data_dict:
        vbf_hashes['vbt_data_hashes'] = extract_vbt_hashes(element['vbt_data'])
        vbf_hashes['vbf_block_hashes'] = calculate_vbf_data_hashes(
            element['vbf_block_data_list'])
        vbf_hashes['file_name'] = element['file_name']
        vbf_hash_list.append(vbf_hashes.copy())

    if len(vbf_hash_list) != 0:
        return True, vbf_hash_list
    logging.error("Test failed: Unable to calculate hashes")
    return False, None


def step_3(dut: Dut, vbf_hash_list):
    """
    action: Comparing calculated vbf block data hash with
        extracted block hash from Verification Block Table

    expected_result: True
    """
    # pylint: disable=unused-argument
    result = []

    for element in vbf_hash_list:
        result.append(compare_hashes(
            element['vbt_data_hashes'], element['vbf_block_hashes'], element['file_name']))

    if len(result) != 0:
        return all(result)
    logging.error("Test failed: Unable to compare hashes")
    return False


def run():
    """
    Sanity check of all calculated data block hashes with all
    extracted hashes from Verification Block Table.
    """

    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False
    try:

        dut.precondition(timeout=60)

        result_step, vbt_data_dict = dut.step(
            step_1, purpose='Extracting all datablocks and VBT data from vbf file')

        if result_step:
            result_step, vbf_hash_list = dut.step(
                step_2, vbt_data_dict, purpose='Calculating vbf block hash and'\
                ' extracting hashes from VBT')

        if result_step:
            result_step = dut.step(
                step_3, vbf_hash_list, purpose='Comparing calculated vbf block hash with'\
                ' extracted block hash from VBT')

        result = result_step
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
