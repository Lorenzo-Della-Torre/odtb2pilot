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

The Python implementation of the gRPC route guide client.
"""

import logging
#from typing import Dict

from supportfunctions.support_can import SupportCAN, CanParam, CanPayload, CanTestExtra
from supportfunctions.support_test_odtb2 import SupportTestODTB2


SC = SupportCAN()
SUTE = SupportTestODTB2()

class SupportService34: # pylint: disable=too-few-public-methods
    """
    class for supporting Service#34
    """


    #@classmethod
    #Support function for Request Download
    @staticmethod
    def request_block_download(can_p: CanParam, vbf_header, vbf_block, stepno=340,
                               purpose="Request Download of block to ECU"):
        """
        Support function for Request Download
        """
        #testresult = True
        # Parameters for FrameControl FC
        #seed = can_p["send"]

        addr_b = vbf_block['StartAddress'].to_bytes(4, 'big')
        len_b = vbf_block['Length'].to_bytes(4, 'big')
        logging.info(" ")
        logging.info("------Request block Download to ECU------")
        logging.info("340: Address: %s, length: %s", addr_b.hex(), len_b.hex())

        cpay: CanPayload = {"payload" : b'\x34' +\
                                        vbf_header["data_format_identifier"].to_bytes(1, 'big') +\
                                        b'\x44'+\
                                        addr_b +\
                                        len_b,
                            "extra" : ''
                           }
        etp: CanTestExtra = {"step_no": stepno,
                             "purpose" : purpose,
                             "timeout" : 0.2,
                             "min_no_messages" : -1,
                             "max_no_messages" : -1
                            }
        logging.info("340: payload : %s", cpay['payload'].hex())
        result = SUTE.teststep(can_p, cpay, etp)
        logging.debug("340: result request: %s", result)
        logging.info("340: received frames: %s", SC.can_frames[can_p["receive"]][0][2])
        result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], '74')
        nbl = SUTE.pp_string_to_bytes(SC.can_frames[can_p["receive"]][0][2][6:10], 4)
        nbl = int.from_bytes(nbl, 'big')
        logging.info("340: nbl received: %s", nbl)
        return result, nbl
