"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 68197
version: 2
title: Autosar BSW cluster versions
purpose:
    To enable readout of the specific version of the (VCC) AUTOSAR cluster(s) implemented
    in the ECU.

description:
    If the ECU contains any AUTOSAR Basic Software cluster a data record with identifier as
    specified in the table below shall be implemented exactly as defined in
    Carcom - Global Master Reference Database.

    -------------------------------------------
    Description	                    Identifier
    -------------------------------------------
    Autosar BSW cluster version	    F126
    -------------------------------------------
    •   It shall be possible to read the data record by using the diagnostic service specified in
        Ref[LC : Volvo Car Corporation - UDS Services - Service 0x22 (ReadDataByIdentifier) Reqs].

    The identifier shall be implemented in the following sessions:
    •   Default session
    •   Extended Session

details:
    Import script - Inherited from older version of requirement
"""

from e_68197_MAIN_1_autosar_bsw_cluster_version import run

if __name__ == '__main__':
    run()
