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
# date:     2020-01-16
# version:  1.0
# reqprod:  400878

# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-09-21
# version:  1.1
# reqprod:  update for YML support

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
from supportfunctions.support_can import SupportCAN, CanParam, CanTestExtra, CanPayload
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_SBL import SupportSBL

from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition
from supportfunctions.support_service11 import SupportService11
from supportfunctions.support_service22 import SupportService22

from hilding.dut import Dut

SIO = SupportFileIO
SC = SupportCAN()
S_CARCOM = SupportCARCOM()
SUTE = SupportTestODTB2()
SSBL = SupportSBL()

PREC = SupportPrecondition()
POST = SupportPostcondition()
SE11 = SupportService11()
SE22 = SupportService22()

def step_1(can_p: CanParam, sa_keys):
    """
    Teststep 1: Activate SBL
    """
    stepno = 1
    purpose = "Download and Activation of SBL"

    result = SSBL.sbl_activation(can_p,
                                 sa_keys,
                                 stepno, purpose)
    return result

def step_2():
    """
    Teststep 2: Read VBF files for ESS file (1st Logical Block)
    """
    stepno = 2
    purpose = "1st files reading"
    result = True
    SUTE.print_test_purpose(stepno, purpose)
    #REQ_53973_SIGCFG_compatible_with current release
    #by default we get files from VBF_Reqprod directory
    #REQ_400878_ess_32263666_AA_6M_header_modified.vbf
    odtb_proj_param = os.environ.get('ODTBPROJPARAM')
    if odtb_proj_param is None:
        odtb_proj_param = '.'

    ess_modif_header = odtb_proj_param + "/VBF_Reqprod/REQ_400878*.vbf"
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), ess_modif_header)
    if not glob.glob(ess_modif_header):
        result = False
    else:
        for f_name in glob.glob(ess_modif_header):
            _, vbf_header, _, _ = SSBL.read_vbf_file(f_name)
    logging.info('%s',vbf_header)
    return result, vbf_header

def step_3(can_p, vbf_header):
    """
    Teststep 3: Flash Erase for wrong Lenght should be aborted
    """

    SSBL.vbf_header_convert(vbf_header)
    #There may be several parts to be erase in VBF-header, loop over them
    for erase_el in vbf_header['erase']:
    # verify RoutineControlRequest is sent for Type 1
        result = SE22.read_did_eda0(can_p)
        cpay: CanPayload = {"payload" : S_CARCOM.can_m_send("RoutineControlRequestSID",\
                                            b'\xFF\x00' +\
                                            erase_el[0].to_bytes(4, byteorder='big') +\
                                            erase_el[1].to_bytes(4, byteorder='big'), b'\x01'),\
                            "extra" : ''
                           }
        etp: CanTestExtra = {"step_no": 3,
                             "purpose" : "RC flash erase",
                             "timeout" : 1,
                             "min_no_messages" : -1,
                             "max_no_messages" : -1
                            }
        #start flash erase, may take long to erase
        result = SUTE.teststep(can_p, cpay, etp)
        logging.info("SE31 RC FlashErase 0xFF00 %s %s, result: %s",
                     erase_el[0].to_bytes(4, byteorder='big'),
                     erase_el[1].to_bytes(4, byteorder='big'),
                     result)

    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='7F3131')

    logging.info('%s', SUTE.pp_decode_7f_response(SC.can_frames[can_p["receive"]][0][2]))

    return result


def run():
    """
    Run - Call other functions from here
    """
    dut = Dut()
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
    timeout = 90
    result = PREC.precondition(can_p, timeout)

    platform=dut.conf.rigs[dut.conf.default_rig]['platform']
    sa_keys = {
        "SecAcc_Gen" : dut.conf.platforms[platform]['SecAcc_Gen'],
        "fixed_key": dut.conf.platforms[platform]["fixed_key"],
        "auth_key": dut.conf.platforms[platform]["auth_key"],
        "proof_key": dut.conf.platforms[platform]["proof_key"]
    }

    if result:
    ############################################
    # teststeps
    ############################################

        # step1:
        # action: DL and activate SBL
        # result: ECU sends positive reply
        result = result and step_1(can_p, sa_keys)

        # step 2:
        # action: Read VBF files for ESS file (1st Logical Block)
        # result:
        result_step2, vbf_header = step_2()
        result = result and result_step2

        # step 3:
        # action: Flash Erase for wrong Lenght should be aborted
        # result: ECU reply with NRC
        result = result and step_3(can_p, vbf_header)

        # step4:
        # action: Hard Reset
        # result: ECU sends positive reply
        result = result and SE11.ecu_hardreset(can_p, stepno=4)
        time.sleep(1)

        # step5:
        # action: verify ECU in default session
        # result: ECU sends positive reply
        result = result and SE22.read_did_f186(can_p, b'\x01', stepno=5)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
