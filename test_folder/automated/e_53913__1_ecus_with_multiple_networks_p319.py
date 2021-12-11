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
# date:     2020-03-17
# version:  1.0
# reqprod:  53913

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
from supportfunctions.support_can           import SupportCAN, CanParam, CanTestExtra, CanPayload
from supportfunctions.support_test_odtb2    import SupportTestODTB2
from supportfunctions.support_precondition  import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition
from supportfunctions.support_file_io       import SupportFileIO
from supportfunctions.support_carcom        import SupportCARCOM
from supportfunctions.support_service10     import SupportService10
from supportfunctions.support_service11     import SupportService11
from supportfunctions.support_service22     import SupportService22
from supportfunctions.support_service27     import SupportService27
from supportfunctions.support_service31     import SupportService31
from supportfunctions.support_SBL           import SupportSBL
from supportfunctions.support_sec_acc       import SupportSecurityAccess

SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
PREC = SupportPrecondition()
POST = SupportPostcondition()
SIO = SupportFileIO
SE10 = SupportService10()
SE11 = SupportService11()
SE22 = SupportService22()
SE27 = SupportService27()
SE31 = SupportService31()
SSBL = SupportSBL()
SSA = SupportSecurityAccess()


def step_4(can_p):
    """
    Teststep 4: verify RoutineControlRequest is sent for Type 1 but no message received
    """
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("RoutineControlRequestSID",
                                        b'\x02\x05',
                                        b'\x01'),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {
        "step_no": 4,
        "purpose": "Verify RC start is sent on other CAN for Check Complete "\
                    + "and Compatible but no message received",
        "timeout": 1,
        "min_no_messages": -1,
        "max_no_messages": -1
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)

    if not result:
        logging.info("Step %s, result: False\n", etp["step_no"])
        logging.info("Step %s RoutineControlRequestSID failed\n", etp["step_no"])
    else:
        logging.info("Step %s RC-request Compl&Comp sent on other CAN\n", etp["step_no"])

    #verify the message has been sent to the ECU
    result = result and bool(SC.can_frames.get(can_p["send"]))
    if not result:
        logging.info("Step %s %s, frames sent (PI):     ", etp["step_no"], can_p["send"])
        logging.info("Step %s %s, frames sent (ECU):    ",
                     etp["step_no"], SC.can_frames.get(can_p["send"]))
        logging.info("Step %s Was wrong CAN interface used?", etp["step_no"])
        logging.info("Step %s Was DBC for sending CAN-frames in place?", etp["step_no"])
        logging.info("Step %s result: False\n", etp["step_no"])

    #verify no message has been receive
    result = result and len(SC.can_frames[can_p["receive"]]) == 0
    if not result:
        logging.info("Step %s Wrong number CAN-frames received", etp["step_no"])
        logging.info("Step %s Number CAN-frames received: %s",
                     etp["step_no"], len(SC.can_frames[can_p["receive"]]))
        logging.info("Step %s result: False\n", etp["step_no"])
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

    starttime = time.time()
    logging.info("Testcase start: %s", datetime.now())
    logging.info("Time: %s \n", time.time())

    ############################################
    # precondition
    ############################################
    timeout = 40
    result = PREC.precondition(can_p, timeout)

    if result:

        ############################################
        # teststeps
        ############################################
        # step 1:
        # action: Verify if preconditions to programming are fulfilled.
        # result: ECU sends positive reply.
        result = result and SE31.routinecontrol_requestsid_prog_precond(can_p, stepno=1)
        logging.debug("Step %s completed: Result = %s", 1, result)

        # step 2:
        # action: Change to programming session (02) to be able to enter the PBL.
        # result:
        result = result and SE10.diagnostic_session_control_mode2(can_p, stepno=2)
        logging.debug("Step %s completed: Result = %s", 2, result)

        # step 3:
        # action: Request Security Access to be able to unlock the server(s) and run the PBL.
        # result: The ECU reply with the Security Access PIN.
        result = result and SE27.activate_security_access(can_p, 3)
        logging.debug("Step %s completed: Result = %s", 3, result)

        # step 4:
        # action: Verify if the SW is Complete and compatible sending the message by RMS CAN.
        # result: No reply should be received.
        result = result and step_4(can_p)
        logging.debug("Step %s completed: Result = %s", 4, result)

        # step 5:
        # action: Hard reset of ECU.
        # result: ECU sends positive reply.
        result = result and SE11.ecu_hardreset(can_p, 5)
        logging.debug("Step %s completed: Result = %s", 5, result)
        time.sleep(1)

        # step 6:
        # action: Verify ECU is in default session (01).
        # result: ECU sends requested DID with current session.
        result = result and SE22.read_did_f186(can_p, b'\x01', stepno=6)
        logging.debug("Step %s completed: Result = %s", 6, result)

    ############################################
    # postCondition
    ############################################
    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
