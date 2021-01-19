""" Testscript for an implicitly tested requirement (tested implicitly)
    Testscript ODTB2 MEPII
    project  BECM basetech MEPII
    author   LDELLATO (Lorenzo Della Torre)
    date     2020-03-23
    version  1.0
    reqprod  52245

    #inspired by httpsgrpc.iodocstutorialsbasicpython.html
    Copyright 2015 gRPC authors.

    Licensed under the Apache License, Version 2.0 (the License);
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        httpwww.apache.orglicensesLICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an AS IS BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

import logging
import sys

logging.basicConfig(format='%(asctime)s - %(message)s',
                    stream=sys.stdout, level=logging.DEBUG)

logging.info("Testcase result tested implicitly by REQPRODs in in LC : " \
             "VCC UDS Session generic reqs and LC : VCC UDS Session ECU reqs.")