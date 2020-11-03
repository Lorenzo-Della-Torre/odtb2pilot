# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2019-05-16
# version:  1.0
# reqprod:  76670
#
# author:   t-kumara(Tanujaluru)
# date:     2020-10-08
# version:  1.1
# reqprod:  update for YML Support
#
## author:  J-ASSAR1 (Joel Assarsson)
# date:     2020-10-16
# version:  1.2
# reqprod:  76519
#
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
from supportfunctions.support_can import SupportCAN, CanParam, CanTestExtra, CanPayload
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition
from supportfunctions.support_service10 import SupportService10
from supportfunctions.support_service22 import SupportService22

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
    teststep 2: Get Generic Snapshot by DTC Number for “All groups” (‘FFFFFF’)
    """

    cpay: CanPayload = {
        "payload" : SC_CARCOM.can_m_send("ReadGenericInformationReportGenericSnapshotByDTCNumber",
                                                         b'\xFF\xFF\xFF',
                                                         b'\xFF'),
        "extra" : ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {"step_no": 2,
                         "purpose" : "Get Generic Snapshot by DTC Number for “All groups” "
                                    +"(‘FFFFFF’)",
                         "timeout" : 2,
                         "min_no_messages" : -1,
                         "max_no_messages" : -1
                        }

    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)
    result = SUTE.teststep(can_p, cpay, etp)
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='EF04')
    return result


def step_3(can_p):
    """
    teststep 3:Get Generic Snapshot by DTC Number for “All groups”
    (‘FFFFFF’) and suppressPosRspMsgIndicationBit = True
    """
    cpay: CanPayload = {
        "payload" : SC_CARCOM.can_m_send(   \
                            "ReadGenericInformationReportGenericSnapshotByDTCNumber(84)",
                            b'\xFF\xFF\xFF',\
                            b'\xFF'),
         "extra" : ''
         }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {"step_no": 3,
                         "purpose" : "Get Generic Snapshot by DTC Number for “All groups”"\
                                    + "(‘FFFFFF’) and suppressPosRspMsgIndicationBit = True",
                         "timeout" : 2,
                         "min_no_messages" : 0,
                         "max_no_messages" : 0
                        }

    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)
    result =  SUTE.teststep(can_p, cpay, etp)
    return result

def step_4(can_p):
    """
    teststep 3:Verify Extended session
    """
    cpay: CanPayload = {
        "payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier", b'\xF1\x86', b''),
        "extra" : b'\x03'
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {"step_no": 4,
                         "purpose" : "Verify Extended session",
                         "timeout" : 1,
                         "min_no_messages" : 1,
                         "max_no_messages" : 1
                        }

    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)
    result = SUTE.teststep(can_p, cpay, etp)
    return result

def run():
    """
    Run - Call other functions from here
    """
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)
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
    timeout = 60
    result = PREC.precondition(can_p, timeout)

    if result:

        ############################################
        # teststeps
        ############################################
        # step 1:
        # action: change to extended session
        # result: BECM report Mode
        result = result and SE10.diagnostic_session_control_mode3(can_p,1)

        # step 2:
        # action: Request report Generic Snapshot By DTC Number
        # result: BECM reply positively
        result = result and step_2(can_p)

        # step 3:
        # action: Get Generic Snapshot by DTC Number for “All groups” (‘FFFFFF’)
        # result: BECM  -NO reply
        result = result and step_3(can_p)

        # step 4:
        # action: Verify Extended session active
        # result: BECM sends active mode
        result = result and step_4(can_p)

        # step 5:
        # action: Change BECM to Default
        # result: BECM sends active Mode
        result = result and SE10.diagnostic_session_control_mode1(can_p,4)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
