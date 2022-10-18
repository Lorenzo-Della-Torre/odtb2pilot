"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

# Testscript Hilding MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2019-12-13
# version:  1.0

# date:     2020-05-04
# version:  1.1
# changes:  parameter support functions

# date:     2021-08-13
# version:  1.3
# changes:  support SecAcc_Gen2

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

The Python implementation of the gRPC route guide client.
"""

import time
from datetime import datetime
import sys
import logging

import odtb_conf
from supportfunctions.support_can import SupportCAN, CanParam, PerParam
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_sec_acc import SupportSecurityAccess, SecAccessParam
from supportfunctions.support_file_io import SupportFileIO

from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_service11 import SupportService11
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service3e import SupportService3e

SIO = SupportFileIO
SC = SupportCAN()
SUTE = SupportTestODTB2()
SSBL = SupportSBL()
SSA = SupportSecurityAccess()

PREC = SupportPrecondition()
SE11 = SupportService11()
SE22 = SupportService22()
SE3E = SupportService3e()

def stop_nmframe():
    """
        stop sending nm_frames  (heartbeat)
    """
    result = True

    logging.debug("Stop heartbeat sent.")
    SC.stop_heartbeat()

    time.sleep(1)
    return result


def restart_nmframe(can_p):
    """
        start sending nmframes (heartbeat) again
    """
    result = True

    stepno = 999
    purpose = "send wakeup frames again, wait for BECM to be awake again"

    logging.info("Step No. {:d}: purpose: {}".format(stepno, purpose))

    hb_param: PerParam = {
        "name" : "Heartbeat",
        "send" : True,
        "id" : "EcmFront1NMFr",
        "nspace" : can_p["namespace"].name,
        "frame" : b'\x1A\x40\xC3\xFF\x01\x00\x00\x00',
        "intervall" : 0.8
        }
    SIO.parameter_adopt_teststep(hb_param)
    # start heartbeat, repeat every x second

    SC.start_heartbeat(can_p["netstub"], hb_param)
    return result


def step_1(can_p: CanParam, sa_keys):
    """
    Teststep 1: Activate SBL
    Download of SBL to ECU and activation.

    If running into problems activating SBL:
    Check if not sending nm_frame and/or TesterPresent helps
    uncomment 'stop_nmframe', SE3E.stop_periodic
    """
    stepno = 1
    purpose = "Download and Activation of SBL"

    #logging.info("Step1, sa_keys: %s", sa_keys)
    #stop_nmframe()
    #SE3E.stop_periodic_tp_zero_suppress_prmib()
    result = SSBL.sbl_activation(can_p,
                                 sa_keys,
                                 stepno, purpose)
    return result

def step_2(can_p: CanParam):
    """
    Teststep 2: ESS Software Part Download

    Some ECU like HLCM don't have ESS vbf file
    if no ESS file present: skip download

    If needed: start sending TesterPresent/ heartbeat again
    """
    stepno = 2
    purpose = "ESS Software Part Download"
    if SSBL.get_ess_filename():
        result = SSBL.sw_part_download(can_p, SSBL.get_ess_filename(),
                                       stepno, purpose)
    else:
        result = True
    #SE3E.start_periodic_tp_zero_suppress_prmib(can_p)
    #restart_nmframe(can_p)
    return result

def step_3(can_p: CanParam):
    """
    Teststep 3: Download other SW Parts
    """
    stepno = 3
    result = True
    purpose = "continue Download SW"
    for i in SSBL.get_df_filenames():
        # if needed: actiate DID EDA0 to check which mode ecu is in:
        #result = result and SE22.read_did_eda0(can_p)
        result = result and SSBL.sw_part_download(can_p, i, stepno, purpose)
    return result

def step_4(can_p: CanParam):
    """
    Teststep 4: Check Complete And Compatible
    """
    stepno = 4

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
        "namespace" : SC.nspace_lookup("Front1CANCfg0"),
        "protocol" : 'can',
        "framelength_max" : 8,
        "padding" : True
        }
    SIO.parameter_adopt_teststep(can_p)

    logging.debug("Testcase start: %s", datetime.now())
    starttime = time.time()
    logging.info("Time: %s \n", time.time())
    ############################################
    # precondition
    ############################################

    # read VBF param when testscript is s started, if empty take default param
    result = SSBL.get_vbf_files()
    timeout = 3600
    result = result and PREC.precondition(can_p, timeout)

    #Init parameter for SecAccess Gen1 / Gen2 (current default: Gen1)
    sa_keys: SecAccessParam = {
        "SecAcc_Gen": 'Gen1',
        "fixed_key": '0102030405',
        "auth_key": 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF',
        "proof_key": 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'
    }

    SIO.parameter_adopt_teststep(sa_keys)

    if result:
        ############################################
        # teststeps
        ############################################
        # step 1:
        # action: download and activate SBL
        # result:
        result = result and step_1(can_p, sa_keys)

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
        # action: Stop sending TesterPresent
        # result: ECU fallback to Mode1 after timeout
        SE3E.stop_periodic_tp_zero_suppress_prmib()
        # timeout more than 5 sec should trigger timeout, causing reset
        # time.sleep(7) wasn't enough with HVBM ecu.
        time.sleep(10)
        # Reset not done anymore. Fallback after timeout should do the job
        #result = result and SE11.ecu_hardreset_5sec_delay(can_p)

        # step 6:
        # action: Check which Mode ECU is in after timeout/reset
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
    #logging.error("This way of doing SWDL should not be used. Run manage.py flash instead\
    #    \n This script is kept for now but should soon be removed")
    run()
