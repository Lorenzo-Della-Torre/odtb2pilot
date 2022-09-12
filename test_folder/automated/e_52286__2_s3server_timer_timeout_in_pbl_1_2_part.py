"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

# Testscript Hilding MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-06-10
# version:  1.0
# reqprod:  52286
#
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-09-15
# version:  1.1
# reqprod:  52286
#
# author:   J-ASSAR1 (Joel Assarsson)
# date:     2020-10-16
# version:  1.2
# reqprod:  52286
#
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

The Python implementation of the gRPC route guide client.
"""

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
from supportfunctions.support_service3e import SupportService3e
from hilding.conf import Conf

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
SE3E = SupportService3e()
conf = Conf()

def step_1(can_p: CanParam):
    """
    Teststep 1: Activate SBL
    """
    stepno = 1
    purpose = "Download and Activation of SBL"

    # Sleep time to avoid NRC37
    time.sleep(5)
    result = SSBL.sbl_activation(can_p,
                                 conf.default_rig_config,
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

    result = result and (SSBL.pp_decode_routine_complete_compatible
                         (SC.can_messages[can_p["receive"]][0][2])
                         == 'Not Complete, Compatible')
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
        result = result and step_1(can_p)

        # step2:
        # action: download ESS Software Part
        # result: ECU sends positive reply
        result = result and SSBL.sw_part_download(can_p, SSBL.get_ess_filename(),
                                                  stepno=2, purpose="ESS Software Part Download")
        time.sleep(1)

        # step3:
        # action:RoutineControl Request SID: startRoutine (01) Check Complete And Compatible
        # result:ECU sends positive reply:“Not Complete, Compatible”
        result = result and step_3(can_p)

        # step4:
        # action: stop sending tester present
        # result:
        #logging.info("Step 4: stop sending tester present.")
        SE3E.stop_periodic_tp_zero_suppress_prmib()

        # step5:
        # action: don't sends a request until timeout occured
        # result:
        logging.info("Step 5: Wait longer than timeout for staying in current mode.")
        logging.info("Step 5: Tester present not sent, no request to ECU.\n")
        time.sleep(6)

        # step6:
        # action: Verify ECU is still in mode prog session
        # result: ECU sends positive reply
        result = result and SE22.verify_pbl_session(can_p, stepno=6)

        # step7:
        # action: don't send a request until timeout occured
        # result:
        logging.info("Step 7: Wait longer than timeout for staying in current mode.")
        logging.info("Step 7: Tester present not sent, no request to ECU.\n")
        time.sleep(6)

        # step8:
        # action: Verify ECU is still in mode prog session
        # result: ECU sends positive reply
        result = result and SE22.verify_pbl_session(can_p, stepno=8)

        # step9:
        # action:
        # result:
        SE3E.start_periodic_tp_zero_suppress_prmib(can_p,
                                                   SIO.extract_parameter_yml("precondition",
                                                                             "tp_name"),
                                                   1.02)

        # step10:
        # action: Download the entire Software
        # result: ECU sends positive reply
        logging.info("Step 10: DL entire software")
        result = result and SE11.ecu_hardreset(can_p, stepno=10)
        result = result and SSBL.sbl_activation(can_p, conf.default_rig_config,\
                                              stepno=10, purpose="DL and activate SBL")
        time.sleep(1)
        result = result and SSBL.sw_part_download(can_p, SSBL.get_ess_filename(),\
                                   stepno=10, purpose="ESS Software Part Download")
        for i in SSBL.get_df_filenames():

            result = result and SSBL.sw_part_download(can_p, i, stepno=10)
        result = result and SSBL.check_complete_compatible_routine(can_p, stepno=10)
        result = result and SE11.ecu_hardreset(can_p, stepno=10)
        time.sleep(1)

    ############################################
    # postCondition
    ############################################
    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
