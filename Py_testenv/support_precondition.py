# project:  ODTB2 testenvironment using SignalBroker
# author:   HWEILER (Hans-Klaus Weiler)
# date:     2020-05-29
# version:  1.0

# Initial version:
# version 1.0:
#   teststep    Common teststeps moved into support for dedicated service
#   pep8        coding is changed to confirm to pep8 (some code left, though)

# inspired by https://grpc.io/docs/tutorials/basic/python.html

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

import logging

from support_can import Support_CAN, CanParam
from support_test_odtb2 import Support_test_ODTB2
from support_service22 import SupportService22


SC = Support_CAN()
#CP = CanParam()
#CPAY = CanPayload()
SUTE = Support_test_ODTB2()
SE22 = SupportService22()

class SupportPrecondition:
    """
    class for supporting Service#11
    """

    #@classmethod
    @staticmethod
    #def precondition(self, stub, can_send, can_receive, can_namespace, timeout=300):
    def precondition(can_p: CanParam, timeout=300):
        """
        Precondition for test running:
        BECM has to be kept alive: start heartbeat
        """

        # start heartbeat, repeat every 0.8 second
        SC.start_heartbeat(can_p["netstub"], "MvcmFront1NMFr", "Front1CANCfg0",
                           b'\x00\x40\xFF\xFF\xFF\xFF\xFF\xFF', 0.4)

        SC.start_periodic(can_p["netstub"], "Networkeptalive",
                          True, "Vcu1ToAllFuncFront1DiagReqFrame",
                          "Front1CANCfg0", b'\x02\x3E\x80\x00\x00\x00\x00\x00', 1.02)

    #SC.subscribe_signal(stub, can_send, can_receive, can_namespace, timeout)
    ##record signal we send as well
    #SC.subscribe_signal(stub, can_receive, can_send, can_namespace, timeout)
        SC.subscribe_signal(can_p, timeout)
        #record signal we send as well
        can_p2: CanParam = {"netstub": can_p["netstub"],
                            "send": can_p["rec"],
                            "rec": can_p["send"],
                            "namespace": can_p["namespace"],
                            "namespace2": can_p["namespace"]
                           }
        SC.subscribe_signal(can_p2, timeout)

        result = SE22.read_did_eda0(can_p)
        logging.info("Precondition testok: %s\n", result)
        return result

    #@classmethod
    @staticmethod
    def precondition_burst(can_p: CanParam, timeout=300):
        """
        Precondition for test running:
        BECM has to be kept alive: start heartbeat
        """
        # start heartbeat, repeat every 0.8 second

        #send burst for 10seconds (10000 x 0.01 sec)
        #to enter prog
        SC.send_burst(can_p["netstub"], "Vcu1ToAllFuncFront1DiagReqFrame", can_p["namespace"],
                      b'\x02\x10\x82\x00\x00\x00\x00\x00', 0.001, 600)
        SC.start_heartbeat(can_p["netstub"], "MvcmFront1NMFr", "Front1CANCfg0",
                           b'\x00\x40\xFF\xFF\xFF\xFF\xFF\xFF', 0.4)

        SC.start_periodic(can_p["netstub"], "Networkeptalive",
                          True, "Vcu1ToAllFuncFront1DiagReqFrame",
                          "Front1CANCfg0", b'\x02\x3E\x80\x00\x00\x00\x00\x00', 1.02)

        SC.send_burst(can_p["netstub"], "Vcu1ToAllFuncFront1DiagReqFrame", can_p["namespace"],
                      b'\x02\x10\x82\x00\x00\x00\x00\x00', 0.001, 5000)
        # timeout = more than maxtime script takes
        #timeout = 1800   #Normally takes about 1000 seconds, give it some extra time"
        timeout = 3600   #Normally takes about 1000 seconds, give it some extra time"

        SC.subscribe_signal(can_p, timeout)
        #record signal we send as well
        can_p2: CanParam = {"netstub": can_p["netstub"],
                            "send": can_p["rec"],
                            "rec": can_p["send"],
                            "namespace": can_p["namespace"],
                            "namespace2": can_p["namespace"]
                           }
        SC.subscribe_signal(can_p2, timeout)

        result = SE22.read_did_eda0(can_p)
        logging.info("Precondition testok: %s\n", result)
        return result
