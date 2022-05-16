"""
/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 398360
version: 4
title: Format of the Verification Block Table
purpose: >
    Define the format of the verification block table

description: >
    The verification block table, encoded with big endian, shall have the following format:
    Verification Block Table Format Identifier. The verification block will start with most
    significant byte of this format identifier. It defines the version of the verification
    block table, mainly intended for tool parsing and format checks in the ECU, i.e. it shall not
    be used to configure e.g. the actual algorithm to be used by the bootloader. Size 16 bits.
    Number of data blocks. This shall be identical to the number of data blocks included in the
    software part. The data block containing the verification block table itself shall not be
    included. Size 16 bits.
    StartAddress [size 32 bits], Length [size 32 bits], Hash value. Every data blocks shall be
    defined, except the block table itself. The size of the hash is dependent of the hash function
    used and is specified elsewhere. The Length is the unprocessed length (see other requirements
    for more details).
    The data blocks shall be sorted according to the order the data blocks are being programmed to
    the ECU.
    Example.
    SHA-256 hash function is used, i.e. each hash value is 256 bits.
    Number of data blocks are two, i.e. the total length of the verification block table, in octets,
    will be (16+16+2x(256+32+32))/8=84 octets.
    The data shown belongs to the verification block. The Verification block starts at address
    0x0007FF00, i.e. it is the third data block in the figure:
    0000
    0002
    00060000 00000013 D78ECD62C62CF1F575D7DEC6D2FD57DA066554FD42EEE5C867E70083BC942262
    00060100 0001EF00 E6027B3F959FAF231B382FFDC64EB23825E6B7CCEA47F5196D02CA2AFDF44188
    The format identifier is 0x0000
    Number of data blocks are two (0x0002)
    Data block 1: Start address 0x00060000 and length 0x00000013. Hash 0xD78ECD...
    Data block 2: Start address 0x00060100 and length 0x0001EF00. Hash 0xE6027B...

details: >
    Verify Software Download(SWDL) with Manipulated format identifier present in Verification Block
    Table of ESS VBF fails.
"""

import logging
from os import listdir
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_service34 import SupportService34
from supportfunctions.support_service36 import SupportService36
from supportfunctions.support_service37 import SupportService37
from supportfunctions.support_lzma import LzmaEncoder

SSBL = SupportSBL()
LZMA = LzmaEncoder()
SE34 = SupportService34()
SE36 = SupportService36()
SE37 = SupportService37()


def load_vbf_files(dut):
    """
    Loads the rig specific VBF files found in rigs/<default-rig-name>/VBFs

    Args:
        dut (Dut): An instance of Dut

    Returns:
        boolean: True if vbfs were loaded successfully, otherwise False
    """
    logging.info("~~~~~~~~ Loading VBFs started ~~~~~~~~")
    vbfs = listdir(dut.conf.rig.vbf_path)
    paths_to_vbfs = [str(dut.conf.rig.vbf_path) + "/" + x for x in vbfs]

    if not paths_to_vbfs:
        logging.error("VBFs file not found, expected in %s ... aborting", paths_to_vbfs)
        return False

    result = SSBL.read_vbf_param(paths_to_vbfs)
    return result


def transfer_data(dut, vbf_header, vbf_block, vbf_block_data):
    """
    Initiate Software Download(SWDL) for a particular VBF block
    Args:
        dut (Dut): An instance of Dut
        vbf_header (dict): VBF file header
        vbf_block (dict): dictionary containing StartAddress, Length & Checksum
        vbf_block_data (str): VBF block data byte string
    Returns:
        bool: True if SWDL is successful
    """
    result, nbl = SE34.request_block_download(dut, vbf_header, vbf_block)
    if not result:
        logging.error("Test failed: RequestDownload(0x34) request failed")
        return False
    result_36 = SE36.flash_blocks(dut, vbf_block_data, vbf_block, nbl)
    if not result_36:
        logging.error("Test failed: TransferData(0x36) request failed")

    result_37 = SE37.transfer_data_exit(dut)
    if not result_37:
        logging.error("Test failed: TransferExit(0x37) request failed")
    return result_36 and result_37


def manipulated_vbt(vbf_block_details):
    """
    manipulated the first 2 bytes of Verification block table
    Args:
        vbf_block_details (list): containing vbf_block_data, vbf_block
    Returns:
        vbf_block_details(list): Manipulated Verification Block table i.e last vbf_block_data
    """
    # getting VBT
    vbt = vbf_block_details[-1]['vbf_block_data']

    # retrive decompressed data
    vbt = LZMA.decode_barray(vbt)

    # convert decompressed VBT data to list of hex
    vbt_hex = list(vbt.hex())

    # Manipulating the first 2 bytes of vbt data(Format Identifier)
    vbt_hex[0:4] = "1111"
    vbt_hex = "".join(vbt_hex)
    vbf_block_details[-1]['vbf_block_data'] = bytearray(vbt_hex, 'utf-8')

    return vbf_block_details


