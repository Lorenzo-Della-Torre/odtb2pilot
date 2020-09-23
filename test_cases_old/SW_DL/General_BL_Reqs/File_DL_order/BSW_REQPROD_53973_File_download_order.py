# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-02-10
# version:  1.0
# reqprod:  53973

# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-09-16
# version:  1.1
# reqprod:  53973

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
from support_can import SupportCAN, CanParam, CanTestExtra
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

def step_4():
    """
    Teststep 4: Read VBF files for ESS file (1st Logical Block)
    """
    stepno = 4
    purpose = "1st files reading"

    SUTE.print_test_purpose(stepno, purpose)
    _, vbf_header, data, data_start = SSBL.read_vbf_file(SSBL.get_ess_filename())
    print(vbf_header)
    return vbf_header, data, data_start

def step_5(data, data_start):
    """
    Teststep 5: Extract data for ESS
    """
    stepno = 5
    purpose = "EXtract data for ESS"

    SUTE.print_test_purpose(stepno, purpose)

    _, block_by, _ = SSBL.block_data_extract(data, data_start)
    return block_by

def step_6(can_p, block_by,
           vbf_header):
    """
    Teststep 6: Verify Request Download the 1st data block (ESS) rejected
    """
    stepno = 6
    purpose = "Verify Request Download the 1st data block (ESS) rejected"

    SUTE.print_test_purpose(stepno, purpose)
    SSBL.vbf_header_convert(vbf_header)
    resultt, _ = SE34.request_block_download(can_p, vbf_header, block_by, stepno,
                                             purpose)
    result = not resultt
    return result

def step_9(can_p):
    """
    Teststep 9: Flash Software Part != ESS
    """
    stepno = 9
    purpose = " Flash Software Part != ESS"

    #REQ_53973_SIGCFG_compatible_with current release
    result = True
    #by default we get files from VBF_Reqprod directory
    swp = "./VBF_Reqprod/REQ_53973_1*.vbf"
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), swp)
    if not glob.glob(swp):
        result = False
    else:
        for f_name in glob.glob(swp):
            result = result and SSBL.sw_part_download(can_p, f_name,
                                                      stepno, purpose)
    return result


def step_11(can_p):
    """
    Teststep 11: Flash remnant Software Part != ESS
    """
    stepno = 11
    purpose = " Flash remnant Software Part != ESS"

    #REQ_53973_SWP's_compatible_with current release
    result = True
    #by default we get files from VBF_Reqprod directory
    swps = "./VBF_Reqprod/REQ_53973_2*.vbf"
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), swps)
    if not glob.glob(swps):
        result = False
    else:
        for f_name in glob.glob(swps):
            result = result and SSBL.sw_part_download(can_p, f_name,
                                                      stepno, purpose)
    return result

def step_12(can_p):
    """
    Teststep 12: Verify the Complete and compatible Routine return Not Complete
    """
    etp: CanTestExtra = {
        "step_no" : 12,
        "purpose" : "Check the Complete and compatible Routine return Not Complete"
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    SUTE.print_test_purpose(etp["step_no"], etp["purpose"])
    result = SSBL.check_complete_compatible_routine(can_p, etp["step_no"])
    result = result and (SSBL.pp_decode_routine_complete_compatible
                         (SC.can_messages[can_p["receive"]][0][2])
                         == 'Not Complete, Compatible')
    return result

def step_13(can_p):
    """
    Teststep 13: Flash Software Part != ESS as in step_9
    """
    stepno = 13
    purpose = " Flash Software Part != ESS as in step_9"

    #REQ_53973_SIGCFG_compatible_with current release
    result = True
    #by default we get files from VBF_Reqprod directory
    swp = "./VBF_Reqprod/REQ_53973_1*.vbf"
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), swp)
    if not glob.glob(swp):
        result = False
    else:
        for f_name in glob.glob(swp):
            result = result and SSBL.sw_part_download(can_p, f_name,
                                                      stepno, purpose)
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
    timeout = 1500
    result = PREC.precondition(can_p, timeout)

    if result:
    ############################################
    # teststeps
    ############################################
        # step 1:
        # action: Verify programming preconditions
        # result: ECU sends positive reply
        result = result and SE31.routinecontrol_requestsid_prog_precond(can_p, stepno=1)

        # step2:
        # action: Change to programming session
        # result: ECU sends positive reply
        result = result and SE10.diagnostic_session_control_mode2(can_p, stepno=2)

        # step 3:
        # action:
        # result:
        result = result and SSA.activation_security_access(can_p, 3,
                                                           "Security Access Request SID")

        # step 4:
        # action: Read VBF files for ESS file (1st Logical Block)
        # result:
        vbf_header, data, data_start = step_4()

        # step 5:
        # action: Extract data for ESS
        # result:
        block_by = step_5(data, data_start)

        # step 6:
        # action: Verify Request Download the 1st data block (ESS) is rejected
        # result: ECU sends positive reply
        result = result and step_6(can_p, block_by, vbf_header)

        # step 7:
        # action: # ECU Reset
        # result: ECU sends positive reply
        result = result and SE11.ecu_hardreset(can_p, stepno=7)
        time.sleep(1)

        # step8:
        # action: DL and activate SBL
        # result: ECU sends positive reply
        result = result and SSBL.sbl_activation(can_p, stepno=8,
                                                purpose="DL and activate SBL")
        time.sleep(1)

        # step 9:
        # action: Flash Software Part != ESS
        # result: ECU sends positive reply
        result = result and step_9(can_p)

        # step10:
        # action: download ESS Software Part
        # result: ECU sends positive reply
        result = result and SSBL.sw_part_download(can_p, SSBL.get_ess_filename(),\
                                   stepno=10, purpose="ESS Software Part Download")
        time.sleep(1)

        # step11:
        # action: Flash remnant Software Part != ESS
        # result: ECU sends positive reply
        result = result and step_11(can_p)

        # step12:
        # action: Verify the Complete and compatible Routine return Not Complete
        # result: ECU sends positive reply
        result = result and step_12(can_p)

        # step13:
        # action: Flash Software Part != ESS as in step_9
        # result: ECU sends positive reply
        result = result and step_13(can_p)

        # step14:
        # action: Check Complete and Compatible
        # result: BECM sends positive reply "Complete and Compatible"
        result = result and SSBL.check_complete_compatible_routine(can_p, stepno=14)


        # step15:
        # action: Hard Reset
        # result: ECU sends positive reply
        result = result and SE11.ecu_hardreset(can_p, stepno=15)
        time.sleep(1)

        # step16:
        # action: verify ECU in default session
        # result: ECU sends positive reply
        result = result and SE10.diagnostic_session_control_mode1(can_p, stepno=16)

    ############################################
    # postCondition
    ############################################


    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
    