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

from datetime import datetime
import time
import logging
import sys

import ODTB_conf

from support_can import SupportCAN, CanParam, PerParam, CanPayload, CanTestExtra
from support_test_odtb2 import SupportTestODTB2
from support_carcom import SupportCARCOM
from support_service22 import SupportService22

SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()
SE22 = SupportService22()


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


def precondition(can_p: CanParam, timeout=300):
    """
        precondition for test running:
        BECM has to be kept alive: start heartbeat
    """

    # start heartbeat, repeat every 0.8 second
    hb_param: PerParam = {
        "name" : "Heartbeat",
        "send" : True,
        "id" : "EcmFront1NMFr",
        "nspace" : can_p["namespace"].name,
        "frame" : b'\x20\x40\x00\xFF\x00\x00\x00\x00',
        "intervall" : 0.8
        }
    # start heartbeat, repeat every x second
    SC.start_heartbeat(can_p["netstub"], hb_param)

    # timeout = more than maxtime script takes
    # needed as thread for registered signals won't stop without timeout
    #timeout = 120   #seconds
    #timeout = 60   #seconds
    timeout = 0

    ##record signal we send as well
    SC.subscribe_signal(can_p, timeout)
    #record signal we send as well
    can_p2: CanParam = {"netstub": can_p["netstub"],
                        "send": can_p["receive"],
                        "receive": can_p["send"],
                        "namespace": can_p["namespace"]
                       }
    SC.subscribe_signal(can_p2, timeout)
    #   1305 BecmFront1NMFr: 8 BECM
    #   58 BECMFront1Fr01
    #   278 BECMFront1Fr02
    # subscribe to signal activated by NM-frame
    can_p3: CanParam = {"netstub": can_p["netstub"],
                        "send": "BECMFront1Fr01",
                        "receive": "BECMFront1Fr01",
                        "namespace": can_p["namespace"]
                       }
    SC.subscribe_signal(can_p3, timeout)
    result = SE22.read_did_eda0(can_p)
    #logging.info("Precondition result: {0}\n".format(result))
    logging.info("Precondition result: %s\n", result)
    return result


def step_2(can_p: CanParam):
    """
        teststep 2: request DID Counter for number of software resets
    """

    stepno = 2
    wait_start = time.time()
    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                         b'\xD0\x34', b''),
                        "extra" : b''
                       }
    etp: CanTestExtra = {"step_no": stepno,\
                         "purpose" : "request DID Counter for number of software resets",\
                         "timeout" : 0.4,\
                         "min_no_messages" : 1,\
                         "max_no_messages" : 1
                        }

    result = SUTE.teststep(can_p, cpay, etp)

    if not result:
        #logging.info("Received frames: {}:".format(SC.can_frames[can_p["receive"]]))
        sdf = SC.can_frames[can_p["receive"]]
        logging.info(f"Received frames: {sdf}")
        #logging.info("Received messages: {}:".format(SC.can_messages[can_p["receive"]]))
        logging.info("Received frames: %s:", SC.can_frames[can_p["receive"]])
        logging.info("Received messages: %s:", SC.can_frames[can_p["receive"]])
        SC.update_can_messages(can_p["receive"])
        #logging.info("can_mess_updated: {}:".format(SC.can_messages[can_p["receive"]]))
        logging.info("can_mess_updated: %s:", SC.can_frames[can_p["receive"]])
    if  frames_received("BECMFront1Fr01", 0.2) < 15:
        result = False
        logging.info("No NM-frames: test failed")
    #logging.info("Step {:d}: Result within {:.3f} seconds.".format\
    #                (stepno, (time.time()-wait_start)))
    logging.info("Step %s: Result within %s seconds.", stepno, (time.time()-wait_start))
    #logging.info("Step {0:d}: result: {1:}\n".format(stepno, result))
    logging.info("Step %s: result: %s\n", stepno, result)
    return result