def software_download_ess(dut, vbf_header, vbf_blocks_details):
    """
    Blockwise software download(SWDL) for ESS Vbf file
    Args:
        dut (class object): Dut instance
        vbf_header (dict): VBF file header
        vbf_blocks_details (list): VBF blocks details (vbf_block, vbf_block_data)
    Returns:
        (bool): True on successful software download
    """
    # Software Download(SWDL) on blocks of ess VBF file
    results = []
    for block_id, block_details in enumerate(vbf_blocks_details):
        logging.info("SWDL on %s of ESS VBF", block_id+1)
        result = transfer_data(dut, vbf_header, block_details["vbf_block"],
                                block_details["vbf_block_data"])

        results.append(result)
        if not result:
            logging.error("Block %s failed", block_id+1)
            break

    if len(results) != 0 and all(results):
        logging.info("Software Download for ESS VBF Completed")
        return True

    logging.error("Software Download for ESS VBF failed")
    return False


def extract_vbf_details(vbf_data, vbf_offset):
    """
    Extracting vbf parameters from Ess VBF file
    Args:
        vbf_data (bytes): vbf data
        vbf_offset (int): vbf offset
    Returns:
        vbf_blocks_details (list): list of vbf_block and vbf_block_data
    """
    vbf_blocks_details = []
    # Extract first vbf block
    vbf_offset, vbf_block, vbf_block_data = SSBL.block_data_extract(vbf_data, vbf_offset)
    vbf_blocks_details.append({'vbf_block': vbf_block, 'vbf_block_data': vbf_block_data})

    # Extract remaining vbf blocks
    while vbf_block['StartAddress'] != 0:
        vbf_offset, vbf_block, vbf_block_data = SSBL.block_data_extract(vbf_data, vbf_offset)
        # Break if no more blocks found
        if vbf_block['StartAddress'] != 0:
            # Preparing vbf_blocks_details list
            vbf_blocks_details.append({'vbf_block': vbf_block, 'vbf_block_data': vbf_block_data})
    return vbf_blocks_details


def software_download_manipulated_ess_vbt(dut, stepno):
    """
    Software download(SWDL) for SBL and manipulated ESS VBFs file type
    Args:
        dut (Dut): An instance of Dut
        stepno   : step no
    Returns:
        (bool): True when SWDL fails with manipulated ESS
    """
    # Activate sbl
    sbl_result = SSBL.sbl_activation(dut, sa_keys=dut.conf.default_rig_config)

    logging.info("Software download (downloading and activating sbl) completed."
                 " Result: %s", sbl_result)

    if sbl_result is False:
        logging.error("Aborting software download due to problems when activating SBL")
        return False

    # Download empty ESS
    _, vbf_header, vbf_data, vbf_offset = SSBL.read_vbf_file(SSBL.get_ess_filename())

    #convert vbf header so values can be used directly
    SSBL.vbf_header_convert(vbf_header)

    # Erase Memory
    result = SSBL.flash_erase(dut, vbf_header, stepno)
    logging.info("flash erase successful")

    if result is False:
        logging.error("flash erase failed")
        return False

    # Manipulating the VBT
    vbf_blocks_details = manipulated_vbt(extract_vbf_details(vbf_data, vbf_offset))
    swdl_result = software_download_ess(dut, vbf_header, vbf_blocks_details)

    if not swdl_result:
        logging.info("Expected SWDL to fail for ESS VBF file with manipulated VBT")
        return True

    logging.error("Test failed: Unexpected result for ESS VBF file")
    return False


def step_1(dut: Dut):
    """
    action: Verify Software Download(SWDL) for VBF file of ESS software part type
            with Manipulated format identifier of Verification Block Table.

    expected_result: Software Download is failed for manipulated VBT of ESS VBF file
    """
    # Set Programming session
    dut.uds.set_mode(2)

    # Load vbfs file
    vbf_result = load_vbf_files(dut)
    logging.info("Software download (loading vbfs) completed. Result: %s", vbf_result)

    if vbf_result is False:
        logging.error("Aborting software download due to problems when loading VBFs")
        return False

    # Software Download with SBL and manipulated ESS VBT
    result = software_download_manipulated_ess_vbt(dut,stepno=1)
    if not result:
        logging.error("Test Failed :Expected result of ESS software download with manipulated VBT")
        return False
    logging.info("Expected result of ESS software download fails with manipulated format"
                 " identifier VBT")
    return True


def run():
    """
    Verify Software Download(SWDL) with Manipulated format identifier present in Verification
    Block Table of ESS VBF fails.
    """
    dut = Dut()

    start_time = dut.start()
    result = False

    try:
        dut.precondition(timeout=600)

        result = dut.step(step_1, purpose="Verify Software Download(SWDL) request for"
                                       " VBF of ESS software part type with Manipulated VBT")

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
