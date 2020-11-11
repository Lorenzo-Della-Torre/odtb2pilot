# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   HWEILER (Hans-Klaus Weiler)
# date:     2020-10-26
# version:  1.0

# main parts from BSW_SWDL:
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-05-04
# version:  1.1

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
from support_can import SupportCAN, CanParam
from support_test_odtb2 import SupportTestODTB2
from support_SBL import SupportSBL
from support_sec_acc import SupportSecurityAccess
from support_file_io import SupportFileIO

from support_precondition import SupportPrecondition
from support_service10 import SupportService10
from support_service11 import SupportService11
from support_service22 import SupportService22

SIO = SupportFileIO
SC = SupportCAN()
SUTE = SupportTestODTB2()
SSBL = SupportSBL()
SSA = SupportSecurityAccess()

PREC = SupportPrecondition()
SE10 = SupportService10()
SE11 = SupportService11()
SE22 = SupportService22()


def step_1(can_p: CanParam):
    """
    Teststep 1: Check mode ECU is in, try to change to mode1
    """
    swdl_needed = False

    logging.info("ECU restore: Display current session, try to change to mode1 (default)")
    SE22.read_did_f186(can_p)
    logging.info("ECU restore: Mode when starting script: %s", SC.can_messages[can_p["receive"]])
    if SC.can_messages[can_p["receive"]] == -1:
        logging.info("ECU restore: No reply from ECU.")
    elif SC.can_messages[can_p["receive"]][0][2].find('62F18601') == -1:
        logging.info("ECU not in default mode. Call session control.")
        SE10.diagnostic_session_control_mode1(can_p)
        #if coming from mode2 it may take a bit
        time.sleep(2)
        SE22.read_did_f186(can_p)

    if SC.can_messages[can_p["receive"]] == -1:
        logging.info("ECU restore: No reply from ECU.")
        swdl_needed = True
    elif SC.can_messages[can_p["receive"]][0][2].find('62F18601') == -1:
        logging.info("Could not change ECU to default mode.")
        swdl_needed = True
    if swdl_needed:
        logging.info ("ECU restore: Could not switch ECU to mode1. Will try to reflash ECU.")
    else:
        logging.info ("ECU restore: Everything seems to be fine. ECU in default mode.")
    return swdl_needed

def step_2(can_p: CanParam):
    """
    Teststep 2: Activate SBL
    """
    stepno = 2
    purpose = "Download and Activation of SBL"
    result = SSBL.sbl_activation(can_p,
                                 stepno, purpose)
    return result

def step_3(can_p: CanParam):
    """
    Teststep 3: ESS Software Part Download
    """
    stepno = 3
    purpose = "ESS Software Part Download"
    result = SSBL.sw_part_download(can_p, SSBL.get_ess_filename(),
                                   stepno, purpose)
    return result

def step_4(can_p: CanParam):
    """
    Teststep 4: Download other SW Parts
    """
    stepno = 4
    result = True
    purpose = "continue Download SW"
    for i in SSBL.get_df_filenames():
        result = result and SE22.read_did_eda0(can_p)
        result = result and SSBL.sw_part_download(can_p, i, stepno, purpose)
    return result

def step_5(can_p: CanParam):
    """
    Teststep 5: Check Complete And Compatible
    """
    stepno = 5

    result = SSBL.check_complete_compatible_routine(can_p, stepno)
    return result


def run():
    """
    Run - Call other functions from here
    """

    # start logging
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)
    #logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.DEBUG)

    # where to connect to signal_broker
    can_p: CanParam = {
        "netstub" : SC.connect_to_signalbroker(odtb_conf.ODTB2_DUT, odtb_conf.ODTB2_PORT),
        "send" : "Vcu1ToBecmFront1DiagReqFrame",
        "receive" : "BecmToVcu1Front1DiagResFrame",
        "namespace" : SC.nspace_lookup("Front1CANCfg0")
        }
    #print("Current function name: ", inspect.stack()[0][3])
    logging.info("Update parameters for testscript, part: %s", inspect.stack()[0][3])
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), can_p)

    logging.info("Testcase start: %s", datetime.now())
    starttime = time.time()
    logging.info("Time: %s \n", time.time())
    ############################################
    # precondition
    ############################################

    # read VBF param when tget_vbf_filesestscript is s started, if empty take default param
    result = SSBL.get_vbf_files()
    timeout = 3600
    result = result and PREC.precondition(can_p, timeout)

    if result:
        ############################################
        # teststeps
        ############################################
        # step 1:
        # action: try to switch ECU to default mode
        # result: True if succeed.
        swdl_needed = step_1(can_p)

        if swdl_needed:
        # step 2:
        # action: download and activate SBL
        # result:
            result = result and step_2(can_p)

        # step 3:
        # action: ESS Software Part Download
        # result:
            result = result and step_3(can_p)

        # step 4:
        # action: Download other SW Parts
        # result:
            result = result and step_4(can_p)

        # step 5:
        # action: Check Complete And Compatible
        # result:
            result = result and step_5(can_p)

        # step 6:
        # action: ECU reset - Restart with downloaded SW
        # result: ECU accepts reset request
            result = result and SE11.ecu_hardreset_5sec_delay(can_p)

        # step 7:
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
