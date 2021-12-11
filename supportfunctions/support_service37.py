"""
/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

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


from supportfunctions.support_can import SupportCAN, CanParam, CanPayload, CanTestExtra
from supportfunctions.support_test_odtb2 import SupportTestODTB2


SC = SupportCAN()
SUTE = SupportTestODTB2()

class SupportService37: # pylint: disable=too-few-public-methods
    """
    class for supporting Service#37
    """

    @staticmethod
    def transfer_data_exit(can_p: CanParam, stepno=370, purpose="Request Transfer Exit"):
        """
        Support function for Request Transfer Exit
        """
        cpay: CanPayload = {"payload": b'\x37',\
                            "extra": ''
                           }
        etp: CanTestExtra = {"step_no": stepno,\
                             "purpose": purpose,\
                             "timeout": 4,\
                             "min_no_messages" : 1,\
                             "max_no_messages" : 1
                            }
        return SUTE.teststep(can_p, cpay, etp)
