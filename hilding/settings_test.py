"""
pytest for hilding/settings.py
"""
from tempfile import TemporaryFile

import pytest

from hilding.settings import Settings
from hilding.settings import get_settings

# pylint: disable=protected-access,redefined-outer-name

@pytest.fixture
def mock_get_settings(monkeypatch):
    """ mock helper function to not touch the file system """
    def get_settings_wrapper():
        settings = get_settings()
        monkeypatch.setitem(
            settings.rig._Rig__sddb_module_cache, "dids",
            {"pbl_diag_part_num": "",
             "app_did_dict": {"F186": {'size': '1'},
                              "EDA0": {'size': '110'},
                              "F12E": {'size': '7'}},
             "pbl_did_dict": {"F12C": {'size': '7'}},
             "sbl_did_dict": {"F122": {'size': '7'}},
             "resp_item_dict": {}})
        monkeypatch.setitem(
            settings.rig._Rig__sddb_module_cache, "dtcs",
            {"sddb_dtcs": {}, "sddb_report_dtc": {}})
        monkeypatch.setitem(
            settings.rig._Rig__sddb_module_cache, "services",
            {"pbl": {}, "sbl": {}, "app": {}})
        return settings
    return get_settings_wrapper

def test_settings():
    """ pytest: setting parsing """
    settings_file_content = b"""
    default_rig: p2
    rigs:
        p2:
            hostname: host2.domain
            user: pi #optional
            platform: spa2
            signal_broker_port: 50051 #optional
    spa2:
        default_signal_send: sendsignal
        default_signal_receive: receivesignal
    """
    settings_file = TemporaryFile()
    settings_file.write(settings_file_content)
    settings_file.seek(0)
    settings = Settings(settings_file_name=None)
    settings.read_settings_file(settings_file, "p2")
    assert settings.default_rig == "p2"
    assert settings.rig.hostname == "host2.domain"
    assert settings.rig.user == "pi"
    assert settings.rig.platform == "spa2"
    assert settings.rig.signal_broker_port == "50051"
    assert settings.rig.default_signal_send == "sendsignal"
    assert settings.rig.default_signal_receive == "receivesignal"

def test_settings_yml():
    """ pytest: settings.yml parsing """
    settings = get_settings()
    assert settings.default_rig
    assert settings.rig.user == "pi"

def test_get_sddb(mock_get_settings):
    """ pytest: testing sddb access """
    settings = mock_get_settings()

    assert "pbl_diag_part_num" in settings.rig.sddb_dids
    assert "sddb_dtcs" in settings.rig.sddb_dtcs
    assert "sddb_report_dtc" in settings.rig.sddb_dtcs
    assert "app" in settings.rig.sddb_services
    assert "pbl" in settings.rig.sddb_services
    assert "sbl" in settings.rig.sddb_services
