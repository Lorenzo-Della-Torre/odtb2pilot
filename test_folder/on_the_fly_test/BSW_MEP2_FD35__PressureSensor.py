"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

# Testscript Hilding MEPII
# project:  BECM basetech MEPII
# author:   HWEILER (Hans-Klaus Weiler)
# date:     2020-06-23
# version:  1.0
# reqprod:

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

The Python implementation of the gRPC route guide client.
"""

import time
from datetime import datetime
import sys
import logging

import odtb_conf
from supportfunctions.support_can import SupportCAN, CanParam #, CanTestExtra
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_sec_acc import SupportSecurityAccess
from supportfunctions.support_carcom import SupportCARCOM

from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition
from supportfunctions.support_service10 import SupportService10
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service3e import SupportService3e

from hilding.dut import Dut

SC = SupportCAN()
S_CARCOM = SupportCARCOM()
SUTE = SupportTestODTB2()
SSA = SupportSecurityAccess()
SSBL = SupportSBL()

PREC = SupportPrecondition()
POST = SupportPostcondition()
SE10 = SupportService10()
SE22 = SupportService22()
SE3E = SupportService3e()


def run():
    """
    Run
    """
    dut = Dut()
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.DEBUG)
    #logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)
    # start logging
    # to be implemented

    #can_p: CanParam = {
    #    "netstub" : SC.connect_to_signalbroker(ODTB_conf.ODTB2_DUT, ODTB_conf.ODTB2_PORT),\
    #    "send" : "Vcu1ToBecmFront1DiagReqFrame",\
    #    "receive" : "BecmToVcu1Front1DiagResFrame",\
    #    "namespace" : SC.nspace_lookup("Front1CANCfg0")
    #    }
    # where to connect to signal_broker
    platform=dut.conf.rigs[dut.conf.default_rig]['platform']
    can_p: CanParam = {
        'netstub': SC.connect_to_signalbroker(odtb_conf.ODTB2_DUT, odtb_conf.ODTB2_PORT),
        'system_stub': '',
        'namespace': dut.conf.platforms[platform]['namespace'],
        'netstub_send': SC.connect_to_signalbroker(odtb_conf.ODTB2_DUT, odtb_conf.ODTB2_PORT),
        'system_stub_send': '',
        'namespace_send': dut.conf.platforms[platform]['namespace'],
        'send': dut.conf.platforms[platform]['signal_send'],
        'receive': dut.conf.platforms[platform]['signal_receive'],
        'signal_periodic': dut.conf.platforms[platform]['signal_periodic'],
        'signal_tester_present': dut.conf.platforms[platform]['signal_tester_present'],
        'wakeup_frame': dut.conf.platforms[platform]['wakeup_frame'],
        'protocol': dut.conf.platforms[platform]['protocol'],
        'framelength_max': dut.conf.platforms[platform]['framelength_max'],
        'padding': dut.conf.platforms[platform]['padding']
        }
        #'padding': dut.conf.platforms[platform]['padding'],
        #'clientid': dut.conf.scriptname
        #}
    #SIO.parameter_adopt_teststep(can_p)

    logging.info("Testcase start: %s", datetime.now())
    starttime = time.time()
    logging.info("Time: %s \n", time.time())
    ############################################
    # precondition
    ############################################

    # read VBF param when testscript is s started, if empty take default param
    #SSBL.get_vbf_files()
    timeout = 60
    #result = PREC.precondition(can_p, timeout)
    result = PREC.precondition_spa2(can_p, timeout)


    ############################################
    # teststeps
    ############################################

    # step1:
    # action:  Request read pressure sensor (DID FD35)
    # result:
    logging.info("Step 1: Read Pressure Sensor.")
    result2, pressure = SE22.read_did_fd35_pressure_sensor(can_p, b'', '1')
    logging.info("Pressure returned: %s \n", pressure)
    print("Step1, received frames: ", SC.can_frames[can_p["receive"]])
    print("Step1, received messages: ", SC.can_messages[can_p["receive"]])
    result = result2 and result

    # step2:
    # action:  Request read pressure sensor (DID 4A28)
    # result:
    logging.info("Step 1: Read Pressure Sensor.")
    result2, pressure = SE22.read_did_4a28_pressure_sensor(can_p, b'', '2')
    logging.info("Pressure returned: %s \n", pressure)
    print("Step2, received frames: ", SC.can_frames[can_p["receive"]])
    print("Step2, received messages: ", SC.can_messages[can_p["receive"]])
    result = result2 and result

    ############################################
    # postCondition
    ############################################
    POST.postcondition(can_p, starttime, result)


if __name__ == '__main__':
    run()
