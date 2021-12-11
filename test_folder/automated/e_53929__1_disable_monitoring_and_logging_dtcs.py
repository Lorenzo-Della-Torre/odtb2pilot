"""
/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

# Testscript Hilding MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-03-23
# version:  1.0
# reqprod:  53929

# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-09-16
# version:  1.1
# reqprod:  53929

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
from supportfunctions.support_service31 import SupportService31

SIO = SupportFileIO
SC = SupportCAN()
SC_CARCOM = SupportCARCOM()
SUTE = SupportTestODTB2()
SSBL = SupportSBL()
SSA = SupportSecurityAccess()

PREC = SupportPrecondition()
POST = SupportPostcondition()
SE10 = SupportService10()
SE11 = SupportService11()
SE22 = SupportService22()
SE31 = SupportService31()




def step_3(can_p):
    """
    Teststep 3: Verify service 19 is disabled in PBL session
    """

    etp: CanTestExtra = {
        "step_no" : 3,
        "purpose" : "Verify service 19 is disabled in PBL session",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
    }

    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDTCInfoSnapshotIdentification",
                                                         b'', b''),
                        "extra" : ''
                       }

    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)

    result = SUTE.teststep(can_p, cpay, etp)

    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='7F1911')
    logging.info('%s', SUTE.pp_decode_7f_response(SC.can_frames[can_p["receive"]][0][2]))
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
    timeout = 1000
    result = PREC.precondition(can_p, timeout)

    if result:
    ############################################
    # teststeps
    ############################################

        # step 1:
        # action: Verify programming preconditions
        # result: ECU sends positive reply
        result = result and SE31.routinecontrol_requestsid_prog_precond(can_p, stepno=1)

        # step2:
        # action: Change to programming session
        # result: ECU sends positive reply
        result = result and SE10.diagnostic_session_control_mode2(can_p, stepno=2)

        # step 3:
        # action: Verify service 19 is disabled in PBL session
        # result: ECU sends positive reply
        result = result and step_3(can_p)

        # step4:
        # action: Hard Reset
        # result: ECU sends positive reply
        result = result and SE11.ecu_hardreset(can_p, stepno=4)
        time.sleep(1)

        # step5:
        # action: Verify ECU in Default Session
        # result: ECU sends positive reply
        result = result and SE10.diagnostic_session_control_mode1(can_p, stepno=5)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
