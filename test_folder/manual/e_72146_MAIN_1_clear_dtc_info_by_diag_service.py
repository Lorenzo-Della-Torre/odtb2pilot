"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

    Testscript for an implicitly tested requirement (tested implicitly)

    Testscript Hilding MEPII
    project:  BECM basetech MEPII
    author:   LDELLATO (Lorenzo Della Torre)
    date:     2020-06-16
    version:  1.0
    reqprod:  72146

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

logging.info("Testcase result: Tested implicitly by REQPRODs in in LC : "
             "LC : VCC - UDS Services - Service 0x14 (ClearDiagnosticInformation) Reqs.:"
             "REQPROD 76496	ClearDiagnosticInformation(14)"
             "REQPROD 76497	ClearDiagnosticInformation(14)-groupOfDTCSpecific DTC"
             "REQPROD 363603 ClearDiagnosticInformation(14)-groupOfDTC All DTCs\
                 in emission related ECU"
             "REQPROD 76498	ClearDiagnosticInformation(14)-groupOfDTC All Groups"
             "REQPROD 74155	P4Server_max response time for clearDiagnosticInformation(14)"
             "REQPROD 74179	Service clearDiagnosticInformation(14) affecting ECU functionality"
             "REQPROD 74465	Entry conditions for diagnostic service ClearDiagnosticInformation(14)"
             "REQPROD 74494	Security access protection for service clearDiagnosticInformation(14)"
             )
