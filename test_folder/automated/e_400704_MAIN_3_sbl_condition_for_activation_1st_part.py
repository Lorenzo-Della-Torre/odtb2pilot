"""
/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

# Testscript Hilding MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-04-21
# version:  1.0
# reqprod:  400704

# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-08-28
# version:  1.1
# reqprod:  400704

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
from supportfunctions.support_sec_acc import SupportSecurityAccess

from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition
from supportfunctions.support_service10 import SupportService10
from supportfunctions.support_service11 import SupportService11
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_service31 import SupportService31
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
SE11 = SupportService11()
SE22 = SupportService22()
SE27 = SupportService27()
SE31 = SupportService31()
SE3E = SupportService3e()

def step_5(can_p, call):
    """
    Teststep 5: Send RoutineControl Request SID startRoutine (01), Activate Secondary Boot-loader
    """
    call = call.to_bytes((call.bit_length()+7) // 8, 'big')
    cpay: CanPayload = {
        "payload":S_CARCOM.can_m_send("RoutineControlRequestSID",
                                      b'\x03\x01' + call, b'\x01'),
        "extra":''
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)

    etp: CanTestExtra = {
        "step_no" : 5,
        "purpose" : "SBL activation with correct call",
        "timeout" : 4,
        "min_no_messages" : -1,
        "max_no_messages" : -1
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)
    result = SUTE.teststep(can_p, cpay, etp)

    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='7F3131')
    logging.info(SUTE.pp_decode_7f_response(SC.can_frames[can_p["receive"]][0][2]))
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
    timeout = 200
    result = PREC.precondition(can_p, timeout)
    if result:

    ############################################
    # teststeps
    ############################################
        # step 1:
        # action: Verify if preconditions to programming are fulfilled.
        # result: ECU sends positive reply if successful.
        result = result and SE31.routinecontrol_requestsid_prog_precond(can_p, 1)

        # step2:
        # action: Change to programming session (02) to be able to enter the PBL.
        # result: ECU sends positive reply if successful.
        result = result and SE10.diagnostic_session_control_mode2(can_p, 2)

        # step 3:
        # action: Request Security Access to be able to unlock the server(s)
        #         and run the primary bootloader.
        # result: Positive reply from support function if Security Access to server is activated.
        result = result and SE27.activate_security_access(can_p, 3)

        # step4:
        # action: Flash the SBL without Check Memory (without verification).
        # result: Positive reply from support function if DL of SBL ok.
        result_dl, vbf_header = SSBL.sbl_download_no_check(can_p, SSBL.get_sbl_filename())
        result = result and result_dl
        time.sleep(1)

        # step 5:
        # action: Send RoutineControl Request SID startRoutine (01) Activate Secondary Boot-loader.
        # result: ECU sends NRC reply after RoutineControl request is sent.
        result = result and step_5(can_p, vbf_header['call'])

        # step 6:
        # action: Reset the ECU with positive response(01)
        # result: ECU sends positive reply if successful.
        result = result and SE11.ecu_hardreset(can_p, 6)
        time.sleep(1)

        # step 7:
        # action: Verify ECU is in default session (01).
        # result: ECU sends requested DID with current session.
        result = result and SE22.read_did_f186(can_p, b'\x01', stepno=7)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
