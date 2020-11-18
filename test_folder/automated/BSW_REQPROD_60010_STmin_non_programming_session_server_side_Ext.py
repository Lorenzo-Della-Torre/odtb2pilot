# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-08-21
# version:  1.0
# reqprod:  60011

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

import parameters.odtb_conf as odtb_conf

from supportfunctions.support_can import SupportCAN, CanParam, CanPayload, CanTestExtra
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO

from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service10 import SupportService10
from supportfunctions.support_sec_acc import SupportSecurityAccess

SSA = SupportSecurityAccess()
SIO = SupportFileIO
SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
PREC = SupportPrecondition()
POST = SupportPostcondition()
SE10 = SupportService10()
SE22 = SupportService22()

def step_2(can_p):
    """
    Teststep 2: Send MF and verify Server reply with CTS with correct ST
    """
    result = True
    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                         b'\xDD\x02\xDD\x0A\xDD\x0C\x49\x47', b''),
                        "extra" : ''
                       }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)

    etp: CanTestExtra = {"step_no": 2,
                         "purpose": "Send MF and verify Server reply with CTS with correct ST",
                         "timeout": 1,
                         "min_no_messages": -1,
                         "max_no_messages": -1
                        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    logging.info("Control Frame from Server: %s", SC.can_cf_received[can_p["receive"]][0][2])
    logging.info("Separation time is [ms]: %d",
                 int(SC.can_cf_received[can_p["receive"]][0][2][4:6], 16))
    #test if ST is less than 15 ms: get ST from saved Control Frame
    result = result and (int(SC.can_cf_received[can_p["receive"]][0][2][4:6], 16) < 15)
    if int(SC.can_cf_received[can_p["receive"]][0][2][4:6], 16) < 15:
        logging.info("ST is less than 15 ms")
    else:
        logging.info("ST is bigger than 15 ms")
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
        'netstub': SC.connect_to_signalbroker(odtb_conf.ODTB2_DUT, odtb_conf.ODTB2_PORT),
        'send': "Vcu1ToBecmFront1DiagReqFrame",
        'receive': "BecmToVcu1Front1DiagResFrame",
        'namespace': SC.nspace_lookup("Front1CANCfg0")
        }
    #Read YML parameter for current function (get it from stack)
    logging.debug("Read YML for %s", str(inspect.stack()[0][3]))
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), can_p)

    logging.info("Testcase start: %s", datetime.now())
    starttime = time.time()
    logging.info("Time: %s \n", time.time())

    ############################################
    # precondition
    ############################################
    timeout = 30
    result = PREC.precondition(can_p, timeout)

    if result:
    ############################################
    # teststeps
    ############################################
    # step1:
    # action: # Change to extended session
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode3(can_p, 1)

    # step2:
    # action:
    # result:
        result = result and step_2(can_p)

    # step3:
    # action: verify current session
    # result: BECM reports extended session
        result = result and SE22.read_did_f186(can_p, dsession=b'\x03', stepno=3)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
