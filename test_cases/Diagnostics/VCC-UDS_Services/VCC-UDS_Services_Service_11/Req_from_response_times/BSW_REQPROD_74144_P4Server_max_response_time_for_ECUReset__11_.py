# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-06-03
# version:  1.1
# reqprod:  74114

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

from support_precondition import SupportPrecondition
from support_postcondition import SupportPostcondition

SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
PREC = SupportPrecondition()
POST = SupportPostcondition()

def step_1(can_par):
    """
    Request session change to Mode1
    """
    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("DiagnosticSessionControl", b'\x01', b''),\
                        "extra" : ''
                        }
    etp: CanTestExtra = {"step_no" : 1,\
                         "purpose" : "get P2_server_max",\
                         "timeout" : 1,\
                         "min_no_messages" : 1,\
                         "max_no_messages" : 1
                         }
    result = SUTE.teststep(can_par, cpay, etp)
    p2_server_max = int(SC.can_messages[can_par["receive"]][0][2][8:10], 16)
    return result, p2_server_max

def step_2(can_par):
    """
    ecu_hardreset
    """
    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ECUResetHardReset", b'', b''),\
                        "extra" : ''
                        }
    etp: CanTestExtra = {"step_no" : 2,\
                         "purpose" : "ECU Reset",\
                         "timeout" : 1,\
                         "min_no_messages" : -1,\
                         "max_no_messages" : -1
                         }
    t_1 = time.time()
    result = SUTE.teststep(can_par, cpay, etp)
    result = result and SUTE.test_message(SC.can_messages[can_par["receive"]], teststring='025101')
    t_2 = SC.can_messages[can_par["receive"]][0][0]
    time.sleep(1)
    return result, t_1, t_2

def step_3(t_1, t_2, p2_server_max):
    """
    Verify (time receive message – time sending request) less than P2_server_max
    """
    stepno = 3
    purpose = "Verify (time receive message – time sending request) less than P2_server_max"
    SUTE.print_test_purpose(stepno, purpose)
    jitter_testenv = 10

    result = (p2_server_max + jitter_testenv)/1000 > (t_2 - t_1)
    logging.info("T difference(s): %s \n", float((p2_server_max + 10)/1000 - (t_2 - t_1)))
    logging.info("Step %s teststatus: %s \n", stepno, result)
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
        "receive" : "BecmToVcu1Front1DiagResFrame",\
        "namespace" : SC.nspace_lookup("Front1CANCfg0")
        }

    logging.info("Testcase start: %s", datetime.now())
    starttime = time.time()
    logging.info("Time: %s \n", time.time())

    ############################################
    # precondition
    ############################################
    timeout = 30
    result = PREC.precondition(can_par, timeout)

    if result:
    ############################################
    # teststeps
    ############################################
        # step 1:
        # action:Change to default session
        # result: positive reply with Parameters P2_server_max and P2*_server_max
        result, p2_server_max = result and step_1(can_par)

        # step 2:
        # action: ECU Reset
        # result:
        result, t_1, t_2 = result and step_2(can_par)

        # step 3:
        # action: Wait for the response message
        # result: (time receive message – time sending request) less than P2_server_max
        result = result and step_3(t_1, t_2, p2_server_max)

    ############################################
    # postCondition
    ############################################

    result = POST.postcondition(can_par, starttime, result)

if __name__ == '__main__':
    run()
