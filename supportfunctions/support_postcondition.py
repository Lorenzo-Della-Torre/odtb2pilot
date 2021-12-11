/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



**********************************************************************************/


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

"""The Python implementation of the gRPC route guide client."""

import logging
import time
from datetime import datetime

from supportfunctions.support_can import SupportCAN, CanParam
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_service10 import SupportService10
from supportfunctions.support_service22 import SupportService22

SC_CARCOM = SupportCARCOM()
SC = SupportCAN()
SE10 = SupportService10()
SE22 = SupportService22()

class SupportPostcondition: # pylint: disable=too-few-public-methods
    """
    class for supporting Postcondition
    """

    @staticmethod
    def postcondition(can_p: CanParam, starttime, result):
        """
        Precondition for test running:
        BECM has to be kept alive: start heartbeat
        """
        logging.info("Postcondition: Display current session, change to mode1 (default)")
        result = SE22.read_did_f186(can_p) and result
        SE10.diagnostic_session_control_mode1(can_p)
        #if coming from mode2 it may take a bit
        time.sleep(2)
        result = SE22.read_did_f186(can_p, b'\x01') and result

        logging.debug("\nTime: %s \n", time.time())
        logging.info("Testcase end: %s", datetime.now())
        logging.info("Time needed for testrun (seconds): %s", int(time.time() - starttime))

        logging.info("Do cleanup now...")
        logging.info("Stop all periodic signals sent")
        SC.stop_periodic_all()

        # deregister signals
        SC.unsubscribe_signals()
        # if threads should remain: try to stop them
        SC.thread_stop()

        logging.info("Test cleanup end: %s\n", datetime.now())

        if result:
            logging.info("Testcase result: PASSED")
        else:
            logging.info("Testcase result: FAILED")
