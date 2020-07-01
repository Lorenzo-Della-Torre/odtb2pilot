""" Testscript for an implicitly tested requirement (tested implicitly)

    Testscript ODTB2 MEPII
    project:  BECM basetech MEPII
    author:   LDELLATO (Lorenzo Della Torre)
    date:     2020-06-16
    version:  1.0
    reqprod:  74494

    Inspired by httpsgrpc.iodocstutorialsbasicpython.html
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

logging.basicConfig(filename='{}.log'.format((__file__)[-3]), format='%(asctime)s - %(message)s',
                    level=logging.INFO)

logging.info("Testcase result: Tested implicitly by REQPROD 76496")