def step_3(can_p: CanParam):
    """
        teststep 3: request DID SW reset type
    """
    stepno = 3
    wait_start = time.time()
    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                         b'\xDA\xC3', b''),
                        "extra" : b''
                       }
    etp: CanTestExtra = {"step_no": stepno,\
                         "purpose" : "request DID SW reset type",\
                         "timeout" : 0.4,\
                         "min_no_messages" : 1,\
                         "max_no_messages" : 1
                        }
    result = SUTE.teststep(can_p, cpay, etp)

    if not result:
        #logging.info("Received frames: {}:".format(SC.can_frames[can_p["receive"]]))
        #logging.info("Received messages: {}:".format(SC.can_messages[can_p["receive"]]))
        logging.info("Received frames: %s:", SC.can_frames[can_p["receive"]])
        logging.info("Received messages: %s:", SC.can_frames[can_p["receive"]])
        SC.update_can_messages(can_p["receive"])
        #logging.info("can_mess_updated: {}:".format(SC.can_messages[can_p["receive"]]))
        logging.info("can_mess_updated: %s:", SC.can_frames[can_p["receive"]])
    if  frames_received("BECMFront1Fr01", 0.2) < 15:
        result = False
        logging.info("No NM-frames: test failed")
    #logging.info("Step {:d}: Result within {:.3f} seconds.".format\
    #                (stepno, (time.time()-wait_start)))
    logging.info("Step %s: Result within %s seconds.", stepno, (time.time()-wait_start))
    #logging.info("Step {0:d}: result: {1:}\n".format(stepno, result))
    logging.info("Step %s: result: %s\n", stepno, result)
    return result


def step_4(can_p: CanParam):
    """
        teststep 4: request DID 5 last reset types
    """

    stepno = 4
    wait_start = time.time()
    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                         b'\xDA\xC6', b''),
                        "extra" : b''
                       }
    etp: CanTestExtra = {"step_no": stepno,\
                         "purpose" : "request DID 5 last reset types",\
                         "timeout" : 0.5,\
                         "min_no_messages" : 1,\
                         "max_no_messages" : 1
                        }
    result = SUTE.teststep(can_p, cpay, etp)

    if not result:
        #logging.info("Received frames: {}:".format(SC.can_frames[can_p["receive"]]))
        #logging.info("Received messages: {}:".format(SC.can_messages[can_p["receive"]]))
        logging.info("Received frames: %s:", SC.can_frames[can_p["receive"]])
        logging.info("Received messages: %s:", SC.can_frames[can_p["receive"]])
        SC.update_can_messages(can_p["receive"])
        #logging.info("can_mess_updated: {}:".format(SC.can_messages[can_p["receive"]]))
        logging.info("can_mess_updated: %s:", SC.can_frames[can_p["receive"]])
    if  frames_received("BECMFront1Fr01", 0.2) < 15:
        result = False
        logging.info("No NM-frames: test failed")
    #logging.info("Step {:d}: Result within {:.3f} seconds.".format\
    #                (stepno, (time.time()-wait_start)))
    logging.info("Step %s: Result within %s seconds.", stepno, (time.time()-wait_start))
    #logging.info("Step {0:d}: result: {1:}\n".format(stepno, result))
    logging.info("Step %s: result: %s\n", stepno, result)
    return result


# teststep 5: request DID 5 last reset types
def step_5(can_p: CanParam):
    """
        teststep 5: request DID 5 last reset types
    """

    stepno = 5
    wait_start = time.time()
    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                         b'\xFD\x71', b''),
                        "extra" : b''
                       }
    etp: CanTestExtra = {"step_no": stepno,\
                         "purpose" : "Lear special: request DID 5 last reset types",\
                         "timeout" : 3.5,\
                         "min_no_messages" : 1,\
                         "max_no_messages" : 1
                        }
    result = SUTE.teststep(can_p, cpay, etp)

    if not result:
        #logging.info("Received frames: {}:".format(SC.can_frames[can_p["receive"]]))
        #logging.info("Received messages: {}:".format(SC.can_messages[can_p["receive"]]))
        logging.info("Received frames: %s:", SC.can_frames[can_p["receive"]])
        logging.info("Received messages: %s:", SC.can_frames[can_p["receive"]])
        SC.update_can_messages(can_p["receive"])
        #logging.info("can_mess_updated: {}:".format(SC.can_messages[can_p["receive"]]))
        logging.info("can_mess_updated: %s:", SC.can_frames[can_p["receive"]])
    if  frames_received("BECMFront1Fr01", 0.2) < 15:
        result = False
        logging.info("No NM-frames: test failed")
    #logging.info("Step {:d}: Result within {:.3f} seconds.".format\
    #                (stepno, (time.time()-wait_start)))
    logging.info("Step %s: Result within %s seconds.", stepno, (time.time()-wait_start))
    #logging.info("Step {0:d}: result: {1:}\n".format(stepno, result))
    logging.info("Step %s: result: %s\n", stepno, result)
    return result


