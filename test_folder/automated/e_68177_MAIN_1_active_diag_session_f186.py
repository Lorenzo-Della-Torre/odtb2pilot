"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 68177
version: 1
title: : Active diagnostic session data record
purpose: >
    To enable readout of the active diagnostic session.

description: >
    A data record with identifier as specified in the table below shall be implemented exactly as
    defined in Carcom - Global Master Reference Database.
    • It shall be possible to read the data record by using the diagnostic service specified in
      Ref[LC : Volvo Car Corporation - UDS Services - Service 0x22 (ReadDataByIdentifier) Reqs].

      *************************************************
        Description	                    Identifier
      *************************************************
        Active diagnostic session      	  F186
      *************************************************

    The identifier shall be implemented in the following sessions:
    • Default session
    • Programming session (which includes both primary and secondary bootloader)
    • Extended Session
details: >
    Import script - Inherited from older version of requirement
"""

import sys
import logging
from e_68177_MAIN_0_active_diag_session_f186 import run

logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)


if __name__ == '__main__':
    run()
