# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-06-05
# version:  1.1
# reqprod:  397438

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

import ODTB_conf
from support_can import SupportCAN, CanParam #, CanTestExtra
from support_test_odtb2 import SupportTestODTB2
from support_SBL import SupportSBL
from support_sec_acc import SupportSecurityAccess
from support_carcom import SupportCARCOM

from support_precondition import SupportPrecondition
from support_postcondition import SupportPostcondition
from support_service10 import SupportService10
from support_service22 import SupportService22
from support_service3e import SupportService3e

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
    #logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.DEBUG)
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)
    # start logging
    # to be implemented

    can_p: CanParam = {
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

    # read VBF param when testscript is s started, if empty take default param
    #SSBL.get_vbf_files()
    timeout = 60
    result = PREC.precondition(can_p, timeout)


    ############################################
    # teststeps
    ############################################

    # step1:
    # action:  Request read pressure sensor (DID FD35)
    # result:
    logging.info("Step 1: Read Pressure Sensor.")
    result2, pressure = SE22.read_did_fd35_pressure_sensor(can_p, b'', '1')
    logging.info("Pressure returned: %s \n", pressure)
    result = result2 and result

    ############################################
    # postCondition
    ############################################
    POST.postcondition(can_p, starttime, result)


if __name__ == '__main__':
    run()
