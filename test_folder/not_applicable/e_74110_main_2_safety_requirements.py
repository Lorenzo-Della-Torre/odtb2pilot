"""
title: Safety requirements
reqprod: 74110
version: 2
purpose:
    Implementation of diagnostics on safety related ECU must comply with Road
    vehicles - Functional safety, International Organization for
    Standardization.
description:
    If the ECU implements safety requirements with an ASIL higher than QM,
    the ECU must ensure that the diagnostic services supported cannot violate
    any of those safety requirements in any session except in
    programmingSession, i.e. to demonstrate independence as required by
    “ISO 26262 2011, Road vehicles — Functional safety, International
    Organization for Standardization”.
    Exception to this requirement is allowed only when approved by Volvo
    Car Corporation and will require that the diagnostic services are
    developed according to “ISO 26262 2011, Road vehicles — Functional safety,
    International Organization for Standardization” and the allocated ASIL of
    those safety requirement for which independence cannot be demonstrated.

details:
    NA. For Design. Valid for application teams also.
    Requirement for the Safety Team.
"""
import logging
import sys

logging.basicConfig(format='%(asctime)s - %(message)s',
                    stream=sys.stdout, level=logging.DEBUG)

logging.info("Testcase result: Not applicable")
