"""
/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

# Testscript Hilding MEPII
# project:  DID overnight test with asleep/awake
# author:   hweiler (Hans-Klaus Weiler)
# date:     2020-06-05
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

"""The Python implementation of the gRPC route guide client."""

import time
from datetime import datetime
import sys
import logging
import inspect

import re
import subprocess
from collections import deque
from typing import Dict

import odtb_conf

from supportfunctions.support_can import SupportCAN, CanParam,\
                                         PerParam, CanPayload, CanTestExtra
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

class LastMessage(Dict): # pylint: disable=too-few-public-methods,inherit-non-class
    """
        Periodic Parameters
    """
    Step5_message: str
    Step6_message: str
    Step9_message: str

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
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), can_af)
    logging.debug("can_af %s", can_af)

    SC.subscribe_signal(can_af, timeout)
    return result, can_af

def step_2(can_p, can_af, numofframe):
    """
        teststep 2: request DID Counter for number of software resets
    """

    stepno = 2
    wait_start = time.time()
    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                         b'\xD0\x34', b''),
                        "extra" : b''
                       }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {"step_no": stepno,\
                         "purpose" : "request DID Counter for number of software resets",\
                         "timeout" : 0.4,\
                         "min_no_messages" : 1,\
                         "max_no_messages" : 1
                        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)

    if not result:
        logging.info("Received frames: %s:", SC.can_frames[can_p["receive"]])
        logging.info("Received messages: %s:", SC.can_frames[can_p["receive"]])
        SC.update_can_messages(can_p["receive"])
        logging.info("can_mess_updated: %s:", SC.can_frames[can_p["receive"]])
    if  frames_received(can_af["receive"], 0.2) < numofframe:
        result = False
        logging.info("No NM-frames: test failed")
    logging.info("Step %s: Result within %s seconds.", stepno, (time.time()-wait_start))
    logging.info("Step %s: result: %s\n", stepno, result)
    return result

def step_3(can_p, can_af, numofframe):
    """
        teststep 3: request DID SW reset type
    """
    stepno = 3
    wait_start = time.time()
    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                         b'\xDA\xC3', b''),
                        "extra" : b''
                       }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {"step_no": stepno,\
                         "purpose" : "request DID SW reset type",\
                         "timeout" : 0.4,\
                         "min_no_messages" : 1,\
                         "max_no_messages" : 1
                        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)
    result = SUTE.teststep(can_p, cpay, etp)

    if not result:
        logging.info("Received frames: %s:", SC.can_frames[can_p["receive"]])
        logging.info("Received messages: %s:", SC.can_frames[can_p["receive"]])
        SC.update_can_messages(can_p["receive"])
        logging.info("can_mess_updated: %s:", SC.can_frames[can_p["receive"]])
    if  frames_received(can_af["receive"], 0.2) < numofframe:
        result = False
        logging.info("No NM-frames: test failed")
    logging.info("Step %s: Result within %s seconds.", stepno, (time.time()-wait_start))
    logging.info("Step %s: result: %s\n", stepno, result)
    return result

def step_4(can_p, can_af, numofframe):
    """
        teststep 4: request DID 5 last reset types
    """

    stepno = 4
    wait_start = time.time()
    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                         b'\xDA\xC6', b''),
                        "extra" : b''
                       }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {"step_no": stepno,
                         "purpose" : "request DID 5 last reset types",
                         "timeout" : 1,
                         "min_no_messages" : 1,
                         "max_no_messages" : 1
                        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)
    result = SUTE.teststep(can_p, cpay, etp)

    if not result:
        logging.info("Received frames: %s:", SC.can_frames[can_p["receive"]])
        logging.info("Received messages: %s:", SC.can_frames[can_p["receive"]])
        SC.update_can_messages(can_p["receive"])
        logging.info("can_mess_updated: %s:", SC.can_frames[can_p["receive"]])
    if  frames_received(can_af["receive"], 0.2) < numofframe:
        result = False
        logging.info("No NM-frames: test failed")
    logging.info("Step %s: Result within %s seconds.", stepno, (time.time()-wait_start))
    logging.info("Step %s: result: %s\n", stepno, result)
    return result

# teststep 5: request DID 5 last reset types
def step_5(can_p, can_af, numofframe, la_ma):
    """
        teststep 5: request DID 5 last reset types
    """

    #global Last_Step5_message
    stepno = 5
    wait_start = time.time()
    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                         b'\xFD\x71', b''),
                        "extra" : b''
                       }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {"step_no": stepno,
                         "purpose" : "Lear special: request DID 5 last reset types",
                         "timeout" : 3.5,
                         "min_no_messages" : 1,
                         "max_no_messages" : -1
                        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)
    result = SUTE.teststep(can_p, cpay, etp)

    if not result:
        logging.info("Received frames: %s:", SC.can_frames[can_p["receive"]])
        logging.info("Received messages: %s:", SC.can_messages[can_p["receive"]])
        SC.update_can_messages(can_p["receive"])
        logging.info("can_mess_updated: %s:", SC.can_messages[can_p["receive"]])
    if  frames_received(can_af["receive"], 0.2) < numofframe:
        result = False
        logging.info("No NM-frames: test failed")
    logging.info("Step %s: Result within %s seconds.", stepno, (time.time()-wait_start))

    #compare received message with the one received in last call
    logging.debug("la_ma: %s", la_ma)
    if la_ma["Step5_message"] == '':
        logging.debug("First step5 message received")
        la_ma["Step5_message"] = SC.can_messages[can_p["receive"]]
        #logging.debug("LM:   %s ", la_ma["Step5_message"])
        #logging.debug("LM[0]: %s", la_ma["Step5_message"][0])
        #logging.debug("LM[0][2]: %s", la_ma["Step5_message"][0][2])

    else:
        logging.debug("Compare payload old with new message received")
        if la_ma["Step5_message"][0][2] == SC.can_messages[can_p["receive"]][0][2]:
            logging.debug("Step5 old/new received message identical")
        else:
            logging.info("Step5 received old: %s", la_ma["Step5_message"][0][2])
            logging.info("Step5 received new: %s", SC.can_messages[can_p["receive"]][0][2])
        la_ma["Step5_message"] = SC.can_messages[can_p["receive"]]

    logging.info("Step %s: result: %s\n", stepno, result)
    return result

def step_6(can_p: CanParam, can_af, numofframe, la_ma):
    """
        teststep 6: request DID 5 last reset types
    """

    #global Last_Step6_message
    stepno = 6
    wait_start = time.time()
    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                         b'\xFD\x72', b''),
                        "extra" : b''
                       }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {"step_no": stepno,
                         "purpose" : "Lear special: request DID 5 last reset types",
                         "timeout" : 3,
                         "min_no_messages" : 1,
                         "max_no_messages" : -1
                        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)
    result = SUTE.teststep(can_p, cpay, etp)
    nm_frame = can_af["receive"]
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), "nm_frame")

    if not result:
        logging.info("Received frames: %s:", SC.can_frames[can_p["receive"]])
        logging.info("Received messages: %s:", SC.can_messages[can_p["receive"]])
        SC.update_can_messages(can_p["receive"])
        logging.info("can_mess_updated: %s:", SC.can_frames[can_p["receive"]])
    if  frames_received(nm_frame, 0.2) < numofframe:
        result = False
        logging.info("No NM-frames: test failed")
    logging.info("Step %s: Result within %s seconds.", stepno, (time.time()-wait_start))


    #compare received message with the one received in last call
    if la_ma["Step6_message"] == '':
        logging.debug("First step6 message received")
        la_ma["Step6_message"] = SC.can_messages[can_p["receive"]]
        #logging.debug("LM:    %s", la_ma["Step6_message"])
        #logging.debug("LM[0]: %s", la_ma["Step6_message"][0])
        #logging.debug("LM[0][2]: %s", la_ma["Step6_message"][0][2])
    else:
        logging.debug("Compare payload old with new message received")
        if la_ma["Step6_message"][0][2] == SC.can_messages[can_p["receive"]][0][2]:
            logging.debug("Step6 old/new received message identical")
        else:
            logging.debug("Step6 received old: %s", la_ma["Step6_message"][0][2])
            logging.debug("Step6 received new: %s", SC.can_messages[can_p["receive"]][0][2])
        la_ma["Step6_message"] = SC.can_messages[can_p["receive"]]

    logging.info("Step %s: result: %s\n", stepno, result)
    return result

def step_7(can_af, numofframe):
    """
        teststep 7: stop heartbeat, wait for BECM to stop sending frames
    """
    result = True

    stepno = 7
    purpose = "stop sending heartbeat, verify BECM stops traffic"

    nm_frame = can_af["receive"]
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), "nm_frame")
    logging.info("Step No. {:d}: purpose: {}".format(stepno, purpose))
    if  frames_received(nm_frame, 0.2) < numofframe:
        result = False
        logging.info("No NM-frames: test failed.")
    logging.info("Stop heartbeat sent.")
    SC.stop_heartbeat()

    time.sleep(4)
    # Shouldn't recevie frames any longer now
    if  frames_received(nm_frame, 0.2) > 0:
        result = False
        logging.info("No NM-frames: test failed.")
    logging.info("Step %s: result: %s\n", stepno, result)
    return result

def step_8(can_af):
    """
        teststep 8: wait 1 Min for BECM to fall asleep
    """
    result = True

    stepno = 8
    purpose = "wait 1 Min for BECM to fall asleep"

    logging.info("Step No. {:d}: purpose: {}".format(stepno, purpose))
    time.sleep(60)

    # Shouldn't recevie frames any longer now
    nm_frame = can_af["receive"]
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), "nm_frame")
    if  frames_received(nm_frame, 0.2) > 0:
        result = False
        logging.info("No NM-frames: test failed.")
    logging.info("Step %s: result: %s\n", stepno, result)
    return result

def step_9(can_p, can_af, numofframe, la_ma):
    """
        teststep 9: send wakeup frame, followed by FD71/FD72 requests
    """
    #global Last_Step9_message
    result = True

    stepno = 9
    purpose = "send wakeup frames again, wait for BECM to be awake again"

    logging.info("Step No. {:d}: purpose: {}".format(stepno, purpose))

    nspace_burst = can_p["namespace"]
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), "nspace_burst")
    frame_burst = b'\x20\x40\x00\xFF\x00\x00\x00\x00'
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), "frame_burst")
    burst_param: PerParam = {
        "name" : "Burst",
        "send" : True,
        "id" : "EcmFront1NMFr",
        "nspace" : nspace_burst,
        "frame" : frame_burst,
        "intervall" : 0.1
        }
    #double names - extract separately
    #SIO.extract_parameter_yml(str(inspect.stack()[0][3]), burst_param)
    hb_param: PerParam = {
        "name" : "Heartbeat",
        "send" : True,
        "id" : "EcmFront1NMFr",
        "nspace" : can_p["namespace"].name,
        "frame" : b'\x1A\x40\xC3\xFF\x01\x00\x00\x00',
        "intervall" : 0.8
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), hb_param)
    # start heartbeat, repeat every x second

    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                         b'\xFD\x71', b'\xFD\x72'),
                        "extra" : b''
                       }
    #print("Step9, payload: ", cpay)
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {"step_no": stepno,
                         "purpose" : "Lear special: request DID 5 last reset types",
                         "timeout" : 8,
                         "min_no_messages" : -1,
                         "max_no_messages" : -1
                        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    SC.send_burst(can_p["netstub"], burst_param, 3)
    SC.start_heartbeat(can_p["netstub"], hb_param)
    wait_start = time.time()
    result = SUTE.teststep(can_p, cpay, etp)

    #SC.update_can_messages(can_p["receive"])
    logging.info("Received messages: %s:", SC.can_messages[can_p["receive"]])

    #compare received message with the one received in last call
    if la_ma["Step9_message"] == '':
        logging.debug("First step9 message received")
        la_ma["Step9_message"] = SC.can_messages[can_p["receive"]]
    else:
        logging.debug("Compare payload old with new message received")
        if la_ma["Step9_message"][0][2] == SC.can_messages[can_p["receive"]][0][2]:
            logging.debug("Step9 old/new received message identical")
        else:
            logging.info("Step9 received old: %s", la_ma["Step9_message"][0][2])
            logging.info("Step9 received new: %s", SC.can_messages[can_p["receive"]][0][2])
        la_ma["Step9_message"] = SC.can_messages[can_p["receive"]]

    if not result:
        logging.info("Received frames: %s:", SC.can_frames[can_p["receive"]])
        logging.info("Received messages: %s:", SC.can_messages[can_p["receive"]])
        SC.update_can_messages(can_p["receive"])
        logging.info("can_mess_updated: %s:", SC.can_frames[can_p["receive"]])
    if  frames_received(can_af["receive"], 0.2) < numofframe:
        result = False
        logging.info("No NM-frames: test failed")
    logging.info("Step %s: Result within %s seconds.", stepno, (time.time()-wait_start))
    logging.info("Step %s: result: %s\n", stepno, result)
    return result

def step_10(can_p, can_af, numofframe):
    """
        teststep 10: send wakeup frames again
    """
    result = True

    stepno = 10
    purpose = "send wakeup frames again, wait for BECM to be awake again"

    logging.info("Step No. {:d}: purpose: {}".format(stepno, purpose))
    hb_param: PerParam = {
        "name" : "Heartbeat",
        "send" : True,
        "id" : "EcmFront1NMFr",
        "nspace" : can_p["namespace"].name,
        "frame" : b'\x1A\x40\xC3\xFF\x01\x00\x00\x00',
        "intervall" : 0.8
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), hb_param)
    # start heartbeat, repeat every x second
    SC.start_heartbeat(can_p["netstub"], hb_param)
    time.sleep(1)

    # Shouldn't recevie frames any longer now
    if  frames_received(can_af["receive"], 0.2) < numofframe:
        result = False
        logging.info("No NM-frames: test failed.")
    logging.info("Step %s: result: %s\n", stepno, result)
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
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), can_p)
    logging.debug("Stack output %s", inspect.stack())

    logging.info("Testcase start: %s", datetime.now())
    starttime = time.time()
    logging.info("Time: %s \n", time.time())

    ############################################
    # precondition
    ############################################
    timeout = 0 #(run forever)
    numofframe = 15
    numofframe2 = SIO.extract_parameter_yml(str(inspect.stack()[0][3]), "numofframe")
    if numofframe2 != '':
        numofframe = numofframe2
    # don't take standard precondition, no TP needed
    start_candump()
    result = PREC.precondition(can_p, timeout)
    #TesterPresent not needed in this testscript
    SE3E.stop_periodic_tp_zero_suppress_prmib()
    result, can_af = precondition_extra(can_p, timeout)

    la_ma: LastMessage = {
        "Step5_message" : '',
        "Step6_message" : '',
        "Step9_message" : ''
    }

    ############################################
    # teststeps
    ############################################
    # step 1:
    # action: change BECM to programming
    # result: BECM reports mode
    result = SE22.read_did_f186(can_p, dsession=b'\x01')

    while result:
        # step2:
        # action: check current session
        # result: BECM reports programmin session
        result = result and step_2(can_p, can_af, numofframe)

        # step3:
        # action: send 'hard_reset' to BECM
        # result: BECM acknowledges message
        result = result and  step_3(can_p, can_af, numofframe)

        # step4:
        # action: check current session
        # result: BECM reports default session
        result = result and  step_4(can_p, can_af, numofframe)

        logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.DEBUG)
        result = result and  step_5(can_p, can_af, numofframe, la_ma)

        result = result and  step_6(can_p, can_af, numofframe, la_ma)
        logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

        result = result and  step_7(can_af, numofframe)
        result = result and  step_8(can_af)

        # send short burst, followed by FD71 request
        # send heartbeat again.
        start_candump()
        result = result and  step_9(can_p, can_af, numofframe, la_ma)

        # if no burst wanted, comment out step_9, use step_10 instead
        #continue sending normal wakeup frames
        #result = result and  step_10(can_p)


    ############################################
    # postCondition
    ############################################

    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.DEBUG)
    #check if problem was temporary and ECU is awake again
    frames_received(can_af["receive"], 0.2)
    frames_received(can_af["receive"], 0.2)
    frames_received(can_af["receive"], 0.2)
    frames_received(can_af["receive"], 0.2)
    frames_received(can_af["receive"], 0.2)
    frames_received(can_af["receive"], 0.2)
    frames_received(can_af["receive"], 0.2)
    frames_received(can_af["receive"], 0.2)
    frames_received(can_af["receive"], 0.2)
    frames_received(can_af["receive"], 0.2)

    logging.info("\nRedo step5, step6 after error occured.")
    step_5(can_p, can_af, numofframe, la_ma)
    step_6(can_p, can_af, numofframe, la_ma)

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
