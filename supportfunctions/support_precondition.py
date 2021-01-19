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
import inspect
import time

from supportfunctions.support_can import SupportCAN, CanParam, PerParam, CanMFParam
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_service3e import SupportService3e
from supportfunctions.support_file_io import SupportFileIO


SC = SupportCAN()
SUTE = SupportTestODTB2()
SE22 = SupportService22()
SE3E = SupportService3e()
SIO = SupportFileIO

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
            "frame" : b'\x1A\x40\xC3\xFF\x01\x00\x00\x00',
            "intervall" : 0.4
            }
        #Read current function name from stack:
        #logging.debug("hb_param before %s", hb_param)
        #logging.debug("Type frame: %s", type(hb_param["frame"]))
        #logging.debug("Read YML for %s", str(inspect.stack()[0][3]))
        SIO.extract_parameter_yml(str(inspect.stack()[0][3]), hb_param)
        logging.debug("hb_param %s", hb_param)

        # start heartbeat, repeat every x second
        SC.start_heartbeat(can_p["netstub"], hb_param)

        #Start testerpresent without reply
        tp_name = "Vcu1ToAllFuncFront1DiagReqFrame"
        #Read current function name from stack:
        new_tp_name = SIO.extract_parameter_yml(str(inspect.stack()[0][3]), "tp_name")
        if new_tp_name != '':
            tp_name = new_tp_name
        #logging.debug("New tp_name: %s", tp_name)
        SE3E.start_periodic_tp_zero_suppress_prmib(can_p, tp_name)

        ##record signal we send as well
        #SC.subscribe_signal(stub, can_receive, can_send, can_namespace, timeout)
        SC.subscribe_signal(can_p, timeout)
        logging.debug("precondition can_p2 %s", can_p)
        #record signal we send as well
        can_p2: CanParam = {"netstub": can_p["netstub"],
                            "send": can_p["receive"],
                            "receive": can_p["send"],
                            "namespace": can_p["namespace"]
                           }
        SC.subscribe_signal(can_p2, timeout)
        #Don't generate FC frames for signals we generated:
        time.sleep(1)

        can_mf: CanMFParam = {
            "block_size": 0,
            "separation_time": 0,
            "frame_control_delay": 10,
            "frame_control_flag": 48,
            "frame_control_auto": False
            }
        #SC.change_mf_fc(can_p["send"], can_mf)
        SC.change_mf_fc(can_p2["receive"], can_mf)

        #pn_sn_list=[['F120', 'PN'],\
        #            ['F12A', 'PN'],\
        #            ['F12B', 'PN'],\
        #            ['F18C', 'SN'],\
        #            ['F12E', 'PN'],\
        #            ['F126', 'VIDCV']]
        pn_sn_list = []
        SIO.extract_parameter_yml(str(inspect.stack()[0][3]), 'pn_sn_list')

        result = SE22.read_did_eda0(can_p, pn_sn_list)
        logging.info("Precondition EDA0: %s\n", result)
        result = SE22.read_did_pbl_pn(can_p) and result
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
        logging.info("Precondition: Sending burst")
        id_burst = "Vcu1ToAllFuncFront1DiagReqFrame"
        #Read current function name from stack:
        new_id_burst = SIO.extract_parameter_yml(str(inspect.stack()[0][3]), "id_burst")
        if new_id_burst != '':
            id_burst = new_id_burst
        SIO.extract_parameter_yml(str(inspect.stack()[0][3]), id_burst)

        frame_burst = b'\x02\x10\x82\x00\x00\x00\x00\x00'
        #Read current function name from stack:
        new_frame_burst = SIO.extract_parameter_yml(str(inspect.stack()[0][3]), "frame_burst")
        if new_frame_burst != '':
            frame_burst = new_frame_burst
        SIO.extract_parameter_yml(str(inspect.stack()[0][3]), frame_burst)

        burst_param: PerParam = {
            "name" : "Burst",
            "send" : True,
            "id" : id_burst,
            "nspace" : can_p["namespace"],
            "frame" : frame_burst,
            "intervall" : 0.001
            }
        SC.send_burst(can_p["netstub"], burst_param, 600)

        # start heartbeat, repeat every 0.4 second
        hb_param: PerParam = {
            "name" : "Heartbeat",
            "send" : True,
            "id" : "MvcmFront1NMFr",
            "nspace" : can_p["namespace"].name,
            "frame" : b'\x1A\x40\xC3\xFF\x01\x00\x00\x00',
            "intervall" : 0.4
            }
        #Read current function name from stack:
        logging.debug("Read YML for %s", str(inspect.stack()[0][3]))
        SIO.extract_parameter_yml(str(inspect.stack()[0][3]), hb_param)
        logging.debug("hp_param %s", hb_param)

        # start heartbeat, repeat every x second
        SC.start_heartbeat(can_p["netstub"], hb_param)

        #Start testerpresent without reply
        tp_name = "Vcu1ToAllFuncFront1DiagReqFrame"
        #Read current function name from stack:
        new_tp_name = SIO.extract_parameter_yml(str(inspect.stack()[0][3]), "tp_name")
        if new_tp_name != '':
            tp_name = new_tp_name
        logging.debug("New tp_name: %s", tp_name)
        SE3E.start_periodic_tp_zero_suppress_prmib(can_p, tp_name)

        SC.send_burst(can_p["netstub"], burst_param, 5000)

        SC.subscribe_signal(can_p, timeout)
        #record signal we send as well
        can_p2: CanParam = {"netstub": can_p["netstub"],
                            "send": can_p["receive"],
                            "receive": can_p["send"],
                            "namespace": can_p["namespace"],
                           }
        SC.subscribe_signal(can_p2, timeout)
        #Don't generate FC frames for signals we generated:
        time.sleep(1)

        can_mf: CanMFParam = {
            "block_size": 0,
            "separation_time": 0,
            "frame_control_delay": 10,
            "frame_control_flag": 48,
            "frame_control_auto": False
            }
        #SC.change_mf_fc(can_p["send"], can_mf)
        SC.change_mf_fc(can_p2["receive"], can_mf)

        result = SE22.read_did_eda0(can_p)
        logging.info("Precondition testok: %s\n", result)
        return result