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
    def security_access_request_seed(can_p: CanParam, sa_keys, stepno=270,
                                     purpose="SecurityAccessRequestSeed"):
        """
            Support function: request seed for calculating security access pin
        """
        def __prepare_request(sa_keys, ecu_mode):
            #SA_GEN1:
            if sa_keys["SecAcc_Gen"] == 'Gen1':
                if ecu_mode == "EXT":
                    payload = S_CARCOM.can_m_send("SecurityAccessRequestSeed_mode1_3", b'', b'')
                else:
                    payload = S_CARCOM.can_m_send("SecurityAccessRequestSeed", b'', b'')

                cpay: CanPayload =\
                        {"payload" : payload,\
                        "extra" : ''
                        }
            #SA_GEN2:
            elif sa_keys["SecAcc_Gen"] == 'Gen2':

                if ecu_mode in ('PBL', 'SBL'):
                    SSA.set_level_key(1)
                elif ecu_mode == "EXT":
                    SSA.set_level_key(5)

                try:
                    payload = SSA.prepare_client_request_seed()
                except OSError:
                    return dict()

                cpay: CanPayload =\
                        {"payload" : payload,\
                        "extra" : ''
                        }
            else:
                logging.info("SA Gen not set.")
                logging.info("SS27, security_access_request_seed, sa_keys: %s", sa_keys)
                raise Exception("Failed:  SecurityAccess parameters not set.")

            logging.info("Seed requested from ECU using the following message (hex): %s",
                         payload.hex())
            return cpay

        def __evaluate_response(sa_keys):
            internal_response = SC.can_messages[can_p["receive"]][0][2]

            # Find if ECU replied with NRC
            if internal_response[2:4] == "7F":
                logging.error("The ECU replied with NRC when requesting seed. ECU response: %s",
                    internal_response)
                return False, ""
            #SA_GEN1:
            # return payload without request reply (6701)
            if sa_keys["SecAcc_Gen"] == 'Gen1':
                seed = SC.can_messages[can_p["receive"]][0][2][6:12]
            #SA_GEN2:
            # return complete payload from CAN-message (multiframe) with request reply (6701)
            # (implemented in SA2 c-library)
            elif sa_keys["SecAcc_Gen"] == 'Gen2':
                seed = SC.can_messages[can_p["receive"]][0][2][4:]

            return True, seed

        #different request in mode 1/3 and mode2
        logging.debug("PBL SecAcc req seed: determine current mode")

        result = False
        seed = ""
        ecu_mode = SE22.get_ecu_mode(can_p)

        logging.info("SecAcc req seed: Current ECU Session : %s",ecu_mode)

        # have to distinguish mode2 from DEF, EXT
        # in DEF, EXT service 2705 has to be used instead of service 2701 in mode2
        if ecu_mode in ('DEF', 'EXT', 'PBL'):
            cpay = __prepare_request(sa_keys, ecu_mode)
            if bool(cpay) is False:
                return False, ""
        elif ecu_mode == 'SBL':
            logging.info("SS27 sec_acc_req_seed: SBL already activated")
            cpay = __prepare_request(sa_keys, ecu_mode)
            if bool(cpay) is False:
                return False, ""
        else:
            logging.debug("SS27 sec_acc_req_seed: ECU current session Unknown")
            ### remove when EDA0 implemented in MEP2
            # use ecu_mode == 'PBL' as default while EDA0 not implemented in MEP2 SA_GEN2
            #SA_GEN2:
            cpay = __prepare_request(sa_keys, "PBL")
            if bool(cpay) is False:
                return False, ""
            ### remove when EDA0 implemented in MEP2

        etp: CanTestExtra = {"step_no": stepno,
                             "purpose" : purpose,
                             "timeout" : 1,
                             "min_no_messages" : 1,
                             "max_no_messages" : 1
                            }
        SUTE.teststep(can_p, cpay, etp)

        result, seed = __evaluate_response(sa_keys)

        return result, seed



    @staticmethod
    def security_access_send_key(can_p: CanParam, sa_keys, payload_value, stepno=271,\
                                     purpose="SecurityAccessSendKey"):
        """
            Support function: request seed for calculating security access pin
        """
        #set default response value
        response = 'ffffff'

        def __evaluate_response(sa_keys):
            # SA_GEN1:
            if sa_keys["SecAcc_Gen"] == 'Gen1':
                result = SUTE.test_message(SC.can_messages[can_p["receive"]], '6702')
                return result, ""
            # SA_GEN2:
            if sa_keys["SecAcc_Gen"] == 'Gen2':
                internal_response = SC.can_messages[can_p["receive"]][0][2]

                if internal_response[2:4] == "7F":
                    logging.error("The ECU replied with NRC when sending key to the ECU. "
                        "Response from the ECU: %s", internal_response)
                    return False, ""

                return True, internal_response[2:(2+4)]

            return False, ""

        ecu_mode = SE22.get_ecu_mode(can_p)
        logging.info("Current ecu mode: %s", ecu_mode)
        #Security Access Send Key

        if ecu_mode in ('DEF', 'EXT'):
            if sa_keys["SecAcc_Gen"] == 'Gen1':
                cpay: CanPayload =\
                {"payload" : S_CARCOM.can_m_send("SecurityAccessSendKey_mode1_3",\
                    payload_value, b''),}

            elif sa_keys["SecAcc_Gen"] == 'Gen2':
                cpay: CanPayload =\
                {"payload" : payload_value,
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
            logging.debug("SS27 sec_acc_req_seed: unknown status")
            ### remove when EDA0 implemented in MEP2
            # use ecu_mode == 'PBL' as default while EDA0 not implemented in MEP2 SA_GEN2
            logging.info("SS27 act as if PBL, SA Gen2. Payload: %s", payload_value.hex())
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

        if result:
            result, response = __evaluate_response(sa_keys)

        return result, response


    def activate_security_access_seed_and_calc(self,
                                               can_p: CanParam,
                                               sa_keys,
                                               step_no=272,
                                               purpose="SecurityAccess"):
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

            ##Security Access Send Key
            #result = result and self.security_access_send_key(can_p, sa_keys, sa_key_calculated,
            #                                                  step_no, purpose)[0]
        #SA_GEN2:
        elif sa_keys["SecAcc_Gen"] == 'Gen2':
            # Set keys in SSA
            #SSA.set_keys(auth_key, proof_key)
            logging.debug("SSA sa_keys param %s", sa_keys)
            SSA.set_keys(sa_keys)

            #Security Access request seed
            result, response = self.security_access_request_seed(can_p, sa_keys, step_no, purpose)

            if not result:
                logging.error("Security access request seed failed.")
                return False, ''

            logging.debug("SA_Gen2: request seed result: %s", result)
            logging.info("SA_Gen2: request seed response: %s", response)
            success = SSA.process_server_response_seed(bytearray.fromhex(response))

            if success == 0:
                logging.debug("SA_Gen2: process_server_response_seed %s", success)
                logging.info("SA_Gen2: Process Server Response Seed Successful")
            else:
                logging.info("SA_Gen2: success = %s (not ok)", success)
                return False, ''

            sa_key_calculated = SSA.prepare_client_send_key()
            logging.debug("SA_Gen2: activate SBL: prepareclient sendkey: %s",
                          sa_key_calculated)
            logging.info("SA_Gen2: activate SBL: prepareclient sendkey (hex): %s",
                         sa_key_calculated.hex())
            logging.debug("SA_Gen2: activate SBL: status before send %s", result)
            logging.info("SA_Gen2: activate SBL: Sending Security access key...")
        else:
            logging.info("SA Gen not set.")
            logging.info("SS27, security_access_send_key, sa_keys: %s", sa_keys)
            raise Exception("Failed:  SecurityAccess parameters not set.")
        return result, sa_key_calculated


    def activate_security_access_send_calculated(self,# pylint: disable=too-many-arguments
                                                 can_p: CanParam,
                                                 sa_keys,
                                                 sa_keys_calculated,
                                                 step_no=272,\
                                                 purpose="SecurityAccess"):
        """
        Support function to activate the Security Access
        SA_GEN1:
        sa_keys: dict with fixed_key set
        SA_GEN2:
        sa_keys: dict with auth_key, proof_key set
        """
        #SA_GEN1:
        result = True
        logging.info("Activate_SA_fixedkey_p2 start")
        logging.info("Sa_keys used %s", sa_keys)
        if sa_keys["SecAcc_Gen"] == 'Gen1':
            #Security Access Send Key
            result = self.security_access_send_key(can_p, sa_keys, sa_keys_calculated,
                                                   step_no, purpose)[0]
            #return result

        #SA_GEN2:
        elif sa_keys["SecAcc_Gen"] == 'Gen2':
            #Security Access Send Key
            result, response = self.security_access_send_key(can_p,
                                                             sa_keys,
                                                             sa_keys_calculated,
                                                             step_no, purpose)
            if not result:
                logging.error("Security access send key failed.")
                return False

            logging.info("SA_Gen2: activate SBL: status after send %s", result)
            logging.info("SA_Gen2 send key response %s", response)
            logging.debug("SA_Gen2: activate SBL: status after send %s", result)
            logging.debug("SA_Gen2 send key response %s", response)
            success = SSA.process_server_response_key(bytearray.fromhex(response))

            if success != 0:
                result = False
                logging.info("SA_Gen2: activate SBL: process_server_response_key not successful")
            else:
                logging.info("SA_Gen2: activate SBL: process_server_response_key successful")
        else:
            logging.info("SA Gen not set.")
            logging.info("SS27, security_access_send_key, sa_keys: %s", sa_keys)
            raise Exception("Failed:  SecurityAccess parameters not set.")
        return result


    def activate_security_access_fixedkey(self, can_p: CanParam, sa_keys, step_no=272,\
                                            purpose="SecurityAccess"):
        """
        Support function to activate the Security Access
        SA_GEN1:
        sa_keys: dict with fixed_key set
        SA_GEN2:
        sa_keys: dict with auth_key, proof_key set
        """
        result, sa_calculated = self.activate_security_access_seed_and_calc(can_p,
                                                                            sa_keys,
                                                                            step_no,
                                                                            purpose)
        result = result and\
                 self.activate_security_access_send_calculated(can_p,
                                                               sa_keys,
                                                               sa_calculated,
                                                               step_no,
                                                               purpose)
        return result
