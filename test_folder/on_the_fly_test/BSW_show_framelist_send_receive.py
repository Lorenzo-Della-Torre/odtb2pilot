"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: none, jira issue EARTEPBSW-1284
version: 1
title: request frame send showing up in received frames if signal registered.
purpose: >
    request frame send showing up in received frames if signal registered.

description: >
    Requests sent to beamy didn't show up as received ones, even when being registered
    as frames to look out for.
    This script shows that beamybroker behaves like intendet now.
"""

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


import time
from datetime import datetime
import sys
import logging

import re
import subprocess
from collections import deque

import odtb_conf

from supportfunctions.support_can import SupportCAN, CanParam
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service3e import SupportService3e

SIO = SupportFileIO
SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
PREC = SupportPrecondition()
POST = SupportPostcondition()
SE22 = SupportService22()
SE3E = SupportService3e()

Last_candumpfiles = deque([])

def start_candump():
    """
        start_candump: start new candump can0 if running on linux
    """
    #global Last_Step9_message
    #result = True

    stepno = 999
    purpose = "execute command: Start new CANDUMP CAN0"

    logging.info("Step No. {:d}: purpose: {}".format(stepno, purpose))
    logging.info("\ntime {:.3f}".format(time.time()))
    f_name_temp = re.split(r"(BSW_)", sys.argv[0])
    f_name = re.split(r"(.py)", f_name_temp[1]+f_name_temp[2])[0]
    t_str = str(time.time()).replace('.', '_')
    f_name = f_name + '_' + t_str + '_can.log'
    #logging.info("Start new canlog: %s", f_name)
    if sys.platform == 'linux':
    #if sys.platform == 'win32':
        logging.info("linux - Start new canlog: %s", f_name)
        #start candump with timestamp, stop after 10sec without signals
        subprocess.Popen(["candump", "-ta", "-T10000", "can0"], stdout=open(f_name, 'w'))
        Last_candumpfiles.append(f_name)
        logging.debug("Last candump_files: %s", Last_candumpfiles)
        if len(Last_candumpfiles) > 10:
            rem_file = Last_candumpfiles.popleft()
            #save only data from last 10 loops
            subprocess.call(["rm", "-f", rem_file])
    else:
        logging.info("operating system %s: Can't start candump.", sys.platform)


def frames_received(can_receive, timespan):
    """
        returns # of frames in can_receive buffer after timespan
    """

    SC.clear_all_can_frames()
    logging.debug("No. frames [%s] before %s sec received: %s",\
                  can_receive, timespan, len(SC.can_frames[can_receive]))

    time.sleep(timespan)
    n_frames = len(SC.can_frames[can_receive])

    logging.info("No. frames [%s] after %s sec received: %s",\
                 can_receive, timespan, len(SC.can_frames[can_receive]))
    return n_frames


def step_2(can_p):
    """
        teststep : show frames in buffer
    """
    result = True

    stepno = 2
    purpose = "show send/receive buffer for registered frames"

    logging.info("Step No. {:d}: purpose: {}".format(stepno, purpose))
    time.sleep(0.1)

    logging.info("\nStep_no %s, frames in buffer: %s", stepno, SC.can_frames)

    logging.info("Frames sent/received in step before:")
    logging.info("List of all frames: %s ", SC.can_frames)
    logging.info("List of frames sent: %s ", SC.can_frames[can_p['send']])
    logging.info("List of frames received: %s", SC.can_frames[can_p['receive']])
    logging.info("Time between request - reply: %s (sec)\n",
                 SC.can_frames[can_p['receive']][0][0] - SC.can_frames[can_p['send']][0][0])
    return result



def run():
    """
        OnTheFly testscript
    """
    # start logging
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)
    #logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.DEBUG)

    # where to connect to signal_broker

    # where to connect to signal_broker
    logging.info("\nConnect to ODTB2_DUT %s\n", odtb_conf.ODTB2_DUT)

    can_p: CanParam = {
        "netstub" : SC.connect_to_signalbroker(odtb_conf.ODTB2_DUT, odtb_conf.ODTB2_PORT),
        "send" : "Vcu1ToBecmFront1DiagReqFrame",
        "receive" : "BecmToVcu1Front1DiagResFrame",
        "namespace" : SC.nspace_lookup("Front1CANCfg0")
        }
    SIO.parameter_adopt_teststep(can_p)

    logging.info("Testcase start: %s", datetime.now())
    starttime = time.time()
    logging.info("Time: %s \n", time.time())

    ############################################
    # precondition
    ############################################
    timeout = 60 #(run forever)

    # if you want a candump (works directly on Rpi only):
    #start_candump()

    starttime = time.time()
    result = PREC.precondition(can_p, timeout)
    #TesterPresent not needed in this testscript
    SE3E.stop_periodic_tp_zero_suppress_prmib()

    ############################################
    # teststeps
    ############################################
    # step 1:
    # action: change BECM to programming
    # result: BECM reports mode
    result = SE22.read_did_f186(can_p, dsession=b'\x01')

    #while time.time() - starttime < timeout:

        # step2:
        # action: loop 1 min, show frames for ID send/received
        # result:
    result = result and step_2(can_p)


    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
