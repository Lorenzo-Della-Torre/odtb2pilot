# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   J-ADSJO
# date:     2021-02-24
# version:  1.0
# reqprod:  72220

#inspired by https://grpc.io/docs/tutorials/basic/python.html

# Copyright 2015 gRPC authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""The Python implementation of the gRPC route guide client."""

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
    Software Erase, Download and check
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


def step_2(can_p: CanParam):
    """
    Teststep 2: ESS Software Part Download
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
    Teststep 3: Download other SW Parts
    """
    stepno = 3
    result = True
    purpose = "Other SW Parts"
    for i in SSBL.get_df_filenames():
        result = result and sw_part_erase_download_check(can_p, i, stepno, purpose)

    return result


def step_4(can_p: CanParam):
    """
    Teststep 4: Check Complete And Compatible
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
        # step 1:
        # action: download and activate SBL
        # result:
        result = result and SSBL.sbl_dl_activation(can_p, 1, "DL and activate SBL")

        # step 2:
        # action: ESS Software Part Download
        # result:
        result = result and step_2(can_p)

        # step 3:
        # action: Download other SW Parts
        # result:
        result = result and step_3(can_p)

        # step 4:
        # action: Check Complete And Compatible
        # result:
        result = result and step_4(can_p)

        # step 5:
        # action: ECU reset - Restart with downloaded SW
        # result: ECU accepts reset request
        result_5 = SE11.ecu_hardreset_5sec_delay(can_p)
        result = result and result_5

        # step 6:
        # action: Check which Mode ECU is in after reset
        # result: All went well. Boot up to Mode 1
        result = result and SE22.read_did_f186(can_p, dsession=b'\x01')
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
