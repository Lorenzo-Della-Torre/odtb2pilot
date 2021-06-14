"""
pytest for hilding/conf.py
"""
import pytest

from hilding.conf import Conf
from hilding import get_conf

# pylint: disable=protected-access,redefined-outer-name

@pytest.fixture
def mock_get_conf(monkeypatch):
    """ mock helper function to not touch the file system """
    def get_conf_wrapper():
        conf = get_conf()
        monkeypatch.setitem(
            conf.rig._Rig__sddb_module_cache, "dids",
            {"pbl_diag_part_num": "",
             "app_did_dict": {"F186": {'size': '1'},
                              "EDA0": {'size': '110'},
                              "F12E": {'size': '7'}},
             "pbl_did_dict": {"F12C": {'size': '7'}},
             "sbl_did_dict": {"F122": {'size': '7'}},
             "resp_item_dict": {}})
        monkeypatch.setitem(
            conf.rig._Rig__sddb_module_cache, "dtcs",
            {"sddb_dtcs": {}, "sddb_report_dtc": {}})
        monkeypatch.setitem(
            conf.rig._Rig__sddb_module_cache, "services",
            {"pbl": {}, "sbl": {}, "app": {}})
        return conf
    return get_conf_wrapper

def test_conf(tmp_path, monkeypatch):
    """ pytest: conf parsing """
    conf_file_content = """
    default_rig: p2
    rigs:
        p2:
            hostname: host2.domain
            user: pi #optional
            platform: hvbm
            signal_broker_port: 50051 #optional
    platforms:
        hvbm:
            default_signal_send: sendsignal
            default_signal_receive: receivesignal
    """
    tmp_path.joinpath("conf_local.yml").write_text(conf_file_content)
    tmp_path.joinpath("conf_default.yml").write_text(conf_file_content)
    def mock_hilding_root():
        return tmp_path
    monkeypatch.setattr(Conf, "hilding_root", mock_hilding_root())
    conf = Conf()
    assert conf.default_rig == "p2"
    assert conf.rig.hostname == "host2.domain"
    assert conf.rig.user == "pi"
    assert conf.rig.platform == "hvbm"
    assert conf.rig.signal_broker_port == "50051"
    assert conf.rig.default_signal_send == "sendsignal"
    assert conf.rig.default_signal_receive == "receivesignal"

def test_get_sddb(mock_get_conf):
    """ pytest: testing sddb access """
    conf = mock_get_conf()
    assert "pbl_diag_part_num" in conf.rig.sddb_dids
    assert "sddb_dtcs" in conf.rig.sddb_dtcs
    assert "sddb_report_dtc" in conf.rig.sddb_dtcs
    assert "app" in conf.rig.sddb_services
    assert "pbl" in conf.rig.sddb_services
    assert "sbl" in conf.rig.sddb_services
