""" Testscript for a requirement which can't be automated and needs to be manually tested.

    Testscript  ODTB2 MEPII
    project     BECM basetech MEPII
    author      USERNAME (firstname surname)
    date        YYYY-MM-DD
    version     1.0
    reqprod     12345

    Inspired by https://grpc.io/docs/tutorials/basic/python.html
    Copyright 2015 gRPC authors.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

import logging
import sys

logging.basicConfig(format='%(asctime)s - %(message)s',
                    stream=sys.stdout, level=logging.DEBUG)

logging.info("Testcase result: Needs to be manually tested")
