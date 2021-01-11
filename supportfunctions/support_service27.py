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
import inspect

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
    def pbl_security_access_request_seed(can_p: CanParam, stepno=270,\
                                         purpose="SecurityAccessRequestSeed"):
        """
            Support function: request seed for calculating security access pin
        """

        #different request in mode 1/3 and mode2
        logging.info("PBL SecAcc req seed: determine current mode")
        SE22.read_did_f186(can_p)
        #SE22.read_did_f186(can_p, dsession=b'')
        logging.info("PBL SecAcc req seed: current mode: %s", SC.can_messages[can_p["receive"]])

        if SUTE.test_message(SC.can_messages[can_p["receive"]], '62F18601')\
            or SUTE.test_message(SC.can_messages[can_p["receive"]], '62F18603'):
            cpay: CanPayload =\
              {"payload" : S_CARCOM.can_m_send("SecurityAccessRequestSeed_mode1_3", b'', b''),\
               "extra" : ''
              }
        elif SUTE.test_message(SC.can_messages[can_p["receive"]], '62F18602'):
            cpay: CanPayload =\
                {"payload" : S_CARCOM.can_m_send("SecurityAccessRequestSeed", b'', b''),\
                 "extra" : ''
                }
        else:
            cpay: CanPayload =\
                {"payload" : S_CARCOM.can_m_send("SecurityAccessRequestSeed", b'', b''),\
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
    def pbl_security_access_send_key(can_p: CanParam, payload_value, stepno=271,\
                                     purpose="SecurityAccessSendKey"):
        """
            Support function: request seed for calculating security access pin
        """
        #Security Access Send Key

        if SUTE.test_message(SC.can_messages[can_p["receive"]], '62F18601')\
            or SUTE.test_message(SC.can_messages[can_p["receive"]], '62F18603'):
            cpay: CanPayload =\
              {"payload" : S_CARCOM.can_m_send("SecurityAccessSendKey_mode1_3",\
                    payload_value, b''),\
               "extra" : ''
              }
        elif SUTE.test_message(SC.can_messages[can_p["receive"]], '62F18602'):
            cpay: CanPayload =\
                {"payload" : S_CARCOM.can_m_send("SecurityAccessSendKey",\
                      payload_value, b''),\
                 "extra" : ''
                }
        else:
            cpay: CanPayload =\
                {"payload" : S_CARCOM.can_m_send("SecurityAccessSendKey",\
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

    def activate_security_access(self,
                                 can_p: CanParam,
                                 step_no=272,
                                 purpose='Security Access Request SID'):
        """
        Teststep : Activate SecurityAccess
        action: Request Security Access to be able to unlock the server(s)
                and run the primary bootloader.
        result: Positive reply from support function if Security Access to server is activated.
        """
        fixed_key = '0102030405'
        new_fixed_key = SIO.extract_parameter_yml(str(inspect.stack()[0][3]), 'fixed_key')
        # don't set empty value if no replacement was found:
        if new_fixed_key != '':
            assert isinstance(new_fixed_key, str)
            fixed_key = new_fixed_key
        else:
            logging.info("Step%s: new_fixed_key is empty. Leave old value.", step_no)
        logging.info("Step%s: fixed_key after YML: %s", step_no, fixed_key)
        result = self.activate_security_access_fixedkey(can_p, fixed_key, step_no,
                                                purpose)
        return result

    def activate_security_access_fixedkey(self, can_p: CanParam, fixed_key, step_no, purpose):
        """
        Support function to activate the Security Access
        """
        #Security Access request seed
        testresult, seed = self.pbl_security_access_request_seed(can_p, step_no, purpose)
        r_0 = SSA.set_security_access_pins(seed, fixed_key)

        #Security Access Send Key
        testresult = testresult and self.pbl_security_access_send_key(can_p, r_0,
                                                                      step_no, purpose)
        return testresult
