# Testscript ODTB2 MEPII
# project:  DID overnight test
# author:   hweiler (Hans-Klaus Weiler)
# date:     2020-05-04
# version:  1.0
# reqprod:  DID overnight test

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
#import logging
#import os
#import sys

import ODTB_conf

from support_can import Support_CAN
from support_test_odtb2 import Support_test_ODTB2
SC = Support_CAN()
SuTe = Support_test_ODTB2()


def frames_received(can_receive, timespan):
    """
        returns # of frames in can_receive buffer after timespan
    """

    SC.clear_all_can_frames()

    time.sleep(timespan)
    n_frames = len(SC.can_frames[can_receive])

    print("No. frames[", can_receive, "] received: ", n_frames)
    return n_frames


def precondition(stub, can_send, can_receive, can_namespace):
    """
        precondition for test running:
        BECM has to be kept alive: start heartbeat
    """

    # start heartbeat, repeat every 0.8 second
    SC.start_heartbeat(stub, "EcmFront1NMFr", "Front1CANCfg0",\
                       b'\x20\x40\x00\xFF\x00\x00\x00\x00', 0.8)

    # timeout = more than maxtime script takes
    # needed as thread for registered signals won't stop without timeout
    #timeout = 120   #seconds
    #timeout = 60   #seconds
    timeout = 0

    SC.subscribe_signal(stub, can_send, can_receive, can_namespace, timeout)
    #record signal we send as well
    SC.subscribe_signal(stub, can_receive, can_send, can_namespace, timeout)

#   1305 BecmFront1NMFr: 8 BECM
#   58 BECMFront1Fr01
#   278 BECMFront1Fr02
    # subscribe to signal activated by NM-frame
    SC.subscribe_signal(stub, "BECMFront1Fr01", "BECMFront1Fr01", can_namespace, timeout)
    print()
    step_0(stub, can_send, can_receive, can_namespace)

def step_0(stub, can_send, can_receive, can_namespace):
    """
        teststep 0: Complete ECU Part/Serial Number(s)
    """

    stepno = 0
    ts_param = {"stub" : stub,\
                "m_send" : SC.can_m_send("ReadDataByIdentifier", b'\xED\xA0', ""),\
                "mr_extra" : '',\
                "can_send" : can_send,\
                "can_rec"  : can_receive,\
                "can_nspace" : can_namespace\
               }
    extra_param = {"purpose" : "Complete ECU Part/Serial Number(s)",\
                   "timeout" : 5,\
                   "min_no_messages" : 1,\
                   "max_no_messages" : 1
                  }

    testresult = SuTe.teststep(ts_param,\
                           stepno, extra_param)
    print(SuTe.PP_CombinedDID_EDA0(SC.can_messages[can_receive][0][2], title=''))
    return testresult

def step_1(stub, can_send, can_receive, can_namespace):
    """
        teststep 1: verify session
    """

    stepno = 1
    ts_param = {"stub" : stub,\
                "m_send" : SC.can_m_send("ReadDataByIdentifier", b'\xF1\x86', ""),\
                "mr_extra" : b'\x01',\
                "can_send" : can_send,\
                "can_rec"  : can_receive,\
                "can_nspace" : can_namespace\
               }
    extra_param = {"purpose" : "Verify default session",\
                   "timeout" : 0.5,\
                   "min_no_messages" : 1,\
                   "max_no_messages" : 1
                  }
    return SuTe.teststep(ts_param,\
                         stepno, extra_param)

def step_2(stub, can_send, can_receive, can_namespace):
    """
        teststep 2: request DID Counter for number of software resets
    """

    stepno = 2
    wait_start = time.time()
    ts_param = {"stub" : stub,\
                "m_send" : SC.can_m_send("ReadDataByIdentifier", b'\xD0\x34', b''),\
                "mr_extra" : '',\
                "can_send" : can_send,\
                "can_rec"  : can_receive,\
                "can_nspace" : can_namespace\
               }
    extra_param = {"purpose" : "request DID Counter for number of software resets",\
                   "timeout" : 0.4,\
                   "min_no_messages" : 1,\
                   "max_no_messages" : 1
                  }
    testresult = SuTe.teststep(ts_param,\
                               stepno, extra_param)
    if not testresult:
        print("Received frames: ", SC.can_frames[can_receive])
        print("Received messages: ", SC.can_messages[can_receive])
        SC.update_can_messages(can_receive)
        print("can_mess_updated ", SC.can_messages[can_receive])
    if  frames_received("BECMFront1Fr01", 0.2) < 15:
        testresult = False
        print("No NM-frames: test failed")
    print("Step", stepno, ": Result within ", "{:7.3f}".format(time.time()-wait_start), "seconds.")
    return testresult

