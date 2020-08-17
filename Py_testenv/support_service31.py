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
import time
import logging

from support_carcom import SupportCARCOM
from support_can import SupportCAN, CanParam, CanPayload, CanTestExtra
from support_test_odtb2 import SupportTestODTB2
from support_service22 import SupportService22


SC = SupportCAN()
SUTE = SupportTestODTB2()
S_CARCOM = SupportCARCOM()
SE22 = SupportService22()

class SupportService31:
    """
    class for supporting Service#31
    """

    @staticmethod
    def routinecontrol_request_sid(can_p: CanParam,
                                   cpay: CanPayload, etp: CanTestExtra
                                  ):
        """
        function used for BECM in Default or Extended mode
        """

        if not 'step_no' in etp:
            etp["step_no"] = 310
        # verify RoutineControlRequest is sent for Type 1
        result = SUTE.teststep(can_p, cpay, etp)
        logging.info(SC.can_messages[can_p["receive"]])
        result = result and (
            SUTE.pp_decode_routine_control_response(SC.can_messages[can_p["receive"]][0][2],
                                                    'Type1,Completed'))
        return result

    @staticmethod
    def routinecontrol_requestsid_prog_precond(can_p: CanParam, stepno=311):
        """
        RC request - are programming preconditions fulfilled
        """
        # verify RoutineControlRequest is sent for Type 1
        cpay: CanPayload = {"payload" : S_CARCOM.can_m_send("RoutineControlRequestSID",
                                                            b'\x02\x06', b'\x01'),\
                            "extra" : ''
                           }
        etp: CanTestExtra = {"step_no": stepno,\
                             "purpose" : "verify RC start sent for Check Prog Precond",\
                             "timeout" : 0.05,\
                             "min_no_messages" : -1,\
                             "max_no_messages" : -1
                            }
        result = SupportService31.routinecontrol_request_sid(can_p, cpay, etp)
        #result = SUTE.teststep(can_p, cpay, stepno, etp)
        #logging.info(SC.can_messages[can_p["receive"]])
        #result = result and (
        #    SUTE.pp_decode_routine_control_response(SC.can_messages[can_p["receive"]][0][2],
        #                                            'Type1,Completed'))
        return result

    @staticmethod
    def routinecontrol_requestsid_complete_compatible(can_p: CanParam, stepno=312):
        """
        RC request - are programming preconditions fulfilled
        """
        # verify RoutineControlRequest is sent for Type 1
        cpay: CanPayload = {"payload" : S_CARCOM.can_m_send("RoutineControlRequestSID",\
                                                           b'\x02\x05', b'\x01'),\
                            "extra" : ''
                           }
        etp: CanTestExtra = {"step_no": stepno,\
                             "purpose" : "verify complete and compatible",\
                             "timeout" : 1,\
                             "min_no_messages" : -1,\
                             "max_no_messages" : -1
                            }
        #testresult = SUTE.teststep(can_p, cpay, stepno, etp)
        #testresult = testresult and (
        #    SUTE.pp_decode_routine_control_response(SC.can_messages[can_p["receive"]][0][2],
        #                                            'Type1,Completed'))

        result = SupportService31.routinecontrol_request_sid(can_p, cpay, etp)
        #testresult = SUTE.teststep(can_p, cpay, stepno, etp)
        #testresult = testresult and (
        #    SUTE.pp_decode_routine_control_response(SC.can_messages[can_p["receive"]][0][2],
        #                                            'Type1,Completed'))
        return result


    @staticmethod
    def routinecontrol_requestsid_flash_erase(can_p: CanParam, header, stepno=313):
        """
        RC request - flash erase
        """
        #There may be several parts to be erase in VBF-header, loop over them

        print("SE31 header: ", header)
        for erase_el in header['erase']:
            # verify RoutineControlRequest is sent for Type 1
            result = SE22.read_did_eda0(can_p)
            cpay: CanPayload = {"payload" : S_CARCOM.can_m_send("RoutineControlRequestSID",\
                                                b'\xFF\x00' +\
                                                erase_el[0].to_bytes(4, byteorder='big') +\
                                                erase_el[1].to_bytes(4, byteorder='big'), b'\x01'),\
                                "extra" : ''
                               }
            etp: CanTestExtra = {"step_no": stepno,\
                                 "purpose" : "RC flash erase",\
                                 "timeout" : 1,\
                                 "min_no_messages" : -1,\
                                 "max_no_messages" : -1
                                }
            #start flash erase, may take long to erase
            result = SUTE.teststep(can_p, cpay, etp)
            logging.info("SE31 RC FlashErase 0xFF00 %s %s, result: %s",
                         erase_el[0].to_bytes(4, byteorder='big'),
                         erase_el[1].to_bytes(4, byteorder='big'),
                         result)

            rc_response = False
            rc_loop = 0
            logging.info("SE31 RC FlashErase wait max 15sec for flash erased")
            while (not rc_response) and (rc_loop < 15):
                SC.clear_can_message(can_p["receive"])
                SC.update_can_messages(can_p["receive"])
                if len(SC.can_messages[can_p["receive"]]) > 0:
                    for all_mess in SC.can_messages[can_p["receive"]]:
                        if all_mess[2].find('71') == 2:
                            logging.info(SC.can_messages[can_p["receive"]])
                            #try to decode message
                            result = result and (
                                SUTE.pp_decode_routine_control_response(all_mess[2],\
                                    'Type1,Completed'))
                            rc_response = True
                        elif  all_mess[2].find('7F') == 2:
                            logging.info(SUTE.pp_decode_7f_response(all_mess[2]))
                        else:
                            logging.info(SC.can_messages[can_p["receive"]])
                time.sleep(1)
                rc_loop += 1
            if rc_loop == 15:
                logging.info("SE31 RC FlashErase: No pos reply received in max time")
                result = False
        return result
