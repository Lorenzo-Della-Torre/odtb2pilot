"""
Reset and flash the ECU
"""
import logging
import time
import traceback

from supportfunctions.support_service31 import SupportService31
from supportfunctions.support_SBL import SupportSBL
from hilding.dut import Dut
from hilding.dut import DutTestError
from hilding.uds import EicDid


log = logging.getLogger('reset_ecu')

def reset_ecu_mode(dut):
    """ reset ecu mode """
    res = dut.uds.active_diag_session_f186()
    log.info(res)

    if not 'mode' in res.details:
        raise DutTestError("Active diagnostics session (F186) request failed")

    mode = res.details['mode']
    modes = {
        1: "default session/mode",
        2: "programming session/mode",
        3: "extended session/mode"
    }
    log.info("The ECU is in %s", modes[mode])

    if mode == 3:
        dut.uds.set_mode(1)
    if mode == 2:
        dut.uds.set_mode(1)
        # not sure why we do the next three steps, but this is how it was done
        # in the original "set ecu to default" script
        dut.uds.set_mode(3)
        dut.uds.set_mode(1)
        dut.uds.read_data_by_id_22(EicDid.complete_ecu_part_number_eda0)
    time.sleep(1)

def software_download(dut):
    """ software download """

    sbl = SupportSBL()

    ess_vbf_file = sbl.get_ess_filename()
    if ess_vbf_file:
        # Some ECU like HLCM don't have ESS vbf file
        # if no ESS file present: skip download
        log.info("ess file software download: %s", ess_vbf_file)
        vbf_version, vbf_header, vbf_data, vbf_offset = sbl.read_vbf_file(ess_vbf_file)

        #convert vbf header so values can be used directly
        sbl.vbf_header_convert(vbf_header)
        log.info("ESS VBF version: %s", vbf_version)

        # Erase Memory
        if not sbl.flash_erase(dut, vbf_header, 101):
            raise DutTestError("Failed transfer data block")

        # Iteration to Download the Software by blocks
        if not sbl.transfer_data_block(dut, vbf_header, vbf_data, vbf_offset):
            raise DutTestError("Failed transfer data block")

        if not SupportService31.check_memory(dut, vbf_header, 102):
            raise DutTestError("Failed check memory")

        log.info("ess vbf files downloaded: %s", ess_vbf_file)

    # download the rest of the vbf files
    vbf_files = sbl.get_df_filenames()
    if not vbf_files:
        raise DutTestError("Could not find the rest of the vbf files")

    log.info("commencing vbf files software download: %s", vbf_files)
    for vbf_file in vbf_files:
        res = dut.uds.read_data_by_id_22(EicDid.complete_ecu_part_number_eda0)
        log.info(res)
        if not 'name' in res.details:
            raise DutTestError(f"Failed before downloading vbf file: {vbf_file}")
        if not sbl.sw_part_download(dut, vbf_file, 103, purpose="sw part download"):
            raise DutTestError(f"Could not download vbf file: {vbf_file}")

    if not sbl.check_complete_compatible_routine(dut, 104):
        raise DutTestError("Failed check complete and compatible")


def reset_and_flash_ecu():
    """ reset ecu """
    dut = Dut()
    start_time = dut.start()
    result = False
    try:
        dut.precondition(timeout=3600)
        dut.step(reset_ecu_mode)
        dut.uds.ecu_reset_1101(delay=5)
        dut.uds.enter_sbl()
        dut.step(software_download)
        dut.uds.ecu_reset_1101(delay=5)
        dut.uds.set_mode(1)
        result = True
    except: # pylint: disable=bare-except
        error = traceback.format_exc()
        log.error("Resetting the ECU failed: %s", error)
    finally:
        dut.postcondition(start_time, result)
