"""
/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

# Testscript Hilding MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2019-12-13
# version:  1.0
# reqprod:  53959

# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-09-17
# version:  1.1
# reqprod:  53959

# author:   J-ADSJO
# date:     2020-12-07
# version:  1.2
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
import os
import sys
import logging
import inspect
import glob
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
    Teststep 3: Not Compatible Software Download
    """
    stepno = 3
    purpose = "Not Compatible Software Download"

    #REQ_53959_SIGCFG_from_previous_release_E3.vbf
    result = True
    odtb_proj_param = os.environ.get('ODTBPROJPARAM')
    if odtb_proj_param is None:
        odtb_proj_param = '.'

    if not glob.glob(odtb_proj_param + "/VBF_Reqprod/REQ_53959_1*.vbf"):
        result = False
    else:
        for f_name in glob.glob(odtb_proj_param + "/VBF_Reqprod/REQ_53959_1*.vbf"):
            result = result and SSBL.sw_part_download(can_p, f_name,
                                                      stepno, purpose)
    return result

def step_4(can_p):
    """
    Teststep 4: Check the Complete and compatible Routine return Not Complete
    """
    time_stamp = [0]

    etp: CanTestExtra = {
        "step_no" : 4,
        "purpose" : "Check the Complete and compatible Routine return Not Complete"
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SSBL.check_complete_compatible_routine(can_p, etp["step_no"])
    result = result and (SSBL.pp_decode_routine_complete_compatible
                         (SC.can_messages[can_p["receive"]][0][2])
                         == 'Not Complete, Compatible')

    time_stamp[0] = SC.can_frames[can_p["send"]][0][0]
    time_stamp.append(SC.can_frames[can_p["receive"]][0][0])
    result = result and ((time_stamp[1] - time_stamp[0])*1000.0 < 25.0)
    if result:
        logging.info("P2Server time (%f) < 25 ms", (time_stamp[1] - time_stamp[0])*1000.0)
    else:
        logging.info("P2Server time (%f) > 25 ms", (time_stamp[1] - time_stamp[0])*1000.0)

    for frame_type, frames in SC.can_frames.items():
        logging.info("%s:", frame_type)
        for frame in frames:
            ts_type, frame_type, frame_byte = frame
            logging.info("%s", [round(1000 * (ts_type - time_stamp[0]), 3), frame_type, frame_byte])

    return result

def step_5(can_p):
    """
    Teststep 5: Complete Software Download
    """
    stepno = 5
    purpose = " Complete Software Download"

    #Download remnants VBF to Complete the Software Download
    result = True
    odtb_proj_param = os.environ.get('ODTBPROJPARAM')
    if odtb_proj_param is None:
        odtb_proj_param = '.'

    swps = odtb_proj_param + "/VBF_Reqprod/REQ_53959_2*.vbf"
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
    time_stamp = [0]

    etp: CanTestExtra = {
        "step_no" : 6,
        "purpose" : "Check the Complete and compatible Routine return Complete not Compatible"
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result_str = SSBL.check_complete_compatible_routine(can_p, etp["step_no"])
    result = (result_str  == 'Complete, Not Compatible')

    logging.info("Step 6: Check(%s == Complete, Not Compatible) :%s",
                     result_str, result)

    time_stamp[0] = SC.can_frames[can_p["send"]][0][0]
    time_stamp.append(SC.can_frames[can_p["receive"]][0][0])
    result = result and ((time_stamp[1] - time_stamp[0])*1000.0 < 25.0)
    if result:
        logging.info("P2Server time (%f) < 25 ms", (time_stamp[1] - time_stamp[0])*1000.0)
    else:
        logging.info("P2Server time (%f) > 25 ms", (time_stamp[1] - time_stamp[0])*1000.0)

    for frame_type, frames in SC.can_frames.items():
        logging.info("%s:", frame_type)
        for frame in frames:
            ts_type, frame_type, frame_byte = frame
            logging.info("%s", [round(1000 * (ts_type - time_stamp[0]), 3), frame_type, frame_byte])

    return result

def step_7(can_p):
    """
    Teststep 7: Flash compatible Software Part
    """
    stepno = 7
    purpose = " Complete Software Download"

    #REQ_53959_SIGCFG_compatible_with current release
    result = True
    odtb_proj_param = os.environ.get('ODTBPROJPARAM')
    logging.info("\nODTBPROJPARAM: %s", odtb_proj_param)
    if odtb_proj_param is None:
        odtb_proj_param = '.'

    swp = odtb_proj_param + "/VBF_Reqprod/REQ_53959_3*.vbf"
    logging.info(swp)
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), swp)
    if not glob.glob(swp):
        result = False
    else:
        for f_name in glob.glob(swp):
            result = result and SSBL.sw_part_download(can_p, f_name,
                                                      stepno, purpose)
    return result

def step_8(can_p):
    """
    Teststep 8: Check the Complete and compatible Routine return Complete and Compatible
    """
    time_stamp = [0]

    etp: CanTestExtra = {
        "step_no" : 8,
        "purpose" : "Check the Complete and compatible Routine return Complete and Compatible"
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result_str = SSBL.check_complete_compatible_routine(can_p, etp["step_no"])
    result = (result_str  == 'Complete, Compatible')

    logging.info("Step 8: Check(%s == Complete, Compatible) :%s",
                     result_str, result)

    time_stamp[0] = SC.can_frames[can_p["send"]][0][0]
    time_stamp.append(SC.can_frames[can_p["receive"]][0][0])
    result = result and ((time_stamp[1] - time_stamp[0])*1000.0 < 25.0)
    if result:
        logging.info("P2Server time (%f) < 25 ms", (time_stamp[1] - time_stamp[0])*1000.0)
    else:
        logging.info("P2Server time (%f) > 25 ms", (time_stamp[1] - time_stamp[0])*1000.0)

    for frame_type, frames in SC.can_frames.items():
        logging.info("%s:", frame_type)
        for frame in frames:
            ts_type, frame_type, frame_byte = frame
            logging.info("%s", [round(1000 * (ts_type - time_stamp[0]), 3), frame_type, frame_byte])

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
        time.sleep(3)

        # step7:
        # action: replace Not compatible SWP with compatible one
        # result: ECU sends positive reply
        result = result and step_7(can_p)

        # step 8:
        # action: Check Complete and Compatible
        # result: BECM sends positive reply "Complete and Compatible"
        #result = result and SSBL.check_complete_compatible_routine(can_p, stepno=8)
        result = result and step_8(can_p)
        time.sleep(3)

        # step9:
        # action: Hard Reset
        # result: ECU sends positive reply
        result_9 = SE11.ecu_hardreset_5sec_delay(can_p, stepno=9)
        time.sleep(1)
        result = result and result_9

        # step10:
        # action: verify ECU in default session
        # result: ECU sends positive reply
        result_10 =  SE22.read_did_f186(can_p, b'\x01', stepno=10)
        result = result_10 and result

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
