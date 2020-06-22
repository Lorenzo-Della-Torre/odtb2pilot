# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-03-31
# version:  1.1
# reqprod:  397438

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

import ODTB_conf
from support_can import SupportCAN, CanParam, CanPayload, CanTestExtra, CanMFParam
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
from support_service3e import SupportService3e

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
SE3E = SupportService3e()

def step_2():
    """
    Teststep 2: Read VBF files for invalid ESS file (1st Logical Block)
    """
    stepno = 2
    purpose = "1st files reading"

    SUTE.print_test_purpose(stepno, purpose)
    ess_vbf_invalid = "./VBF_Reqprod/REQ_397438_32290520AA_SPA2_ESS_used_as_invalid.vbf"
    _, _, _, _, _, erase = SSBL.read_vbf_file(ess_vbf_invalid)
    return erase

def step_3(can_par, erase):
    """
    Teststep 3:verify Flash Erase routine reply with an NRC
    """
    stepno = 3
    can_mf: CanMFParam = SIO.extract_parameter_yml(
        "step_{}".format(stepno),
        block_size=0,
        separation_time=0,
        frame_control_delay=0,
        frame_control_flag=48,
        frame_control_auto=False
        )

    SC.change_mf_fc(can_par["send"], can_mf)
    time.sleep(1)
    cpay: CanPayload = SIO.extract_parameter_yml(
        "step_{}".format(stepno),
        payload=S_CARCOM.can_m_send("RoutineControlRequestSID", b'\xFF\x00' + erase, b'\x01'),
        extra=''
        )

    etp: CanTestExtra = SIO.extract_parameter_yml(
        "step_{}".format(stepno),
        step_no=3,
        purpose="Flash Erase ",
        timeout=20,
        min_no_messages=-1,
        max_no_messages=-1
        )

    result = SUTE.teststep(can_par, cpay, etp)
    result = result and SUTE.test_message(SC.can_messages[can_par["receive"]], teststring='7F3131')
    logging.info('%s', SUTE.pp_decode_7f_response(SC.can_frames[can_par["receive"]][0][2]))
    return result

def run():
    """
    Run - Call other functions from here
    """
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.DEBUG)

    # start logging
    # to be implemented

    # where to connect to signal_broker
    can_par: CanParam = SIO.extract_parameter_yml(
        "main",
        netstub=SC.connect_to_signalbroker(ODTB_conf.ODTB2_DUT, ODTB_conf.ODTB2_PORT),
        send="Vcu1ToBecmFront1DiagReqFrame",
        receive="BecmToVcu1Front1DiagResFrame",
        namespace=SC.nspace_lookup("Front1CANCfg0")
        )

    logging.info("Testcase start: %s", datetime.now())
    starttime = time.time()
    logging.info("Time: %s \n", time.time())
    ############################################
    # precondition
    ############################################
    # read VBF param when testscript is s started, if empty take default param
    SSBL.get_vbf_files()
    timeout = 600
    result = PREC.precondition(can_par, timeout)
    if result:

    ############################################
    # teststeps
    ############################################
        # step1:
        # action:
        # result:
        result = result and SSBL.sbl_activation(can_par, 1, "DL and activate SBL")
        time.sleep(1)

        # step2:
        # action:
        # result:
        erase = step_2()

        # step3:
        # action:
        # result:
        result = result and step_3(can_par, erase)

        # step4:
        # action:
        # result:
        result = result and SSBL.sw_part_download(can_par, SSBL.get_ess_filename(),\
                                   4, "ESS Software Part Download")
        time.sleep(1)

        # step5:
        # action:
        # result:
        for i in SSBL.get_df_filenames():

            result = result and SSBL.sw_part_download(can_par, i, 5)

        # step6:
        # action:
        # result:
        result = result and SSBL.check_complete_compatible_routine(can_par, 6)

        # step 7:
        # action: # ECU Reset
        # result:
        result = result and SE11.ecu_hardreset(can_par, 7)

        # step8:
        # action: verify current session
        # result: BECM reports default session
        result = result and SE22.read_did_f186(can_par, dsession=b'\x01')#, 8)

    ############################################
    # postCondition
    ############################################
    POST.postcondition(can_par, starttime, result)

if __name__ == '__main__':
    run()
