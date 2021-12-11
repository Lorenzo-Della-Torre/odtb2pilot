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
# date:     2019-12-13
# version:  1.0
# reqprod:  53957

# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-09-16
# version:  1.1
# reqprod:  53957

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

The Python implementation of the gRPC route guide client.
"""

import time
from datetime import datetime
import os
import sys
import logging
import inspect
import glob

import odtb_conf
from supportfunctions.support_can import SupportCAN, CanParam
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

def step_7(can_p):
    """
    Teststep 7: Download Different SW Parts variant
    """
    stepno = 7
    purpose = "Download SWP1 variant"
    result = True
    odtb_proj_param = os.environ.get('ODTBPROJPARAM')
    if odtb_proj_param is None:
        odtb_proj_param = '.'

    #by default we get files from VBF_Reqprod directory
    #REQ_53957_32325411XC_SWP1variant.vbf
    variant = odtb_proj_param + "/VBF_Reqprod/REQ_53957*.vbf"
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), variant)
    if not glob.glob(variant):
        result = False
    else:
        for f_name in glob.glob(variant):
            result = result and SSBL.sw_part_download(can_p, f_name,
                                                      stepno, purpose)
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
        # action: download ESS Software Part
        # result: ECU sends positive reply
        result = result and SSBL.sw_part_download(can_p, SSBL.get_ess_filename(),\
                                   stepno=2, purpose="ESS Software Part Download")
        time.sleep(1)

        # step3:
        # action: Download the remnants Software Parts
        # result: ECU sends positive reply
        for swp in SSBL.get_df_filenames():

            result = result and SSBL.sw_part_download(can_p, swp, stepno=3)

        # step4:
        # action: Check Complete and Compatible
        # result: ECU sends "Complete and Compatible" reply
        result = result and SSBL.check_complete_compatible_routine(can_p, stepno=4)

        # step5:
        # action: Hard Reset
        # result: ECU sends positive reply
        result = result and SE11.ecu_hardreset(can_p, stepno=5)

        # step6:
        # action: DL and activate SBL
        # result: ECU sends positive reply
        result = result and SSBL.sbl_activation(can_p, stepno=6, purpose="DL and activate SBL")
        time.sleep(1)

        # step7:
        # action: Download Different SW Parts variant
        # result: ECU sends positive reply
        result = result and step_7(can_p)

        # step8:
        # action: Check Complete and Compatible
        # result: ECU sends "Complete and Compatible" reply
        result = result and SSBL.check_complete_compatible_routine(can_p, stepno=8)

        # step9:
        # action: Hard Reset
        # result: ECU sends positive reply
        result = result and SE11.ecu_hardreset(can_p, stepno=9)

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
