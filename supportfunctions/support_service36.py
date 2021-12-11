/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



**********************************************************************************/


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

"""The Python implementation of the gRPC route guide client."""

import logging
from supportfunctions.support_can import SupportCAN, CanParam, CanPayload, CanTestExtra
from supportfunctions.support_test_odtb2 import SupportTestODTB2


SC = SupportCAN()
SUTE = SupportTestODTB2()

class SupportService36: # pylint: disable=too-few-public-methods
    """
    class for supporting Service#36
    """

    @staticmethod
    def flash_blocks(can_p: CanParam, vbf_block_data, vbf_block, nbl,
                     stepno=360, purpose="flash block"):
        # pylint: disable= too-many-arguments
        """
        Support function for Transfer Data
        """
        pad = 0

        for i in range(int(vbf_block['Length']/(nbl-2))+1):

            logging.info("360 Flash blocks: Block %s of %s",
                         1+i, 1+int(vbf_block['Length']/(nbl-2)))
            pad = (nbl-2)*i
            i += 1
            ibyte = bytes([i % 256])

            cpay: CanPayload = {"payload" : b'\x36' + ibyte + vbf_block_data[pad:pad + nbl-2],
                                "extra" : ''
                               }
            etp: CanTestExtra = {"step_no": stepno,
                                 "purpose" : purpose,
                                 "timeout" : 0.2,
                                 "min_no_messages" : -1,
                                 "max_no_messages" : -1
                                }
            result = SUTE.teststep(can_p, cpay, etp)
            result = result and SUTE.test_message(SC.can_messages[can_p["receive"]], '76')
        return result
