"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

""" legacy configuration file for old scripts """
from hilding import get_conf

ODTB2_DUT = get_conf().rig.hostname
ODTB2_PORT = get_conf().rig.signal_broker_port
