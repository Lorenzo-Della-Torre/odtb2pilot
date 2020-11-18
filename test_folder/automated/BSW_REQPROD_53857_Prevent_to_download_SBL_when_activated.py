# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-01-14
# version:  1.1
# reqprod:  53857

# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-09-23
# version:  1.2
# reqprod:  53857

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
from supportfunctions.support_service31 import SupportService31
from supportfunctions.support_service34 import SupportService34

import parameters.odtb_conf as odtb_conf

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
SE31 = SupportService31()
SE34 = SupportService34()

def step_7():
    """
    Teststep 7: Read VBF files for SBL file (1st Logical Block)
    """
    stepno = 7
    purpose = "SBL files reading"

    SUTE.print_test_purpose(stepno, purpose)
    _, vbf_header, data, data_start = SSBL.read_vbf_file(SSBL.get_sbl_filename())
    return vbf_header, data, data_start

def step_8(data, data_start):
    """
    Teststep 8: Extract data for SBL
    """
    stepno = 8
    purpose = "EXtract data for SBL"

    SUTE.print_test_purpose(stepno, purpose)

    _, block_by, _ = SSBL.block_data_extract(data, data_start)
    return block_by

def step_9(can_p, block_by,
           vbf_header):
    """
    Teststep 9: Request Download the 1st data block (SBL)
    """
    SSBL.vbf_header_convert(vbf_header)
    addr_b = block_by['StartAddress'].to_bytes(4, 'big')
    len_b = block_by['Length'].to_bytes(4, 'big')

    cpay: CanPayload = {"payload" : b'\x34' +\
                                    vbf_header["data_format_identifier"].to_bytes(1, 'big') +\
                                    b'\x44'+\
                                    addr_b +\
                                    len_b,
                        "extra" : ''
                       }

    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)

    etp: CanTestExtra = {"step_no": 9,
                         "purpose" : "Request Download the 1st data block",
                         "timeout" : 0.05,
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

    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='7F3431')

    logging.info('%s', SUTE.pp_decode_7f_response(SC.can_frames[can_p["receive"]][0][2]))
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
    timeout = 300
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
        result = result and SSA.activation_security_access(can_p, 3,
                                                           "Security Access Request SID")
        # step 4:
        # action: SBL Download
        # result: BECM sends positive reply
        logging.info("step_4: SBL Download")
        result_step4, _ = SSBL.sbl_download(can_p, SSBL.get_sbl_filename(),
                                            stepno=4)
        result = result and result_step4
        time.sleep(1)

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
        # action: Read VBF files for SBL
        # result:
        vbf_header, data, data_start = step_7()

        # step 8:
        # action: Extract data for the 1st data block from SBL
        # result:
        block_by = step_8(data, data_start)

        # step 9:
        # action: Verify request Download the 1st data block (SBL) is rejected
        # result: ECU sends NRC reply
        result = result and step_9(can_p, block_by, vbf_header)

        # step10:
        # action: Hard Reset
        # result: ECU sends positive reply
        result = result and SE11.ecu_hardreset(can_p, stepno=10)
        time.sleep(1)

        # step11:
        # action: DL and activate SBL
        # result: ECU sends positive reply
        result = result and SSBL.sbl_activation(can_p, stepno=11,
                                                purpose="DL and activate SBL")
        time.sleep(1)

        # step12:
        # action: Hard Reset
        # result: ECU sends positive reply
        result = result and SE11.ecu_hardreset(can_p, stepno=12)
        time.sleep(1)

        # step13:
        # action: verify ECU in default session
        # result: ECU sends positive reply
        result = result and SE22.read_did_f186(can_p, b'\x01', stepno=13)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