def step_3(stub, can_send, can_receive, can_namespace):
    """
        teststep 3: request DID SW reset type
    """

    stepno = 3
    wait_start = time.time()
    ts_param = {"stub" : stub,\
                "m_send" : SC.can_m_send("ReadDataByIdentifier", b'\xDA\xC3', b''),\
                "mr_extra" : '',\
                "can_send" : can_send,\
                "can_rec"  : can_receive,\
                "can_nspace" : can_namespace\
               }
    extra_param = {"purpose" : "request DID SW reset type",\
                   "timeout" : 0.4,\
                   "min_no_messages" : 1,\
                   "max_no_messages" : 1\
                  }
    testresult = SuTe.teststep(ts_param,\
                               stepno, extra_param)
    if not testresult:
        print("Received frames: ", SC.can_frames[can_receive])
        print("Received messages: ", SC.can_messages[can_receive])
        SC.update_can_messages(can_receive)
        print("can_mess_updated ", SC.can_messages[can_receive])
    if  frames_received("BECMFront1Fr01", 0.2) < 15:
        testresult = False
        print("No NM-frames: test failed")
    print("Step", stepno, ": Result within ", "{:7.3f}".format(time.time()-wait_start), "seconds.")
    return testresult


def step_4(stub, can_send, can_receive, can_namespace):
    """
        teststep 4: request DID 5 last reset types
    """

    stepno = 4
    wait_start = time.time()
    ts_param = {"stub" : stub,\
                "m_send" : SC.can_m_send("ReadDataByIdentifier", b'\xDA\xC6', b''),\
                "mr_extra" : '',\
                "can_send" : can_send,\
                "can_rec"  : can_receive,\
                "can_nspace" : can_namespace\
               }
    extra_param = {"purpose" : "request DID 5 last reset types",\
                   "timeout" : 0.5,\
                   "min_no_messages" : 1,\
                   "max_no_messages" : 1\
                  }
    testresult = SuTe.teststep(ts_param,\
                               stepno, extra_param)
    if not testresult:
        print("Received frames: ", SC.can_frames[can_receive])
        print("Received messages: ", SC.can_messages[can_receive])
        SC.update_can_messages(can_receive)
        print("can_mess_updated ", SC.can_messages[can_receive])
    if  frames_received("BECMFront1Fr01", 0.2) < 15:
        testresult = False
        print("No NM-frames: test failed")
    print("Step", stepno, ": Result within ", "{:7.3f}".format(time.time()-wait_start), "seconds.")
    return testresult


# teststep 5: request DID 5 last reset types
def step_5(stub, can_send, can_receive, can_namespace):
    """
        teststep 5: request DID 5 last reset types
    """

    stepno = 5
    wait_start = time.time()
    ts_param = {"stub" : stub,\
                "m_send" : SC.can_m_send("ReadDataByIdentifier", b'\xFD\x71', b''),\
                "mr_extra" : '',\
                "can_send" : can_send,\
                "can_rec"  : can_receive,\
                "can_nspace" : can_namespace\
               }
    extra_param = {"purpose" : "request DID 5 last reset types",\
                   "timeout" : 0.9,\
                   "min_no_messages" : -1,\
                   "max_no_messages" : -1\
                  }
    testresult = SuTe.teststep(ts_param,\
                               stepno, extra_param)
    if not testresult:
        print("Received frames: ", SC.can_frames[can_receive])
        print("Received messages: ", SC.can_messages[can_receive])
        SC.update_can_messages(can_receive)
        print("can_mess_updated ", SC.can_messages[can_receive])
    if  frames_received("BECMFront1Fr01", 0.2) < 15:
        testresult = False
        print("No NM-frames: test failed")
    print("Step", stepno, ": Result within ", "{:7.3f}".format(time.time()-wait_start), "seconds.")
    return testresult


