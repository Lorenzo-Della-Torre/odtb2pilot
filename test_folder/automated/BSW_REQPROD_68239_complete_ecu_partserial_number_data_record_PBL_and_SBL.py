# Testscript ODTB2 MEPII
# project: BECM basetech MEPII
# author:  T-kumara (Tanuj Kumar Aluru)
# date:    2020-10-26
# version:  1.0
# reqprod:  62839

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
from supportfunctions.support_can import SupportCAN, CanParam, CanPayload, CanTestExtra
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service10 import SupportService10

SIO = SupportFileIO
SC = SupportCAN()
S_CARCOM = SupportCARCOM()
SUTE = SupportTestODTB2()
SSBL = SupportSBL()

PREC = SupportPrecondition()
POST = SupportPostcondition()
SE22 = SupportService22()
SE10 = SupportService10()


def step_3(can_p):
    '''
    Validate ECU Part/Serial Numbers in PBL Session
    '''
    cpay : CanPayload = {
        "payload": S_CARCOM.can_m_send( "ReadDataByIdentifier", b'\xED\xA0', b""),
        "extra": b'',
    }
    etp : CanTestExtra = {
        "step_no": 3,
        "purpose": 'Validate formats of ECU PN/SN numbesrs in PBL',
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1,
    }
    result = SUTE.teststep(can_p,cpay, etp)
    logging.info("Complete ECU Serial Part Number in PBL : %s",\
                            SC.can_messages[can_p["receive"]][0][2])
    rec_message = SC.can_messages[can_p['receive']][0][2]
    pn_sn = [['F121', 'PN'],['F12A', 'PN'],['F12B', 'PN'],['F18C', 'SN'],['F125', 'PN']]
    result = result and SUTE.validate_combined_did_eda0(rec_message,pn_sn)
    return  result

def step_7(can_p):
    '''
    Validate ECU Part/Serial Numbers in SBL Session
    '''
    cpay : CanPayload = {"payload" : S_CARCOM.can_m_send("ReadDataByIdentifier",
                                                             b'\xED\xA0', b''),
                        "extra" : ''
    }
    etp: CanTestExtra = {"step_no": 7,
                        "purpose" : 'Validate formats of ECU PN/SN numbers in SBL',
                        "timeout" : 1,
                        "min_no_messages" : -1,
                        "max_no_messages" : -1
    }
    result = SUTE.teststep(can_p, cpay, etp)
    logging.info("Complete ECU Serial Part Number in SBL : %s",\
                            SC.can_messages[can_p["receive"]][0][2])
    rec_message = SC.can_messages[can_p['receive']][0][2]
    pn_sn = [['F122', 'PN'],['F12A', 'PN'],['F12B', 'PN'],['F18C', 'SN'],['F124', 'PN']]
    result = result and SUTE.validate_combined_did_eda0(rec_message,pn_sn)
    return result

def run():
    """
    Run - Call other functions from here
    """
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
    SSBL.get_vbf_files()
    timeout = 200
    result = PREC.precondition(can_p, timeout)
    if result:
    ############################################
    # teststeps
    ############################################
        # step 1:
        # action: Change session to Programming
        # result: BECM reply positively
        result = result and SE10.diagnostic_session_control_mode2(can_p,1)
        time.sleep(2)

        # step 2 :
        # action: Verify Programming Session
        # result: BECM reply positively
        result = result and SE22.verify_pbl_session(can_p,2)

        # step 3:
        # action: Validate PN/SN Numbers in PBL
        # result: BECM reply positively
        result = result and step_3(can_p)

        # step 4:
        # action: Change ECU to Default Session
        # result: BECM reply positively
        result = result and SE10.diagnostic_session_control_mode1(can_p,4)

        # step 5:
        # action: Active DL and SBL
        # result: BECM reply positively
        result = result and SSBL.sbl_dl_activation(can_p, 5, "DL and activate SBL")

        # step 6:
        # action: Verify SBL session
        # result: BECM reply positively
        result = result and SE22.verify_sbl_session(can_p,6)

        # step 7:
        # action: Validate PN/SN Numbers in SBL
        # result: BECM reply positively
        result = result and step_7(can_p)

        # step 8:
        # action: Change to Default Session
        # result: BECM reply positively
        result = result and SE10.diagnostic_session_control_mode1(can_p,8)
    ############################################
    # postCondition
    ############################################
    POST.postcondition(can_p, starttime, result)

if __name__ == "__main__":
    run()
