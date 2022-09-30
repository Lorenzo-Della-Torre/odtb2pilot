"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 129845
version: 1
title: Secondary Bootloader Software Version Number data record

purpose: >
    To enable readout of the version number of the Secondary Bootloader SW.

description: >
    A data record with identifier as specified in the table below shall be implemented exactly as
    defined in Carcom - Global Master Reference Database (GMRDB).

    |                   Description	                           |  Identifier  |
    |Secondary Bootloader Software Version Number data record  |  	F124      |

    •	It shall be possible to read the data record by using the diagnostic service specified in
        Ref[LC : Volvo Car Corporation - UDS Services - Service 0x22 (ReadDataByIdentifier) Reqs].
    •	The identifier shall be BCD encoded, right justified and all unused digit shall be filled
        with 0.

    The ECU shall support the identifier in the following sessions:
    •   Programming session (which includes secondary bootloader).


details: >
    Import script - Inherited from older version of requirement
"""

from e_129845_MAIN_0_sbl_sw_vn_data_record import run

if __name__ == '__main__':
    run()
