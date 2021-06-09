"""
pytest: dut testing
"""

import os
import pytest

from hilding.dut import Dut
from hilding.dut import DutTestError
from hilding.dut import get_dut_custom
from hilding.legacy import get_parameters

from protogenerated.common_pb2 import Empty
import protogenerated.system_api_pb2
if hasattr(protogenerated.system_api_pb2, "License"):
    from protogenerated.system_api_pb2 import LicenseStatus # pylint: disable=no-name-in-module

def test_dut():
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


def test_get_parameters():
    """ pytest: testing get_parameters """
    parameters = get_parameters()
    assert "run" in parameters
    assert "send" in parameters["run"]
    assert "receive" in parameters["run"]
    platform = os.getenv("ODTBPROJ")
    if platform == "MEP2_SPA1":
        assert parameters["run"]["send"] == "Vcu1ToBecmFront1DiagReqFrame"
        assert parameters["run"]["receive"] == "BecmToVcu1Front1DiagResFrame"
    if platform == "MEP2_SPA2":
        assert parameters["run"]["send"] == "HvbmdpToHvbmUdsDiagRequestFrame"
        assert parameters["run"]["receive"] == "HvbmToHvbmdpUdsDiagResponseFrame"

def test_get_dut_custom():
    """ pytest: testing get_dut_custom """
    with pytest.raises(FileNotFoundError, match=r"Could not find .*dut_test.yml"):
        get_dut_custom()
