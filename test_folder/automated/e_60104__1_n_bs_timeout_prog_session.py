"""
Testscript Hilding MEPII
project:  BECM basetech MEPII
author:   DHJELM (Daniel Hjelm)
date:     2020-11-16
version:  1.0
reqprod:  60104

title:
N_Bs timeout in programming session

purpose:
From a system perspective it is important that both sender and receiver side
times out roughly the same time. The timeout value shall be high enough to not
be affected by situations like occasional high busloads and low enough to get a
user friendly system if for example an ECU is not connected.

description:
N_Bs timeout value shall be 1000ms in programming session.

Testscript for an implicitly tested requirement (tested implicitly)
"""

import logging

logging.basicConfig(filename='{}.log'.format((__file__)[-3]), format='%(asctime)s - %(message)s',
                    level=logging.INFO)

logging.info("Testcase result: Tested implicitly by REQPROD 60102")
