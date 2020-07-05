# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-07-05
# version:  1.1
# reqprod:  74450

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
from support_can import SupportCAN, CanParam, CanTestExtra
from support_test_odtb2 import SupportTestODTB2
from support_carcom import SupportCARCOM
from support_file_io import SupportFileIO

from support_precondition import SupportPrecondition
from support_postcondition import SupportPostcondition
from support_service10 import SupportService10
from support_service22 import SupportService22

SIO = SupportFileIO
SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
PREC = SupportPrecondition()
POST = SupportPostcondition()
SE10 = SupportService10()
SE22 = SupportService22()

def step_1():
    """
    Teststep 1: send signal vehicle velocity < 3km/h
    """
    stepno = 1
    purpose = "send signal vehicle velocity < 3km/h"
    SUTE.print_test_purpose(stepno, purpose)

    # where to connect to signal_broker
    can_par_ex: CanParam = {
        "netstub" : SC.connect_to_signalbroker(ODTB_conf.ODTB2_DUT, ODTB_conf.ODTB2_PORT),
        "name" : 'VehSpdLgtSafe',
        "send" : True,
        "id" : "VCU1Front1Fr06",
        "intervall" : 0.015,
        "frame" : b'\x80\xd5\x00\x00\x00\x00\x00\x00',
        "nspace" : "Front1CANCfg0"
    }
    #SIO.extract_parameter_yml("step_{}".format(stepno), can_par)
    SC.start_periodic(can_par_ex["netstub"], can_par_ex)

def step_4():
    """
    Teststep 4: send signal vehicle velocity > 3km/h
    """
    stepno = 4
    purpose = "send signal vehicle velocity > 3km/h"
    SUTE.print_test_purpose(stepno, purpose)

    # where to connect to signal_broker
    can_par_ex_2: CanParam = {
        "name" : 'VehSpdLgtSafe',
        "send" : True,
        "id" : "VCU1Front1Fr06",
        "intervall" : 0.015,
        "frame" : b'\x80\xd6\x00\x00\x00\x00\x00\x00',
        "nspace" : "Front1CANCfg0"
    }
    #SIO.extract_parameter_yml("step_{}".format(stepno), can_par)
    SC.set_periodic(can_par_ex_2)

def step_5(can_par):
    """
    Teststep 5: Request session change to Mode2
    """
    etp: CanTestExtra = {
        "step_no" : 5,
        "purpose" : "Request session change to Mode2",
        "timeout" : 1,
        "min_no_messages" : -1,
        "max_no_messages" : -1
    }
    #SIO.extract_parameter_yml("step_{}".format(stepno), etp)
    SE10.diagnostic_session_control(can_par, etp, b'\x02')
    result = SE10.diagnostic_session_control(can_par, etp, b'\x02')
    result = result and SUTE.test_message(SC.can_messages[can_par["receive"]], teststring='7F1022')
    logging.info(SUTE.pp_decode_7f_response(SC.can_frames[can_par["receive"]][0][2]))

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
        "netstub" : SC.connect_to_signalbroker(ODTB_conf.ODTB2_DUT, ODTB_conf.ODTB2_PORT),
        "send" : "Vcu1ToBecmFront1DiagReqFrame",
        "receive" : "BecmToVcu1Front1DiagResFrame",
        "namespace" : SC.nspace_lookup("Front1CANCfg0")
    }
    SIO.extract_parameter_yml("main", can_par)
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
    # step1:
    # action:
    # result: BECM reports mode
        step_1()

    # step2:
    # action: # Change to programming session
    # result: BECM reports mode
        SE10.diagnostic_session_control_mode2(can_par, 2)
        result = result and SE10.diagnostic_session_control_mode2(can_par, 2)

    # step3:
    # action: # Change to default session
    # result: BECM reports mode
        result = result and SE10.diagnostic_session_control_mode1(can_par, 3)

    # step4:
    # action:
    # result: BECM reports mode
        step_4()
        time.sleep(2)

    # step5:
    # action:
    # result: BECM reports mode
        result = result and step_5(can_par)

    ############################################
    # postCondition
    ############################################

    result = POST.postcondition(can_par, starttime, result)

if __name__ == '__main__':
    run()
