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
title: Verification Block Table Format Identifier - Definition 
purpose: >
    Define the applicable value of the Verification Block Table Format Identifier

description: >
    The Verification Block Table Format Identifier shall be according to Table - Verification Block
    Format Identifier
    Example.
    The signing method used is, as defined in REQPROD 410732, e.g. SHA256_RSA2048. This means that
    Verification Block Table Format Identifier shall be 0x0000


details: >
    Verify all downloaded software is completed in a sequence.
        1. Software Download(SWDL) for SBL VBF file
        2. Software Download(SWDL) fail for modified ESS VBF file.
"""

import logging
from glob import glob
from hilding.conf import Conf
from hilding.dut import Dut
from hilding.dut import DutTestError
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_service34 import SupportService34
from supportfunctions.support_service36 import SupportService36
from supportfunctions.support_service37 import SupportService37
from supportfunctions.support_service31 import SupportService31
from supportfunctions.support_lzma import LzmaEncoder

LZMA = LzmaEncoder()
CNF = Conf()
SSBL = SupportSBL()
SE27 = SupportService27()
SE31 = SupportService31()
SE34 = SupportService34()
SE36 = SupportService36()
SE37 = SupportService37()


def read_vbf_file(dut, vbf_type):
    """
    Read vbf file and extract vbf header, vbf block and vbf block data
    Args:
        dut (class obj): dut instance
        vbf_type (str): SBL or ESS
    Returns:
    (bool): True when successfully extracted vbf parameters
        vbf_header (dict): vbf header dictionary
        vbf_blocks_details (dict): VBF blocks details (vbf_block, vbf_block_data)
    """
    rig_vbf_path = dut.conf.rig.vbf_path
    vbf_file_paths = glob(str(rig_vbf_path) + "/*.vbf")

    if len(vbf_file_paths) > 0:
        for vbf_file_path in vbf_file_paths:
            _, vbf_header, vbf_data, vbf_offset = SSBL.read_vbf_file(vbf_file_path)
            vbf_header = dict(vbf_header)

            if vbf_header['sw_part_type'] == vbf_type:
                SSBL.vbf_header_convert(vbf_header)
                vbf_blocks_details = extract_vbf_blocks(vbf_data, vbf_offset)

                return True, vbf_header, vbf_blocks_details

    logging.error("No %s VBF found in %s", vbf_type, rig_vbf_path)
    return False, None, None


def extract_vbf_blocks(vbf_data, vbf_offset):
    """
    Extract all the Verification Block File(VBF) blocks & block data
    Args:
        vbf_data (str): Complete vbf data
        vbf_offset (int): vbf offset
    Returns:
        vbf_block_details (list): VBF blocks details (vbf_block, vbf_block_data)
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

    logging.info("Number of VBF blocks extracted from the VBF file: %s", len(vbf_blocks_details))
    return vbf_blocks_details


def transfer_data(dut, vbf_header, vbf_block, vbf_block_data):
    """
    Initiate Software Download(SWDL) for a particular VBF block
    Args:
        dut (class object): Dut instance
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
        vbf_block_details
        vbf_header (dict): VBF file header
        vbf_block (dict): dictionary containing StartAddress, Length & Checksum
        vbf_block_data (str): VBF block data byte string
    Returns:
        vbf_block_details(dict): Manipulated Verification Bloch table i.e last vbf_block_data
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


def block_wise_software_download(dut, vbf_header, vbf_blocks_details, vbf_type):
    """
    Blockwise software download(SWDL)
    Args:
        dut (class object): Dut instance
        vbf_header (dict): VBF file header
        vbf_blocks_details (list): VBF blocks details (vbf_block, vbf_block_data)
        vbf_type (str): SBL or ESS
    Returns:
        (bool): True on successful software download
    """
    # Software Download(SWDL) on all blocks of respective VBF file
    results = []
    for block_id, block_details in enumerate(vbf_blocks_details):
        logging.info("SWDL on %s of %s VBF", block_id+1, vbf_type)
        result = transfer_data(dut, vbf_header, block_details["vbf_block"],
                                block_details["vbf_block_data"])

        results.append(result)
        if not result:
            logging.error("Block %s failed", block_id+1)
            break

    if len(results) != 0 and all(results):
        logging.info("Software Download for %s VBF Completed", vbf_type)
        return True

    logging.error("Software Download for %s VBF failed", vbf_type)
    return False


def step_1(dut: Dut):
    """
    action: Enter into Programming Session and security access with valid key.

    expected_result: ECU is in programming session and security access is successful.
    """
    dut.uds.set_mode(2)
    result = SE27.activate_security_access_fixedkey(dut, sa_keys=CNF.default_rig_config,
                                                    step_no=272, purpose="SecurityAccess")
    if result:
        logging.info("Security access Successful")
        return True

    logging.error("Test Failed: Security access denied")
    return False


def step_2(dut: Dut):
    """
    action: Verify Software Download(SWDL) for VBF file of SBL software part type.

    expected_result: Software Download(SWDL) Succesful for SBL VBF file
    """
    result, vbf_header, vbf_blocks_details = read_vbf_file(dut, 'SBL')


    if not result:
        logging.error("Test failed: Unable to extract VBF file parameters")
        return False

    result = block_wise_software_download(dut, vbf_header, vbf_blocks_details, 'SBL')

    result_check_mem = SE31.check_memory(dut, vbf_header, stepno=2)

    if not result_check_mem:
        logging.error("Test Failed: CheckMemory failed ")

    if result:
        logging.info("Download Download Successful for SBL VBF file")
        return True

    logging.error("Test failed: Software Download(SWDL) failed for SBL VBF file")
    return False


def step_3(dut: Dut):
    """
    action: Verify Software Download(SWDL) for VBF file of ESS software part type
            with Manipulated Verification Block Table.

    expected_result: Software Download should fail for ESS VBF file as manipulating VBT
    """
    result, vbf_header, vbf_blocks_details = read_vbf_file(dut, 'ESS')

    if not result:
        logging.error("Test failed: Unable to extract VBF file parameters")
        return False

    #Manipulating the VBT
    vbf_blocks_details = manipulated_vbt(vbf_blocks_details)

    result = block_wise_software_download(dut, vbf_header, vbf_blocks_details, 'ESS')

    result_check_mem = SE31.check_memory(dut, vbf_header, stepno=2)

    if not result_check_mem:
        logging.error("Test Failed: CheckMemory failed ")

    if not result:
        logging.info('Software Download(SWDL) failed for ESS VBF file with manipulated VBT')
        return True

    logging.error("Test failed: Software Download(SWDL) Successful for ESS VBF file")
    return False



def run():
    """
    Verify all downloaded software is completed in a sequence(SBL, ESS) and download is not
    completed for ESS vbf file with Manipulated VBT data
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=150)

        result_step = dut.step(step_1, purpose="Enter into programming session and security"
                                                " access to ECU.")

        if result_step:
            result_step = dut.step(step_2, purpose="Verify Software Download(SWDL) request"
                                                    " for VBF of SBL software part type.")

        if result_step:
            result_step = dut.step(step_3, purpose="Verify Software Download(SWDL) request"
                                                     " for VBF of ESS software part type"
                                                     " with Manipulated VBT")

        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
