"""
/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

"""
title:   2-byte base DTC definition

reqprod: 481758
version: 0
purpose:
    All DTC information shall be supported by Volvo Cars tools and must
    therefore be defined in GMRDB

description: >

    Rationale:
    A faulty component shall be identified by the base DTC (DTC High Byte and
    DTC Middle Byte, i.e. excluding the FailureTypeByte).
    Each faulty item should have a unique base DTC as long as this improves the
    accuracy of the fault tracing and repair method. The definition and
    structure of a base DTC must be in accordance with SAEJ2012.

    Requirement:
    All parts and components (this includes both external and internal parts)
    monitored by an ECU shall each have a unique (if not specifically stated
    otherwise in other Volvo Car requirements) 2-byte base DTC with the
    following properties:

     * The description of the base DTC shall match the definition of the
       monitored part or component.

     * The structure of the base DTC shall be in accordance with SAEJ2012.

details:

    Tested by inspection. A validation of all defined DTCs in the SDDB can also
    be a method. Hilding or dSpace HIL is not needed for this.

"""
import logging
import sys

logging.basicConfig(format='%(asctime)s - %(message)s',
                    stream=sys.stdout, level=logging.DEBUG)

logging.info("Testcase result: To be inspected")
