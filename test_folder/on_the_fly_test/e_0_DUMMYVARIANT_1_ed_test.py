"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

"""

import logging

from hilding.dut import Dut
from hilding.dut import DutTestError

def step_1(dut: Dut):
    """
    action:
        Change ECU mode using functional addresssing
    expected_result: >
        ECU: positive result
    """
    # the .dbc files have the following information
    # spa1:
    #  BO_ 2047 Vcu1ToAllFuncFront1DiagReqFrame: 8 VCU1
    #   SG_ Vcu1ToAllFuncFront1DiagReqNpdu : 7|64@0+ (1,0) [0|0]
    #   "" BECM, ECM, ESM, IGM, ISGM, MVCM, TCM
    # spa2:
    #  BO_ 2047 HvbmdpToAllUdsDiagRequestFrame : 8 HVBMdp
    #   SG_ HvbmdpToAllUdsHvbm1canNPdu : 7|64@0+ (1,0) [0|0]
    #   "" HVBM
    # note: 2047 decimal = 0x7ff
    # hence, we set the addressing as follows:

   # if dut.conf.rig.platform == 'ihfa_v436':
   #     dut.send = "IHFAdpToIHFAUdsDiagRequestFrame"
   # else:
   #     raise DutTestError("Your platform is not supported in this test")

    # parameters = dut.get_platform_yml_parameters(__file__)
    # dut.send = parameters.get("send")
    # logging.info("dut.send = %s", dut.send)
    # if not dut.send:
    #     raise DutTestError("Your platform is not supported in this test")

    dut.uds.set_mode(1)

    if dut.uds.mode != 1:
        raise DutTestError("Could not change mode using functional addressing")

    # reset the send signal to original setting
    # dut.send = dut.conf.rig.signal_send

def run():
    """ Supporting functional requests """
    dut = Dut()
    start_time = dut.start()
    result = False
    try:
        dut.precondition()
        dut.step(step_1)
        result = True

    except DutTestError as error:
        logging.error("The testcase for ed_test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)
if __name__ == '__main__':
    run()