def step_6(stub, can_send, can_receive, can_namespace):
    """
        teststep 6: request DID 5 last reset types
    """

    stepno = 6
    wait_start = time.time()
    ts_param = {"stub" : stub,\
                "m_send" : SC.can_m_send("ReadDataByIdentifier", b'\xFD\x72', b''),\
                "mr_extra" : '',\
                "can_send" : can_send,\
                "can_rec"  : can_receive,\
                "can_nspace" : can_namespace\
               }
    extra_param = {"purpose" : "request DID 5 last reset types",\
                   "timeout" : 0.4,\
                   "min_no_messages" : -1,\
                   "max_no_messages" : -1\
                  }
    testresult = SuTe.teststep(ts_param,\
                               stepno, extra_param)
    if not testresult:
        print("Received frames: ", SC.can_frames[can_receive])
        print("Received messages: ", SC.can_messages[can_receive])
        SC.update_can_messages(can_receive)
        print("can_mess_updated ", SC.can_messages[can_receive])
    if  frames_received("BECMFront1Fr01", 0.2) < 15:
        testresult = False
        print("No NM-frames: test failed")
    print("Step", stepno, ": Result within ", "{:7.3f}".format(time.time()-wait_start), "seconds.")
    return testresult



def run():
    """
        OnTheFly testscript
    """

    #start logging
    # to be implemented

    # where to connect to signal_broker
    network_stub = SC.connect_to_signalbroker(ODTB_conf.ODTB2_DUT, ODTB_conf.ODTB2_PORT)

    can_send = "Vcu1ToBecmFront1DiagReqFrame"
    can_receive = "BecmToVcu1Front1DiagResFrame"
    can_namespace = SC.nspace_lookup("Front1CANCfg0")

    print("Testcase start: ", datetime.now())
    starttime = time.time()
    print("time ", time.time())
    print()
    ############################################
    # precondition
    ############################################
    precondition(network_stub, can_send, can_receive, can_namespace)

    ############################################
    # teststeps
    ############################################
    # step 1:
    # action: change BECM to programming
    # result: BECM reports mode
    testresult = step_1(network_stub, can_send, can_receive, can_namespace)

    while testresult:
        # step2:
        # action: check current session
        # result: BECM reports programmin session
        testresult = testresult and step_2(network_stub, can_send, can_receive, can_namespace)

        #   1305 BecmFront1NMFr: 8 BECM
        #   58 BECMFront1Fr01
        #   278 BECMFront1Fr02
        #frames_received("BECMFront1Fr01", 0.2)
        # step3:
        # action: send 'hard_reset' to BECM
        # result: BECM acknowledges message
        testresult = testresult and  step_3(network_stub, can_send, can_receive, can_namespace)
        #frames_received("BECMFront1Fr01", 0.2)

        # step4:
        # action: check current session
        # result: BECM reports default session
        testresult = testresult and  step_4(network_stub, can_send, can_receive, can_namespace)
        #frames_received("BECMFront1Fr01", 0.2)

        testresult = testresult and  step_5(network_stub, can_send, can_receive, can_namespace)
        #frames_received("BECMFront1Fr01", 0.2)

        testresult = testresult and  step_6(network_stub, can_send, can_receive, can_namespace)
        #frames_received("BECMFront1Fr01", 0.2)
        #time.sleep(10)


    ############################################
    # postCondition
    ############################################

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
    print()
    print("Redo step5, step6 after error occured")
    step_5(network_stub, can_send, can_receive, can_namespace)
    step_6(network_stub, can_send, can_receive, can_namespace)
    print()
    print("time ", time.time())
    print("Testcase end: ", datetime.now())
    print("Time needed for testrun (seconds): ", int(time.time() - starttime))

    print("Do cleanup now...")
    print("Stop heartbeat sent")
    SC.stop_heartbeat()

    # deregister signals
    SC.unsubscribe_signals()
    # if threads should remain: try to stop them
    SC.thread_stop()

    print("Test cleanup end: ", datetime.now())
    print()
    if testresult:
        print("Testcase result: PASSED")
    else:
        print("Testcase result: FAILED")

if __name__ == '__main__':
    run()
