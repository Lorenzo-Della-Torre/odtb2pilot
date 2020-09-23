# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2019-12-13
# version:  1.0
# reqprod:  53959

# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-09-17
# version:  1.1
# reqprod:  53959

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

def step_3(can_p):
    """
    Teststep 3: Not Compatible Software Download
    """
    stepno = 3
    purpose = "Not Compatible Software Download"

    #REQ_53959_SIGCFG_from_previous_release_E3.vbf
    result = True
    if not glob.glob("./VBF_Reqprod/REQ_53959_1*.vbf"):
        result = False
    else:
        for f_name in glob.glob("./VBF_Reqprod/REQ_53959_1*.vbf"):
            result = result and SSBL.sw_part_download(can_p, f_name,
                                                      stepno, purpose)
    return result

def step_4(can_p):
    """
    Teststep 3: Check the Complete and compatible Routine return Not Complete
    """
    etp: CanTestExtra = {
        "step_no" : 4,
        "purpose" : "Check the Complete and compatible Routine return Not Complete"
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    SUTE.print_test_purpose(etp["step_no"], etp["purpose"])
    result = SSBL.check_complete_compatible_routine(can_p, etp["step_no"])
    result = result and (SSBL.pp_decode_routine_complete_compatible
                         (SC.can_messages[can_p["receive"]][0][2])
                         == 'Not Complete, Compatible')
    return result

def step_5(can_p):
    """
    Teststep 5: Complete Software Download
    """
    stepno = 5
    purpose = " Complete Software Download"

    #Download remnants VBF to Complete the Software Download
    result = True
    swps = "./VBF_Reqprod/REQ_53959_2*.vbf"
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), swps)
    if not glob.glob(swps):
        result = False
    else:
        for f_name in glob.glob(swps):
            result = result and SSBL.sw_part_download(can_p, f_name,
                                                      stepno, purpose)
    return result

def step_6(can_p):
    """
    Teststep 6: Check the Complete and compatible Routine return Complete Not Compatible
    """
    etp: CanTestExtra = {
        "step_no" : 6,
        "purpose" : "Check the Complete and compatible Routine return Complete not Compatible"
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    SUTE.print_test_purpose(etp["step_no"], etp["purpose"])
    result = SSBL.check_complete_compatible_routine(can_p, etp["step_no"])
    result = result and (SSBL.pp_decode_routine_complete_compatible
                         (SC.can_messages[can_p["receive"]][0][2])
                         == 'Complete, Not Compatible')
    return result

def step_7(can_p):
    """
    Teststep 7: Flash compatible Software Part
    """
    stepno = 7
    purpose = " Complete Software Download"

    #REQ_53959_SIGCFG_compatible_with current release
    result = True
    swp = "./VBF_Reqprod/REQ_53959_3*.vbf"
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

        # step3:
        # action: download SWP not compatible with current version
        # result: ECU sends positive reply
        result = result and step_3(can_p)

        # step4:
        # action: verify SWDL Not complete
        # result: ECU sends positive reply "Not Complete, Compatible"
        result = result and step_4(can_p)

        # step5:
        # action: Download the remnants Software Parts
        # result: ECU sends positive reply
        result = result and step_5(can_p)

        # step6:
        # action: verify SWDL Not compatible
        # result: ECU sends positive reply "Complete, Not Compatible"
        result = result and step_6(can_p)
        time.sleep(1)

        # step7:
        # action: replace Not compatible SWP with compatible one
        # result: ECU sends positive reply
        result = result and step_7(can_p)

        # step 8:
        # action: Check Complete and Compatible
        # result: BECM sends positive reply "Complete and Compatible"
        result = result and SSBL.check_complete_compatible_routine(can_p, stepno=8)

        # step9:
        # action: Hard Reset
        # result: ECU sends positive reply
        result = result and SE11.ecu_hardreset(can_p, stepno=9)
        time.sleep(1)

        # step10:
        # action: verify ECU in default session
        # result: ECU sends positive reply
        result = result and SE10.diagnostic_session_control_mode1(can_p, stepno=10)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
