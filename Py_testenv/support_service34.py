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

#import logging
#from typing import Dict

from support_can import SupportCAN, CanMFParam, CanParam, CanPayload, CanTestExtra
from support_test_odtb2 import SupportTestODTB2


SC = SupportCAN()
SUTE = SupportTestODTB2()

class SupportService34: # pylint: disable=too-few-public-methods
    """
    class for supporting Service#34
    """


    #@classmethod
    #Support function for Request Download
    @staticmethod
    def request_block_download(can_p: CanParam, purpose, data, stepno=340):
        """
        Support function for Request Download
        """
        #testresult = True
        # Parameters for FrameControl FC
        #seed = can_p["send"]

        can_mf_param: CanMFParam = {
            'block_size' : 0,
            'separation_time' : 0,
            'frame_control_delay' : 0, #no wait
            'frame_control_flag' : 48, #continue send
            'frame_control_auto' : False
            }
        SC.change_mf_fc(can_p["send"], can_mf_param)

        addr_b = data["b_addr"].to_bytes(4, 'big')
        len_b = data["b_len"].to_bytes(4, 'big')
        cpay: CanPayload = {"payload" : b'\x34' + data["data_format"] + b'\x44'+\
                                       addr_b + len_b,\
                            "extra" : ''
                           }
        etp: CanTestExtra = {"step_no": stepno,\
                             "purpose" : purpose,\
                             "timeout" : 0.05,\
                             "min_no_messages" : -1,\
                             "max_no_messages" : -1
                            }
        testresult = SUTE.teststep(can_p, cpay, etp)
        testresult = testresult and SUTE.test_message(SC.can_messages[can_p["receive"]], '74')
        nbl = SUTE.pp_string_to_bytes(SC.can_frames[can_p["receive"]][0][2][6:10], 4)
        #if self._debug:
        #    print("NBL: {}".format(nbl))
        #nbl = int.from_bytes(SC.can_frames[can_p["receive"]][0][2][6:10])
        nbl = int.from_bytes(nbl, 'big')
        return testresult, nbl
