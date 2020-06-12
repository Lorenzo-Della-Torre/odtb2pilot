# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-06-10
# version:  1.2
# reqprod:  52286
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
import sys
import logging

import ODTB_conf
from support_can import SupportCAN, CanParam, CanPayload, CanTestExtra
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
SE31 = SupportService31()
SE3E = SupportService3e()

def step_3(can_par):
    """
    Teststep 3: Check the Complete and compatible Routine return Not Complete
    """
    stepno = 3
    purpose = "Check the Complete and compatible Routine return Not Complete"
    SUTE.print_test_purpose(stepno, purpose)
    result = SSBL.check_complete_compatible_routine(can_par, stepno)

    result = result and (SSBL.pp_decode_routine_complete_compatible\
                         (SC.can_messages[can_par["can_rec"]][0][2])\
                         == 'Not Complete, Compatible')
    return result

def step_6(can_par):
    """
    Teststep 6: verify session
    """
    stepno = 6
    cpay: CanPayload = SIO.extract_parameter_yml(
        "step_{}".format(stepno),
        payload=S_CARCOM.can_m_send("ReadDataByIdentifier", b'\xF1\x21', b''),
        extra=''
        )

    etp: CanTestExtra = SIO.extract_parameter_yml(
        "step_{}".format(stepno),
        step_no=6,
        timeout=1,
        purpose="Verify Programming session in PBL",
        min_no_messages=-1,
        max_no_messages=-1
        )

    result = SUTE.teststep(can_par, cpay, etp)
    result = result and SUTE.test_message(SC.can_messages[can_par["receive"]],\
                                          teststring='F121')

    return result

def step_8(can_par):
    """
    Teststep 8: verify session
    """
    stepno = 8
    cpay: CanPayload = SIO.extract_parameter_yml(
        "step_{}".format(stepno),
        payload=S_CARCOM.can_m_send("ReadDataByIdentifier", b'\xF1\x21', b''),
        extra=''
        )

    etp: CanTestExtra = SIO.extract_parameter_yml(
        "step_{}".format(stepno),
        step_no=8,
        timeout=1,
        purpose="Verify Programming session in PBL",
        min_no_messages=-1,
        max_no_messages=-1
        )

    result = SUTE.teststep(can_par, cpay, etp)
    result = result and SUTE.test_message(SC.can_messages[can_par["receive"]],\
                                          teststring='F121')

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
    # read arguments for files to DL:
    f_sbl = ''
    f_ess = ''
    f_df = []
    for f_name in sys.argv:
        if not f_name.find('.vbf') == -1:
            logging.info("Filename to DL: %s \n", f_name)
            if not f_name.find('sbl') == -1:
                f_sbl = f_name
            elif not f_name.find('ess') == -1:
                f_ess = f_name
            else:
                f_df.append(f_name)
    SSBL.__init__(f_sbl, f_ess, f_df)
    SSBL.show_filenames()
    time.sleep(4)

    timeout = 60
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
        result = result and SSBL.sw_part_download(can_par, SSBL.get_ess_filename(),\
                                   2, "ESS Software Part Download")
        time.sleep(1)

        # step3:
        # action:
        # result:
        result = result and step_3(can_par)

        # step4:
        # action: stop sending tester present
        # result:
        logging.info("Step 4: stop sending tester present.")
        SE3E.stop_periodic_tp_zero_suppress_prmib()

        # step5:
        # action: don't send a request until timeout occured
        # result:
        logging.info("Step 5: Wait longer than timeout for staying in current mode.")
        logging.info("Step 5: Tester present not sent, no request to ECU.\n")
        time.sleep(6)

        # step6:
        # action: Verify ECU is still in mode prog session
        # result:
        result = result and step_6(can_par)

        # step7:
        # action: don't send a request until timeout occured
        # result:
        logging.info("Step 7: Wait longer than timeout for staying in current mode.")
        logging.info("Step 7: Tester present not sent, no request to ECU.\n")
        time.sleep(6)

        # step8:
        # action: Verify ECU is still in mode prog session
        # result:
        result = result and step_8(can_par)

        # step9:
        # action:
        # result:
        SE3E.start_periodic_tp_zero_suppress_prmib(can_par,\
                                              "Vcu1ToAllFuncFront1DiagReqFrame",\
                                              1.02)

        # step10:
        # action:
        # result:
        logging.info("Step 10: DL entire software")
        result = result and SE11.ecu_hardreset(can_par, 10)
        result = result and SSBL.sbl_activation(can_par, 10, "DL and activate SBL")
        time.sleep(1)
        result = result and SSBL.sw_part_download(can_par, SSBL.get_ess_filename(),\
                                   10, "ESS Software Part Download")
        for i in SSBL.get_df_filenames():

            result = result and SSBL.sw_part_download(can_par, i, 10)
        result = result and SSBL.check_complete_compatible_routine(can_par, 10)
        result = result and SE11.ecu_hardreset(can_par, 10)

    ############################################
    # postCondition
    ############################################
    POST.postcondition(can_par, starttime, result)

if __name__ == '__main__':
    run()
