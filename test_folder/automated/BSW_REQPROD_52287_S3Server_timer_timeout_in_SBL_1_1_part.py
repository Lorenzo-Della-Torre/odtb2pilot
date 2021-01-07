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
import inspect

import odtb_conf
from supportfunctions.support_can import SupportCAN, CanParam
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_sec_acc import SupportSecurityAccess

from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition
from supportfunctions.support_service10 import SupportService10
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service3e import SupportService3e

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

def step_1(can_p: CanParam):
    """
    Teststep 1: Activate SBL
    """
    stepno = 1
    purpose = "Download and Activation of SBL"
    fixed_key = '0102030405'
    new_fixed_key = SIO.extract_parameter_yml(str(inspect.stack()[0][3]), 'fixed_key')
    # don't set empty value if no replacement was found:
    if new_fixed_key != '':
        assert isinstance(new_fixed_key, str)
        fixed_key = new_fixed_key
    else:
        logging.info("Step%s: new_fixed_key is empty. Leave old value.", stepno)
    logging.info("Step%s: fixed_key after YML: %s", stepno, fixed_key)

    result = SSBL.sbl_activation(can_p,
                                 fixed_key,
                                 stepno, purpose)
    return result

def run():
    """
    Run - Call other functions from here
    """
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

    # start logging
    # to be implemented

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
    SSBL.get_vbf_files()
    time.sleep(4)

    timeout = 500
    result = PREC.precondition(can_p, timeout)
    if result:
    ############################################
    # teststeps
    ############################################

        # step1:
        # action: DL and activation of SBL
        # result: ECU sends positive reply
        result = result and step_1(can_p)

        # step2:
        # action: Verify ECU in SBL
        # result: ECU sends positive reply
        result = result and SE22.verify_sbl_session(can_p, stepno=2)

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
        # action: Verify ECU is still in SBL
        # result: ECU sends positive reply
        result = result and SE22.verify_sbl_session(can_p, stepno=5)

        # step6:
        # action: wait longher than timeout
        # result:
        logging.info("Step 6: Wait longher than timeout for staying in current mode.")
        logging.info("Step 6: No request to ECU as before.")
        time.sleep(6)

        # step7:
        # action: Verify ECU change to default session
        # result: ECU sends positive reply
        result = result and SE22.read_did_f186(can_p, b'\x01', stepno=7)

    ############################################
    # postCondition
    ############################################
    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
