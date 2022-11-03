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
# project:  BSE_e76542__3
# author:   hweiler (Hans-Klaus Weiler)
# date:     2022-09-01
# version:  1.0
# reqprod:  DID overnight test with asleep/awake

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

from hilding.dut import Dut

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
    stepno = 999
    purpose = "execute command: Start new CANDUMP CAN0"

    logging.info("Step No. {:d}: purpose: {}".format(stepno, purpose))
    logging.info("\ntime {:.3f}".format(time.time()))
    #f_name_temp = re.split(r"(BSW_)", sys.argv[0])
    f_name_temp = re.split(r"(e_)", sys.argv[0])
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


def precondition_extra(can_p: CanParam, timeout=300):
    """
        precondition_extra for test running:
        register extra signal for being able to count
        how often signal is send if ECU is alive

        subscribe to signal activated by NM-frame: can_af.
        Signal is sent repetitively when ECU is alive.
        BECMFront1Fr01 chosen here as sent out most frequently

        SPA1 BECM DBC:
        1305 BecmFront1NMFr: 8 BECM
        58 BECMFront1Fr01
        278 BECMFront1Fr02
    """
    result = True
    can_af: CanParam = {"netstub": can_p["netstub"],
                        "send": "BECMFront1Fr01",
                        "receive": "BECMFront1Fr01",
                        "namespace": can_p["namespace"]
                       }
    SIO.parameter_adopt_teststep(can_af)
    logging.debug("can_af %s", can_af)

    SC.subscribe_signal(can_af, timeout)
    return result, can_af

def step_2(can_af, numofframe):
    """
        teststep 2: request DID Counter for number of software resets
    """

    stepno = 2

    result = True
    logging.info("Stepno: %s", stepno)
    logging.info("Collect static frames for 0.5 seconds")

    if  frames_received(can_af["receive"], 0.5) < numofframe:
        result = False
        logging.info("No NM-frames: test failed")
    logging.info("Step %s: result: %s\n", stepno, result)
    return result


def step_3(can_af):
    """
        teststep 3: check min/max time between static frames received
    """

    result = True
    min_diff = 9999
    max_diff = 0
    jitter = 0
    stepno = 3
    logging.info("SC.can_frames[can_af] %s", SC.can_frames[can_af['receive']])
    n_frames = len(SC.can_frames[can_af['receive']])

    logging.info("Step %s:", stepno)
    logging.info("Frames %s received: %s", can_af, n_frames)

    old_timestamp = SC.can_frames[can_af['receive']][0][0]

    for i in SC.can_frames[can_af['receive']][1:]:
        #logging.info("value i taken %s", i)
        new_timestamp = i[0]
        #logging.info("current timestamp %s", new_timestamp)
        diff = new_timestamp - old_timestamp
        old_timestamp = new_timestamp
        if diff > max_diff:
            max_diff = diff
        if diff < min_diff:
            min_diff = diff
        new_jitter = max_diff - min_diff
        if new_jitter > jitter:
            jitter = new_jitter
        logging.info("Min_diff %s, max_diff %s, Current jitter: %s", min_diff, max_diff, jitter)

    return result


def run():
    """
        OnTheFly testscript
    """
    dut = Dut()

    # where to connect to signal_broker
    logging.info("\nConnect to ODTB2_DUT %s\n", odtb_conf.ODTB2_DUT)

    platform=dut.conf.rigs[dut.conf.default_rig]['platform']
    can_p: CanParam = {
        'netstub': SC.connect_to_signalbroker(odtb_conf.ODTB2_DUT, odtb_conf.ODTB2_PORT),
        'send': dut.conf.platforms[platform]['signal_send'],
        'receive': dut.conf.platforms[platform]['signal_receive'],
        'namespace': dut.conf.platforms[platform]['namespace'],
        'signal_periodic': dut.conf.platforms[platform]['signal_periodic'],
        'signal_tester_present': dut.conf.platforms[platform]['signal_tester_present'],
        'wakeup_frame': dut.conf.platforms[platform]['wakeup_frame'],
        'protocol': dut.conf.platforms[platform]['protocol'],
        'framelength_max': dut.conf.platforms[platform]['framelength_max'],
        'padding': dut.conf.platforms[platform]['padding']
        }
        #'padding': dut.conf.platforms[platform]['padding'],
        #'clientid': dut.conf.scriptname
        #}
    SIO.parameter_adopt_teststep(can_p)

    logging.info("Testcase start: %s", datetime.now())
    starttime = time.time()
    logging.info("Time: %s \n", time.time())

    ############################################
    # precondition
    ############################################
    timeout = 30
    numofframe = 15 # needed to check if ecu is sending static frames
    numofframe2 = SIO.parameter_adopt_teststep("numofframe")
    if numofframe2 != '':
        numofframe = numofframe2

    start_candump()
    result = PREC.precondition(can_p, timeout)
    #TesterPresent not needed in this testscript
    SE3E.stop_periodic_tp_zero_suppress_prmib()
    result, can_af = precondition_extra(can_p, timeout)


    ############################################
    # teststeps
    ############################################
    # step 1:
    # action: check if ecu is in default mode
    # result: BECM reports mode
    result = SE22.read_did_f186(can_p, dsession=b'\x01')

    # step2:
    # action: receive static frames
    # result: if frames received as expected -> TRUE
    result = result and step_2(can_af, numofframe)


    # step3:
    # action: show measured jitter
    # result:
    result = result and  step_3(can_af)



    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
