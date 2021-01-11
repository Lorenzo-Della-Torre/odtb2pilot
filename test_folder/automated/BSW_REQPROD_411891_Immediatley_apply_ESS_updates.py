# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   J-ASSAR1 (Joel Assarsson)
# date:     2020-09-13
# version:  2.0
# reqprod:  411891

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
import os
import sys
import logging
import inspect
from typing import Dict

import odtb_conf
from supportfunctions.support_can import SupportCAN, CanParam
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_sec_acc import SupportSecurityAccess
from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_service11 import SupportService11
from supportfunctions.support_service22 import SupportService22

SC = SupportCAN()
SUTE = SupportTestODTB2()
SSBL = SupportSBL()
SSA = SupportSecurityAccess()
PREC = SupportPrecondition()
POST = SupportPostcondition()
SC_CARCOM = SupportCARCOM()
SIO = SupportFileIO
SE11 = SupportService11()
SE22 = SupportService22()


class VbfFilePath(Dict): # pylint: disable=too-few-public-methods,inherit-non-class
    """
        Filepath to a .vbf file
    """
    path: str

def step_2(can_p):
    """
    Teststep 2: ESS Software Part Download older version
    """
    stepno = 2
    purpose = "ESS Software Part Download older version"

    odtb_proj_param = os.environ.get('ODTBPROJPARAM')
    if odtb_proj_param is None:
        odtb_proj_param = '.'
    ess_vbf_old: VbfFilePath = {
        "path": odtb_proj_param + "/" +
                "VBF_Reqprod/REQ_411891_ess_32263151_AA_6M_old_version_file.vbf"
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), ess_vbf_old)

    logging.debug("Step %s started: %s", stepno, purpose)
    try:
        result = SSBL.sw_part_download(can_p, ess_vbf_old["path"], stepno, purpose)
    except FileNotFoundError as err:
        result = False
        logging.info("Step %s Fatal Error:\n%s", stepno, err)

    logging.debug("Step %s completed: result = %s", stepno, result)
    return result

def step_3(can_p):
    """
    Teststep 3: Updated ESS Software Part Download
    """
    stepno = 3
    purpose = "Updated ESS Software Part Download"

    logging.debug("Step %s started: %s", stepno, purpose)
    ess_vbf_up = SSBL.get_ess_filename()
    result = SSBL.sw_part_download(can_p, ess_vbf_up, stepno, purpose)
    logging.debug("Step %s completed: result = %s", stepno, result)
    return result


def step_5(can_p):
    """
    Teststep 5: Check if Complete And Compatible
    """
    stepno = 5
    purpose = "Verify completeness and compatibility"

    logging.debug("Step %s started: %s", stepno, purpose)
    result = SSBL.check_complete_compatible_routine(can_p, stepno)
    result = result and (SSBL.pp_decode_routine_complete_compatible
                         (SC.can_messages[can_p["receive"]][0][2]) == 'Complete, Compatible')
    logging.debug("Step %s completed: result = %s", stepno, result)
    return result


def run():
    """
    Run - Call other functions from here
    """
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

    # where to connect to signal_broker
    can_p: CanParam = {
        'netstub': SC.connect_to_signalbroker(odtb_conf.ODTB2_DUT, odtb_conf.ODTB2_PORT),
        'send': "Vcu1ToBecmFront1DiagReqFrame",
        'receive': "BecmToVcu1Front1DiagResFrame",
        'namespace': SC.nspace_lookup("Front1CANCfg0")
        }
    #Read YML parameter for current function (get it from stack)
    logging.debug("Read YML for %s", str(inspect.stack()[0][3]))
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), can_p)

    logging.info("Testcase start: %s", datetime.now())
    starttime = time.time()
    logging.info("Time: %s \n", time.time())
    ############################################
    # precondition
    ############################################
    # read VBF param when testscript is s started, if empty take default param
    SSBL.get_vbf_files()
    timeout = 3600
    result = PREC.precondition(can_p, timeout)
    if result:

    ############################################
    # teststeps
    ############################################
        # step 1:
        # action: SBL Activation.
        # result: Positive reply from support function if DL and Activation of SBL ok.
        result = result and SSBL.sbl_dl_activation(can_p, 1, "DL and activate SBL")

        # step 2:
        # action: Download the ESS SW Part, older version.
        # result: Positive reply from support function if DL of SWP ok.
        #result = result and step_2(can_p)

        # step 3:
        # action: Verify that is possible to download the updated ESS SW Part without resetting.
        # result: Positive reply from support function if DL of SWP ok.
        result = result and step_3(can_p)
        result = result and step_5(can_p)

        # step 4:
        # action: Download EXE, SIGCFG and CARCFG SWPs.
        # result: Positive reply from support function if DL of SWP’s ok.
        for i in SSBL.get_df_filenames():
            result = result and SSBL.sw_part_download(can_p, i, stepno=4)
            logging.debug("Step 4, part %s completed: Result = %s", i, result)

        # step 5:
        # action: Check if Complete And Compatible.
        # result: ECU sends positive reply: “Complete, Compatible”.
        result = result and step_5(can_p)

        # step 6:
        # action: Send ECUReset Hard reset(01).
        # result: ECU sends positive reply.
        result = result and SE11.ecu_hardreset_5sec_delay(can_p)
        logging.debug("Step 6 completed: Result = %s", result)

        # step 7:
        # action: Verify ECU is in default session (01).
        # result: ECU sends positive reply.
        result = result and SE22.read_did_f186(can_p, dsession=b'\x01')
        logging.debug("Step 7 completed: Result = %s", result)

    ############################################
    # postCondition
    ############################################
    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
