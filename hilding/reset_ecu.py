"""
Reset and reflash (do a software download to) the ECU if necessary
"""
import logging
import time
import traceback

from hilding.dut import Dut
from hilding.dut import DutTestError
from hilding.uds import EicDid
from hilding.flash import software_download


log = logging.getLogger('reset_ecu')

def reset_ecu_mode(dut: Dut):
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

    if mode in [2, 3]:
        dut.uds.set_mode(1)
        mode = dut.uds.mode
        dut.uds.read_data_by_id_22(EicDid.complete_ecu_part_number_eda0)
    time.sleep(1)
    if mode != 1:
        dut.uds.ecu_reset_1101(delay=5)
        dut.uds.set_mode(1)
        mode = dut.uds.mode
    if mode != 1:
        software_download(dut)
        dut.uds.ecu_reset_1101(delay=5)
        dut.uds.set_mode(1)
        mode = dut.uds.mode
    if mode != 1:
        raise DutTestError("Could not reset the ECU to mode/session 1")

def reset_and_flash_ecu():
    """ reset ecu """
    dut = Dut()
    start_time = dut.start()
    result = False
    try:
        dut.precondition(timeout=3600)
        dut.step(reset_ecu_mode)
        result = True
    except: # pylint: disable=bare-except
        error = traceback.format_exc()
        log.error("Resetting the ECU failed: %s", error)
    finally:
        dut.postcondition(start_time, result)
