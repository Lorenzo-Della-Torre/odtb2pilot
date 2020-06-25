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

from support_can import SupportCAN, CanParam, PerParam
from support_test_odtb2 import SupportTestODTB2
from support_service22 import SupportService22
from support_service3e import SupportService3e


SC = SupportCAN()
SUTE = SupportTestODTB2()
SE22 = SupportService22()
SE3E = SupportService3e()

class SupportPrecondition:
    """
    class for supporting Service#11
    """

    @staticmethod
    def precondition(can_p: CanParam, timeout=300):
        """
        Precondition for test running:
        BECM has to be kept alive: start heartbeat
        """

        # start heartbeat, repeat every 0.8 second
        hb_param: PerParam = {
            "name" : "Heartbeat",
            "send" : True,
            "id" : "MvcmFront1NMFr",
            "nspace" : can_p["namespace"].name,
            "frame" : b'\x00\x40\xFF\xFF\xFF\xFF\xFF\xFF',
            "intervall" : 0.4
            }

        # start heartbeat, repeat every x second
        SC.start_heartbeat(can_p["netstub"], hb_param)

        #Start testerpresent without reply
        SE3E.start_periodic_tp_zero_suppress_prmib(can_p)

        ##record signal we send as well
        #SC.subscribe_signal(stub, can_receive, can_send, can_namespace, timeout)
        SC.subscribe_signal(can_p, timeout)
        print("precondition can_p2", can_p)
        #record signal we send as well
        can_p2: CanParam = {"netstub": can_p["netstub"],
                            "send": can_p["receive"],
                            "receive": can_p["send"],
                            "namespace": can_p["namespace"]
                           }
        SC.subscribe_signal(can_p2, timeout)

        result = SE22.read_did_eda0(can_p)
        logging.info("Precondition testok: %s\n", result)
        return result

    @staticmethod
    def precondition_burst(can_p: CanParam, timeout=300):
        """
        Precondition for test running:
        BECM has to be kept alive: start heartbeat
        """
        # start heartbeat, repeat every 0.8 second

        #send burst for 10seconds (10000 x 0.01 sec)
        #to enter prog
        burst_param: PerParam = {
            "name" : "Burst",
            "send" : True,
            "id" : "Vcu1ToAllFuncFront1DiagReqFrame",
            "nspace" : can_p["namespace"],
            "frame" : b'\x02\x10\x82\x00\x00\x00\x00\x00',
            "intervall" : 0.001
            }
        SC.send_burst(can_p["netstub"], burst_param, 600)

        hb_param: PerParam = {
            "name" : "Heartbeat",
            "send" : True,
            "id" : "MvcmFront1NMFr",
            "nspace" : can_p["namespace"].name,
            "frame" : b'\x00\x40\xFF\xFF\xFF\xFF\xFF\xFF',
            "intervall" : 0.4
            }
        SC.start_heartbeat(can_p["netstub"], hb_param)

        per_param: PerParam = {
            "name" : "Networkeptalive",
            "send" : True,
            "id" : "Vcu1ToAllFuncFront1DiagReqFrame",
            "nspace" : can_p["namespace"].name,
            "frame" : b'\x02\x3E\x80\x00\x00\x00\x00\x00',
            "intervall" : 1.02
            }
        SC.start_periodic(can_p["netstub"], per_param)

        SC.send_burst(can_p["netstub"], burst_param, 5000)

        SC.subscribe_signal(can_p, timeout)
        #record signal we send as well
        can_p2: CanParam = {"netstub": can_p["netstub"],
                            "send": can_p["receive"],
                            "receive": can_p["send"],
                            "namespace": can_p["namespace"],
                           }
        SC.subscribe_signal(can_p2, timeout)

        result = SE22.read_did_eda0(can_p)
        logging.info("Precondition testok: %s\n", result)
        return result

    @staticmethod
    def precondition_spa2(can_p: CanParam, timeout=300):
        """
        Precondition for test running:
        BECM has to be kept alive: start heartbeat
        """

        # start heartbeat, repeat every 0.8 second
        hb_param: PerParam = {
            "name" : "Heartbeat",
            "send" : True,
            "id" : "HvbmdpNmFrame", #SPA1: MvcmFront1NMFr",
            "nspace" : can_p["namespace"].name,
            "frame" : b'\x00\x40\xFF\xFF\xFF\xFF\xFF\xFF',
            "intervall" : 0.4
            }

        # start heartbeat, repeat every x second
        SC.start_heartbeat(can_p["netstub"], hb_param)

        #Start testerpresent without reply
        SE3E.start_periodic_tp_zero_suppress_prmib(can_p, 'HvbmdpToAllUdsDiagRequestFrame')

        ##record signal we send as well
        #SC.subscribe_signal(stub, can_receive, can_send, can_namespace, timeout)
        SC.subscribe_signal(can_p, timeout)
        #record signal we send as well
        can_p2: CanParam = {"netstub": can_p["netstub"],
                            "send": can_p["receive"],
                            "receive": can_p["send"],
                            "namespace": can_p["namespace"]
                           }
        SC.subscribe_signal(can_p2, timeout)

        result = SE22.read_did_eda0(can_p)
        logging.info("Precondition testok: %s\n", result)
        return result

    @staticmethod
    def precondition_burst_spa2(can_p: CanParam, timeout=300):
        """
        Precondition for test running:
        BECM has to be kept alive: start heartbeat
        """
        # start heartbeat, repeat every 0.8 second

        #send burst for 10seconds (10000 x 0.01 sec)
        #to enter prog
        burst_param: PerParam = {
            "name" : "Burst",
            "send" : True,
            "id" : "HvbmdpToAllUdsDiagRequestFrame",
            "nspace" : can_p["namespace"],
            "frame" : b'\x02\x10\x82\x00\x00\x00\x00\x00',
            "intervall" : 0.001
            }
        SC.send_burst(can_p["netstub"], burst_param, 600)

        hb_param: PerParam = {
            "name" : "Heartbeat",
            "send" : True,
            "id" : "HvbmdpNmFrame", #SPA1: MvcmFront1NMFr",
            "nspace" : can_p["namespace"].name,
            "frame" : b'\x00\x40\xFF\xFF\xFF\xFF\xFF\xFF',
            "intervall" : 0.4
            }
        # start heartbeat, repeat every x second
        SC.start_heartbeat(can_p["netstub"], hb_param)

        #Start testerpresent without reply
        SE3E.start_periodic_tp_zero_suppress_prmib(can_p, 'HvbmdpToAllUdsDiagRequestFrame')


        SC.send_burst(can_p["netstub"], burst_param, 5000)

        SC.subscribe_signal(can_p, timeout)
        #record signal we send as well
        can_p2: CanParam = {"netstub": can_p["netstub"],
                            "send": can_p["receive"],
                            "receive": can_p["send"],
                            "namespace": can_p["namespace"],
                           }
        SC.subscribe_signal(can_p2, timeout)

        result = SE22.read_did_eda0(can_p)
        logging.info("Precondition testok: %s\n", result)
        return result
