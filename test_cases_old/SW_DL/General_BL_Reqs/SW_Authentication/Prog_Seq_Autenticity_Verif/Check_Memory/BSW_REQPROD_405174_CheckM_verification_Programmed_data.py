# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-02-05
# version:  1.0
# reqprod:  405174

# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-09-21
# version:  1.1
# reqprod:  405174

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
from support_can import SupportCAN, CanParam, CanTestExtra, CanPayload, CanMFParam
from support_test_odtb2 import SupportTestODTB2
from support_carcom import SupportCARCOM
from support_file_io import SupportFileIO
from support_SBL import SupportSBL
from support_sec_acc import SupportSecurityAccess

from support_precondition import SupportPrecondition
from support_postcondition import SupportPostcondition
from support_service10 import SupportService10
from support_service11 import SupportService11
from support_service22 import SupportService22
from support_service31 import SupportService31
from support_service34 import SupportService34


SIO = SupportFileIO
SC = SupportCAN()
S_CARCOM = SupportCARCOM()
SUTE = SupportTestODTB2()
SSBL = SupportSBL()
SSA = SupportSecurityAccess()

PREC = SupportPrecondition()
POST = SupportPostcondition()
SE10 = SupportService10()
SE11 = SupportService11()
SE22 = SupportService22()
SE31 = SupportService31()
SE34 = SupportService34()

def step_3(can_p, vbf_header):
    """
    Teststep 3: 1st Check memory with verification failed
    """
    stepno = 3
    purpose = "1st Check Memory with verification failed"
    #modify the sw signature removing the last two number and replacing with 16 by default
    #Python converted the sw signature to int
    vbf_header["sw_signature_dev"] = int(str(vbf_header["sw_signature_dev"])[:-2]+ '16')

    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), vbf_header["sw_signature_dev"])

    result = SSBL.check_memory(can_p, vbf_header,
                               stepno, purpose)
    result = result and (SSBL.pp_decode_routine_check_memory
                         (SC.can_messages[can_p["receive"]][0][2])
                         == 'The signed data could not be authenticated')
    logging.info(SSBL.pp_decode_routine_check_memory(SC.can_messages[can_p["receive"]][0][2]))
    return result

def step_4(can_p, vbf_header):
    """
    Teststep 4: 2nd Check memory with verification failed
    """
    stepno = 4
    purpose = "2nd Check Memory with verification failed"
    #modify the sw signature removing the last two number and replacing with 14 by default
    #Python converted the sw signature to int
    vbf_header["sw_signature_dev"] = int(str(vbf_header["sw_signature_dev"])[:-2]+ '14')

    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), vbf_header["sw_signature_dev"])

    result = SSBL.check_memory(can_p, vbf_header,
                               stepno, purpose)
    result = result and (SSBL.pp_decode_routine_check_memory
                         (SC.can_messages[can_p["receive"]][0][2])
                         == 'The signed data could not be authenticated')
    logging.info(SSBL.pp_decode_routine_check_memory(SC.can_messages[can_p["receive"]][0][2]))
    return result

def step_5(can_p, vbf_header_original):
    """
    Teststep 5: 3rd Check memory with Negative Response
    """
    # In VBF header sw_signature_dev was stored as hex, Python converts that into int.
    # It has to be converted to bytes to be used as payload
    sw_signature = vbf_header_original['sw_signature_dev'].to_bytes\
                        ((vbf_header_original['sw_signature_dev'].bit_length()+7) // 8, 'big')

    cpay: CanPayload = {"payload" : S_CARCOM.can_m_send("RoutineControlRequestSID",
                                                        b'\x02\x12' + sw_signature, b'\x01'),
                        "extra" : ''
                       }

    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)

    etp: CanTestExtra = {"step_no" : 5,
                         "purpose" : "3rd Check memory with Negative Response",
                         "timeout" : 2,
                         "min_no_messages" : -1,
                         "max_no_messages" : -1
                        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    #change Control Frame parameters
    can_mf: CanMFParam = {
        "block_size": 0,
        "separation_time": 0,
        "frame_control_delay": 0, #no wait
        "frame_control_flag": 48, #continue send
        "frame_control_auto": False
        }

    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), can_mf)

    SC.change_mf_fc(can_p["receive"], can_mf)
    result = SUTE.teststep(can_p, cpay, etp)

    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='7F31')
    logging.info(SUTE.pp_decode_7f_response(SC.can_frames[can_p["receive"]][0][2]))
    return result

