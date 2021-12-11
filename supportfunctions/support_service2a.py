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
import inspect
#import time
from collections import namedtuple
from supportfunctions.support_can import SupportCAN, CanParam, CanPayload, CanTestExtra
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO

SC = SupportCAN()
SC_CARCOM = SupportCARCOM()
SUPPORT_TEST = SupportTestODTB2()
SIO = SupportFileIO

Infoentry = namedtuple('Infoentry', 'did name c_sid c_did c_size scal_val_list err_msg payload')

class SupportService2A:
    # These will take some more time to get rid of.
    # pylint: disable=eval-used,too-many-branches,too-many-locals,too-many-nested-blocks,undefined-variable,too-many-statements,too-many-arguments
    """
    class for supporting Service#2A
    """

    @staticmethod
    def read_did_eda0(can_p: CanParam,\
                      pn_sn_list=[], stepno=220): # pylint: disable=dangerous-default-value
        """
        Copy from Service#22, not having implemented Service#2A yet
        Read composite DID EDA0: Complete ECU Part/Serial Number(s)
        """
        cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                             b'\xED\xA0', b''),
                            "extra" : ''
                           }
        SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)

        etp: CanTestExtra = {"step_no": stepno,
                             "purpose" : "Service22: Complete ECU Part/Serial Number(s)",
                             "timeout" : 1,
                             "min_no_messages" : -1,
                             "max_no_messages" : -1
                            }
        SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)

        #pn_sn_list=[['F120', 'PN'],\
        #            ['F12A', 'PN'],\
        #            ['F12B', 'PN'],\
        #            ['F18C', 'SN'],\
        #            ['F12E', 'PN']]
        SIO.extract_parameter_yml(str(inspect.stack()[0][3]), 'pn_sn_list')

        result = SUPPORT_TEST.teststep(can_p, cpay, etp)
        if SC.can_messages[can_p["receive"]]:
            rec_message = SC.can_messages[can_p["receive"]][0][2]
            if pn_sn_list != []:
                logging.debug("S220: validate reply contains PN/SN: %s", pn_sn_list)
                result = result and\
                     SUPPORT_TEST.validate_combined_did_eda0(rec_message,
                                                             pn_sn_list,
                                                            )
            logging.info('%s',
                         SUPPORT_TEST.pp_combined_did_eda0(rec_message,
                                                           title=''))
        else:
            logging.info('%s', "No messages received for request Read DID EDA0")
            logging.info("Frames received: %s", SC.can_frames[can_p["receive"]])
            logging.info("Messages received: %s", SC.can_messages[can_p["receive"]])
            result = False
        return result

    @staticmethod
    def read_did_f186(can_p: CanParam, dsession=b'', stepno=221):
        """
        Copy from service#22, not having implemented Service#2A yet
        Read DID F186: Active Diagnostic Session
        """
        cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                             b'\xF1\x86', b''),
                            "extra" : dsession
                           }
        etp: CanTestExtra = {"step_no": stepno,
                             "purpose" : "Service22: Active Diagnostic Session",
                             "timeout" : 1,
                             "min_no_messages" : 1,
                             "max_no_messages" : 1
                            }

        result = SUPPORT_TEST.teststep(can_p, cpay, etp)
        #time.sleep(1)
        return result
