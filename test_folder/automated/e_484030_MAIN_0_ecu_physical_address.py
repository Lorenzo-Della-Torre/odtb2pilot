# Testscript Hilding MEPII
# project:  ECU basetech MEPII
# author:   J-ADSJO (Johan Adsjö)
# date:     2021-02-26
# version:  1.0
# reqprod:  484030

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
import sys

logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)
logging.info("This REQPROD is implicitly tested by all tests where a physical address\
 message is used to read data by identifier e.g. REQPROD_68177.")
logging.info("Testcase result: Tested implicitly by e.g. REQPROD_68177 (tested implicitly)")