def step_6(can_p: CanParam):
    """
        teststep 6: request DID 5 last reset types
    """

    stepno = 6
    wait_start = time.time()
    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                         b'\xFD\x72', b''),
                        "extra" : b''
                       }
    etp: CanTestExtra = {"step_no": stepno,\
                         "purpose" : "Lear special: request DID 5 last reset types",\
                         "timeout" : 2,\
                         "min_no_messages" : 1,\
                         "max_no_messages" : 1
                        }
    result = SUTE.teststep(can_p, cpay, etp)

    #print("Received messages: ", SC.can_messages[can_p["receive"]])
    if not result:
        #logging.info("Received frames: {}:".format(SC.can_frames[can_p["receive"]]))
        #logging.info("Received messages: {}:".format(SC.can_messages[can_p["receive"]]))
        logging.info("Received frames: %s:", SC.can_frames[can_p["receive"]])
        logging.info("Received messages: %s:", SC.can_frames[can_p["receive"]])
        SC.update_can_messages(can_p["receive"])
        #logging.info("can_mess_updated: {}:".format(SC.can_messages[can_p["receive"]]))
        logging.info("can_mess_updated: %s:", SC.can_frames[can_p["receive"]])
    if  frames_received("BECMFront1Fr01", 0.2) < 15:
        result = False
        logging.info("No NM-frames: test failed")
    #logging.info("Step {:d}: Result within {:.3f} seconds.".format\
    #                (stepno, (time.time()-wait_start)))
    logging.info("Step %s: Result within %s seconds.", stepno, (time.time()-wait_start))
    #logging.info("Step {0:d}: result: {1:}\n".format(stepno, result))
    logging.info("Step %s: result: %s\n", stepno, result)
    return result



def step_7():
    """
        teststep 7: stop heartbeat, wait for BECM to stop sending frames
    """
    result = True

    stepno = 7
    purpose = "stop sending heartbeat, verify BECM stops traffic"

    logging.info("Step No. {:d}: purpose: {}".format(stepno, purpose))
    #print("Step No. ", stepno, " purpose: ", purpose)
    if  frames_received("BECMFront1Fr01", 0.2) < 15:
        result = False
        logging.info("No NM-frames: test failed.")
    logging.info("Stop heartbeat sent.")
    SC.stop_heartbeat()

    time.sleep(3)
    # Shouldn't recevie frames any longer now
    if  frames_received("BECMFront1Fr01", 0.2) > 0:
        result = False
        logging.info("No NM-frames: test failed.")
    #logging.info("Step {0:d}: result: {1:}\n".format(stepno, result))
    logging.info("Step %s: result: %s\n", stepno, result)
    return result


def step_8():
    """
        teststep 8: wait 1 Min for BECM to fall asleep
    """
    result = True

    stepno = 8
    purpose = "wait 1 Min for BECM to fall asleep"

    logging.info("Step No. {:d}: purpose: {}".format(stepno, purpose))
    time.sleep(60)

    # Shouldn't recevie frames any longer now
    if  frames_received("BECMFront1Fr01", 0.2) > 0:
        result = False
        logging.info("No NM-frames: test failed.")
    #logging.info("Step {0:d}: result: {1:}\n".format(stepno, result))
    logging.info("Step %s: result: %s\n", stepno, result)
    return result


