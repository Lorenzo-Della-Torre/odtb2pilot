"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 404696
version: 3
title: Verification Block Table Format Identifier-Definition
purpose: >
    Define the applicable value of the Verification Block Table Format Identifier

description: >
    The Verification Block Table Format Identifier shall be according to Table - Verification Block
    Format Identifier
    Example.
    The signing method used is, as defined in REQPROD 410732, e.g. SHA256_RSA2048. This means that
    Verification Block Table Format Identifier shall be 0x0000


details: >
    Verify Software Download (SWDL) fail for modified ESS VBF file
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
    Manipulating the first 2 bytes of Verification block table
    Args:
        vbf_block_details (list) containing vbf_block_data, vbf_block
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


def block_wise_software_download_ess(dut, vbf_header, vbf_blocks_details):
    """
    Blockwise software download(SWDL) for ESS Vbf file
    Args:
        dut (class object): Dut instance
        vbf_header (dict): VBF file header
        vbf_blocks_details (list): VBF blocks details (vbf_block, vbf_block_data)
    Returns:
        (bool): True on successful software download
    """
    # Software Download(SWDL) for blocks of ess VBF file
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

def extract_vbf_details_vbt(vbf_data, vbf_offset):
    """
    Extracting vbf parameters from ESS VBFs file
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

def software_download_manipulated_ess_vbt(dut):
    """
    Software download(SWDL) for SBL and manipulated ESS VBFs file type
    Args:
        dut (Dut): An instance of Dut
    Returns:
        (bool): True on successful software download
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
    result = SSBL.flash_erase(dut, vbf_header, stepno=1)

    # Manipulating the VBT
    vbf_blocks_details = manipulated_vbt(extract_vbf_details_vbt(vbf_data, vbf_offset))
    swdl_result = result and block_wise_software_download_ess(dut, vbf_header, vbf_blocks_details)

    if not swdl_result:
        logging.info("Expected result for SWDL ESS VBF file  fails with manipulated VBT")
        return True

    logging.error("Test failed: Unexpected result for ESS VBF file")
    return False


def step_1(dut: Dut):
    """
    action: Verify Software Download(SWDL) for VBF file of ESS software part type
            with Manipulated format identifier of Verification Block Table.

    expected_result: Software Download is failed for manipulated VBT of ESS VBF file
    """
    # Set default session
    dut.uds.set_mode(1)

    # Load vbfs file
    vbf_result = load_vbf_files(dut)
    logging.info("Software download (loading vbfs) completed. Result: %s", vbf_result)

    if vbf_result is False:
        logging.error("Aborting software download due to problems when loading VBFs")
        return False

    # Software Download with SBL and manipulated ESS VBT
    result = software_download_manipulated_ess_vbt(dut)
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
