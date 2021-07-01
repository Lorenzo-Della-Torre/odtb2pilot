"""
ECU software download
"""
import logging
import traceback

from supportfunctions.support_service31 import SupportService31
from supportfunctions.support_SBL import SupportSBL
from hilding.dut import Dut
from hilding.dut import DutTestError
from hilding.uds import EicDid


log = logging.getLogger('sw_download')

def software_download(dut):
    """ software download """

    sbl = SupportSBL()

    vbf_files = [str(f.resolve()) for f in dut.conf.rig.vbf_path.glob("*.vbf")]
    log.info(vbf_files)
    if not sbl.read_vbf_param(vbf_files):
        DutTestError("Could not load vbf files")

    ess_vbf_file = sbl.get_ess_filename()
    if ess_vbf_file:
        # Some ECU like HLCM don't have ESS vbf file
        # if no ESS file present: skip download
        sbl2 = SupportSBL()
        log.info("ess file software download: %s", ess_vbf_file)
        vbf_version, vbf_header, vbf_data, vbf_offset = sbl2.read_vbf_file(ess_vbf_file)

        #convert vbf header so values can be used directly
        sbl2.vbf_header_convert(vbf_header)
        log.info("ESS VBF version: %s", vbf_version)

        # Erase Memory
        if not sbl2.flash_erase(dut, vbf_header, 101):
            raise DutTestError("Failed transfer data block")

        # Iteration to Download the Software by blocks
        if not sbl2.transfer_data_block(dut, vbf_header, vbf_data, vbf_offset):
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


def flash():
    """ flash the ecu """
    dut = Dut()
    start_time = dut.start()
    result = False
    try:
        dut.precondition(timeout=3600)
        dut.step(software_download)
        result = True
    except: # pylint: disable=bare-except
        error = traceback.format_exc()
        log.error("Flashing (that is, doing software download to) the ECU failed: %s", error)
    finally:
        dut.postcondition(start_time, result)
