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


from support_can import Support_CAN, CanParam, CanPayload, CanTestExtra
from support_test_odtb2 import Support_test_ODTB2


SC = Support_CAN()
SUTE = Support_test_ODTB2()

class SupportService10:
    """
    class for supporting Service#10
    """

    @staticmethod
    def diagnostic_session_control(can_p: CanParam,
                                   etp: CanTestExtra,
                                   stepno='100',
                                   mode=b'\x01'):
        """
        Request session change to 'mode'
        """
        cpay: CanPayload = {"m_send" : SC.can_m_send("DiagnosticSessionControl", mode, ""),\
                            "mr_extra" : ''
                           }
        return SUTE.teststep(can_p, cpay, stepno, etp)

    @staticmethod
    def diagnostic_session_control_mode1(can_p: CanParam, stepno='101'):
        """
        Request session change to Mode1
        """
        etp: CanTestExtra = {"purpose" : "Change to default session(01)",\
                             "timeout" : 1,\
                             "min_no_messages" : 1,\
                             "max_no_messages" : 1
                            }
        return SupportService10.diagnostic_session_control(can_p, etp, stepno, b'\x01')

    @staticmethod
    def diagnostic_session_control_mode2(can_p: CanParam, stepno='102'):
        """
        Request session change to Mode2
        """
        etp: CanTestExtra = {"purpose" : "Change to programming session(02)",\
                             "timeout" : 1,\
                             "min_no_messages" : -1,\
                             "max_no_messages" : -1
                            }
        return SupportService10.diagnostic_session_control(can_p, etp, stepno, b'\x02')

    @staticmethod
    def diagnostic_session_control_mode3(can_p: CanParam, stepno='103'):
        """
        Request session change to Mode2
        """
        etp: CanTestExtra = {"purpose" : "Change to extended session(03)",\
                             "timeout" : 1,\
                             "min_no_messages" : 1,\
                             "max_no_messages" : 1
                            }
        return SupportService10.diagnostic_session_control(can_p, etp, stepno, b'\x03')
