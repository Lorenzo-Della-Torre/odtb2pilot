"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
reqprod: 488703
version: 0
title: SecOC configuration - SecOCClusterKeyID.

purpose: >
    To allow the possibility to configure the KeyID for each PDU.

description: >
    This configuration is applicable if multiple SecOC keys are used on the same ECU.
    It can be skipped in case only one SecOC key is used on the ECU.

    It shall be possible to configure which SecOC Cluster Key Identifier shall be used for
    each PDU by configuring the parameter SecOCClusterKeyID.

    Note: SecOCClusterKeyID here is OEM configuration to uniquely identify key for each
    SecOC cluster. ECUs shall internally define how this value can be mapped to actual
    key slot ID in the storage

details: >
    Not applicable because we only have one cluster and one key.

"""

import logging
import sys

logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

logging.info("Testcase result: Not applicable")
