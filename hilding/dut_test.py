/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



**********************************************************************************/


"""
pytest: dut testing
"""

import os

from hilding.dut import Dut
from hilding.dut import DutTestError
from hilding import get_conf

from protogenerated.common_pb2 import Empty
import protogenerated.system_api_pb2
if hasattr(protogenerated.system_api_pb2, "License"):
    from protogenerated.system_api_pb2 import LicenseStatus # pylint: disable=no-name-in-module

def _test_dut():
    """ pytest: testing dut """
    dut = Dut()
    # list available signals
    configuration = dut.system_stub.GetConfiguration(Empty())
    ns = [ni.namespace for ni in configuration.networkInfo]
    platform = os.getenv("ODTBPROJ")
    if platform == "MEP2_SPA1":
        assert ns[0].name == "BecmRmsCanFr1"
        assert ns[1].name == "Front1CANCfg0"
        assert ns[2].name == "RpiGPIO"

        front_can_signals = dut.system_stub.ListSignals(ns[1])
        front_can_signal_names = [
            frame.signalInfo.id.name for frame in front_can_signals.frame]

        assert "Vcu1ToBecmFront1DiagReqFrame" in front_can_signal_names
        assert "BecmToVcu1Front1DiagResFrame" in front_can_signal_names

        try:
            # only test this if we are using beamy signal broker
            status = dut.system_stub.GetLicenseInfo(Empty()).status
            assert status == LicenseStatus.VALID, \
                "Check your license, status is: %d" % status
        except AttributeError:
            pass


def test_upload_folder():
    """ pytest: testing upload_folder """
    dut = Dut()
    try:
        dut.reconfigure_broker(
            "BO_ 1875 HvbmdpToHvbmUdsDiagRequestFrame : 8 HVBMdp",
            "BO_ 1875 HvbmdpToHvbmUdsDiagRequestFrame : 7 HVBMdp"
        )
    except DutTestError:
        pass


def test_get_signal_broker_parameters():
    """ pytest: testing send and receive parameters """
    rig = get_conf().rig
    if rig.platform == "becm":
        assert rig.signal_send == "Vcu1ToBecmFront1DiagReqFrame"
        assert rig.signal_receive == "BecmToVcu1Front1DiagResFrame"
    if rig.platform == "hvbm":
        assert rig.signal_send == "HvbmdpToHvbmUdsDiagRequestFrame"
        assert rig.signal_receive == "HvbmToHvbmdpUdsDiagResponseFrame"
