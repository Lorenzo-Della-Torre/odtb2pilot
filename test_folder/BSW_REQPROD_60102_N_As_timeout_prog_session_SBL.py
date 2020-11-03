# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-06-25
# version:  1.0
# reqprod:  60102

# author:   HWEILER (Hans-Klaus Weiler)
# date:     2020-08-04
# version:  1.1
# changes:  update support function, YML

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

import parameters.odtb_conf

from supportfunctions.support_can import SupportCAN, CanParam, CanMFParam, CanPayload, CanTestExtra
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO

from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service11 import SupportService11
from supportfunctions.support_service10 import SupportService10
from supportfunctions.support_service31 import SupportService31
from supportfunctions.support_service34 import SupportService34
from supportfunctions.support_sec_acc import SupportSecurityAccess
from supportfunctions.support_SBL import SupportSBL


SSA = SupportSecurityAccess()
SSBL = SupportSBL()
SIO = SupportFileIO
SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
PREC = SupportPrecondition()
POST = SupportPostcondition()
SE11 = SupportService11()
SE10 = SupportService10()
SE22 = SupportService22()
SE31 = SupportService31()
SE34 = SupportService34()
def step_2():
    """
    Teststep 2: Read VBF files for ESS file (1st Logical Block)
    """
    stepno = 2
    purpose = "1st files reading"

    SUTE.print_test_purpose(stepno, purpose)
    #ess_vbf_invalid = "./VBF_Reqprod/REQ_397438_32290520AA_SPA2_ESS_used_as_invalid.vbf"
    ess_vbf_invalid = "./VBF_Reqprod/REQ_60102_ess_different_project.vbf"
    SSBL.get_ess_filename()
    _, vbf_header, _, _ = SSBL.read_vbf_file(ess_vbf_invalid)
    SSBL.vbf_header_convert(vbf_header)
    #logging.info(erase)
    return vbf_header

def step_3(can_p):
    """
    Teststep 3: set FC delay > 1000 ms
    """
    stepno = 3
    purpose = "set FC delay > 1000 ms"
    result = True
    SUTE.print_test_purpose(stepno, purpose)

    #change Control Frame parameters
    can_mf: CanMFParam = {
        "block_size": 0,
        "separation_time": 0,
        "frame_control_delay": 1050,
        "frame_control_flag": 48,
        "frame_control_auto": False
        }
    SC.change_mf_fc(can_p["send"], can_mf)
    return result

def step_4(can_p, vbf_header):
    """
    Teststep 4: Send MF request
    """
    stepno = 4

    #Take first element of list to erase
    erase_el = vbf_header["erase"][0]
    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("RoutineControlRequestSID",\
                                                         b'\xFF\x00' +\
                                                         erase_el[0].to_bytes(4, byteorder='big') +\
                                                         erase_el[1].to_bytes(4, byteorder='big'),
                                                         b'\x01'),\
                        "extra" : ''
                       }
    etp: CanTestExtra = {"step_no": stepno,\
                         "purpose" : "Send MF request",\
                         "timeout" : 1,\
                         "min_no_messages" : -1,\
                         "max_no_messages" : -1
                        }
    #start flash erase, may take long to erase
    result = SUTE.teststep(can_p, cpay, etp)

    logging.info("Result after request: %s", result)
    #test if frames contain all the IDs expected
    logging.info("Test if request timed out:")
    logging.debug("Frames received: %s", SC.can_frames[can_p["receive"]])
    logging.info("Messages received: %s", SC.can_messages[can_p["receive"]])

    if not len(SC.can_messages[can_p["receive"]]) == 0:
        logging.info("Len Mess received: %s", len(SC.can_messages[can_p["receive"]]))

    logging.info("Step %s: Result teststep: %s \n", stepno, result)
    return result

def step_5(can_p):
    """
    Teststep 5: send CF with with CF delay < 1000 ms
    """
    stepno = 5
    purpose = "set FC delay < 1000 ms"
    result = True
    SUTE.print_test_purpose(stepno, purpose)

    #change Control Frame parameters
    can_mf: CanMFParam = {
        "block_size": 0,
        "separation_time": 0,
        "frame_control_delay": 950,
        "frame_control_flag": 48,
        "frame_control_auto": False
        }
    SC.change_mf_fc(can_p["send"], can_mf)
    return result

def step_6(can_p, vbf_header):
    """
    Teststep 6: Send first frame of a multi frame request
    """

    # routine should give negative result as fault ESS was used
    result = not SE31.routinecontrol_requestsid_flash_erase(can_p, vbf_header, stepno=6)

    result = SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='7F3131')
    logging.info('%s', SUTE.pp_decode_7f_response(SC.can_frames[can_p["receive"]][0][2]))
    logging.info("Result after request: %s", result)
    return result


def step_7(can_p):
    """
    Teststep 7: verify session SBL
    """
    result = SE22.read_did_eda0(can_p, stepno=7)
    logging.info("Complete Part/serial received: %s", SC.can_messages[can_p["receive"]])

    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]],\
                                          teststring='F122')
    return result

def step_9(can_p):
    """
    Teststep 9: set back frame_control_delay to default
    """
    stepno = 9
    purpose = "set back frame_control_delay to default"

    can_mf: CanMFParam = {
        "block_size": 0,
        "separation_time": 0,
        "frame_control_delay": 0,
        "frame_control_flag": 48,
        "frame_control_auto": False
        }

    SUTE.print_test_purpose(stepno, purpose)
    SC.change_mf_fc(can_p["send"], can_mf)

def step_10(can_p):
    """
    Teststep 10: verify session SBL
    """
    result = SE22.read_did_eda0(can_p, stepno=11)
    logging.info("Complete Part/serial received: %s", SC.can_messages[can_p["receive"]])

    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]],\
                                          teststring='F122')
    return result

def run():
    """
    Run - Call other functions from here
    """
    #logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.DEBUG)
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
    # read VBF param when testscript is s started, if empty take default param
    SSBL.get_vbf_files()
    timeout = 180
    result = PREC.precondition(can_p, timeout)

    if result:
    ############################################
    # teststeps
    ############################################
        # step1:
        # action: Download and activate SBL
        # result: True, if all went fine
        result = result and SSBL.sbl_activation(can_p, 1, "DL and activate SBL")
        time.sleep(1)

        # step2:
        # action: Read invalid ESS file, for not erasing part of flash
        # result:
        vbf_header = step_2()

        # step3:
        # action: set FC delay > 1000 ms
        # result:
        result = result and step_3(can_p)

        # step4:
        # action: Send multi frame request DIDs
        # result: No reply to request as timeout
        result = result and step_4(can_p, vbf_header)

        # step5:
        # action: set FC delay < 1000 ms
        # result:
        result = result and step_5(can_p)

        # step6:
        # action: Send multi frame request DIDs
        # result: Reply to request as no timeout
        result = result and step_6(can_p, vbf_header)

        # step7:
        # action: Verify SBL session still active
        # result:
        result = result and step_7(can_p)

        # step10:
        # action: restore FC timing
        # result:
        step_9(can_p)

        # step10:
        # action: verify SBL session still active
        # result:
        result = result and step_10(can_p)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
