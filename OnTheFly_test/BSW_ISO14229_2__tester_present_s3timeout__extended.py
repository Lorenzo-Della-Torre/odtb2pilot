# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-06-05
# version:  1.1
# reqprod:  397438

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
from support_can import SupportCAN, CanParam #, CanTestExtra
from support_test_odtb2 import SupportTestODTB2
from support_SBL import SupportSBL
from support_sec_acc import SupportSecurityAccess
from support_carcom import SupportCARCOM

from support_precondition import SupportPrecondition
from support_postcondition import SupportPostcondition
from support_service10 import SupportService10
from support_service22 import SupportService22
from support_service3e import SupportService3e

SC = SupportCAN()
S_CARCOM = SupportCARCOM()
SUTE = SupportTestODTB2()
SSA = SupportSecurityAccess()
SSBL = SupportSBL()

PREC = SupportPrecondition()
POST = SupportPostcondition()
SE10 = SupportService10()
SE22 = SupportService22()
SE3E = SupportService3e()


def run():
    """
    Run
    """
    #logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.DEBUG)
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)
    # start logging
    # to be implemented

    can_p: CanParam = {
        "netstub" : SC.connect_to_signalbroker(ODTB_conf.ODTB2_DUT, ODTB_conf.ODTB2_PORT),\
        "send" : "Vcu1ToBecmFront1DiagReqFrame",\
        "receive" : "BecmToVcu1Front1DiagResFrame",\
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
            logging.info("Filename to DL: %s \n", f_name)
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
    timeout = 60
    result = PREC.precondition(can_p, timeout)


    ############################################
    # teststeps
    ############################################
    # step 1:
    # action: Verify default session
    # result:
    logging.info("Step 1: Verify ECU is in default session.")
    result = SE22.read_did_f186(can_p, b'\x01', '1')
    #result and step_1(can_param)

    # step2:
    # action:
    # result:
    logging.info("Step 2: Request change to mode3 (extended session).")
    result = result and SE10.diagnostic_session_control_mode3(can_p, '2')
    #erase = step_2()

    # step3:
    # action:
    # result:
    logging.info("Step 3: Verify ECU change to requested session mode.")
    result = result and SE22.read_did_f186(can_p, b'\x03', '3')


    logging.info("Step 4: Request Complete ECU part/serial numbers (EDA0).")
    result = SE22.read_did_eda0(can_p)
    message = SC.can_messages[can_p["receive"]][0][2]
    logging.info("Message to analyse: %s", message)
    if (not message.find('F120') == -1) and (not message.find('F12E') == -1):
        logging.info("Step 4: Application Diagnostic Database Part Number found in message.")
        logging.info("Step 4: ECU Software Part Numbers found in message.")
        SUTE.pp_combined_did_eda0_becm_mode1_mode3(message, "EDA0 for mode1/mode3:\n")
    else:
        logging.info("Step 4: Complete ECU part/serial numbers (EDA0)"\
                     "did not give expected result.")
        result = False

    # step5:
    # action: don't send a request until timeout occured
    # result:
    logging.info("Step 5: Wait longer than timeout for staying in current mode.")
    logging.info("Step 5: Tester present sent, but no request to ECU.")
    time.sleep(6)

    # step6:
    # action: Verify ECU is still in mode extended session
    # result:
    logging.info("Step 5: Verify ECU did not change session mode.")
    result = result and SE22.read_did_f186(can_p, b'\x03', '6')

    # step7:
    # action: stop sending tester present
    # result:
    logging.info("Step 7: stop sending tester present.")
    SE3E.stop_periodic_tp_zero_suppress_prmib()

    # step8:
    # action: wait longer than timeout
    # result:
    logging.info("Step 8: Wait longer than timeout for staying in current mode.")
    logging.info("Step 8: Tester present not sent, no request to ECU as before.")
    time.sleep(8)

    # step9:
    # action: verify ECU changed to default
    # result:
    logging.info("Step 8: Verify ECU changed to default session.")
    result = result and SE22.read_did_f186(can_p, b'\x01', '9')

    ############################################
    # postCondition
    ############################################
    POST.postcondition(can_p, starttime, result)


if __name__ == '__main__':
    run()
