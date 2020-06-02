# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2019-12-13
# version:  1.0

# date:     2020-05-04
# version:  1.1
# changes:  parameter support functions

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

import ODTB_conf
from support_can import Support_CAN, CanParam
from support_test_odtb2 import Support_test_ODTB2
from support_SBL import Support_SBL
from support_SecAcc import Support_Security_Access

from support_precondition import SupportPrecondition
from support_service11 import SupportService11
from support_service22 import SupportService22

SC = Support_CAN()
SUTE = Support_test_ODTB2()
SSBL = Support_SBL()
SSA = Support_Security_Access()

PREC = SupportPrecondition()
SE11 = SupportService11()
SE22 = SupportService22()


def step_1(can_p: CanParam):
    """
    Teststep 1: Activate SBL
    """
    stepno = 1
    purpose = "Download and Activation of SBL"
    result = SSBL.sbl_activation(can_p,\
                                 stepno, purpose)
    return result

def step_2(can_p: CanParam):
    """
    Teststep 2: ESS Software Part Download
    """
    stepno = 2
    purpose = "ESS Software Part Download"
    result = SSBL.sw_part_download(can_p, SSBL.get_ess_filename(),\
                                   stepno, purpose)
    return result

def step_3(can_p: CanParam):
    """
    Teststep 3: Download other SW Parts
    """
    stepno = 3
    result = True
    purpose = "continue Download SW"
    for i in SSBL.get_df_filenames():

        result = result and SSBL.sw_part_download(can_p, i, stepno, purpose)
    return result

def step_4(can_p: CanParam):
    """
    Teststep 4: Check Complete And Compatible
    """
    stepno = 4
    purpose = "verify RoutineControl start are sent for Type 1"

    result = SSBL.check_complete_compatible_routine(can_p, stepno, purpose)
    return result


def run():
    """
    Run - Call other functions from here
    """
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.DEBUG)

    # start logging
    # to be implemented

    # where to connect to signal_broker
    can_par: CanParam = {
        "netstub" : SC.connect_to_signalbroker(ODTB_conf.ODTB2_DUT, ODTB_conf.ODTB2_PORT),\
        "send" : "Vcu1ToBecmFront1DiagReqFrame",\
        "rec" : "BecmToVcu1Front1DiagResFrame",\
        "namespace" : SC.nspace_lookup("Front1CANCfg0")
        }

    logging.info("Testcase start: %s", datetime.now())
    starttime = time.time()
    logging.info("Time: %s \n", time.time())
    ############################################
    # precondition
    ############################################

    # read arguments for files to DL:
    f_sbl = ''
    f_ess = ''
    f_df = []
    for f_name in sys.argv:
        if not f_name.find('.vbf') == -1:
            print("Filename to DL: ", f_name)
            if not f_name.find('sbl') == -1:
                f_sbl = f_name
            elif not f_name.find('ess') == -1:
                f_ess = f_name
            else:
                f_df.append(f_name)
    SSBL.__init__(f_sbl, f_ess, f_df)
    SSBL.show_filenames()
    time.sleep(10)

    # read VBF param when testscript is s started, if empty take default param
    SSBL.get_vbf_files()
    timeout = 3600
    result = PREC.precondition(can_par, timeout)

    if result:
        ############################################
        # teststeps
        ############################################
        # step 1:
        # action: verify RoutineControl start is sent for Type 1
        # result: BECM sends positive reply

        #extra reset when DL didn't start correct after unfinished SWDL
        #result = result and step_5(network_stub, can_send, can_receive, can_namespace)

        result = result and step_1(can_par)
        #result = step_4(network_stub, can_send, can_receive, can_namespace)
        # step 2:
        # action:
        # result: BECM sends positive reply
        result = result and step_2(can_par)

        # step 3:
        # action:
        # result: BECM sends positive reply
        result = result and step_3(can_par)

        # step 4:
        # action:
        # result: BECM sends positive reply
        result = result and step_4(can_par)

        # step 5:
        # action: ECU reset - Restart with downloaded SW
        # result: ECU accepts reset request
        result = result and SE11.ecu_hardreset(can_par)

        # step 6:
        # action: Check which Mode ECU is in after reset
        # result: All went well. Boot up to Mode 1
        result = result and SE22.read_did_f186(can_par, dsession=b'\x01')
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