def step_7(can_p, vbf_header):
    """
    Teststep 7: 1st Check memory with verification failed
    """
    stepno = 7
    purpose = "1st Check Memory with verification failed"
    #modify the sw signature removing the last two number and replacing with 16 by default
    #Python converted the sw signature to int
    vbf_header["sw_signature_dev"] = int(str(vbf_header["sw_signature_dev"])[:-2]+ '16')

    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), vbf_header["sw_signature_dev"])

    result = SSBL.check_memory(can_p, vbf_header,
                               stepno, purpose)
    result = result and (SSBL.pp_decode_routine_check_memory
                         (SC.can_messages[can_p["receive"]][0][2])
                         == 'The signed data could not be authenticated')
    logging.info(SSBL.pp_decode_routine_check_memory(SC.can_messages[can_p["receive"]][0][2]))
    return result

def step_8(can_p, vbf_header_original):
    """
    Teststep 8: 2nd Check memory with verification positive
    """
    stepno = 8
    purpose = "2nd Check memory with verification positive"
    result = SSBL.check_memory(can_p, vbf_header_original,
                               stepno, purpose)
    result = result and (SSBL.pp_decode_routine_check_memory
                         (SC.can_messages[can_p["receive"]][0][2])
                         == 'The verification is passed')
    logging.info(SSBL.pp_decode_routine_check_memory(SC.can_messages[can_p["receive"]][0][2]))
    return result
'''
def step_10(can_p):
    """
    Teststep 10: Check the Complete and compatible Routine return Complete Not Compatible
    """
    etp: CanTestExtra = {
        "step_no" : 10,
        "purpose" : "Check the Complete and compatible Routine return Complete not Compatible"
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    SUTE.print_test_purpose(etp["step_no"], etp["purpose"])
    result = SSBL.check_complete_compatible_routine(can_p, etp["step_no"])
    result = result and (SSBL.pp_decode_routine_complete_compatible
                         (SC.can_messages[can_p["receive"]][0][2])
                         == 'Complete, Not Compatible')
    return result
    '''
def run():
    """
    Run - Call other functions from here
    """
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

    # start logging
    # to be implemented

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
    timeout = 1500
    result = PREC.precondition(can_p, timeout)

    if result:
    ############################################
    # teststeps
    ############################################

        # step1:
        # action: DL and activate SBL
        # result: ECU sends positive reply
        result = result and SSBL.sbl_activation(can_p, stepno=1,\
                                                purpose="DL and activate SBL")
        time.sleep(1)

        # step2:
        # action: download ESS Software Part no check
        # result: ECU sends positive reply
        logging.info("ESS Software Part Download no check")
        result_step2, vbf_header = SSBL.sw_part_download_no_check(can_p, SSBL.get_ess_filename(),
                                                                  stepno=2)
        result = result and result_step2
        time.sleep(1)
        #save original sw signature for step 5 and step8
        original_sw_signature = vbf_header["sw_signature_dev"]

        # step 3:
        # action: 1st Check memory with verification failed
        # result: BECM sends positive reply
        result = result and step_3(can_p, vbf_header)

        # step 4:
        # action: 2nd Check Memory with verification failed
        # result: BECM sends positive reply
        result = result and step_4(can_p, vbf_header)

        # step 5:
        # action: 3rd Check memory with Negative Response
        # result: BECM sends positive reply
        vbf_header["sw_signature_dev"] = original_sw_signature
        result = result and step_5(can_p, vbf_header)

        # step6:
        # action: download ESS Software Part
        # result: ECU sends positive reply
        logging.info("Step_6: ESS Software Part Download no check")
        result = result and SSBL.sw_part_download_no_check(can_p, SSBL.get_ess_filename(),
                                                           stepno=6)
        time.sleep(1)

        # step 7:
        # action: 1st Check memory with verification failed
        # result: BECM sends positive reply
        result = result and step_7(can_p, vbf_header)
        #time.sleep(1)

        # step 8:
        # action: 2nd Check memory with verification positive
        # result: BECM sends positive reply
        vbf_header["sw_signature_dev"] = original_sw_signature
        result = result and step_8(can_p, vbf_header)

        # step9:
        # action: Download the remnants Software Parts
        # result: ECU sends positive reply
        #Download the remnants Software Parts
        for swp in SSBL.get_df_filenames():

            result = result and SSBL.sw_part_download(can_p, swp, stepno=9)

        # step10:
        # action: Check Complete and Compatible
        # result: ECU sends "Complete and Compatible" reply
        #result = result and step_10(can_p)
        result = result and SSBL.check_complete_compatible_routine(can_p, stepno=10)

        # step11:
        # action: Hard Reset
        # result: ECU sends positive reply
        result = result and SE11.ecu_hardreset(can_p, stepno=11)
        time.sleep(1)

        # step12:
        # action: verify ECU in default session
        # result: ECU sends positive reply
        result = result and SE10.diagnostic_session_control_mode1(can_p, stepno=12)

    ############################################
    # postCondition
    ############################################
    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
