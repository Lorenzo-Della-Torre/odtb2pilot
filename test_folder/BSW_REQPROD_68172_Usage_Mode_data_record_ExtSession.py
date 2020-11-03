# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   J-ASSAR1 (Joel Assarsson)
# date:     2020-10-23
# version:  1.0
# reqprod:  68172
#
# inspired by https://grpc.io/docs/tutorials/basic/python.html
#
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
import inspect

from datetime               import datetime
import sys
import logging

import parameters.odtb_conf as odtb_conf
from supportfunctions.support_can            import SupportCAN, CanParam, CanTestExtra, CanPayload
from supportfunctions.support_test_odtb2     import SupportTestODTB2
from supportfunctions.support_carcom         import SupportCARCOM
from supportfunctions.support_file_io        import SupportFileIO
from supportfunctions.support_precondition   import SupportPrecondition
from supportfunctions.support_postcondition  import SupportPostcondition
from supportfunctions.support_service10      import SupportService10
from supportfunctions.support_service22      import SupportService22

SIO         = SupportFileIO
SC          = SupportCAN()
SUTE        = SupportTestODTB2()
SC_CARCOM   = SupportCARCOM()
PREC        = SupportPrecondition()
POST        = SupportPostcondition()
SE10        = SupportService10()
SE22        = SupportService22()


def step_2(can_p):
    """
    Step 2: Send ReadDataByIdentifier(0xDD0A) and verify that ECU replies with correct DID.
    """
    etp: CanTestExtra = {
        "step_no": 2,
        "purpose" : "ReadDataByIdentifier(0xDD0A) and verify answer",
        "timeout" : 1,
        "min_no_messages" : -1,
        "max_no_messages" : -1
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                        b'\xDD\x0A',
                                        b''),
        "extra": ''
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)

    result = SUTE.teststep(can_p, cpay, etp)
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='DD0A')
    logging.info("ReadDataByIdentifier(0xDD0A): %s", SC.can_messages[can_p["receive"]][0][2])
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
    timeout = 40
    result = PREC.precondition(can_p, timeout)

    if result:
        ############################################
        # teststeps
        ############################################
        # step 1:
        # action: Change to Extended session
        # result: BECM reports mode
        result = SE10.diagnostic_session_control_mode3(can_p, stepno=1)

        # step 2:
        # action: Send ReadDataByIdentifier(0xDD0A)
        # result: ECU send requested DIDs
        result = result and step_2(can_p)

        # step 3:
        # action: Verify current session
        # result: BECM reports extended session
        result = result and SE22.read_did_f186(can_p, dsession=b'\x03', stepno=3)

        # step 4:
        # action: Change to Default session
        # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode1(can_p, stepno=4)

    ############################################
    # postCondition
    ############################################
    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
