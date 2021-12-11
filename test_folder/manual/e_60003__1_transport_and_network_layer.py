/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



**********************************************************************************/


""" Testscript for an implicitly tested requirement (tested implicitly)

    Testscript Hilding MEPII
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
import sys

logging.basicConfig(format='%(asctime)s - %(message)s', stream=sys.stdout, level=logging.INFO)

logging.info("Testcase result: Tested implicitly by REQPRODs in LC: "
             "VCC DoCAN - SW reqs.:"
             "Requirements from section Addressing formats:"
             "REQPROD 60112 Supporting functional requests"
             "Requirements from section BlockSize (BS) parameter definition:"
             "REQPROD 60006 BlockSize parameter non-programming session server side"
             "Requirements from section CAN frame data and payload configuration:"
             "REQPROD 60129 Length of Classic CAN frames"
             "Requirements from section Max number of FC. Wait frame transmission (N_WFTmax):"
             "REQPROD 60015 N_WFTmax value for server side"
             "Requirements from section Separation( STmin) parameter definition:"
             "REQPROD 60010 Separation time (STmin) non-programming session server side"
             "Requirements from section Soparation time between sigle frames:"
             "REQPROD 380118 Separation time between single frames - programming session"
             "Requirements from section Timing parameters:"
             "REQPROD 60017 N_As_timeout_non_prog_session:"
             "Requirements from section Transport and Network Layer:"
             "REQPROD 60004 Precedence of requirements"
             "Requirements from section Unexpected arrival of N_PDU:"
             "REQPROD 60109 Duplex communication"
             "Requirements from section Use data frame by frame:"
             "REQPROD 128908 Forward N_Data from each N_PDU to upper layer"
             )
