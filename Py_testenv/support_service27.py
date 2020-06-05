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


from support_carcom import SupportCARCOM
from support_can import SupportCAN, CanParam, CanPayload, CanTestExtra
from support_test_odtb2 import SupportTestODTB2

SC = SupportCAN()
SUTE = SupportTestODTB2()
S_CARCOM = SupportCARCOM()

class SupportService27:
    """
    class for supporting Service#27
    """


    @staticmethod
    def pbl_security_access_request_seed(can_p: CanParam, stepno, purpose):
        """
            Support function: request seed for calculating security access pin
        """

        cpay: CanPayload = {"payload" : S_CARCOM.can_m_send("SecurityAccessRequestSeed", b'', b''),\
                            "extra" : ''
                           }
        etp: CanTestExtra = {"step_no": stepno,\
                             "purpose" : purpose,\
                             "timeout" : 1,\
                             "min_no_messages" : -1,\
                             "max_no_messages" : -1
                            }
        result = SUTE.teststep(can_p, cpay, etp)

        seed = SC.can_messages[can_p["receive"]][0][2][6:12]
        return result, seed



    @staticmethod
    def pbl_security_access_send_key(can_p: CanParam, payload_value, stepno, purpose):
        """
            Support function: request seed for calculating security access pin
        """
        #Security Access Send Key
        cpay: CanPayload = {"payload" : S_CARCOM.can_m_send("SecurityAccessSendKey",\
                                payload_value, b''),\
                            "extra" : ''
                           }
        etp: CanTestExtra = {"step_no": stepno,\
                             "purpose" : purpose,\
                             "timeout" : 0.1,\
                             "min_no_messages" : -1,\
                             "max_no_messages" : -1
                            }
        result = SUTE.teststep(can_p, cpay, etp)
        result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], '6702')
        return result