def step_9(can_p: CanParam):
    """
        teststep 9: send wakeup frames again
    """
    result = True

    stepno = 9
    purpose = "send wakeup frames again, wait for BECM to be awake again"

    logging.info("Step No. {:d}: purpose: {}".format(stepno, purpose))
    hb_param: PerParam = {
        "name" : "Heartbeat",
        "send" : True,
        "id" : "EcmFront1NMFr",
        "nspace" : can_p["namespace"].name,
        "frame" : b'\x20\x40\x00\xFF\x00\x00\x00\x00',
        "intervall" : 0.8
        }
    # start heartbeat, repeat every x second
    SC.start_heartbeat(can_p["netstub"], hb_param)
    time.sleep(1)

    # Shouldn't recevie frames any longer now
    if  frames_received("BECMFront1Fr01", 0.2) < 15:
        result = False
        logging.info("No NM-frames: test failed.")
    #logging.info("Step {0:d}: result: {1:}\n".format(stepno, result))
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
    can_p: CanParam = {
        "netstub" : SC.connect_to_signalbroker(ODTB_conf.ODTB2_DUT, ODTB_conf.ODTB2_PORT),\
        "send" : "Vcu1ToBecmFront1DiagReqFrame",\
        "receive" : "BecmToVcu1Front1DiagResFrame",\
        "namespace" : SC.nspace_lookup("Front1CANCfg0")
        }

    logging.info("Testcase start: %s", datetime.now())
    starttime = time.time()
    logging.info("Time: %s \n", time.time())

    ############################################
    # precondition
    ############################################
    # timeout = 0 (run forever)
    precondition(can_p, 0)

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
        result = result and step_2(can_p)

        #   1305 BecmFront1NMFr: 8 BECM
        #   58 BECMFront1Fr01
        #   278 BECMFront1Fr02
        #frames_received("BECMFront1Fr01", 0.2)
        # step3:
        # action: send 'hard_reset' to BECM
        # result: BECM acknowledges message
        result = result and  step_3(can_p)
        #frames_received("BECMFront1Fr01", 0.2)

        # step4:
        # action: check current session
        # result: BECM reports default session
        result = result and  step_4(can_p)
        #frames_received("BECMFront1Fr01", 0.2)

        logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.DEBUG)
        result = result and  step_5(can_p)
        #frames_received("BECMFront1Fr01", 0.2)

        result = result and  step_6(can_p)
        #frames_received("BECMFront1Fr01", 0.2)
        #time.sleep(10)
        logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

        result = result and  step_7()
        result = result and  step_8()
        result = result and  step_9(can_p)


    ############################################
    # postCondition
    ############################################

    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.DEBUG)
    frames_received("BECMFront1Fr01", 0.2)
    frames_received("BECMFront1Fr01", 0.2)
    frames_received("BECMFront1Fr01", 0.2)
    frames_received("BECMFront1Fr01", 0.2)
    frames_received("BECMFront1Fr01", 0.2)
    frames_received("BECMFront1Fr01", 0.2)
    frames_received("BECMFront1Fr01", 0.2)
    frames_received("BECMFront1Fr01", 0.2)
    frames_received("BECMFront1Fr01", 0.2)
    frames_received("BECMFront1Fr01", 0.2)
    #print()
    logging.info("\nRedo step5, step6 after error occured.")
    #print("Redo step5, step6 after error occured")
    step_5(can_p)
    step_6(can_p)
    print()
    logging.info("\ntime {:.3f}".format(time.time()))
    logging.info("Testcase end: {:.3f}".format(datetime.now()))
    logging.info("Time needed for testrun (seconds): {:.3f}".format(int(time.time() - starttime)))
    #print("time ", time.time())
    #print("Testcase end: ", datetime.now())
    #print("Time needed for testrun (seconds): ", int(time.time() - starttime))

    logging.info("Do cleanup now...")
    logging.info("Stop heartbeat sent")
    #print("Do cleanup now...")
    #print("Stop heartbeat sent")
    SC.stop_heartbeat()

    # deregister signals
    SC.unsubscribe_signals()
    # if threads should remain: try to stop them
    SC.thread_stop()

    logging.info("Test cleanup end: {:.3f}\n".format(datetime.now()))
    #print("Test cleanup end: ", datetime.now())
    #print()
    if result:
        logging.info("Testcase result: PASSED")
        #print("Testcase result: PASSED")
    else:
        logging.info("Testcase result: FAILED")
        #print("Testcase result: FAILED")

if __name__ == '__main__':
    run()
