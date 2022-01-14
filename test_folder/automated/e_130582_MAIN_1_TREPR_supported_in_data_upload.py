"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 130582
version: 1
title: TransferData (36) - transferResponseParameterRecord (TREPR_) supported in data upload
purpose: >
    Purpose	Compliance with VCC Tools

description: >
    The ECU shall support TransferData - transferResponseParameterRecord (TREPR_) when the data
    direction is from the ECU to the Tester (i.e during upload of data).

details: >
    ECU does not support SID 35 So it is NA.
    On execution recieved-
    Negative response (Service 35), serviceNotSupported (1100000000)
"""

import logging
import sys

logging.basicConfig(format=' %(message)s',
                    stream=sys.stdout, level=logging.INFO)

logging.info("Testcase result: Not applicable")
