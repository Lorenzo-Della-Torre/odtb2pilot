# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-01-08
# version:  1.1
# reqprod:  53854

# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-09-23
# version:  1.2
# reqprod:  53854

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

from supportfunctions.support_can import SupportCAN, CanParam, CanTestExtra, CanPayload, CanMFParam
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_sec_acc import SupportSecurityAccess
from supportfunctions.support_rpi_gpio import SupportRpiGpio

from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition
from supportfunctions.support_service10 import SupportService10
from supportfunctions.support_service11 import SupportService11
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_service31 import SupportService31


SIO = SupportFileIO
SC = SupportCAN()
S_CARCOM = SupportCARCOM()
SUTE = SupportTestODTB2()
SSBL = SupportSBL()
SSA = SupportSecurityAccess()
SGPIO = SupportRpiGpio()

PREC = SupportPrecondition()
POST = SupportPostcondition()
SE10 = SupportService10()
SE11 = SupportService11()
SE22 = SupportService22()
SE27 = SupportService27()
SE31 = SupportService31()

def step_4(can_p):
    """
    Teststep 4:Flash Erase in PBL reply with Aborted
    """
    #memory address of PBL: PBL start with the address 80000000 for all ECU
    memory_add = SUTE.pp_string_to_bytes(str('80000000'), 4)
    #memory size to erase
    memory_size = SUTE.pp_string_to_bytes(str('0000C000'), 4)

    erase = memory_add + memory_size

    cpay: CanPayload = {"payload" : S_CARCOM.can_m_send("RoutineControlRequestSID", b'\xFF\x00' +
                                                        erase, b'\x01'),
                        "extra" : ''
                       }

    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)

    etp: CanTestExtra = {"step_no" : 4,
                         "purpose" : "Flash Erase Routine reply Aborted in PBL",
                         "timeout" : 1,
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
    time.sleep(1)
    result = SUTE.teststep(can_p, cpay, etp)
    result = result and SUTE.pp_decode_routine_control_response(SC.can_frames
                                                                [can_p["receive"]][0][2],
                                                                'Type1,Aborted')

    return result


def step_7(can_p):
    """
    Teststep 7:Flash Erase of PBL memory address is not allowed
    """

    #memory address of PBL: PBL start with the address 80000000 for all ECU
    memory_add = SUTE.pp_string_to_bytes(str('80000000'), 4)
    #memory size to erase
    memory_size = SUTE.pp_string_to_bytes(str('0000C000'), 4)

    erase = memory_add + memory_size

    cpay: CanPayload = {"payload" : S_CARCOM.can_m_send("RoutineControlRequestSID", b'\xFF\x00' +
                                                        erase, b'\x01'),
                        "extra" : ''
                       }

    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)

    etp: CanTestExtra = {"step_no" : 7,
                         "purpose" : "Flash Erase of PBL memory address is not allowed",
                         "timeout" : 1,
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
    time.sleep(1)
    result = SUTE.teststep(can_p, cpay, etp)
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='7F3131')
    print(SUTE.pp_decode_7f_response(SC.can_frames[can_p["receive"]][0][2]))
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
    timeout = 500
    result = PREC.precondition(can_p, timeout)

    if result:
    ############################################
    # teststeps
    ############################################

        # step 1:
        # action: Verify programming preconditions
        # result: ECU sends positive reply
        result = result and SE31.routinecontrol_requestsid_prog_precond(can_p, stepno=1)
        time.sleep(1)

        # step 2:
        # action: Change to programming session
        # result: ECU sends positive reply
        result = result and SE10.diagnostic_session_control_mode2(can_p, stepno=2)

        # step 3:
        # action: Security Access Request SID
        # result: ECU sends positive reply
        result = result and SE27.activate_security_access(can_p, 3)

        # step 4:
        # action: Flash Erase in PBL reply with Aborted
        # result: BECM sends positive reply
        result = result and step_4(can_p)

        # step 5:
        # action: SBL Download
        # result: BECM sends positive reply
        logging.info("step_5: SBL Download")
        result_step5, vbf_sbl_header = SSBL.sbl_download(can_p, SSBL.get_sbl_filename(),
                                                         stepno=5)
        result = result and result_step5
        time.sleep(1)

        # step 6:
        # action: SBL Activation
        # result: BECM sends positive reply
        logging.info("step_6: SBL Activation")
        result = result and SSBL.activate_sbl(can_p, vbf_sbl_header, stepno=6)

        # step 7:
        # action: Flash Erase of PBL memory address is not allowed
        # result: BECM sends positive reply
        result = result and step_7(can_p)

        # step8:
        # action: Hard Reset
        # result: ECU sends positive reply
        result = result and SE11.ecu_hardreset_5sec_delay(can_p, stepno=8)

        # step9:
        # action: verify ECU in default session
        # result: ECU sends positive reply
        result = result and SE22.read_did_f186(can_p, b'\x01', stepno=9)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()