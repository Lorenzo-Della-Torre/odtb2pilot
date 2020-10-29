# Testscript ODTB2 MEPII
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

"""The Python implementation of the gRPC route guide client."""

from datetime import datetime
import logging
import inspect
import sys
import time

from support_precondition import SupportPrecondition
from support_postcondition import SupportPostcondition
from support_can import SupportCAN, CanParam
from support_file_io import SupportFileIO
from support_test_odtb2 import SupportTestODTB2

import odtb_conf

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
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), can_p)

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
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

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