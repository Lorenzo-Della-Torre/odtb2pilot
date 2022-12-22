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
from supportfunctions.support_can import SupportCAN, CanParam, CanTestExtra, CanPayload
from supportfunctions.support_test_odtb2 import SupportTestODTB2

SSBL = SupportSBL()
SE22 = SupportService22()
SE34 = SupportService34()
SE36 = SupportService36()
SE37 = SupportService37()
SC = SupportCAN()
SUTE = SupportTestODTB2()


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


def partial_flash_blocks(can_p: CanParam, vbf_block_data, vbf_block, nbl,
                         stepno=360, purpose="flash block"):
    # pylint: disable= too-many-arguments
    """
    Function for Transfer Data
    Args:
    Returns:
        (bool): True when successfully flashed block
    """
    result = True
    pad = 0
    logging.info("------Start Downloading blocks------")
    block_value = int((vbf_block['Length']-1)/(nbl-2))+1
    for i in range(block_value-1):

        logging.info("360: Flash blocks: Block %s of %s",
                      1+i, 1+int(vbf_block['Length']/(nbl-2)))
        pad = (nbl-2)*i
        i += 1
        ibyte = bytes([i % 256])

        cpay: CanPayload = {"payload" : b'\x36' + ibyte + vbf_block_data[pad:pad + nbl-2],
                            "extra" : ''}
        etp: CanTestExtra = {"step_no": stepno,
                             "purpose" : purpose,
                             "timeout" : 0.2,
                             "min_no_messages" : -1,
                             "max_no_messages" : -1}
        result = SUTE.teststep(can_p, cpay, etp)
        result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], '76')
    return result


def transfer_data(dut, vbf_header, vbf_block, vbf_block_data, partial_flash_flag):
    """
    Initiate Software Download(SWDL) for a particular VBF block
    Args:
        dut (Dut): An instance of Dut
        vbf_header (dict): VBF file header
        vbf_block (dict): Dictionary containing StartAddress, Length & Checksum
        vbf_block_data (str): VBF block data byte string
        partial_flash_flag (bool): Flag, True when block is flashed partially
    Returns:
        (bool): True if block download is successful
    """
    result, nbl = SE34.request_block_download(dut, vbf_header, vbf_block)
    if not result:
        logging.error("Test Failed: RequestDownload(0x34) request failed")
        return False

    if partial_flash_flag:
        result = partial_flash_blocks(dut, vbf_block_data, vbf_block, nbl)
        if not result:
            logging.error("Test Failed: TransferData(0x36) request failed")
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
        logging.error("Test Failed: ESS download failed")
        return False

    logging.info("Successfully downloaded ESS")
    return True


def step_3(dut: Dut):
    """
    action: Partially download first block for VBF file of EXE software part type
    expected_result: Successfully verified that flashing starts before all blocks are transferred
    """
    result, vbf_header, vbf_blocks_details = read_vbf(dut, vbf_type='EXE')
    if not result:
        logging.error("Test Failed: Unable to extract VBF file parameters")
        return False, None, None

    # Flash erase
    result_flash_erase = SSBL.flash_erase(dut, vbf_header, stepno=3)
    if not result_flash_erase:
        logging.error("Test Failed: Unable to complete Flash Erase")
        return False, None, None

    # Request partial download of first block of EXE
    result = transfer_data(dut, vbf_header, vbf_blocks_details[0]["vbf_block"],
             vbf_blocks_details[0]["vbf_block_data"], partial_flash_flag=True)

    if result:
        logging.info("Partial software download for first block of EXE VBF completed")
        return True, vbf_header, vbf_blocks_details[1]

    logging.error("Partial software download for first block of EXE VBF failed")
    return False, None, None


def step_4(dut: Dut, vbf_header, vbf_blocks_details):
    """
    action: Download second block for VBF file of EXE software part type
    expected_result: Second block of EXE software part should be downloaded
    """
    result = transfer_data(dut, vbf_header, vbf_blocks_details["vbf_block"],
                            vbf_blocks_details["vbf_block_data"], partial_flash_flag=False)
    if result:
        logging.info("Software download for EXE VBF completed")
        return True

    logging.error("Software download for EXE VBF failed")
    return False


def step_5(dut: Dut):
    """
    action: Download EXE and DATA
    expected_result: Should successfully download EXE and DATA
    """
    # Download the EXE and DATA file to the ECU
    ess_result = swdl.download_application_and_data(dut)
    if not ess_result:
        logging.error("Test Failed: EXE and DATA download failed")
        return False

    logging.info("Successfully downloaded EXE and DATA")
    return True


def step_6(dut: Dut):
    """
    action: Check complete and compatible
    expected_result: Downloaded software should be complete And compatible
    """
    # Check Complete And Compatible
    check_result = swdl.check_complete_and_compatible(dut)

    if check_result is False:
        logging.error("Aborting software download due to problems when checking C & C")
        return False

    logging.info("Check Complete And Compatible done, Result: %s", check_result)
    return True


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
        dut.precondition(timeout=5000)

        result_step = dut.step(step_1, purpose="SBL activation")
        if result_step:
            result_step = dut.step(step_2, purpose="Download ESS")
        if result_step:
            result_step, vbf_header, vbf_blocks_details = dut.step(step_3, purpose="Partially"
                                                                   " download first block for VBF"
                                                                   " file of EXE software part"
                                                                   " type")
        if result_step:
            result_step = dut.step(step_4, vbf_header, vbf_blocks_details, purpose="Download"
                                   " second block for VBF file of EXE software part type")
        if result_step:
            result_step = dut.step(step_5, purpose="Download EXE and DATA")
        if result_step:
            result_step = dut.step(step_6, purpose="Check complete and compatible")
        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
        logging.error("DutTestError occured")
    finally:
        logging.info("entering postcondition")
        logging.info("ecu issue: wait 4sec for ecu to do fallback/recover")
        time.sleep(5)
        logging.info("Request current session (22 F186")
        SE22.read_did_f186(dut)
        time.sleep(1)
        current_ecu_mode = SE22.get_ecu_mode(dut)
        time.sleep(4) #make sure 5sec SecAcc seed delay is over
        ecu_restore_result = True
        if current_ecu_mode == 'SBL' :
        # end current dl request
            SE37.transfer_data_exit(dut)
        else:
        # ecu did fallback/reset
        # do full SWDL
            logging.info("Reactivate SBL again")
            #ecu_restore_result = dut.step(step_1, purpose="Redo SBL activation")
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
            #ecu_restore_result = dut.step(step_6, purpose="Check complete and compatible")\
            #                     and ecu_restore_result
            ecu_restore_result = swdl.check_complete_and_compatible(dut)\
                                 and ecu_restore_result
        logging.info("ECU restore:")
        logging.info("ecu_restore_result %s", ecu_restore_result)
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
