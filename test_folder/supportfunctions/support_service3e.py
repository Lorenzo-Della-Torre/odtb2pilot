# project:  ODTB2 testenvironment using SignalBroker
# author:   HWEILER (Hans-Klaus Weiler)
# date:     2020-06-01
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

from support_can import SupportCAN, CanParam, CanPayload, CanTestExtra, PerParam
from support_test_odtb2 import SupportTestODTB2

SC = SupportCAN()
SUTE = SupportTestODTB2()

class SupportService3e:
    """
    class for supporting Service#3E
    """

    @staticmethod
    def tester_present(can_p: CanParam, cpay: CanPayload, etp: CanTestExtra):
        """
        Support function for Request Transfer Exit
        """
        #cpay: CanPayload = {"payload" : b'\x3E',\
        #                    "extra" : ''
        #                   }
        #etp: CanTestExtra = {"purpose" : purpose,\
        #                     "timeout" : 0.2,\
        #                     "min_no_messages" : 1,\
        #                     "max_no_messages" : 1
        #                    }
        if not 'step_no' in etp:
            etp["step_no"] = 3140
        result = SUTE.teststep(can_p, cpay, etp)
        return result

    @staticmethod
    def tester_present_zero_subfunction(can_p: CanParam, stepno=3141):
        """
        Support function for Request Transfer Exit
        """
        cpay: CanPayload = {"payload" : b'\x3E\x00',\
                            "extra" : b''
                           }
        etp: CanTestExtra = {"step_no": stepno,\
                             "purpose" : "TesterPresent zero subfunction",\
                             "timeout" : 0.2,\
                             "min_no_messages" : 1,\
                             "max_no_messages" : 1
                            }
        testresult = SupportService3e.tester_present(can_p, cpay, etp)
        return testresult

    @staticmethod
    def tester_present_zero_suppress_prmib(can_p: CanParam, stepno=3142):
        """
        tester present zero with suppressPosRspMsgIndicationBit set
        """
        #testresult = True
        cpay: CanPayload = {"payload" : b'\x3E\x80',\
                            "extra" : b''
                           }
        etp: CanTestExtra = {"step_no": stepno,\
                             "purpose" : "TesterPresent zero subfunction",\
                             "timeout" : 0.2,\
                             "min_no_messages" : 1,\
                             "max_no_messages" : 1
                            }
        testresult = SupportService3e.tester_present(can_p, cpay, etp)
        return testresult

    @staticmethod
    def start_periodic_tp_zero_suppress_prmib(can_p: CanParam,\
                                              can_id="Vcu1ToAllFuncFront1DiagReqFrame",\
                                              periodic=1.02):
        """
        Support function for Request Transfer Exit
        """

        per_param: PerParam = {"name" : "TesterPresent_periodic",
                               "send": True,
                               "id": can_id,
                               "nspace": can_p["namespace"].name,
                               "frame": b'\x02\x3E\x80\x00\x00\x00\x00\x00',
                               "intervall": periodic
                               }
        SC.start_periodic(can_p["netstub"], per_param)

    @staticmethod
    def stop_periodic_tp_zero_suppress_prmib():
        """
        Support function for Request Transfer Exit
        """
        SC.stop_periodic("TesterPresent_periodic")
