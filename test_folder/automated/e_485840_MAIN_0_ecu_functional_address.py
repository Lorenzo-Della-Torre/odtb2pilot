"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

testscript: Hilding MEPII
project:    BECM basetech MEPII
author:     GANDER10 (Gustav Andersson)
date:       2021-02-25
version:    0
reqprod:    485840

title:
    ECU functional address ; 0

purpose:
    To dedicate a functional logical address for the ECU

description:
    Rationale:
        To make it possible for the tester to send a functional request to all ECUs in the vehicle
        at the same time. Functional addressed requests are used both in the manufacturing and
        aftersales process.

    Req:
        The ECU shall implement the functional address specified in the table below.

            - ECU Functional address | 0x1FFF

details:
    Implicitly tested by:
        REQPROD 60112 (Supporting functional requests)
"""

from e_60112__1_functional_requests import run

if __name__ == '__main__':
    run()
