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
import logging

from support_can import Support_CAN, CanParam, CanPayload, CanTestExtra
from support_test_odtb2 import Support_test_ODTB2


SC = Support_CAN()
SUTE = Support_test_ODTB2()

class SupportService31:
    """
    class for supporting Service#31
    """

    @staticmethod
    def routinecontrol_request_sid(can_p: CanParam,
                                   cpay: CanPayload, etp: CanTestExtra,
                                   stepno='310'
                                  ):
        """
        function used for BECM in Default or Extended mode
        """

        # verify RoutineControlRequest is sent for Type 1
        result = SUTE.teststep(can_p, cpay, stepno, etp)
        logging.info(SC.can_messages[can_p["rec"]])
        result = result and (
            SUTE.PP_Decode_Routine_Control_response(SC.can_messages[can_p["rec"]][0][2],
                                                    'Type1,Completed'))
        return result

    @staticmethod
    def routinecontrol_requestsid_prog_precond(can_p: CanParam, stepno='311'):
        """
        RC request - are programming preconditions fulfilled
        """
        # verify RoutineControlRequest is sent for Type 1
        cpay: CanPayload = {"m_send" : SC.can_m_send("RoutineControlRequestSID",
                                                     b'\x02\x06', b'\x01'),\
                            "mr_extra" : ''
                           }
        etp: CanTestExtra = {"purpose" : "verify RC start sent for Check Prog Precond",\
                             "timeout" : 0.05,\
                             "min_no_messages" : -1,\
                             "max_no_messages" : -1
                            }
        result = SupportService31.routinecontrol_request_sid(can_p, cpay, etp, stepno)
        #result = SUTE.teststep(can_p, cpay, stepno, etp)
        #logging.info(SC.can_messages[can_p["rec"]])
        #result = result and (
        #    SUTE.PP_Decode_Routine_Control_response(SC.can_messages[can_p["rec"]][0][2],
        #                                            'Type1,Completed'))
        return result

    @staticmethod
    def routinecontrol_requestsid_complete_compatible(can_p: CanParam, stepno='312'):
        """
        RC request - are programming preconditions fulfilled
        """
        # verify RoutineControlRequest is sent for Type 1
        cpay: CanPayload = {"m_send" : SC.can_m_send("RoutineControlRequestSID",\
                                            b'\x02\x05', b'\x01'),\
                            "mr_extra" : ''
                           }
        etp: CanTestExtra = {"purpose" : "verify complete and compatible",\
                             "timeout" : 1,\
                             "min_no_messages" : -1,\
                             "max_no_messages" : -1
                            }
        #testresult = SUTE.teststep(can_p, cpay, stepno, etp)
        #testresult = testresult and (
        #    SUTE.PP_Decode_Routine_Control_response(SC.can_messages[can_p["rec"]][0][2],
        #                                            'Type1,Completed'))

        result = SupportService31.routinecontrol_request_sid(can_p, cpay, etp, stepno)
        #testresult = SUTE.teststep(can_p, cpay, stepno, etp)
        #testresult = testresult and (
        #    SUTE.PP_Decode_Routine_Control_response(SC.can_messages[can_p["rec"]][0][2],
        #                                            'Type1,Completed'))
        return result


    @staticmethod
    def routinecontrol_requestsid_flash_erase(can_p: CanParam, erase, stepno='313'):
        """
        RC request - flash erase
        """
        # verify RoutineControlRequest is sent for Type 1
        cpay: CanPayload = {"m_send" : SC.can_m_send("RoutineControlRequestSID",\
                                            b'\xFF\x00' + erase, b'\x01'),\
                            "mr_extra" : ''
                           }
        etp: CanTestExtra = {"purpose" : "RC flash erase",\
                             "timeout" : 15,\
                             "min_no_messages" : -1,\
                             "max_no_messages" : -1
                            }
        result = SupportService31.routinecontrol_request_sid(can_p, cpay, etp, stepno)
        return result
