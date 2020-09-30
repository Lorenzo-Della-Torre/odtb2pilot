# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-01-15
# version:  1.0
# reqprod:  400894

# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-09-22
# version:  1.1
# reqprod:  400894

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

def step_3():
    """
    Teststep 3: Read VBF files for 1st SWP file (1st Logical Block)
    """
    stepno = 3
    purpose = "1st files reading"

    SUTE.print_test_purpose(stepno, purpose)
    data_files = SSBL.get_df_filenames()
    _, vbf_header, data, data_start = SSBL.read_vbf_file(data_files[0])
    return vbf_header, data, data_start

def step_4(data, data_start):
    """
    Teststep 4: Extract data for the 1st data block from 1st SWP
    """
    stepno = 4
    purpose = "Extract data for the 1st data block from 1st file"

    SUTE.print_test_purpose(stepno, purpose)

    _, block_by_1, _ = SSBL.block_data_extract(data, data_start)
    return block_by_1

def step_5(can_p, block_by_1,
           vbf_header):
    """
    Teststep 5: Request Download the 1st data block (1nd Logical Block)
    """
    stepno = 5
    purpose = "Request Download the 1st data block (1nd Logical Block)"

    SUTE.print_test_purpose(stepno, purpose)
    SSBL.vbf_header_convert(vbf_header)
    result, _ = SE34.request_block_download(can_p, vbf_header, block_by_1, stepno,
                                            purpose)
    return result

def step_6():
    """
    Teststep 6: Read VBF files for 2nd SWP file (1st Logical Block)
    """
    stepno = 6
    purpose = "1st files reading"

    SUTE.print_test_purpose(stepno, purpose)
    data_files = SSBL.get_df_filenames()
    _, vbf_header, data, data_start = SSBL.read_vbf_file(data_files[1])
    return vbf_header, data, data_start

def step_7(data, data_start):
    """
    Teststep 7: Extract data for the 1st data block from 2nd SWP
    """
    stepno = 7
    purpose = "Extract data for the 1st data block from 2nd file"

    SUTE.print_test_purpose(stepno, purpose)

    _, block_by_2, _ = SSBL.block_data_extract(data, data_start)
    return block_by_2

def step_8(can_p, block_by_2,
           vbf_header):
    """
    Teststep 8: Request Download the 1st data block (2nd Logical Block)
    """
    SSBL.vbf_header_convert(vbf_header)
    addr_b = block_by_2['StartAddress'].to_bytes(4, 'big')
    len_b = block_by_2['Length'].to_bytes(4, 'big')

    cpay: CanPayload = {"payload" : b'\x34' +\
                                    vbf_header["data_format_identifier"].to_bytes(1, 'big') +\
                                    b'\x44'+\
                                    addr_b +\
                                    len_b,
                        "extra" : ''
                       }

    etp: CanTestExtra = {"step_no": 8,
                         "purpose" : "Request Download the 1st data block",
                         "timeout" : 0.05,
                         "min_no_messages" : -1,
                         "max_no_messages" : -1
                        }

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
    timeout = 2000
    result = PREC.precondition(can_p, timeout)

    if result:
    ############################################
    # teststeps
    ############################################

        # step1:
        # action: DL and activate SBL
        # result: ECU sends positive reply
        result = result and SSBL.sbl_activation(can_p, stepno=1,
                                                purpose="DL and activate SBL")
        time.sleep(1)

        # step2:
        # action: download ESS Software Part
        # result: ECU sends positive reply
        result = result and SSBL.sw_part_download(can_p, SSBL.get_ess_filename(),\
                                   stepno=2, purpose="ESS Software Part Download")
        time.sleep(1)

        # step 3:
        # action: Read VBF files for 1st SWP file (1st Logical Block)
        # result:
        vbf_header, data, data_start = step_3()

        # step 4:
        # action: Extract data for the 1st data block from 1st SWP
        # result:
        block_by_1 = step_4(data, data_start)

        # step 5:
        # action: Request Download the 1st data block (1nd Logical Block)
        # result: ECU sends positive reply
        result = result and step_5(can_p, block_by_1, vbf_header)

        # step 6:
        # action: Read VBF files for 2nd SWP file (1st Logical Block)
        # result:
        vbf_header, data, data_start = step_6()

        # step 7:
        # action: Extract data for the 1st data block from 2nd SWP
        # result:
        block_by_2 = step_7(data, data_start)

        # step 8:
        # action: Verify request Download the 1st data block (2nd Logical Block) is rejected
        # result: ECU sends NRC reply
        result = result and step_8(can_p, block_by_2, vbf_header)

        # step 9:
        # action: Request Download the 1st Logical Block
        # result: ECU sends positive reply
        result = result and SSBL.sw_part_download(can_p, SSBL.get_df_filenames()[0], stepno=9)

        # step10:
        # action: Download the remnants Software Parts
        # result: ECU sends positive reply
        #Download the remnants Software Parts
        for swp in SSBL.get_df_filenames()[1:]:

            result = result and SSBL.sw_part_download(can_p, swp, stepno=10)

        # step11:
        # action: Check Complete and Compatible
        # result: ECU sends "Complete and Compatible" reply
        result = result and SSBL.check_complete_compatible_routine(can_p, stepno=11)

        # step12:
        # action: Hard Reset
        # result: ECU sends positive reply
        result = result and SE11.ecu_hardreset(can_p, stepno=12)
        time.sleep(1)

        # step13:
        # action: verify ECU in default session
        # result: ECU sends positive reply
        result = result and SE10.diagnostic_session_control_mode1(can_p, stepno=13)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
