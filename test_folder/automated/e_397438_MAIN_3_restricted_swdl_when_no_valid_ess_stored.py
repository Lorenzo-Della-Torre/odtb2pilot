"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

# Testscript Hilding MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-03-31
# version:  1.1
# reqprod:  397438

# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-08-28
# version:  1.2
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
import os
import sys
import logging
import inspect

import odtb_conf

from supportfunctions.support_can import SupportCAN, CanParam, CanPayload, CanTestExtra
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

    #ess_vbf_invalid = odtb_proj_param +\
    #                  "/VBF_Reqprod/REQ_397438_32290520AA_SPA2_ESS_used_as_invalid.vbf"
    ess_vbf_invalid = odtb_proj_param + "/VBF_Reqprod/REQ_397438_ess_different_project.vbf"
    SSBL.get_ess_filename()
    _, vbf_header, _, _ = SSBL.read_vbf_file(ess_vbf_invalid)
    SSBL.vbf_header_convert(vbf_header)
    #logging.info(erase)
    return vbf_header

def step_3(can_p, vbf_header):
    """
    Teststep 3: Send MF request erase
    """
    #Take first element of list to erase
    erase_el = vbf_header["erase"][0]
    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("RoutineControlRequestSID",\
                                                         b'\xFF\x00' +\
                                                         erase_el[0].to_bytes(4, byteorder='big') +\
                                                         erase_el[1].to_bytes(4, byteorder='big'),
                                                         b'\x01'),\
                        "extra" : ''
                       }
    etp: CanTestExtra = {"step_no": 3,
                         "purpose" : "Send MF request erase",
                         "timeout" : 1,
                         "min_no_messages" : -1,
                         "max_no_messages" : -1
                        }
    #start flash erase, may take long to erase
    result = SUTE.teststep(can_p, cpay, etp)
    result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], teststring='7F3131')
    logging.info('%s', SUTE.pp_decode_7f_response(SC.can_frames[can_p["receive"]][0][2]))
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
    timeout = 3600
    result = PREC.precondition(can_p, timeout)
    if result:

    ############################################
    # teststeps
    ############################################
        # step1:
        # action: DL and anctivation of SBL
        # result: ECU sends positive reply
        result = result and step_1(can_p)

        # step2:
        # action: Read VBF files for ESS not valid file (1st Logical Block)
        # result:
        erase = step_2()

        # step3:
        # action: Send MF request erase
        # result: ECU reply with NRC
        result = result and step_3(can_p, erase)

        # step4:
        # action: DL right ESS
        # result: ECU sends positive reply
        result = result and SSBL.sw_part_download(can_p, SSBL.get_ess_filename(),
                                                  stepno=4, purpose="ESS Software Part Download")
        time.sleep(1)

        # step5:
        # action: DL rest of the files
        # result: ECU sends positive reply
        for i in SSBL.get_df_filenames():

            result = result and SSBL.sw_part_download(can_p, i, stepno=5)

        # step6:
        # action: check complete & compatible
        # result: ECU sends positive reply "complete & compatible"
        result = result and SSBL.check_complete_compatible_routine(can_p, stepno=6)

        # step 7:
        # action: # ECU Reset
        # result: ECU sends positive reply
        result = result and SE11.ecu_hardreset_5sec_delay(can_p, stepno=7)

        # step8:
        # action: verify current session
        # result: BECM reports default session
        result = result and SE22.read_did_f186(can_p, dsession=b'\x01', stepno=8)

    ############################################
    # postCondition
    ############################################
    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
