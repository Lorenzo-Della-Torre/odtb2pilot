# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-06-10
# version:  1.2
# reqprod:  52286
# #inspired by https://grpc.io/docs/tutorials/basic/python.html
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
from support_can import SupportCAN, CanParam, CanPayload, CanTestExtra
from support_test_odtb2 import SupportTestODTB2
from support_carcom import SupportCARCOM
from support_file_io import SupportFileIO
from support_SBL import SupportSBL
from support_sec_acc import SupportSecurityAccess

from support_precondition import SupportPrecondition
from support_postcondition import SupportPostcondition
from support_service10 import SupportService10
from support_service22 import SupportService22
from support_service3e import SupportService3e

SIO = SupportFileIO
SC = SupportCAN()
S_CARCOM = SupportCARCOM()
SUTE = SupportTestODTB2()
SSBL = SupportSBL()
SSA = SupportSecurityAccess()

PREC = SupportPrecondition()
POST = SupportPostcondition()
SE10 = SupportService10()
SE22 = SupportService22()
SE3E = SupportService3e()

def step_2(can_par):
    """
    Teststep 2: verify session
    """
    stepno = 2
    cpay: CanPayload = SIO.extract_parameter_yml(
        "step_{}".format(stepno),
        payload=S_CARCOM.can_m_send("ReadDataByIdentifier", b'\xF1\x22', b''),
        extra=''
        )

    etp: CanTestExtra = SIO.extract_parameter_yml(
        "step_{}".format(stepno),
        step_no=2,
        timeout=1,
        purpose="Verify Programming session in SBL",
        min_no_messages=-1,
        max_no_messages=-1
        )

    result = SUTE.teststep(can_par, cpay, etp)
    result = result and SUTE.test_message(SC.can_messages[can_par["receive"]],\
                                          teststring='F122')

    return result

def step_5(can_par):
    """
    Teststep 5: verify session
    """
    stepno = 5
    cpay: CanPayload = SIO.extract_parameter_yml(
        "step_{}".format(stepno),
        payload=S_CARCOM.can_m_send("ReadDataByIdentifier", b'\xF1\x22', b''),
        extra=''
        )

    etp: CanTestExtra = SIO.extract_parameter_yml(
        "step_{}".format(stepno),
        step_no=5,
        timeout=1,
        purpose="Verify Programming session in SBL",
        min_no_messages=-1,
        max_no_messages=-1
        )

    result = SUTE.teststep(can_par, cpay, etp)
    result = result and SUTE.test_message(SC.can_messages[can_par["receive"]],\
                                          teststring='F122')

    return result

def run():
    """
    Run - Call other functions from here
    """
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.DEBUG)

    # start logging
    # to be implemented

    # where to connect to signal_broker
    can_par: CanParam = SIO.extract_parameter_yml(
        "main",
        netstub=SC.connect_to_signalbroker(ODTB_conf.ODTB2_DUT, ODTB_conf.ODTB2_PORT),
        send="Vcu1ToBecmFront1DiagReqFrame",
        receive="BecmToVcu1Front1DiagResFrame",
        namespace=SC.nspace_lookup("Front1CANCfg0")
        )

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
    time.sleep(4)

    timeout = 500
    result = PREC.precondition(can_par, timeout)
    if result:
    ############################################
    # teststeps
    ############################################

        # step1:
        # action:
        # result:
        result = result and SSBL.sbl_activation(can_par, 1, "DL and activate SBL")
        time.sleep(1)

        # step2:
        # action:
        # result:
        result = result and step_2(can_par)

        # step3:
        # action: stop sending tester present
        # result:
        logging.info("Step 3: stop sending tester present.")
        SE3E.stop_periodic_tp_zero_suppress_prmib()

        # step4:
        # action: wait shorter than timeout
        # result:
        logging.info("Step 4: Wait shorter than timeout for staying in current mode.")
        logging.info("Step 4: No request to ECU.")
        time.sleep(4)

        # step5:
        # action:
        # result:
        result = result and step_5(can_par)

        # step6:
        # action: wait longher than timeout
        # result:
        logging.info("Step 6: Wait longher than timeout for staying in current mode.")
        logging.info("Step 6: No request to ECU as before.")
        time.sleep(6)

        # step7:
        # action:
        # result:
        result = result and SE22.read_did_f186(can_par, b'\x01', '7')

    ############################################
    # postCondition
    ############################################
    POST.postcondition(can_par, starttime, result)

if __name__ == '__main__':
    run()
