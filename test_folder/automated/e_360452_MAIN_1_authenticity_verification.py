"""
/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

# Testscript Hilding MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-02-27
# version:  1.0
# reqprod:  360452

# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-09-23
# version:  1.1
# reqprod:  360452

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
from supportfunctions.support_can import SupportCAN, CanParam, CanTestExtra
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

def step_3(can_p):
    """
    Teststep 3: Check the Complete and compatible Routine return Not Complete
    """
    etp: CanTestExtra = {
        "step_no" : 3,
        "purpose" : "Check the Complete and compatible Routine return Not Complete"
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    SUTE.print_test_purpose(etp["step_no"], etp["purpose"])
    result = SSBL.check_complete_compatible_routine(can_p, etp["step_no"])
    print(SSBL.pp_decode_routine_complete_compatible(SC.can_messages[can_p["receive"]][0][2]))
    result = result and (SSBL.pp_decode_routine_complete_compatible
                         (SC.can_messages[can_p["receive"]][0][2])
                         == 'Not Complete, Compatible')
    res_before_check_memory = SC.can_messages[can_p["receive"]][0][2]
    return result, res_before_check_memory

def step_4(can_p, vbf_header):
    """
    Teststep 4: Check memory with verification positive
    """
    stepno = 4
    purpose = "Check memory with verification positive"

    SUTE.print_test_purpose(stepno, purpose)

    result = SE31.check_memory(can_p, vbf_header, stepno)

    result = result and (SSBL.pp_decode_routine_check_memory
                         (SC.can_messages[can_p["receive"]][0][2])
                         == 'The verification is passed')
    logging.info(SSBL.pp_decode_routine_check_memory(SC.can_messages[can_p["receive"]][0][2]))
    return result

def step_5(can_p):
    """
    Teststep 5: Check the Complete and compatible Routine return Not Complete
    """
    etp: CanTestExtra = {
        "step_no" : 5,
        "purpose" : "Check the Complete and compatible Routine return Not Complete"
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    SUTE.print_test_purpose(etp["step_no"], etp["purpose"])
    result = SSBL.check_complete_compatible_routine(can_p, etp["step_no"])
    print(SSBL.pp_decode_routine_complete_compatible(SC.can_messages[can_p["receive"]][0][2]))
    result = result and (SSBL.pp_decode_routine_complete_compatible
                         (SC.can_messages[can_p["receive"]][0][2])
                         == 'Not Complete, Compatible')
    res_after_check_memory = SC.can_messages[can_p["receive"]][0][2]
    return result, res_after_check_memory

def step_6(res_after_check_memory, res_before_check_memory):
    """
    Teststep 6: Check Complete And Compatible messages differ before and after Check Memory
    """
    stepno = 6
    purpose = "Check Complete And Compatible messages differ before and after Check Memory"
    SUTE.print_test_purpose(stepno, purpose)
    result = res_after_check_memory != res_before_check_memory
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

        # step1:
        # action: DL and activate SBL
        # result: ECU sends positive reply
        result = result and step_1(can_p)

        # step2:
        # action: download ESS Software Part no check
        # result: ECU sends positive reply
        logging.info("ESS Software Part Download no check")
        result_step2, vbf_header = SSBL.sw_part_download_no_check(can_p, SSBL.get_ess_filename(),
                                                                  stepno=2)
        result = result and result_step2

        # step 3:
        # action: Check the Complete and compatible Routine return Not Complete
        # result: BECM sends positive reply
        result_step3, res_before_check_memory = step_3(can_p)
        result = result and result_step3

        # step 4:
        # action: Check memory positive reply
        # result: BECM sends positive reply
        result = result and step_4(can_p, vbf_header)

        # step 5:
        # action: Check the Complete and compatible Routine return Not Complete
        # result: BECM sends positive reply
        result_step5, res_after_check_memory = step_5(can_p)
        result = result and result_step5

        # step 6:
        # action: Check Complete And Compatible messages differ before and after Check Memory
        # result: BECM sends positive reply
        result = result and step_6(res_after_check_memory, res_before_check_memory)

        # step7:
        # action: Download the remnants Software Parts
        # result: ECU sends positive reply
        #Download the remnants Software Parts
        for swp in SSBL.get_df_filenames():

            result = result and SSBL.sw_part_download(can_p, swp, stepno=7)

        # step8:
        # action: Check Complete and Compatible
        # result: ECU sends "Complete and Compatible" reply
        result = result and SSBL.check_complete_compatible_routine(can_p, stepno=8)

        # step9:
        # action: Hard Reset
        # result: ECU sends positive reply
        result = result and SE11.ecu_hardreset(can_p, stepno=9)
        time.sleep(1)

        # step10:
        # action: verify ECU in default session
        # result: ECU sends positive reply
        result = result and SE22.read_did_f186(can_p, b'\x01', stepno=10)

    ############################################
    # postCondition
    ############################################
    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
