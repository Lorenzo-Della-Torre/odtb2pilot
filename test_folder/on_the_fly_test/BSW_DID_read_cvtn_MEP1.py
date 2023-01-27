# Testscript ODTB2 MEPII
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
                                         CanPayload, CanTestExtra
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

def step_2(can_p):
    """
        teststep 2: request DID CVTN1 voltages
    """

    stepno = 2
    #wait_start = time.time()
    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                         b'\x4A\x24', b''),
                        "extra" : b''
                       }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {"step_no": stepno,\
                         "purpose" : "request DID CVTN1 voltages",\
                         "timeout" : 1,\
                         "min_no_messages" : 1,\
                         "max_no_messages" : 1
                        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)

    return result

def step_3(can_p):
    """
        teststep 3: request DID CVTN2 voltages
    """

    stepno = 3
    #wait_start = time.time()
    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                         b'\x4A\x27', b''),
                        "extra" : b''
                       }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {"step_no": stepno,\
                         "purpose" : "request DID CVTN2 voltages",\
                         "timeout" : 1,\
                         "min_no_messages" : 1,\
                         "max_no_messages" : 1
                        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)

    return result

def step_4(can_p):
    """
        teststep 4: request DID CVTN3 voltages
    """

    stepno = 4
    #wait_start = time.time()
    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                         b'\x4A\x29', b''),
                        "extra" : b''
                       }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {"step_no": stepno,\
                         "purpose" : "request DID CVTN3 voltages",\
                         "timeout" : 1,\
                         "min_no_messages" : 1,\
                         "max_no_messages" : 1
                        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)

    return result

def step_5(can_p):
    """
        teststep 5: request DID CVTN4 voltages
    """

    stepno = 5
    #wait_start = time.time()
    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                         b'\x4A\x2A', b''),
                        "extra" : b''
                       }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {"step_no": stepno,\
                         "purpose" : "request DID CVTN4 voltages",\
                         "timeout" : 1,\
                         "min_no_messages" : 1,\
                         "max_no_messages" : 1
                        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)

    return result

def step_6(can_p):
    """
        teststep 6: request DID CVTN5 voltages
    """

    stepno = 6
    #wait_start = time.time()
    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                         b'\x4A\x2B', b''),
                        "extra" : b''
                       }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {"step_no": stepno,\
                         "purpose" : "request DID CVTN5 voltages",\
                         "timeout" : 1,\
                         "min_no_messages" : 1,\
                         "max_no_messages" : 1
                        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)

    return result

def step_7(can_p):
    """
        teststep 7: request DID CVTN6 voltages
    """

    stepno = 7
    #wait_start = time.time()
    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                         b'\x4A\x2C', b''),
                        "extra" : b''
                       }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {"step_no": stepno,\
                         "purpose" : "request DID CVTN6 voltages",\
                         "timeout" : 1,\
                         "min_no_messages" : 1,\
                         "max_no_messages" : 1
                        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)

    return result

def step_8(can_p):
    """
        teststep 8: request DID CVTN7 voltages
    """

    stepno = 8
    #wait_start = time.time()
    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                         b'\x4A\x2D', b''),
                        "extra" : b''
                       }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {"step_no": stepno,\
                         "purpose" : "request DID CVTN7 voltages",\
                         "timeout" : 1,\
                         "min_no_messages" : 1,\
                         "max_no_messages" : 1
                        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)

    return result

def step_9(can_p):
    """
        teststep 9: request DID CVTN8 voltages
    """

    stepno = 9
    #wait_start = time.time()
    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                         b'\x4A\x2E', b''),
                        "extra" : b''
                       }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {"step_no": stepno,\
                         "purpose" : "request DID CVTN8 voltages",\
                         "timeout" : 1,\
                         "min_no_messages" : 1,\
                         "max_no_messages" : 1
                        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)

    return result

def step_10(can_p):
    """
        teststep 10: request DID CVTN9 voltages
    """

    stepno = 10
    #wait_start = time.time()
    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                         b'\x4A\x2F', b''),
                        "extra" : b''
                       }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    etp: CanTestExtra = {"step_no": stepno,\
                         "purpose" : "request DID CVTN9 voltages",\
                         "timeout" : 1,\
                         "min_no_messages" : 1,\
                         "max_no_messages" : 1
                        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

    result = SUTE.teststep(can_p, cpay, etp)

    return result




def run():
    """
        OnTheFly testscript
    """
    # start logging
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)
    #logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.DEBUG)

    # where to connect to signal_broker
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
    timeout = 30 #(0 =run forever)
    # don't take standard precondition, no TP needed
    start_candump()
    result = PREC.precondition(can_p, timeout)
    #TesterPresent not needed in this testscript
    SE3E.stop_periodic_tp_zero_suppress_prmib()
    #result, can_af = precondition_extra(can_p, timeout)
    result, _ = precondition_extra(can_p, timeout)

    ############################################
    # teststeps
    ############################################
    # step 1:
    # action: change BECM to programming
    # result: BECM reports mode
    result = SE22.read_did_f186(can_p, dsession=b'\x01')

    #if result:
    #while True:
    for _ in range(2):
        # step2:
        # action: check current sensor
        # result: BECM reports programmin session
        result = result and step_2(can_p)

        # step3:
        # action: send 'hard_reset' to BECM
        # result: BECM acknowledges message
        #result = step_3(can_p) and result
        result = result and step_3(can_p)

        # step4:
        # action: check current session
        # result: BECM reports default session
        #result = step_4(can_p) and result
        result = result and step_4(can_p)
        result = result and step_5(can_p)
        result = result and step_6(can_p)
        result = result and step_7(can_p)
        result = result and step_8(can_p)
        result = result and step_9(can_p)
        result = result and step_10(can_p)
        time.sleep(2)

    ############################################
    # postCondition
    ############################################

    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.DEBUG)
    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
