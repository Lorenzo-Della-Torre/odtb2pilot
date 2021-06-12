"""
pytest for hilding/settings.py
"""
from tempfile import TemporaryFile

from hilding.settings import Settings
from hilding.settings import get_settings

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
    print(settings)
    assert settings.default_rig
    assert settings.rig.user == "pi"

def test_get_sddb(monkeypatch):
    """ pytest: testing sddb access """
    # pylint: disable=protected-access
    settings = get_settings()
    monkeypatch.setitem(
        settings.rig._Rig__sddb_module_cache, "dids",
        {"pbl_diag_part_num": ""})
    monkeypatch.setitem(
        settings.rig._Rig__sddb_module_cache, "dtcs",
        {"sddb_dtcs": {}, "sddb_report_dtc": {}})
    monkeypatch.setitem(
        settings.rig._Rig__sddb_module_cache, "services",
        {"pbl": {}, "sbl": {}, "app": {}})

    assert settings.rig.sddb_dids == {"pbl_diag_part_num": ""}
    assert settings.rig.sddb_dtcs == {"sddb_dtcs": {}, "sddb_report_dtc": {}}
    assert settings.rig.sddb_services == {"pbl": {}, "sbl": {}, "app": {}}
