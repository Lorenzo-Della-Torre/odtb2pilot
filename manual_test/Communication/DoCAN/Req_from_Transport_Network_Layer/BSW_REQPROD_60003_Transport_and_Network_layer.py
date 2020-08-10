""" Testscript for an implicitly tested requirement (tested implicitly)

    Testscript ODTB2 MEPII
    project:  BECM basetech MEPII
    author:   LDELLATO (Lorenzo Della Torre)
    date:     2020-05-16
    version:  1.0
    reqprod:  60003

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

logging.info("Testcase result: Tested implicitly by REQPRODs in in LC : "
             "VCC DoCAN - SW reqs.:"
             "Requirements from section Addressing formats"
             "Requirements from section BlockSize (BS) parameter definition"
             "Requirements from section CAN frame data and payload configuration"
             "Requirements from section Max number of FC. Wait frame transmission (N_WFTmax)"
             "Requirements from section Separation( STmin) parameter definition"
             "Requirements from section Soparation time between sigle frames"
             "Requirements from section Timing parameters"
             "Requirements from section Transport and Network Layer"
             "Requirements from section Unexpected arrival of N_PDU"
             "Requirements from section Use data frame by frame"
             )