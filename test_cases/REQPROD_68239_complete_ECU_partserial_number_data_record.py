# Testscript ODTB2 MEPII
# project: BECM basetech MEPII
# author:  T-kumara (Tanuj Kumar Aluru)
# date:    2020-10-26
# version:  1.0
# reqprod:  62839

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
import glob
import odtb_conf
from support_can import SupportCAN, CanParam,CanPayload, CanTestExtra
from support_test_odtb2 import SupportTestODTB2
from support_carcom import SupportCARCOM
from support_file_io import SupportFileIO
from support_SBL import SupportSBL
from support_precondition import SupportPrecondition
from support_postcondition import SupportPostcondition
from support_service22 import SupportService22
from support_service10 import SupportService10

SIO = SupportFileIO
SC = SupportCAN()
S_CARCOM = SupportCARCOM()
SUTE = SupportTestODTB2()
SSBL = SupportSBL()

PREC = SupportPrecondition()
POST = SupportPostcondition()
SE22 = SupportService22()
SE10 = SupportService10()

def verify_ecu_partnumbers(can_p,dict,did,result):
    '''
    Verify the ECU Part Serial Numbers
    '''
    if did == 'F120' :
        logging.info("Diagnostic Part Number :%s", dict[did.lower()])
        result = result and SUTE.test_message(SC.can_messages[can_p['receive']],teststring='F120')
    elif  did == 'F12A' :
        logging.info("ECU Core Part Number : %s", dict[did.lower()])
        result = result and SUTE.test_message(SC.can_messages[can_p['receive']],teststring='F12A')
    elif  did == 'F12B' :
        logging.info("ECU Delivery Assembly Part Number : %s", dict[did.lower()])
        result = result and SUTE.test_message(SC.can_messages[can_p['receive']],teststring='F12B')
    elif  did == 'F18C' :
        logging.info("ECU  Serial Number :%s",dict["serial"])
        result = result and SUTE.test_message(SC.can_messages[can_p['receive']],teststring='F18C')
    return result

def step_1(can_p,did,stepno):
    '''
    Read Complete ECU Part Serial Number data record
    '''
    cpay: CanPayload = {
        "payload": S_CARCOM.can_m_send( "ReadDataByIdentifier", b'\xED\xA0', b""),
        "extra": b'',
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)

    etp: CanTestExtra = {
        "step_no": stepno,
        "purpose": "Request EDA0 - Complete ECU part/serial number ",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1,
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)
    result = SUTE.teststep(can_p,cpay, etp)
    dic = SUTE.combined_did_eda0_becm_mode1_mode3(SC.can_messages[can_p['receive']][0][2])
    result = verify_ecu_partnumbers(can_p,dic,did,result )
    return  result

def step_6(can_p):
    '''
    Verify F12E identifier
    '''
    cpay: CanPayload = {
        "payload": S_CARCOM.can_m_send( "ReadDataByIdentifier", b'\xED\xA0', b""),
        "extra": b'',
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)

    etp: CanTestExtra = {
        "step_no": 6,
        "purpose": "Request EDA0 - Complete ECU part/serial number ",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1,
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)
    result = SUTE.teststep(can_p,cpay, etp)
    message = SC.can_messages[can_p['receive']][0][2]
    f12e_dict = SUTE.pp_did_f12e(message, title='')
    logging.info("Software part Number :%s",f12e_dict)
    result = result and SUTE.test_message(SC.can_messages[can_p['receive']], teststring='F12E')
    return  result

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
    # read VBF param when testscript is s started, if empty take default param
    SSBL.get_vbf_files()
    timeout = 60
    result = PREC.precondition(can_p, timeout)
    if result:
    ############################################
    # teststeps
    ############################################

        # step 1:
        # action: Request 0xF120 identifier
        # result: BECM reply positively
        result = result and step_1(can_p,"F120", stepno=1)

        # step 3:
        # action: Request 0xF12A identifier
        # result: BECM reply positively
        result = result and step_1(can_p,"F12A", stepno=2)

        # step 4:
        # action: Request 0XF12B identifier
        # result: BECM reply positively
        result = result and step_1(can_p,"F12B", stepno=3)

        # step 4:
        # action: Request 0xF18C identifier
        # result: BECM reply positively
        result = result and step_1(can_p,"F18C", stepno=4)

        # step 5:
        # action: Request EDA0 identifier
        # result: BECM reply positively
        result = result and step_6(can_p)

    ############################################
    # postCondition
    ############################################
    POST.postcondition(can_p, starttime, result)

if __name__ == "__main__":
    run()
