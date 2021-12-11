/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



**********************************************************************************/


# Testscript Hilding MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-01-15
# version:  1.0
# reqprod:  400894
# Changes: update for YML support
# author:   J-ADSJO
# date:     2020-10-14
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
from supportfunctions.support_can import SupportCAN, CanParam, CanTestExtra, CanPayload
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_sec_acc import SupportSecurityAccess

from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition
from supportfunctions.support_service10 import SupportService10
from supportfunctions.support_service11 import SupportService11
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service31 import SupportService31
from supportfunctions.support_service34 import SupportService34

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

def step_1(can_p: CanParam):
    """
    Teststep 1: Activate SBL
    """
    stepno = 1
    purpose = "Download and Activation of SBL"
    fixed_key = '0102030405'
    new_fixed_key = SIO.extract_parameter_yml(str(inspect.stack()[0][3]), 'fixed_key')
    # don't set empty value if no replacement was found:
    if new_fixed_key != '':
        assert isinstance(new_fixed_key, str)
        fixed_key = new_fixed_key
    else:
        logging.info("Step%s: new_fixed_key is empty. Leave old value.", stepno)
    logging.info("Step%s: fixed_key after YML: %s", stepno, fixed_key)

    result = SSBL.sbl_activation(can_p,
                                 fixed_key,
                                 stepno, purpose)
    return result

def step_3():
    """
    Teststep 3: Read VBF files for 1st SWP file (1st Logical Block)
    """
    stepno = 3
    purpose = "Read VBF files for 1st SWP file (1st Logical Block)"
    result = False
    SUTE.print_test_purpose(stepno, purpose)

    data_files = SSBL.get_df_filenames()
    if len(data_files) > 0:
        _, vbf_header, data, data_start = SSBL.read_vbf_file(data_files[0])
        if len(data) > 0:
            result = True
        else:
            logging.info("Step 3, SSBL.read_vbf_file() returned empty data")
    else:
        logging.info("Step 3, SSBL.get_df_filenames() returned empty data")
        vbf_header  = []
        data        = []
        data_start  = []

    return result, vbf_header, data, data_start

def step_4(data, data_start):
    """
    Teststep 4: Extract data for the 1st data block from 1st SWP
    """
    stepno = 4
    purpose = "Extract data for the 1st data block from 1st file"
    result = False
    SUTE.print_test_purpose(stepno, purpose)

    _, block_by_1, _ = SSBL.block_data_extract(data, data_start)
    if len(block_by_1) > 0:
        result = True
    else:
        logging.info("Step 4, SSBL.block_data_extract() returned empty data")

    return result, block_by_1

def step_5(can_p, block_by_1, vbf_header):
    """
    Teststep 5: Request Download the 1st data block (1nd Logical Block)
    """
    stepno = 5
    purpose = "Request Download the 1st data block (1nd Logical Block)"
    SUTE.print_test_purpose(stepno, purpose)

    SSBL.vbf_header_convert(vbf_header)
    result, _ = SE34.request_block_download(can_p, vbf_header, block_by_1, stepno, purpose)
    return result

def step_6():
    """
    Teststep 6: Read VBF files for 2nd SWP file (1st Logical Block)
    """
    stepno = 6
    purpose = "Read VBF files for 2nd SWP file (1st Logical Block)"
    result = False
    SUTE.print_test_purpose(stepno, purpose)

    data_files = SSBL.get_df_filenames()
    if len(data_files) > 0:
        _, vbf_header, data, data_start = SSBL.read_vbf_file(data_files[1])
        if len(data) > 0:
            result = True
        else:
            logging.info("Step 6, SSBL.read_vbf_file() returned empty data")
    else:
        logging.info("Step 6, SSBL.get_df_filenames() returned empty data")
        vbf_header  = []
        data        = []
        data_start  = []

    return result, vbf_header, data, data_start


