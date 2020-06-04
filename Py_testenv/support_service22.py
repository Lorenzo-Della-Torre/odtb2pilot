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

from support_can import SupportCAN, CanParam, CanPayload, CanTestExtra
from support_test_odtb2 import SupportTestODTB2
from support_carcom import SupportCARCOM

SC = SupportCAN()
SUTE = SupportTestODTB2()
SC_CARCOM = SupportCARCOM()

class SupportService22:
    """
    class for supporting Service#22
    """


    #@classmethod
    @staticmethod
    def read_did_eda0(can_p: CanParam):
        """
        Read composite DID EDA0: Complete ECU Part/Serial Number(s)
        """
        stepno = 220
        cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                             b'\xED\xA0', ""),
                            "extra" : ''
                           }
        etp: CanTestExtra = {"purpose" : "Service22: Complete ECU Part/Serial Number(s)",\
                             "timeout" : 1,\
                             "min_no_messages" : -1,\
                             "max_no_messages" : -1
                            }

    #can_m_send = SC.can_m_send("ReadDataByIdentifier", b'\xED\xA0', "")
    #can_mr_extra = ''

        result = SUTE.teststep(can_p, cpay, stepno, etp)
        if not len(SC.can_messages[can_p["rec"]]) == 0:
            logging.info('%s',\
                         SUTE.pp_combined_did_eda0(SC.can_messages[can_p["rec"]][0][2],\
                                                    title='')
                        )
        else:
            logging.info('%s', "No messages received for request Read DID EDA0")
            result = False
        return result

    #@classmethod
    @staticmethod
    #def read_did_f186(self, stub, can_send, can_receive, can_namespace, dsession=b''):
    def read_did_f186(can_p: CanParam, dsession=b''):
        """
        Read DID F186: Active Diagnostic Session
        """
        stepno = 221
        cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                             b'\xF1\x86', ""),
                            "extra" : dsession
                           }
        etp: CanTestExtra = {"purpose" : "Service22: Active Diagnostic Session",\
                             "timeout" : 1,\
                             "min_no_messages" : 1,\
                             "max_no_messages" : 1
                            }

        result = SUTE.teststep(can_p, cpay, stepno, etp)
        #time.sleep(1)
        return result
