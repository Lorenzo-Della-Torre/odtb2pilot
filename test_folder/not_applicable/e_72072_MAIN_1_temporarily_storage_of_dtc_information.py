"""
/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

# Testscript Hilding MEPII
# project:  BECM basetech MEPII
# author:   G-HERMA6 (Gunnar Hermansson)
# date:     2020-12-16
# version:  1.0
# reqprod:  72072

# #inspired by https://grpc.io/docs/tutorials/basic/python.html
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
import sys

logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

# Not applicable:
# N/A because all DTC info is stored in the ECU.
logging.info("Testcase result: Not applicable")
