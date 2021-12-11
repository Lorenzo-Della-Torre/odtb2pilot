"""

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

# date:     2021-08-13
# version:  1.1
# changes:  support SecAcc_Gen2

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

The Python implementation of the gRPC route guide client.
"""
import logging

from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_can import SupportCAN, CanParam, CanPayload, CanTestExtra
from supportfunctions.support_file_io import SupportFileIO
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_sec_acc import SupportSecurityAccess
from supportfunctions.support_service22 import SupportService22

SSA = SupportSecurityAccess()
SC = SupportCAN()
SIO = SupportFileIO
SUTE = SupportTestODTB2()
S_CARCOM = SupportCARCOM()
SE22 = SupportService22()

class SupportService27:
    """
    class for supporting Service#27
    """


    @staticmethod
    def security_access_request_seed(can_p: CanParam, sa_keys, stepno=270,\
                                     purpose="SecurityAccessRequestSeed"):
        """
            Support function: request seed for calculating security access pin
        """

        #different request in mode 1/3 and mode2
        logging.info("PBL SecAcc req seed: determine current mode")

        result = True
        ecu_mode = SE22.get_ecu_mode(can_p)

        logging.info("PBL SecAcc req seed: current mode: %s",\
                     SC.can_messages[can_p["receive"]])

        if ecu_mode in ('DEF', 'EXT'):
            cpay: CanPayload =\
              {"payload" : S_CARCOM.can_m_send("SecurityAccessRequestSeed_mode1_3", b'', b''),\
               "extra" : ''
              }
        elif ecu_mode == 'PBL':
            #SA_GEN1:
            if sa_keys["SecAcc_Gen"] == 'Gen1':
                cpay: CanPayload =\
                      {"payload" : S_CARCOM.can_m_send("SecurityAccessRequestSeed", b'', b''),\
                       "extra" : ''
                      }
            #SA_GEN2:
            elif sa_keys["SecAcc_Gen"] == 'Gen2':
                SSA.set_level_key(1)
                payload = SSA.prepare_client_request_seed()
                cpay: CanPayload =\
                      {"payload" : payload,\
                       "extra" : ''
                      }
            else:
                logging.info("SA Gen not set.")
                logging.info("SS27, security_access_request_seed, sa_keys: %s", sa_keys)
                raise Exception("Failed:  SecurityAccess parameters not set.")

        elif ecu_mode == 'SBL':
            logging.info("SS27 sec_acc_req_seed: SBL already activated")
        else:
            logging.info("SS27 sec_acc_req_seed: unknown status")
            ### remove when EDA0 implemented in MEP2
            # use ecu_mode == 'PBL' as default while EDA0 not implemented in MEP2 SA_GEN2
            #SA_GEN2:
            SSA.set_level_key(1)
            payload = SSA.prepare_client_request_seed()
            cpay: CanPayload =\
                {"payload" : payload,\
                 "extra" : ''
                }
            ### remove when EDA0 implemented in MEP2

        etp: CanTestExtra = {"step_no": stepno,
                             "purpose" : purpose,
                             "timeout" : 1,
                             "min_no_messages" : 1,
                             "max_no_messages" : 1
                            }
        if ecu_mode == 'SBL':
            logging.info("SBL already active. Don't try to activate again.")
        else:
            result = SUTE.teststep(can_p, cpay, etp)
        #SA_GEN1:
        # return payload without request reply (6701)
        if sa_keys["SecAcc_Gen"] == 'Gen1':
            seed = SC.can_messages[can_p["receive"]][0][2][6:12]
        #SA_GEN2:
        # return complete payload from CAN-message (multiframe) with request reply (6701)
        # (implemented in SA2 c-library)
        elif sa_keys["SecAcc_Gen"] == 'Gen2':
            seed = SC.can_messages[can_p["receive"]][0][2][4:]
        #return payload from CAN-message (multiframe) without request reply (6701)
        #seed = SC.can_messages[can_p["receive"]][0][2][8:]
        else:
            logging.info("SA Gen not set.")
            logging.info("SS27, security_access_request_seed, sa_keys: %s", sa_keys)
            raise Exception("Failed:  SecurityAccess parameters not set.")

        return result, seed



    @staticmethod
    def security_access_send_key(can_p: CanParam, sa_keys, payload_value, stepno=271,\
                                     purpose="SecurityAccessSendKey"):
        """
            Support function: request seed for calculating security access pin
        """
        ecu_mode = SE22.get_ecu_mode(can_p)
        logging.info("Current ecu mode: %s", ecu_mode)
        #Security Access Send Key

        if ecu_mode in ('DEF', 'EXT'):
            cpay: CanPayload =\
              {"payload" : S_CARCOM.can_m_send("SecurityAccessSendKey_mode1_3",\
                    payload_value, b''),\
               "extra" : ''
              }
        elif ecu_mode == 'PBL':
            if sa_keys["SecAcc_Gen"] == 'Gen1':
            #SA_GEN1:
                cpay: CanPayload =\
                    {"payload" : S_CARCOM.can_m_send("SecurityAccessSendKey",\
                                 payload_value, b''),\
                     "extra" : ''
                    }
            #SA_GEN2:
            elif sa_keys["SecAcc_Gen"] == 'Gen2':
                cpay: CanPayload =\
                    {"payload" : payload_value,\
                     "extra" : ''
                    }
            else:
                logging.info("SA Gen not set.")
                logging.info("SS27, security_access_send_key, sa_keys: %s", sa_keys)
                raise Exception("Failed:  SecurityAccess parameters not set.")
        elif ecu_mode == 'SBL':
            logging.info("SS27 sec_acc_req_seed: SBL already activated")
        else:
            logging.info("SS27 sec_acc_req_seed: unknown status")
            ### remove when EDA0 implemented in MEP2
            # use ecu_mode == 'PBL' as default while EDA0 not implemented in MEP2 SA_GEN2
            logging.info("SS27 act as if PBL, SA Gen2. Payload: %s", payload_value)
            cpay: CanPayload =\
                {"payload" : payload_value,\
                 "extra" : ''
                }
            ### remove when EDA0 implemented in MEP2

        etp: CanTestExtra = {"step_no": stepno,\
                             "purpose" : purpose,\
                             "timeout" : 1,\
                             "min_no_messages" : 1,\
                             "max_no_messages" : 1
                            }
        result = SUTE.teststep(can_p, cpay, etp)
        #result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], '6702')
        #SA_GEN1:
        # return result
        #SA_GEN2:
        response = SC.can_messages[can_p["receive"]][0][2][6:(6+4)]
        return result, response


    def activate_security_access_fixedkey(self, can_p: CanParam, sa_keys, step_no, purpose):
        """
        Support function to activate the Security Access
        SA_GEN1:
        sa_keys: dict with fixed_key set
        SA_GEN2:
        sa_keys: dict with auth_key, proof_key set
        """
        #SA_GEN1:
        if sa_keys["SecAcc_Gen"] == 'Gen1':
            #Security Access request seed
            result, seed = self.security_access_request_seed(can_p, sa_keys, step_no, purpose)
            #solve task for SecAccess Gen1 using reply to seed and fixed_key
            sa_key_calculated = SSA.set_security_access_pins(seed, sa_keys)

            #Security Access Send Key
            result = result and self.security_access_send_key(can_p, sa_keys, sa_key_calculated,
                                                              step_no, purpose)

        #SA_GEN2:
        elif sa_keys["SecAcc_Gen"] == 'Gen2':
            # Set keys in SSA
            #SSA.set_keys(auth_key, proof_key)
            logging.info("SSA sa_keys param %s", sa_keys)
            SSA.set_keys(sa_keys)

            #Security Access request seed
            result, response = self.security_access_request_seed(can_p, sa_keys, step_no, purpose)

            logging.info("SA_Gen2: request seed result: %s", result)
            logging.info("SA_Gen2: request seed response: %s", response)
            success = SSA.process_server_response_seed(bytearray.fromhex(response))

            if success == 0:
                logging.info("SA_Gen2: process_server_response_seed %s", success)
                logging.info("SA_Gen2: success = 0 (ok)")
            else:
                logging.info("SA_Gen2: success = %s (not ok)", success)
                return False

            payload = SSA.prepare_client_send_key()
            logging.info("SA_Gen2: activate SBL: prepareclient sendkey: %s", payload)
            logging.info("SA_Gen2: activate SBL: prepareclient sendkey (hex): %s", payload.hex())
            logging.info("SA_Gen2: activate SBL: status before send %s", result)
            logging.info("SA_Gen2: activate SBL: security_access_send_key")

            #Security Access Send Key
            result2, response = self.security_access_send_key(can_p,
                                                              sa_keys,
                                                              payload, step_no, purpose)

            result = result and result2
            logging.info("SA_Gen2: activate SBL: status after send %s", result2)
            logging.info("SA_Gen2 send key response %s", response)
            success = SSA.process_server_response_key(bytearray.fromhex(response))

            logging.info("SA_Gen2: activate SBL: process_server_response_key %s", success)
            if success != 0:
                result = False
        else:
            logging.info("SA Gen not set.")
            logging.info("SS27, security_access_send_key, sa_keys: %s", sa_keys)
            raise Exception("Failed:  SecurityAccess parameters not set.")
        return result
