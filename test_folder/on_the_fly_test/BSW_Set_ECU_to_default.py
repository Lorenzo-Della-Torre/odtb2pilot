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

# date:     2020-05-04
# version:  1.1
# changes:  parameter support functions

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

import odtb_conf
from supportfunctions.support_can import SupportCAN, CanParam, CanTestExtra, CanPayload
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_sec_acc import SupportSecurityAccess
from supportfunctions.support_file_io import SupportFileIO

from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_service10 import SupportService10
from supportfunctions.support_service11 import SupportService11
from supportfunctions.support_service22 import SupportService22

SIO = SupportFileIO
SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
SSBL = SupportSBL()
SSA = SupportSecurityAccess()

PREC = SupportPrecondition()
SE10 = SupportService10()
SE11 = SupportService11()
SE22 = SupportService22()


def test_mode1(can_p):
    """
    Testmode1: verify session, try to set default
    """
    step_no = 803
    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                         b'\xF1\x86', b''),
                        "extra" : b'\x01'
                       }
    etp: CanTestExtra = {"step_no": step_no,
                         "purpose" : "Verify Default session",
                         "timeout" : 1,
                         "min_no_messages" : 1,
                         "max_no_messages" : 1
                        }

    result = SUTE.teststep(can_p, cpay, etp)

    if SUTE.test_message(SC.can_messages[can_p['receive']], '62F18601'):
        logging.info("BSW_Set_ECU_to_default: ECU in default mode.")
    elif SUTE.test_message(SC.can_messages[can_p['receive']], '62F18603'):
        logging.info("BSW_Set_ECU_to_default: ECU in extended mode. Try to set to default")
        SE10.diagnostic_session_control_mode1(can_p)
    elif SUTE.test_message(SC.can_messages[can_p['receive']], '62F18602'):
        SE22.read_did_eda0(can_p)
        logging.info("BSW_Set_ECU_to_default: ECU in prog mode. Try to set to default")
        SE10.diagnostic_session_control_mode1(can_p)
        SE10.diagnostic_session_control_mode3(can_p)
        SE10.diagnostic_session_control_mode1(can_p)
        SE22.read_did_eda0(can_p)
    #result = result and SUTE.test_message(SC.can_messages[can_p['receive']], teststring='025101')
    time.sleep(1)
    return result

def step_1(can_p):
    """
    Teststep 1: Activate SBL
    """
    stepno = 1
    purpose = "Download and Activation of SBL"
    fixed_key = '0102030405'
    new_fixed_key = SIO.extract_parameter_yml(str(inspect.stack()[0][3]), 'fixed_key')
    # don't set empty value if no replacement was found:
    if new_fixed_key:
        if type(fixed_key) != type(new_fixed_key):# pylint: disable=unidiomatic-typecheck
            fixed_key = eval(new_fixed_key)# pylint: disable=eval-used
        else:
            fixed_key = new_fixed_key
    else:
        logging.info("Step%s new_fixed_key is empty. Discard.", stepno)
    logging.info("Step%s: fixed_key after YML: %s", stepno, fixed_key)

    result = SSBL.sbl_activation(can_p,
                                 fixed_key,
                                 stepno, purpose)
    return result

def step_2(can_p):
    """
    Teststep 2: ESS Software Part Download
    """
    stepno = 2
    purpose = "ESS Software Part Download"
    # Some ECU like HLCM don't have ESS vbf file
    # if no ESS file present: skip download
    if SSBL.get_ess_filename():
        result = SSBL.sw_part_download(can_p, SSBL.get_ess_filename(),
                                       stepno, purpose)
    else:
        result = True
    return result

def step_3(can_p):
    """
    Teststep 3: Download other SW Parts
    """
    stepno = 3
    result = True
    purpose = "continue Download SW"
    for i in SSBL.get_df_filenames():
        result = result and SE22.read_did_eda0(can_p)
        result = result and SSBL.sw_part_download(can_p, i, stepno, purpose)
    return result

