"""
The Python implementation of the gRPC route guide client.

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

# project:  Hilding testenvironment using SignalBroker
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
"""

import logging
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

        logging.info(
            "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Precondition started~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")

        #There is an issue in unsubscribe_signals() that generates a lot of errors in the log.
        #In order to not confuse users this was simply removed from the log by disabling the logger
        logger = logging.getLogger()
        logger.disabled = True

        # deregister signals
        # Adding unsubscribe in precondition to remove all the unwanted subscriptions
        # from the previous scripts if any.
        SC.unsubscribe_signals()

        logger.disabled = False

        #Temporary fix - add missing parameters in can_p
        for key in CanParam():
            if not key in can_p:
                can_p[key] = CanParam()[key]

        # start heartbeat, repeat every 0.4 second
        hb_param: PerParam = {
            "name" : "Heartbeat",
            "id" : "BecmFront1NMFr",
            "nspace" : can_p["namespace"],
            "frame" : b'\x1A\x40\xC3\xFF\x01\x00\x00\x00',
            "intervall" : 0.4
            }
        #Read current function name from stack:
        SIO.parameter_adopt_teststep(hb_param)
        hb_param["send"] = True
        logging.debug("hb_param %s", hb_param)

        # start heartbeat, repeat every x second
        SC.start_heartbeat(can_p["netstub"], hb_param)

        #Start testerpresent without reply
        tp_name = "Vcu1ToAllFuncFront1DiagReqFrame"
        #Read current function name from stack:
        new_tp_name = SIO.parameter_adopt_teststep("tp_name")

        if new_tp_name != '':
            tp_name = new_tp_name
        #logging.debug("New tp_name: %s", tp_name)
        SE3E.start_periodic_tp_zero_suppress_prmib(can_p, tp_name)

        ##record signal we send as well
        #SC.subscribe_signal(stub, can_receive, can_send, can_namespace, timeout)
        SC.subscribe_signal(can_p, timeout)
        logging.debug("precondition can_p2 %s", can_p)
        #record signal we send as well
        #can_p2: CanParam = {"netstub": can_p["netstub"],
        #                    "system_stub" : can_p["system_stub"],
        #                    "send": can_p["receive"],
        #                    "receive": can_p["send"],
        #                    "namespace": can_p["namespace"]
        #                   }
        can_p2 = CanParam()
        for i in can_p:
            can_p2[i] = can_p[i]
        can_p2["send"] = can_p["receive"]
        can_p2["receive"] = can_p["send"]

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
        SC.change_mf_fc(can_p2["receive"], can_mf)

        pn_sn_list = []
        SIO.parameter_adopt_teststep('pn_sn_list')

        result = SE22.read_did_f186(can_p, b'\01')
        logging.info("Precondition ECU Mode 1 checked usine 22F186: %s\n", result)

        result = SE22.read_did_eda0(can_p, pn_sn_list)
        logging.info("Precondition show all PN/SN using EDA0: %s\n", result)

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

        #Temporary fix - add missing parameters in can_p
        for key in CanParam():
            if not key in can_p:
                can_p[key] = CanParam()[key]

        #send burst for 10seconds (10000 x 0.01 sec)
        #to enter prog
        logging.info("Precondition: Sending burst")
        id_burst = "Vcu1ToAllFuncFront1DiagReqFrame"
        #Read current function name from stack:
        new_id_burst = SIO.parameter_adopt_teststep("id_burst")
        if new_id_burst != '':
            id_burst = new_id_burst
        SIO.parameter_adopt_teststep(id_burst)

        frame_burst = b'\x02\x10\x82\x00\x00\x00\x00\x00'
        #Read current function name from stack:
        new_frame_burst = SIO.parameter_adopt_teststep("frame_burst")
        if new_frame_burst != '':
            frame_burst = new_frame_burst
        SIO.parameter_adopt_teststep(frame_burst)

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
            "nspace" : can_p["namespace"],
            "frame" : b'\x1A\x40\xC3\xFF\x01\x00\x00\x00',
            "intervall" : 0.4
            }
        #Read current function name from stack:
        #logging.debug("Read YML for %s", str(inspect.stack()[0][3]))
        SIO.parameter_adopt_teststep(hb_param)
        logging.debug("hp_param %s", hb_param)

        # start heartbeat, repeat every x second
        SC.start_heartbeat(can_p["netstub"], hb_param)

        #Start testerpresent without reply
        tp_name = "Vcu1ToAllFuncFront1DiagReqFrame"
        #Read current function name from stack:
        new_tp_name = SIO.parameter_adopt_teststep("tp_name")
        if new_tp_name != '':
            tp_name = new_tp_name
        logging.debug("New tp_name: %s", tp_name)
        SE3E.start_periodic_tp_zero_suppress_prmib(can_p, tp_name)

        SC.send_burst(can_p["netstub"], burst_param, 5000)

        SC.subscribe_signal(can_p, timeout)
        #record signal we send as well
        can_p2: CanParam = {"netstub": can_p["netstub"],
                            "system_stub": can_p["system_stub"],
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

        pn_sn_list = []
        SIO.parameter_adopt_teststep('pn_sn_list')

        result = SE22.read_did_eda0(can_p, pn_sn_list)
        logging.info("Precondition testok: %s\n", result)
        return result
