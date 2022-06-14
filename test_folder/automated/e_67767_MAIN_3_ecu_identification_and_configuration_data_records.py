"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 67767
version: 3
title: ECU identification and configuration data records
purpose: >
    Volvo car corporation defines mandatory data records in GMRDB

description: >
    ECU identification and configuration data records with data identifiers in the range as
    specified in the table below shall be implemented exactly as they are defined in
    carcom - global master reference database
    --------------------------------------------------------------
    Manufacturer	                Identifier range
    --------------------------------------------------------------
    Volvo Car Corporation	        EDA0 - EDFF
    Geely	                        ED20 - ED7F
    --------------------------------------------------------------

details: >
    Import script - Inherited from older version of requirement
"""

from e_67767_MAIN_2_ecu_identification_and_configuration_data_records import run

if __name__ == '__main__':
    run()
