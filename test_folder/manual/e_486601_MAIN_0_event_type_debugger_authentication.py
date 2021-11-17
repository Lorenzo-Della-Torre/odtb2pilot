"""
reqprod: 486601
version: 0
title: Event Type - Debugger Authentication
purpose: >
    Define general event types that are applicable for ECUs supporting unlock of debug ports.

description: >
    This requirement is only applicable if debugger ports are agreed with OEM to be enabled and
    protected with access control mechanism as per "LC: Secure Debug".

    The ECU shall implement event type "Debugger Authentication " data record with identifier
    0xD0B8 as defined in OEM diagnostic database. An ECU might support mechanism for e.g. repair
    analysis at ECU supplier where user/role is authenticated to provide access to debug ports.
    Such access control events and events related to debug ports enable/disable status shall be
    logged.

    Event Header: SecurityEventHeaderType 2 shall be applied, i.e. using two counters.
    Size 32+32 bits.
    Event Records:
    Time. Size 32 bits
    EventCode. As defined in "Table – Debugger Authentication Event Code". Size 8 bits.
    AdditionalEventData. Omitted.

    Event Code    Event
    0x00    No History stored
    0x01    Failed to unlock access control mechanism for debugger authentication
    0x02    Attempt to enable/open JTAG debug port failed
    0x03    Attempt to disable/close JTAG debug port failed
    0x04    Attempt to enable/open debug port 1 failed
    0x05    Attempt to disable/close debug port 1 failed
    -    -
    0x7E    Attempt to enable/open debug port n failed
    0x7F    Attempt to disable/close debug port n failed
    0x80    Reserved
    0x81    Access control mechanism for debugger authentication is unlocked successfully
    0x82    JTAG debug port enabled successfully
    0x83    JTAG debug port disabled successfully
    0x84    Debug port 1 enabled successfully
    0x85    Debug port 1 disabled successfully
    -    -
    0xFE    Debug port n enabled successfully
    0xFF    Debug port n disabled successfully
    Table – Debugger Authentication Event Code

    Note: Other debug ports includes additional JTAG debug ports, Serial Wire Debug (SWD) interface,
    Background Debug Mode (BDM) interface and other debug interfaces supported by ECU.

    Access Control: Option (3) as defined in "REQPROD 469450: Security Audit Log - Access Control"
    shall be applied.

details: >
    Manual test.\
    (1) Connect the debugger and validate that is not possible to attach to the MCU (do debugging)\
    (2) Unlock debug port.\
    (3) With debugger attach to MCU and try some debugging steps (such as read out parts of the
 flash)
"""

import logging
import sys

logging.basicConfig(format='%(asctime)s - %(message)s',
                    stream=sys.stdout, level=logging.DEBUG)

logging.info("Testcase result: MANUAL")
