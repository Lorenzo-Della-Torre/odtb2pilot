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
# author:   G-HERMA6 (Gunnar Hermansson)
# date:     2020-10-21
# version:  2.0
# reqprod:  none


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

from datetime import datetime
import logging
import sys
import time

import odtb_conf
from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition
from supportfunctions.support_can import SupportCAN, CanParam
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_test_odtb2 import SupportTestODTB2

from hilding.dut import Dut

PREC = SupportPrecondition()
POST = SupportPostcondition()
SC = SupportCAN()
SIO = SupportFileIO()
SUTE = SupportTestODTB2()


def step_1(can_p, can_receive, can_namespace):
    """
    Teststep 1: register RMS signal
    """
    stepno = 1
    purpose = "register RMS signal"
    SUTE.print_test_purpose(stepno, purpose)

    can_p: CanParam = {
        "netstub" : can_p['netstub'],
        "send" : can_p['send'],
        "receive" : can_receive,
        "namespace" : can_namespace,
    }
    SIO.parameter_adopt_teststep(can_p)

    SC.subscribe_signal(can_p, timeout=60)
    time.sleep(1)

    result = SC.update_can_messages(can_receive)
    logging.info("All CAN messages updated")

    time.sleep(10)
    logging.info("Step %s: %s messages received", stepno, len(SC.can_messages[can_receive]))
    logging.info("Step %s: messages: %s", stepno, SC.can_messages[can_receive])
    logging.info("Step %s: %s frames received", stepno, len(SC.can_frames[can_receive]))
    logging.info("Step %s: frames: %s", stepno, SC.can_frames[can_receive])

    result = result and len(SC.can_frames[can_receive]) > 10

    logging.info("Step %s teststatus: %s", stepno, result)

    return result


def run():
    """
    Run - Call other functions from here
    """
    dut = Dut()
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

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
    SIO.parameter_adopt_teststep(can_p)

    logging.info("Testcase start: %s", datetime.now())
    starttime = time.time()
    logging.info("Time: %s \n", time.time())

    ############################################
    # precondition
    ############################################
    result = PREC.precondition(can_p, timeout=60)

    if result:
        ############################################
        # teststeps
        ############################################
        # step 1:
        # action: Register RMS message
        # result: BECM send requested signals
        result = result and step_1(can_p,
                                   can_receive="BecmRmsCanFr03",
                                   can_namespace=SC.nspace_lookup("BecmRmsCanFr1"))

    ############################################
    # postCondition
    ############################################
    POST.postcondition(can_p, starttime, result)


if __name__ == '__main__':
    run()
