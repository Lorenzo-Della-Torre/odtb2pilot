"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 76171
version: 3
title: ReadDataByIdentifier (22) - multiple identifiers with one request
purpose: >
    The manufacturing and aftersales tool supports reading several DIDs simultaneously from one
    ECU. Since the time for each request will be to long, the ECU shall be able to package
    several data record in one response message

description: >
    The ECU shall support a minimum 10 dataIdentifiers, or as many dataIdentifiers as implemented,
    in one single ReadDataByIdentifier request in default and extended diagnostic session.
    The ECU is permitted to reject requests with multiple dataIdentifiers when the response is
    larger than 61 bytes. In programmingSession only one dataIdentifier needs to be supported.

details: >
    Import script - Inherited from older version of requirement
"""

from e_76171_MAIN_2_read_did_multiple_request import run

if __name__ == '__main__':
    run()
