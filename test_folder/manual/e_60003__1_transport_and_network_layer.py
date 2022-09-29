"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

reqprod: 60003
version: 1
title: Transport and Network layer
purpose: >
    Standardise communication to ensure all ECUs uses the same diagnostic communication
    specifications. ISO standard shall be followed as far as possible unless otherwise specified
    to reduce cost and make implementation easier.

description: >
    The transport/network layer shall be compliant to Road vehicles - Diagnostic communication over
    Controller Area Network (DoCAN) - Part 2: Transport protocol and network layer services with the
    restrictions/additions as defined by this document. If there are contradictions between this
    specification, LC : VCC - DoCAN, and Road vehicles - Diagnostic communication over Controller
    Area Network (DoCAN) - Part 2: Transport protocol and network layer services, then this
    specification shall override Road vehicles - Diagnostic communication over Controller Area
    Network (DoCAN) - Part 2: Transport protocol and network layer services.

details: >
    Implicitly tested script
"""

import logging
import sys

logging.basicConfig(format='%(asctime)s - %(message)s', stream=sys.stdout, level=logging.INFO)

logging.info("Testcase result: tested implicitly by REQPRODs in LC: "
             "VCC DoCAN - SW reqs.:"
             "Requirements from section Addressing formats:"
             "REQPROD 60112 Supporting functional requests"
             "Requirements from section BlockSize (BS) parameter definition:"
             "REQPROD 60006 BlockSize parameter non-programming session server side"
             "Requirements from section CAN frame data and payload configuration:"
             "REQPROD 60129 Length of Classic CAN frames"
             "Requirements from section Max number of FC. Wait frame transmission (N_WFTmax):"
             "REQPROD 60015 N_WFTmax value for server side"
             "Requirements from section Separation( STmin) parameter definition:"
             "REQPROD 60010 Separation time (STmin) non-programming session server side"
             "Requirements from section Soparation time between sigle frames:"
             "REQPROD 380118 Separation time between single frames - programming session"
             "Requirements from section Timing parameters:"
             "REQPROD 60017 N_As_timeout_non_prog_session:"
             "Requirements from section Transport and Network Layer:"
             "REQPROD 60004 Precedence of requirements"
             "Requirements from section Unexpected arrival of N_PDU:"
             "REQPROD 60109 Duplex communication"
             "Requirements from section Use data frame by frame:"
             "REQPROD 128908 Forward N_Data from each N_PDU to upper layer"
             )