def step_7(data, data_start):
    """
    Teststep 7: Extract data for the 1st data block from 2nd SWP
    """
    stepno = 7
    purpose = "Extract data for the 1st data block from 2nd SWP"
    result = False
    SUTE.print_test_purpose(stepno, purpose)

    _, block_by_2, _ = SSBL.block_data_extract(data, data_start)
    if len(block_by_2) > 0:
        result = True
    else:
        logging.info("Step 7, SSBL.block_data_extract() returned empty data")
    return result, block_by_2


def step_8(can_p, block_by_2, vbf_header):
    """
    Teststep 8: Request Download, the 1st data block (2nd Logical Block) is rejected
    """
    SSBL.vbf_header_convert(vbf_header)

    cpay: CanPayload = {
        "payload": b'\x34' +\
            vbf_header["data_format_identifier"].to_bytes(1, 'big') +\
            b'\x44' +\
            block_by_2['StartAddress'].to_bytes(4, 'big') +\
            block_by_2['Length'].to_bytes(4, 'big'),
        "extra": '',
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)

    etp: CanTestExtra = {
        "step_no": 8,
        "purpose": "Request Download, the 1st data block (2nd Logical Block) is rejected",
        "timeout": 0.05,
        "min_no_messages": -1,
        "max_no_messages": -1,
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='7F3431')
    logging.info('Step %s, received message: %s', etp["step_no"],
                 SUTE.pp_decode_7f_response(SC.can_frames[can_p["receive"]][0][2]))
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
    timeout = 2000
    result = PREC.precondition(can_p, timeout)

    if result:
        ############################################
        # teststeps
        ############################################
        # step 1:
        # action: DL and activate SBL
        # result: ECU sends positive reply
        result = result and step_1(can_p)

        # step 2:
        # action: download ESS Software Part
        # result: ECU sends positive reply
        result = result and SSBL.sw_part_download(can_p, SSBL.get_ess_filename(), stepno=2,
                                                  purpose="ESS Software Part Download")
        time.sleep(1)

        # step 3:
        # action: Read VBF files for 1st SWP file (1st Logical Block)
        # result:
        testresult, vbf_header, data, data_start = step_3()
        result = result and testresult

        # step 4:
        # action: Extract data for the 1st data block from 1st SWP
        # result:
        testresult, block_by_1 = step_4(data, data_start)
        result = result and testresult

        # step 5:
        # action: Request Download the 1st data block (1nd Logical Block)
        # result: ECU sends positive reply
        result = result and step_5(can_p, block_by_1, vbf_header)

        # step 6:
        # action: Read VBF files for 2nd SWP file (1st Logical Block)
        # result:
        testresult, vbf_header, data, data_start = step_6()
        result = result and testresult

        # step 7:
        # action: Extract data for the 1st data block from 2nd SWP
        # result:
        testresult, block_by_2 = step_7(data, data_start)
        result = result and testresult

        # step 8:
        # action: Verify request Download the 1st data block (2nd Logical Block) is rejected
        # result: ECU sends NRC reply
        result = result and step_8(can_p, block_by_2, vbf_header)

        # step 9:
        # action: Request Download the 1st Logical Block
        # result: ECU sends positive reply
        result = result and SSBL.sw_part_download(can_p, SSBL.get_df_filenames()[0], stepno=9)

        # step 10:
        # action: Download the remnants Software Parts
        # result: ECU sends positive reply
        #Download the remnants Software Parts
        for swp in SSBL.get_df_filenames()[1:]:
            result = result and SSBL.sw_part_download(can_p, swp, stepno=10)

        # step 11:
        # action: Check Complete and Compatible
        # result: ECU sends "Complete and Compatible" reply
        result = result and SSBL.check_complete_compatible_routine(can_p, stepno=11)

        # step 12:
        # action: Hard Reset
        # result: ECU sends positive reply
        result = result and SE11.ecu_hardreset(can_p, stepno=12)
        time.sleep(1)

        # step 13:
        # action: verify ECU in default session
        # result: ECU sends positive reply
        result = result and SE10.diagnostic_session_control_mode1(can_p, stepno=13)

    ############################################
    # postCondition
    ############################################
    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
