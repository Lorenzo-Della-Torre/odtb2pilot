"""
reqprod: 418372
version: 2
title:
    ECU Software Structure Part Number data record

purpose:
    To enable readout of the part number of the ECU Software Structure.

description: >
    If the ECU supports the Software Authentication concept where each data
    file is signed and verified individually as defined in Ref[*LC : General
    Software Authentication*], a data record shall be implemented as specified
    in the table below.

    ECU Software Structure Part Number: F12C

    It shall be possible to read the data record by using the diagnostic
    service specified in Ref[*LC : Volvo Car Corporation - UDS Services -
    Service 0x22 (ReadDataByIdentifier) Reqs*].  The ECU shall implement the
    data record exactly as defined in *Carcom - Global Master Referenced
    Database (GMRDB)*.

    The ECU shall support the identifier in the following sessions:
     - Programming session (which includes both primary and secondary bootloader)

details: >
    A ECU software part number should look like something like this: 32263666 AA.
    This test ensures that the format is correct and if possible corresponds to
    the same ecu software part number that can be extracted with eda0.

"""

import sys
import logging

from hilding.dut import Dut
from hilding.dut import DutTestError
from hilding.uds import IoVmsDid
from hilding.uds import EicDid
from supportfunctions.support_SBL import SupportSBL
###SecAccessParam only available after SecAccGen2 merge
#from supportfunctions.support_sec_acc import SecAccessParam


def step_1(dut):
    """
    action:
        Get the complete ecu part numbers from another did to have something to
        compare it with

    expected_result: >
        ECU: Positive response

    comment:
        All the part numbers should be returned
    """
    eda0_response = dut.uds.read_data_by_id_22(
        EicDid.complete_ecu_part_number_eda0)
    logging.info(eda0_response)

    if eda0_response.empty() or not "F12E_valid" in eda0_response.data["details"]:
        raise DutTestError("Could not retrieve complete ecu part number")
    return eda0_response.data["details"]["F12E_valid"][-1]


def step_2(dut):
    """
    action:
        Set ecu to programming mode/session

    expected_result: >
        ECU: Empty response

    comment: Mode 2 should be set
    """
    dut.uds.set_mode(2)


def step_3(dut, eda0_f12c_valid):
    """
    action:
        Test that the format of the software part number is correct. That is
        consist of 8 consecutive numbers, followed by a space, and followed by
        two letters.

    expected_result:
        The format should be correct

    comment: >
        spa1: also test if the software part number from eda0 matches with the
        one we get from f12c
    """
    verify_f12c(dut, eda0_f12c_valid)


def step_4(dut: Dut, sa_keys):
    """
    action:
        Set ecu to programming mode (sbl)

    expected_result: >
        ECU: Empty response

    comment: Mode 2 should be set and in sbl mode
    """
    sbl = SupportSBL()
    sbl.get_vbf_files()
    if not sbl.sbl_activation(
        dut, sa_keys, stepno='4',
            purpose="Activate Secondary bootloader"):
        DutTestError("Could not set ecu in sbl mode")


def step_5(dut, eda0_f12c_valid):
    """
    action:
        Test that the format of the software part number is correct. That is
        consist of 8 consecutive numbers, followed by a space, and followed by
        two letters.

    expected_result:
        The format should be correct

    comment: >
        spa1: also test if the software part number from eda0 matches with the
        one we get from f12c
    """
    verify_f12c(dut, eda0_f12c_valid)


def verify_f12c(dut: Dut, eda0_f12c_valid):
    """ verify the f12c part number from eda0 with a direct f12c call """
    f12c_response = dut.uds.read_data_by_id_22(
        IoVmsDid.ecu_software_structure_part_number_f12c)
    logging.info(f12c_response)

    if f12c_response.empty() or "F12E_valid" in f12c_response.details:
        raise DutTestError("No software structure part number received")

    f12c_valid = f12c_response.details["F12C_valid"]

    logging.info("platform: %s", dut.conf.rig.platform)
    if dut.conf.rig.platform == "becm":
        assert eda0_f12c_valid == f12c_valid, \
            "ecu software structure part numbers does not match: " + \
            "\neda0: %s\nf12c: %s" % (
                eda0_f12c_valid, f12c_valid)

def run():
    """
    ECU Software Structure Part Number data record
    """
    logging.basicConfig(
        format=' %(message)s', stream=sys.stdout, level=logging.INFO)

    dut = Dut()
    start_time = dut.start()
    result = False

    #Init parameter for SecAccess Gen1 / Gen2 (current default: Gen1)
###SecAccessParam only available after SecAccGen2 merge
    #sa_keys: SecAccessParam = {
    sa_keys = {
        "SecAcc_Gen": 'Gen1',
        "fixed_key": '0102030405',
        "auth_key": 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF',
        "proof_key": 'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'
    }

    #SIO.extract_parameter_yml(str(inspect.stack()[0][3]), sa_keys)

    try:
        dut.precondition(timeout=200)

        eda0_f12c_valid = dut.step(step_1, purpose="get eda0")

        dut.step(step_2,
                 purpose="set programming mode (pbl)")

        dut.step(step_3, eda0_f12c_valid,
                 purpose="get f12c and compare values in pbl")

        dut.step(step_4, sa_keys,
                 purpose="set programming mode (sbl)")

        dut.step(step_5, eda0_f12c_valid,
                 purpose="get f12c and compare values in sbl")

        result = True
    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)

if __name__ == '__main__':
    run()
