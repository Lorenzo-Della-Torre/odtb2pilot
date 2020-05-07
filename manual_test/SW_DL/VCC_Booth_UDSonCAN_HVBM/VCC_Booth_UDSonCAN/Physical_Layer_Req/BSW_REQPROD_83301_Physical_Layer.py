""" Testscript for an implicitly tested requirement (tested implicitly)
    Testscript ODTB2 MEPII
    project  BECM basetech MEPII
    author   LDELLATO (Lorenzo Della Torre)
    date     2020-04-02
    version  1.0
    reqprod  38801

    #inspired by httpsgrpc.iodocstutorialsbasicpython.html
    Copyright 2015 gRPC authors.

    Licensed under the Apache License, Version 2.0 (the License);
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        httpwww.apache.orglicensesLICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an AS IS BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
"""

import logging
import sys

logging.basicConfig(format='%(asctime)s - %(message)s',
                    stream=sys.stdout, level=logging.DEBUG)

logging.info("Testcase result tested implicitly by REQPROD_53848_Communication_protocol" \
             "REQPROD_53849_Applicable_CAN_standards" \
             "REQPROD_53850_The_priority_between_standard_documents_and_this_document" \
             "REQPROD_53853_PLL_bypass" \
             "REQPROD_53861_PLL_locking" \
             "REQPROD_53862_Resychronisation_strategy" \
             "REQPROD_53863_Sample_mode" \
             "REQPROD_53864_Bit_time_setup_for_500_kbps" \
             "REQPROD_53881_Standards_for_CAN_interface" \
             "REQPROD_53883_Behaviour_outside_normal_supply_voltage_range" \
             "REQPROD_53884_CAN_bus_level_during_reset" \
             "REQPROD_53885_Bus_fault_reporting")
