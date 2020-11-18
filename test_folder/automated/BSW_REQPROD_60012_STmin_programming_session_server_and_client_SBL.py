# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-08-21
# version:  1.0
# reqprod:  60012

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

"""The Python implementation of the gRPC route guide client."""

import time
from datetime import datetime
import os
import sys
import logging
import inspect

import parameters.odtb_conf as odtb_conf

from supportfunctions.support_can import SupportCAN, CanParam
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO

from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service11 import SupportService11
from supportfunctions.support_service10 import SupportService10
from supportfunctions.support_service31 import SupportService31
from supportfunctions.support_service34 import SupportService34
from supportfunctions.support_sec_acc import SupportSecurityAccess
from supportfunctions.support_SBL import SupportSBL


SSA = SupportSecurityAccess()
SSBL = SupportSBL()
SIO = SupportFileIO
SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
PREC = SupportPrecondition()
POST = SupportPostcondition()
SE11 = SupportService11()
SE10 = SupportService10()
SE22 = SupportService22()
SE31 = SupportService31()
SE34 = SupportService34()

def step_2():
    """
    Teststep 2: Read VBF files for ESS file (1st Logical Block)
    """
    stepno = 2
    purpose = "1st files reading"

    SUTE.print_test_purpose(stepno, purpose)
    odtb_proj_param = os.environ.get('ODTBPROJPARAM')
    if odtb_proj_param is None:
        odtb_proj_param = '.'

    #ess_vbf_invalid = "./VBF_Reqprod/REQ_397438_32290520AA_SPA2_ESS_used_as_invalid.vbf"
    ess_vbf_invalid = odtb_proj_param + "/VBF_Reqprod/REQ_60012_ess_different_project.vbf"
    SSBL.get_ess_filename()
    _, vbf_header, _, _ = SSBL.read_vbf_file(ess_vbf_invalid)
    SSBL.vbf_header_convert(vbf_header)
    #logging.info(erase)
    return vbf_header

def step_3(can_p, vbf_header):
    """
    Teststep 3: Send first frame of a multi frame request verify ST is 0
    """

    # routine should give negative result as fault ESS was used
    result = not SE31.routinecontrol_requestsid_flash_erase(can_p, vbf_header, stepno=3)

    result = SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='7F3131')
    logging.info('%s', SUTE.pp_decode_7f_response(SC.can_frames[can_p["receive"]][0][2]))
    logging.info("Result after request: %s", result)

    logging.info("Control Frame from Server: %s", SC.can_cf_received[can_p["receive"]][0][2])

    #test if ST is 0 ms: get ST from saved Control Frame
    result = result and (int(SC.can_cf_received[can_p["receive"]][0][2][4:6], 16) == 0)
    if int(SC.can_cf_received[can_p["receive"]][0][2][4:6], 16) == 0:
        logging.info("ST is 0 ms")
    else:
        logging.info("ST is not 0 ms")
    return result

def step_4(can_p):
    """
    Teststep 4: verify session SBL
    """
    result = SE22.read_did_eda0(can_p, stepno=4)
    logging.info("Complete Part/serial received: %s", SC.can_messages[can_p["receive"]])

    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]],\
                                          teststring='F122')
    return result

def run():
    """
    Run - Call other functions from here
    """
    #logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.DEBUG)
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
    timeout = 180
    result = PREC.precondition(can_p, timeout)

    if result:
    ############################################
    # teststeps
    ############################################
        # step1:
        # action: Download and activate SBL
        # result: True, if all went fine
        result = result and SSBL.sbl_activation(can_p, 1, "DL and activate SBL")
        time.sleep(1)

        # step2:
        # action: Read invalid ESS file, for not erasing part of flash
        # result:
        vbf_header = step_2()

        # step3:
        # action: Send multi frame request DIDs
        # result: Reply to request as no timeout
        result = result and step_3(can_p, vbf_header)

        # step4:
        # action: Verify SBL session still active
        # result:
        result = result and step_4(can_p)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