def step_4(can_p):
    """
    Teststep 4: Check Complete And Compatible
    """
    stepno = 4

    result = SSBL.check_complete_compatible_routine(can_p, stepno)
    return result


def step_6(can_p):
    """
    Teststep 6: verify session
    """
    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                         b'\xF1\x86', b''),
                        "extra" : b'\x01'
                       }
    etp: CanTestExtra = {"step_no": 6,
                         "purpose" : "Verify Default session",
                         "timeout" : 1,
                         "min_no_messages" : 1,
                         "max_no_messages" : 1
                        }

    result = SUTE.teststep(can_p, cpay, etp)
    time.sleep(1)
    return result

def run():# pylint: disable=too-many-statements
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

    ## read arguments for files to DL:
    #f_sbl = ''
    #f_ess = ''
    #f_df = []
    #for f_name in sys.argv:
    #    if not f_name.find('.vbf') == -1:
    #        print("Filename to DL: ", f_name)
    #        if not f_name.find('sbl') == -1:
    #            f_sbl = f_name
    #        elif not f_name.find('ess') == -1:
    #            f_ess = f_name
    #        else:
    #            f_df.append(f_name)
    #SSBL.__init__(f_sbl, f_ess, f_df)
    #SSBL.show_filenames()
    #time.sleep(10)

    # read VBF param when testscript is s started, if empty take default param
    SSBL.get_vbf_files()
    timeout = 3600
    result = PREC.precondition(can_p, timeout)

    #if result:
    ############################################
    # teststeps
    ############################################
    # step 1:
    # action: verify RoutineControl start is sent for Type 1
    # result: BECM sends positive reply

    #extra reset when DL didn't start correct after unfinished SWDL
    #result = result and step_5(network_stub, can_send, can_receive, can_namespace)

    result = test_mode1(can_p)
    # if ECU wasn't in Mode1, test if were able to switch mode
    if not result:
        result = test_mode1(can_p)

    # No success? Try to reset ECU, request mode after reset
    if not result:
        SE11.ecu_hardreset_5sec_delay(can_p)
        #request_ecu_reset(can_p)
        result = test_mode1(can_p)

    #result = result and step_d2(network_stub, can_send, can_receive, can_namespace)

    # still not mode1? Is software incomplete?
    # try to download new software

    # step 1:
    # action: download SBL and activate
    # result:
    if not result:
        result = step_1(can_p)

        #result = step_4(network_stub, can_send, can_receive, can_namespace)
        # step 2:
        # action: ESS Software Part Download
        # result:
        result = result and step_2(can_p)

        # step 3:
        # action: Download other SW Parts
        # result:
        result = result and step_3(can_p)

        # step 4:
        # action: Check Complete And Compatible
        # result: SW download complete and compatible, test ok
        result = result and step_4(can_p)

    # step 5:
    # action: ECU Reset
    # result:
    result = result and SE11.ecu_hardreset_5sec_delay(can_p)

    # step 6:
    # action: verify session
    # result: BECM mode 1
    #result = result and step_6(network_stub, can_send, can_receive, can_namespace)
    SE22.read_did_eda0(can_p)

    SE10.diagnostic_session_control_mode2(can_p)
    SE22.read_did_eda0(can_p)
    SE10.diagnostic_session_control_mode1(can_p)
    SE22.read_did_eda0(can_p)
    result = result and\
             SE22.read_did_f186(can_p,
                                dsession=b'\x01')
    ############################################
    # postCondition
    ############################################

    logging.debug("\nTime: %s \n", time.time())
    logging.info("Testcase end: %s", datetime.now())
    logging.info("Time needed for testrun (seconds): %s", int(time.time() - starttime))

    logging.info("Do cleanup now...")
    logging.info("Stop all periodic signals sent")
    SC.stop_periodic_all()

    # deregister signals
    SC.unsubscribe_signals()
    # if threads should remain: try to stop them
    SC.thread_stop()

    logging.info("Test cleanup end: %s\n", datetime.now())

    if result:
        logging.info("Testcase result: PASSED")
    else:
        logging.info("Testcase result: FAILED")


if __name__ == '__main__':
    run()
