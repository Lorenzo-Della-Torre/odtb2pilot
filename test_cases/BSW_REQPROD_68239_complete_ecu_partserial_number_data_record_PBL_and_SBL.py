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
import odtb_conf
from support_can import SupportCAN, CanParam, CanPayload, CanTestExtra
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

def verify_ecu_partnumbers(can_p,response,did,result):
    '''
    Verify the ECU Part Serial Numbers
    '''
    if did == 'F121' :
        pos = response.find('F121')
        print(pos)
        partnumber = SUTE.pp_partnumber(response[pos+4: pos+18])
        logging.info("Diagnostic  Part Number :%s", partnumber)
        result = result and SUTE.test_message(SC.can_messages[can_p['receive']],teststring='F121')
    elif  did == 'F12A' :
        pos = response.find('F12A')
        partnumber = SUTE.pp_partnumber(response[pos+4: pos+18])
        logging.info("ECU Core Assembly Part Number :%s", partnumber)
        result = result and SUTE.test_message(SC.can_messages[can_p['receive']],teststring='F12A')
    elif  did == 'F12B' :
        pos = response.find('F12B')
        partnumber = SUTE.pp_partnumber(response[pos+4: pos+18])
        logging.info("ECU Delivery Part Number :%s", partnumber)
        result = result and SUTE.test_message(SC.can_messages[can_p['receive']],teststring='F12B')
    elif  did == 'F18C' :
        pos = response.find('F18C')
        partnumber = SUTE.pp_partnumber(response[pos+4: pos+18])
        logging.info("ECU Serial Part Number: %s", partnumber)
        result = result and SUTE.test_message(SC.can_messages[can_p['receive']],teststring='F18C')
    elif  did == 'F122' :
        pos = response.find('F122')
        partnumber = result and SUTE.pp_partnumber(response[pos+4: pos+18])
        logging.info("Diagnostic Part Number: %s",  partnumber)
        result = SUTE.test_message(SC.can_messages[can_p['receive']],teststring='F122')
    elif  did == 'F124' :
        pos = response.find('F124')
        partnumber = SUTE.pp_partnumber(response[pos+4: pos+18])
        logging.info( "Software Part Number: %s", partnumber)
        result = result and SUTE.test_message(SC.can_messages[can_p['receive']],teststring='F124')
    else :
        pos = response.find('F125')
        partnumber = SUTE.pp_partnumber(response[pos+4: pos+18])
        logging.info("Software  Part Number: %s", partnumber)
        result = result and SUTE.test_message(SC.can_messages[can_p['receive']],teststring='F125')
    return result

def step(can_p,did, stepno):
    '''
    Read Complete ECU Part Serial Number data record
    '''
    cpay : CanPayload = {
        "payload": S_CARCOM.can_m_send( "ReadDataByIdentifier", b'\xED\xA0', b""),
        "extra": b'',
    }
    etp : CanTestExtra = {
        "step_no": stepno,
        "purpose": f' ECU part/serial number in PBL: {did}',
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1,
    }
    result = SUTE.teststep(can_p,cpay, etp)
    response =  SC.can_messages[can_p['receive']][0][2]
    logging.info("Complete ECU Serial Part Number in PBL : %s",\
                            SC.can_messages[can_p["receive"]][0][2])
    result = verify_ecu_partnumbers(can_p, response, did,result)
    return  result

def step_sbl(can_p,did,stepno):
    '''
    ReadDataByIdentifier {did} and verify the response with partnumberts
    '''
    cpay : CanPayload = {"payload" : S_CARCOM.can_m_send("ReadDataByIdentifier",
                                                             b'\xED\xA0', b''),
                        "extra" : ''
    }
    etp: CanTestExtra = {"step_no": stepno,
                        "purpose" : f' ECU part/serial number in SBL: {did}',
                        "timeout" : 1,
                        "min_no_messages" : -1,
                        "max_no_messages" : -1
    }
    result = SUTE.teststep(can_p, cpay, etp)
    res = SC.can_messages[can_p['receive']][0][2]
    logging.info("Complete ECU Serial Part Number in SBL : %s",\
                            SC.can_messages[can_p["receive"]][0][2])
    result = verify_ecu_partnumbers(can_p, res, did,result )
    return result

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
    timeout = 200
    result = PREC.precondition(can_p, timeout)
    if result:
    ############################################
    # teststeps
    ############################################
        # step 1:
        # action: Change session to Programming
        # result: BECM reply positively
        result = result and SE10.diagnostic_session_control_mode2(can_p,1)
        time.sleep(2)
        # step 2 :
        # action: Verify Programming Session
        # result: BECM reply positively
        result = result and SE22.verify_pbl_session(can_p,2)
        # step 3:
        # action: Request Diagnostic Part Number
        # result: BECM reply positively
        result = result and step(can_p, 'F121',stepno=3)
        # step 4:
        # action: Request ECU Core Assembly Part Number
        # result: BECM reply positively
        result = result and step(can_p, 'F12A',stepno=4)
        # step 5:
        # action: Request Delivery Core Assembly Part Number
        # result: BECM reply positively
        result = result and step(can_p, 'F12B',stepno=5)
        # step 6:
        # action: Request ECU Serial Number
        # result: BECM reply positively
        result = result and step(can_p, 'F18C',stepno=6)
        # step 7:
        # action: Request ECU Software Part Number
        # result: BECM reply positively
        result = result and step(can_p, 'F125',stepno=7)
        # step 8:
        # action: Change ECU to Default Session
        # result: BECM reply positively
        result = result and SE10.diagnostic_session_control_mode1(can_p,8)
        # step 9:
        # action: Active DL and SBL
        # result: BECM reply positively
        result = result and SSBL.sbl_activation(can_p,9,"DL and activate SBL")
        # step 10:
        # action: Verify SBL session
        # result: BECM reply positively
        result = result and SE22.verify_sbl_session(can_p,10)
        # step 11:
        # action: Request Diagnostic Part Number
        # result: BECM reply positively
        result = result and step_sbl(can_p,'F122',stepno=11)
        # step 12:
        # action: Request ECU Core Assembly Part Number
        # result: BECM reply positively
        result = result and step_sbl(can_p,'F12A',stepno=12)
        # step 13:
        # action: Request Delivery Core Assembly Part Number
        # result: BECM reply positively
        result = result and step_sbl(can_p,'F12B',stepno=13)
        # step 14:
        # action: Request ECU Serial Number
        # result: BECM reply positively
        result = result and step_sbl(can_p,'F18C',stepno=14)
        # step 15:
        # action: Request Software Part Number
        # result: BECM reply positively
        result = result and step_sbl(can_p,'F124',stepno=15)
        # step 16:
        # action: Change to Default Session
        # result: BECM reply positively
        result = result and SE10.diagnostic_session_control_mode1(can_p,16)
    ############################################
    # postCondition
    ############################################
    POST.postcondition(can_p, starttime, result)

if __name__ == "__main__":
    run()
