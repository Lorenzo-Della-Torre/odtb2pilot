"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 74109
version: 2
title: Allowed diagnostic services
purpose: >
    Define which diagnostic services to allow. Ensures all suppliers uses the same diagnostic
    services as well as preventing supplier from using not allowed diagnostic services.

description: >
    The ECU shall only support the diagnostic services specified in the requirement sections from
    Volvo Car Corporation.

details: >
    Import script - Inherited from older version of requirement

"""

from e_74109_MAIN_1_allowed_diag_services import run

if __name__ == '__main__':
    run()
