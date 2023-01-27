"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 53978
version: 1
title: Writing of received data
purpose: >
    To decrease the total_transfer_time programming time the ECU shall start writing data to the
    non-volatile memory before the complete message is received.

description: >
    The ECU shall start writing data to the non-volatile memory before the complete message is
    received, decompression included if supported. The positive response shall be sent after all
    data included in the TransferData request is written to the non-volatile memory.
    As non-volatile memories normally only allow one write operation for each erase operation
    the ECU must know how many data bytes it has written to the non-volatile memory. If the client
    transfers the same block again the ECU shall count the number of received data bytes and start
    to write data at the first unwritten non-volatile memory position.

details: >
    Verify flashing starts before all blocks are transferred by verifying transfer of an already
    started block is quicker than transferring a block with no part of it being flashed already.
"""

import time
import logging
from glob import glob
from hilding.dut import Dut
from hilding.dut import DutTestError
import hilding.flash as swdl
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service34 import SupportService34
from supportfunctions.support_service36 import SupportService36
from supportfunctions.support_service37 import SupportService37

SSBL = SupportSBL()
SE22 = SupportService22()
SE34 = SupportService34()
SE36 = SupportService36()
SE37 = SupportService37()


def read_vbf(dut, vbf_type):
    """
    Read vbf file and extract vbf header, vbf block and vbf block data
    Args:
        dut (Dut): An instance of Dut
        vbf_type (str): ESS
    Returns:
        (bool): True when extracted VBF parameters successfully
        vbf_header (dict): Vbf header dictionary
        vbf_blocks_details (dict): List of dictionaries containing block wise details
                                   (vbf_block, vbf_block_data)
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
    Extract all the VBF blocks and block data
    Args:
        vbf_data (str): Complete vbf data
        vbf_offset (int): Vbf offset
    Returns:
        vbf_block_details (list): List of dictionaries containing block wise details
                                  (vbf_block, vbf_block_data)
    """
    vbf_blocks_details = []

    for _ in range(20):
        vbf_offset, vbf_block, vbf_block_data = SSBL.block_data_extract(vbf_data, vbf_offset)
        # Break if no more blocks found
        if vbf_block['StartAddress'] == 0:
            break

        # Preparing vbf_blocks_details list
        vbf_blocks_details.append({'vbf_block': vbf_block, 'vbf_block_data': vbf_block_data})

    logging.info("Number of VBF blocks extracted from the VBF file: %s", len(vbf_blocks_details))
    return vbf_blocks_details


def transfer_data(dut, vbf_header, vbf_block, vbf_block_data):
    """
    Initiate Software Download(SWDL) for a particular VBF block
    Args:
        dut (Dut): An instance of Dut
        vbf_header (dict): VBF file header
        vbf_block (dict): Dictionary containing StartAddress, Length & Checksum
        vbf_block_data (str): VBF block data byte string
    Returns:
        (bool): True if block download is successful
    """
    result, nbl = SE34.request_block_download(dut, vbf_header, vbf_block)
    if not result:
        logging.error("Test Failed: RequestDownload(0x34) request failed")
        return False

    result = SE36.flash_blocks(dut, vbf_block_data, vbf_block, nbl)
    if not result:
        logging.error("Test Failed: TransferData(0x36) request failed")
        return False

    result = SE37.transfer_data_exit(dut)
    if not result:
        logging.error("Test Failed: TransferExit(0x37) request failed")
        return False

    return True


def exe_block_software_download(dut, vbf_header, vbf_blocks_details):
    """
    Block wise software download(SWDL)
    Args:
        dut (Dut): An instance of Dut
        vbf_header (dict): VBF file header
        vbf_blocks_details (list): List of dictionaries containing block wise details
                                   (vbf_block, vbf_block_data)
    Returns:
        (bool): True on successful software download
    """
    start_time = time.time()
    result = transfer_data(dut, vbf_header, vbf_blocks_details["vbf_block"],
                            vbf_blocks_details["vbf_block_data"])
    end_time = time.time()

    elapsed_time = end_time-start_time

    if result:
        logging.info("Software download for first block of EXE VBF completed")
        return True, elapsed_time

    logging.error("Software download for first block of EXE VBF failed")
    return False, elapsed_time


def step_1(dut: Dut):
    """
    action: SBL activation
    expected_result: SBL activation should be successful
    """
    SSBL.get_vbf_files()
    result = SSBL.sbl_activation(dut, sa_keys=dut.conf.default_rig_config)
    if not result:
        logging.error("Test Failed: SBL activation failed")
        return False

    logging.info("Successfully activated SBL")
    return True


def step_2(dut: Dut):
    """
    action: Download ESS
    expected_result: Should successfully download ESS
    """
    # Download the ESS file to the ECU
    ess_result = swdl.download_ess(dut)
    if not ess_result:
        logging.error("Test Failed: ESS Download failed")
        return False

    logging.info("Successfully downloaded ESS")
    return True


def step_3(dut: Dut):
    """
    action: Download first block for VBF file of EXE software part type
    expected_result: Transfer time of first time block download should be greater than transfer
                     time of second time block download because transfer of an already started
                     block is quicker than transferring a block with no part of it being flashed
                     already
    """
    result, vbf_header, vbf_blocks_details = read_vbf(dut, vbf_type='EXE')
    if not result:
        logging.error("Test Failed: Unable to extract VBF file parameters")
        return False, None, None

    # Flash erase
    result_flash_erase = SSBL.flash_erase(dut, vbf_header, stepno=3)
    if not result_flash_erase:
        logging.error("Test Failed: Unable to complete flash erase")
        return False, None

    # Request download first block of EXE
    result, first_block_transfer_time = exe_block_software_download(dut, vbf_header,
                                        vbf_blocks_details[0])
    if not result:
        return False, None, None

    # Repeat request download first block of EXE
    result, repeat_first_block_transfer_time = exe_block_software_download(dut, vbf_header,
                                               vbf_blocks_details[0])
    # if not result:
    #     return False, None, None

    logging.info("Repeat block transfer time: %s sec", repeat_first_block_transfer_time)
    logging.info("First block transfer time: %s sec", first_block_transfer_time)

    if repeat_first_block_transfer_time <= first_block_transfer_time:
        logging.info("Successfully verified that flashing starts before all blocks are"
                     " transferred")
        return True, vbf_header, vbf_blocks_details[1]

    logging.error("Test Failed: Failed to verify that flashing starts before all blocks are"
                  " transferred")
    return False, None, None


def step_4(dut: Dut, vbf_header, vbf_blocks_details):
    """
    action: Download second block for VBF file of EXE software part type
    expected_result: Second block of EXE software part should be downloaded
    """
    result = transfer_data(dut, vbf_header, vbf_blocks_details["vbf_block"],
                            vbf_blocks_details["vbf_block_data"])
    if result:
        logging.info("Software download for EXE VBF completed")
        return True

    logging.error("Software download for EXE VBF failed")
    return False


def step_5(dut: Dut):
    """
    action: Download DATA
    expected_result: Should successfully download DATA
    """
    result, vbf_header, vbf_blocks_details = read_vbf(dut, vbf_type='DATA')
    if not result:
        logging.error("Test Failed: Unable to extract VBF file parameters")
        return False

    results = []

    # Flash erase
    result_flash_erase = SSBL.flash_erase(dut, vbf_header, stepno=5)
    if not result_flash_erase:
        logging.error("Test Failed: Unable to complete Flash Erase")
        return False, None

    for block_id, block_details in enumerate(vbf_blocks_details):
        logging.info("SWDL on %s of DATA VBF", block_id+1)
        # Block wise download of DATA VBF file
        if block_id == 1:
            result = transfer_data(dut, vbf_header, block_details["vbf_block"],
                                    block_details["vbf_block_data"])
            results.append(result)

    if len(results) != 0 and all(results):
        logging.info("Software download for DATA VBF completed")
        return True

    logging.error("Software download for DATA VBF failed")
    return False


def run():
    """
    Verify flashing starts before all blocks are transferred by verifying transfer of an already
    started block is quicker than transferring a block with no part of it being flashed already.
    """
    dut = Dut()

    start_time = dut.start()
    result = False
    result_step = False

    try:
        dut.precondition(timeout=3000)

        result_step = dut.step(step_1, purpose="SBL activation")
        if result_step:
            result_step = dut.step(step_2, purpose="Download ESS")
        if result_step:
            result_step, vbf_header, vbf_blocks_details = dut.step(step_3, purpose="Download"
                                                                   " first block for VBF file"
                                                                   " of EXE software part type")
        if result_step:
            result_step = dut.step(step_4, vbf_header, vbf_blocks_details, purpose="Download"
                                   " second block for VBF file of EXE software part type")
        if result_step:
            result_step = dut.step(step_5, purpose="Download DATA")
        result = result_step

    except DutTestError as error:
        logging.error("Test Failed: %s", error)
        logging.error("DutTestError occured")
    finally:
        logging.info("Entering postcondition")
        logging.info("ecu issue: wait 4sec for ecu to do fallback/recover")
        time.sleep(5)
        logging.info("Request current session (22 F186")
        SE22.read_did_f186(dut)
        time.sleep(1)
        current_ecu_mode = SE22.get_ecu_mode(dut)
        time.sleep(4) # Make sure 5sec SecAcc seed delay is over
        ecu_restore_result = True
        if current_ecu_mode == 'SBL' :
        # end current dl request
            SE37.transfer_data_exit(dut)
        else:
        # ecu did fallback/reset
        # Do full SWDL
            logging.info("Reactivate SBL again")
            # ecu_restore_result = dut.step(step_1, purpose="Redo SBL activation")
            SSBL.get_vbf_files()
            ecu_restore_result = SSBL.sbl_activation(dut,
                                                     sa_keys=dut.conf.default_rig_config,
                                                     purpose="Redo SBL activation")
            logging.info("Download ESS again")
            ecu_restore_result = SSBL.sw_part_download(dut,
                                                       SSBL.get_ess_filename(),
                                                       purpose="Redo Download ESS")\
                                 and ecu_restore_result

                                       #swdl.download_ess(dut) and ecu_restore_result
            #dut.step(step_2, purpose="Redo Download ESS")
        # ecu still in SBL, no SecAcc needed, redo files missing
        for i in SSBL.get_df_filenames():
            logging.info("File to flash: %s", i)
            ecu_restore_result = SSBL.sw_part_download(dut, i, stepno=999,
                                 purpose="flash_exe_data")\
                                 and ecu_restore_result
            ecu_restore_result = swdl.check_complete_and_compatible(dut)\
                                 and ecu_restore_result
        logging.info("ECU restore:")
        logging.info("ecu_restore_result %s", ecu_restore_result)
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
