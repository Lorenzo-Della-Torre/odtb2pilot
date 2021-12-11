"""
reqprod: 72220
version: 1
title: Erase Memory response time
purpose:
    Erasing Flash Memory is a time consuming routine that needs longer time
    than allowed for other routines

description: >
    The response time P4server_max for the Erase Memory routine shall be 60s.

    If the data that shall be erased exceeds 1 megabyte, it is allowed to
    increase the response time with 20s for each additional megabyte.

    Data erase size (megabyte): 1, 2, -, 5

    P4server_max (seconds): 60, 80, -, 140

    The P4server_max for an ESS update shall be defined by the size of the
    total memory, e.g. the sum of all erase requests for all programmable data
    files

"""

import time
from datetime import datetime
import sys
import logging
import inspect

import odtb_conf
from supportfunctions.support_can import SupportCAN, CanParam
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_sec_acc import SupportSecurityAccess
from supportfunctions.support_file_io import SupportFileIO

from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_service11 import SupportService11
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service31 import SupportService31

SIO = SupportFileIO
SC = SupportCAN()
SUTE = SupportTestODTB2()
SSBL = SupportSBL()
SSA = SupportSecurityAccess()

PREC = SupportPrecondition()
SE11 = SupportService11()
SE22 = SupportService22()
SE31 = SupportService31()


# Support Function for flashing SW Parts
def sw_part_erase_download_check(can_p: CanParam, file_n, stepno, purpose):
    """
    software erase, download and check
    """
    logging.info("sw_part_edc: %s", purpose)
    logging.info("sw_part_edc filename: %s", file_n)
    # Read vbf file for SBL download
    vbf_version, vbf_header, vbf_data, vbf_offset = SSBL.read_vbf_file(file_n)
    #convert vbf header so values can be used directly
    SSBL.vbf_header_convert(vbf_header)
    logging.info("\nVBF header: %s", vbf_header)
    logging.info("VBF version: %s", vbf_version)
    logging.info("VBF offset: %s \n", vbf_offset)

    # Erase Memory
    result = SE31.routinecontrol_requestsid_flash_erase(can_p, vbf_header, stepno)
    logging.info("SSBL: flash_erase EraseMemory, result: %s", result)

    time_0 = SC.can_frames[can_p["send"]][0][0]
    time_1 = SC.can_frames[can_p["receive"]][0][0]
    result = result and ((time_1 - time_0) < 60.5)
    if result:
        logging.info("P4Server time (%f) < 60 sec", (time_1 - time_0))
    else:
        logging.info("P4Server time (%f) > 60 sec", (time_1 - time_0))

    for frame_type, frames in SC.can_frames.items():
        logging.info("%s:", frame_type)
        for frame in frames:
            logging.info(frame)


    # Iteration to Download the Software by blocks
    result = result and SSBL.transfer_data_block(can_p, vbf_header, vbf_data, vbf_offset)

    # Check memory
    result = result and SE31.check_memory(can_p, vbf_header, stepno)

    return result

def step_1(can_p: CanParam):
    """
    action: download and activate sbl
    expected_result: positive reply
    """
    return SSBL.sbl_dl_activation(can_p, 1, "DL and activate SBL")


def step_2(can_p: CanParam):
    """
    action: ess software part download
    expected_result: positive reply
    """
    stepno = 2
    purpose = "ESS Software Part"
    # Some ECU like HLCM don't have ESS vbf file
    # if no ESS file present: skip download
    if SSBL.get_ess_filename():
        result = sw_part_erase_download_check(can_p, SSBL.get_ess_filename(),
                                               stepno, purpose)
    else:
        result = True
    return result

def step_3(can_p: CanParam):
    """
    action: download other software parts
    expected_result: positive reply
    """
    stepno = 3
    result = True
    purpose = "Other SW Parts"
    for i in SSBL.get_df_filenames():
        result = result and sw_part_erase_download_check(can_p, i, stepno, purpose)

    return result


def step_4(can_p: CanParam):
    """
    action: check complete and compatible
    expected_result: positive reply
    """
    stepno = 4
    result = SSBL.check_complete_compatible_routine(can_p, stepno)

    time_0 = SC.can_frames[can_p["send"]][0][0]
    time_1 = SC.can_frames[can_p["receive"]][0][0]
    result = result and ((time_1 - time_0)*1000.0 < 25.0)
    if result:
        logging.info("P2Server time (%f) < 25 ms", (time_1 - time_0)*1000.0)
    else:
        logging.info("P2Server time (%f) > 25 ms", (time_1 - time_0)*1000.0)

    for frame_type, frames in SC.can_frames.items():
        logging.info("%s:", frame_type)
        for frame in frames:
            ts_type, frame_type, frame_byte = frame
            logging.info("%s", [round(1000 * (ts_type - time_0), 3),
              frame_type, frame_byte])

    return result

def step_5(can_p: CanParam):
    """
    action: ecu reset - restart with downloaded sw
    expected_result: ecu accepts reset request
    """
    return SE11.ecu_hardreset_5sec_delay(can_p)


def step_6(can_p: CanParam):
    """
    action: check which mode ecu is in after reset
    expected_result: all went well. boot up to mode 1
    """
    return SE22.read_did_f186(can_p, dsession=b'\x01')


def run():
    """
    Run - Call other functions from here
    """

    # start logging
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

    # where to connect to signal_broker
    can_p: CanParam = {
        "netstub" : SC.connect_to_signalbroker(odtb_conf.ODTB2_DUT, odtb_conf.ODTB2_PORT),
        "send" : "Vcu1ToBecmFront1DiagReqFrame",
        "receive" : "BecmToVcu1Front1DiagResFrame",
        "namespace" : SC.nspace_lookup("Front1CANCfg0")
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), can_p)

    logging.info("Testcase start: %s", datetime.now())
    starttime = time.time()
    logging.info("Time: %s \n", time.time())
    ############################################
    # precondition
    ############################################

    # read VBF param when testscript is s started, if empty take default param
    result = SSBL.get_vbf_files()
    timeout = 3600
    result = result and PREC.precondition(can_p, timeout)

    if result:
        ############################################
        # teststeps
        ############################################
        result = result and step_1(can_p)

        result = result and step_2(can_p)

        result = result and step_3(can_p)

        result = result and step_4(can_p)

        result_5 = step_5(can_p)
        result = result and result_5

        result = result and step_6(can_p)

    ############################################
    # postCondition
    ############################################

    logging.debug("\nTime: %s \n", time.time())
    logging.info("Testcase end: %s", datetime.now())
    logging.info("Time needed for testrun (seconds): %s", int(time.time() - starttime))

    logging.info("Do cleanup now...")
    logging.info("Stop all periodic signals sent")
    SC.stop_periodic_all()

    # deregister signals
    SC.unsubscribe_signals()
    # if threads should remain: try to stop them
    SC.thread_stop()

    logging.info("Test cleanup end: %s\n", datetime.now())

    if result:
        logging.info("Testcase result: PASSED")
    else:
        logging.info("Testcase result: FAILED")


if __name__ == '__main__':
    run()
