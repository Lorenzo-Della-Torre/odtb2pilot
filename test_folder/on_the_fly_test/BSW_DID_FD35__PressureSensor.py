"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

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

"""The Python implementation of the gRPC route guide client."""

import time
from datetime import datetime
import sys
import logging
import inspect

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
from supportfunctions.support_file_io import SupportFileIO

SIO = SupportFileIO
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

def step_1(can_p):
    """
    Teststep 1: Request read pressure sensor (DID FD35)
    """
    step_no = 1
    did_pressure = b'\xFD\x35'
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), 'did_pressure')
    did_pressure_new = SIO.extract_parameter_yml(str(inspect.stack()[0][3]), 'did_pressure')
    # don't set empty value if no replacement was found:
    if did_pressure_new:
        if type(did_pressure) != type(did_pressure_new):# pylint: disable=unidiomatic-typecheck
            did_pressure = eval(did_pressure_new)# pylint: disable=eval-used
        else:
            did_pressure = did_pressure_new
    else:
        logging.info("Step%s did_pressure_new is empty. Discard.", step_no)
    logging.info("Step%s: did_pressure after YML: %s", step_no, did_pressure.hex())

    result, pressure = SE22.read_did_pressure_sensor(can_p, did_pressure, b'', '1')
    logging.info("Pressure returned: %s \n", pressure)
    logging.info("Step%s, received frames: %s", step_no, SC.can_frames[can_p["receive"]])
    logging.info("Step%s, received messages: %s", step_no, SC.can_messages[can_p["receive"]])
    return result


def run():
    """
    Run
    """
    #logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.DEBUG)
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

    #can_p: CanParam = {
    #    "netstub" : SC.connect_to_signalbroker(ODTB_conf.ODTB2_DUT, ODTB_conf.ODTB2_PORT),\
    #    "send" : "HvbmdpToHvbmUdsDiagRequestFrame",\
    #    "receive" : "HvbmToHvbmdpUdsDiagResponseFrame",\
    #    "namespace" : SC.nspace_lookup("Front1CANCfg0")
    #    }

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
    #result = PREC.precondition_spa2(can_p, timeout)


    ############################################
    # teststeps
    ############################################

    # step1:
    # action:  Request read pressure sensor (DID FD35)
    # result:
    result = result and step_1(can_p)

    ############################################
    # postCondition
    ############################################
    POST.postcondition(can_p, starttime, result)


if __name__ == '__main__':
    run()
