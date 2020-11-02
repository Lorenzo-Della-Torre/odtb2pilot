# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2019-12-13
# version:  1.0
# reqprod:  53858

# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-09-28
# version:  1.1
# reqprod:  53858

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
from support_can import SupportCAN, CanParam, CanTestExtra, CanPayload
from support_test_odtb2 import SupportTestODTB2
from support_carcom import SupportCARCOM
from support_file_io import SupportFileIO
from support_SBL import SupportSBL
from support_sec_acc import SupportSecurityAccess
from support_rpi_gpio import SupportRpiGpio

from support_precondition import SupportPrecondition
from support_postcondition import SupportPostcondition
from support_service10 import SupportService10
from support_service11 import SupportService11
from support_service22 import SupportService22
from support_service31 import SupportService31
from support_service3e import SupportService3e
from support_service27 import SupportService27


SIO = SupportFileIO
SC = SupportCAN()
S_CARCOM = SupportCARCOM()
SUTE = SupportTestODTB2()
SSBL = SupportSBL()
SSA = SupportSecurityAccess()
SGPIO = SupportRpiGpio()

PREC = SupportPrecondition()
POST = SupportPostcondition()
SE10 = SupportService10()
SE11 = SupportService11()
SE22 = SupportService22()
SE27 = SupportService27()
SE31 = SupportService31()
SE3E = SupportService3e()

def step_4(can_p):
    """
    Teststep 4: test presence of fake service 2E
    """

    etp: CanTestExtra = {"step_no": 4,
                         "purpose" : "verify fake service 2E is not active",
                         "timeout" : 1, # wait for message to arrive, but don't test (-1)
                         "min_no_messages" : -1,
                         "max_no_messages" : -1
                        }

    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    cpay: CanPayload = {"payload" : b'\x2E\xF1\x86\x02',
                        "extra" : ''
                       }

    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)

    result = SUTE.teststep(can_p, cpay, etp)

    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], '7F2E31')
    print(SUTE.pp_decode_7f_response(SC.can_messages[can_p["receive"]][0][2]))
    time.sleep(1)
    return result

def step_5(can_p):
    """
    Teststep 5: Security Access Request SID
    """
    result, seed = SE27.pbl_security_access_request_seed(can_p, stepno=5,
                                                         purpose="Security Access Request SID")
    #verify SID = 000000
    result = result and seed == '000000'

    return result, seed

def step_6(can_p, seed):
    """
    Testresult 6: Verify Security Access Send Key reply NRC
    """
    etp: CanTestExtra = {"step_no": 6,
                         "purpose" : "Verify Security Access Send Key reply NRC",
                         "timeout" : 1, # wait for message to arrive, but don't test (-1)
                         "min_no_messages" : -1,
                         "max_no_messages" : -1
                        }

    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    fixed_key = 'FFFFFFFFFF'
    r_0 = SSA.set_security_access_pins(seed, fixed_key)

    cpay: CanPayload = {"payload" : S_CARCOM.can_m_send("SecurityAccessSendKey",
                                                        r_0, b''),
                        "extra" : ''
                       }

    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)

    result = SUTE.teststep(can_p, cpay, etp)
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], '7F2724')
    time.sleep(1)
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
    timeout = 100
    result = PREC.precondition(can_p, timeout)

    if result:
    ############################################
    # teststeps
    ############################################

        # step1:
        # action: DL and activate SBL
        # result: ECU sends positive reply
        result = result and SSBL.sbl_activation(can_p, stepno=1,
                                                purpose="DL and activate SBL")
        time.sleep(1)

        # step 2:
        # action: Test presence of tester preset Zero Sub Function
        # result: BECM sends positive reply
        result = result and SE3E.tester_present_zero_subfunction(can_p, stepno=2)

        # step 3:
        # action: Test presence of service 22
        # result: BECM sends positive reply
        result = result and SE22.read_did_eda0(can_p, stepno=3)

        # step 4:
        # action: Test presence of service 2E
        # result: BECM reply with NRC
        result = result and step_4(can_p)

        # step 5:
        # action: verify Security Access Request SID = 000000
        # result: BECM sends positive reply
        result_step5, seed = SE27.pbl_security_access_request_seed(can_p, stepno=5,\
                                  purpose="Security Access Request SID")
        result = result and result_step5

        # step 6:
        # action: Verify Security Access Send Key reply NRC
        # result: BECM reply NRC
        result = result and step_6(can_p, seed)

        # step 7:
        # action: test presence of Diagnostic Session Control ECU Programming Session
        # result: ECU sends positive reply
        result = result and SE10.diagnostic_session_control_mode2(can_p, stepno=7)

        # step 8:
        # action: Verify ECU in SBL
        # result: BECM sends positive reply
        result = result and SE22.verify_sbl_session(can_p, stepno=8)

        # step 9:
        # action: test presence of Diagnostic Session Control ECU Default Session
        # result: ECU sends positive reply
        result = result and SE10.diagnostic_session_control_mode1(can_p, stepno=9)
        time.sleep(1)

        # step10:
        # action: Hard Reset
        # result: ECU sends positive reply
        result = result and SE11.ecu_hardreset(can_p, stepno=10)
        time.sleep(1)

        # step11:
        # action: verify ECU in default session
        # result: ECU sends positive reply
        result = result and SE22.read_did_f186(can_p, b'\x01', stepno=11)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
