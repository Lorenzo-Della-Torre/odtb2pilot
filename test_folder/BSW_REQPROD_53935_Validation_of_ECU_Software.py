# Testscript ODTB2 MEPII
# project:  BECM basetech MEPII
# author:   LDELLATO (Lorenzo Della Torre)
# date:     2019-12-13
# version:  1.0
# reqprod:  53935

# author:   LDELLATO (Lorenzo Della Torre)
# date:     2020-09-15
# version:  1.1
# reqprod:  53935

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

from supportfunctions.support_can import SupportCAN, CanParam, CanTestExtra
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_sec_acc import SupportSecurityAccess
from supportfunctions.support_rpi_gpio import SupportRpiGpio

from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition
from supportfunctions.support_service10 import SupportService10
from supportfunctions.support_service11 import SupportService11
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service31 import SupportService31

import parameters.odtb_conf

SIO = SupportFileIO
SC = SupportCAN()
S_CARCOM = SupportCARCOM()
SUTE = SupportTestODTB2()
SSBL = SupportSBL()
SSA = SupportSecurityAccess()
SGPIO = SupportRpiGpio()

PREC = SupportPrecondition()
POST = SupportPostcondition()
SE10 = SupportService10()
SE11 = SupportService11()
SE22 = SupportService22()
SE31 = SupportService31()


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

def step_4(can_p):
    """
    Teststep 4: Switch the ECU off and on
    """
    stepno = 4
    purpose = "Switch the ECU off and on"
    SUTE.print_test_purpose(stepno, purpose)
    time.sleep(1)
    result = True
    print("Relais1 on")
    SGPIO.t_send_gpio_signal_hex(can_p["netstub"], "Relais1", SC.nspace_lookup("RpiGPIO"), b'\x00')
    time.sleep(3)
    print("Relais1 off")
    SGPIO.t_send_gpio_signal_hex(can_p["netstub"], "Relais1", SC.nspace_lookup("RpiGPIO"), b'\x01')
    time.sleep(2)
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

        # step 1:
        # action: DL and activate SBL
        # result: ECU sends positive reply
        result = result and SSBL.sbl_activation(can_p, stepno=1, purpose="DL and activate SBL")
        time.sleep(1)

        # step 2:
        # action: download ESS Software Part
        # result: ECU sends positive reply
        result = result and SSBL.sw_part_download(can_p, SSBL.get_ess_filename(),\
                                   stepno=2, purpose="ESS Software Part Download")
        time.sleep(1)

        # step 3:
        # action: Check the Complete and compatible Routine return Not Complete
        # result: ECU sends positive reply
        result = result and step_3(can_p)

        # step 4:
        # action: Switch the ECU off and on
        # result:
        result = result and step_4(can_p)

        # step 5:
        # action: Verify ECU is still in mode prog session
        # result: ECU sends positive reply
        result = result and SE22.verify_pbl_session(can_p, stepno=5)

        # step 6:
        # action: DL and activate SBL
        # result: ECU sends positive reply
        result = result and SSBL.sbl_activation(can_p, stepno=6, purpose="DL and activate SBL")
        time.sleep(1)

        # step 7:
        # action: Download the remnants Software Parts
        # result: ECU sends positive reply
        result = result and SSBL.sw_part_download(can_p, SSBL.get_ess_filename(),\
                                   stepno=2, purpose="ESS Software Part Download")

        for swp in SSBL.get_df_filenames():

            result = result and SSBL.sw_part_download(can_p, swp, stepno=7)

        # step 8:
        # action: Check Complete and Compatible
        # result: ECU sends "Complete and Compatible" reply
        result = result and SSBL.check_complete_compatible_routine(can_p, stepno=8)

        # step 9:
        # action: Hard Reset
        # result: ECU sends positive reply
        result = result and SE11.ecu_hardreset(can_p, stepno=9)
        time.sleep(1)

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
