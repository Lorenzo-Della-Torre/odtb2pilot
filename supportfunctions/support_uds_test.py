"""
Pytest unit tests for support_uds.py

The class takes replies as hex strings from the ECU and parses out the relevant parts.
"""
import pytest
from supportfunctions.support_uds import UdsResponse
from supportfunctions.support_uds import extract_fields


def test_uds_response():
    """ pytest: UdsResponse """
    # test the did F12C
    f12c_response = "100A62F12C32263666204141"
    response = UdsResponse(f12c_response)
    assert response.data['did'] == "F12C"
    assert response.data['details']['valid'] == "32263666 AA"

    # test the composite did EDA0
    eda0 = "104A62EDA0F12032299361204142F12A32290749202020F12BFFFFFFFFFFFFFF" + \
    "F12E053229942520414532299427204143322994292041453229943020414132263666204141" + \
    "F18C30400011"
    response = UdsResponse(eda0)
    assert response.data['details']['F12E_valid'][-1] == "32263666 AA"

def test_uds_reponse_with_mode():
    """ pytest: make sure uds response with mode works properly """
    # test the did F122
    f122_response = "XXXX62F122"
    response = UdsResponse(f122_response, mode=3)
    assert response.data['did'] == "F122"
    with pytest.raises(KeyError):
        UdsResponse(f122_response, mode=1)

def test_dtc_snapshot():
    """ pytest: test parsing of dtc snapshots """

    dtc_snapshot = \
        "116859040B4A00AF2019DD0000000000DD01000000DD0200DD0A00DD0B000000" + \
        "DD0C004028FFEF25074802000001480300004947000649FA00" + \
        "4A2A00000000000000000000000000000000000000000000000000000000FFFF" + \
        "4B1900000000000000004B1A00000000000000004B1B0000000000000000" + \
        "D02102D9010110D96007D007D007D0DAD00000DB755817E8DB9F2000" + \
        "DBA400040000DBB400000000FFFF000000000000000000000000000000000000" + \
        "F40D00F4463C2119DD0000000000DD01000000DD0200DD0A00DD0B000000" + \
        "DD0C004028FFF2095A4802000001480300004947000049FA0" + \
        "04A2A00000000000000000000000000000000000000000000000000000000FFFF" + \
        "4B1900000000000000004B1A00000000000000004B1B0000000000000000" + \
        "D02102D9010110D96007D007D007D0DAD00000DB75581590DB9F2000" + \
        "DBA400040000DBB400000000FFFF000000000000000000000000000000000000" + \
        "F40D00F4463C"

    res = UdsResponse(dtc_snapshot)
    assert "dtc" in res.data
    assert res.data["dtc"] == "0B4A00"
    assert res.data["sid"] == "59"
    assert res.data["service"] == "ReadDTCInformation"

def test_negative_response():
    """ pytest: test negative responses """
    negative_response = "037F191300000000"
    res = UdsResponse(negative_response)
    assert res.data["nrc"] == "13"
    assert res.data["nrc_name"] == "incorrectMessageLengthOrInvalidFormat"
    res = UdsResponse("037F001100000000")
    print(res)
    assert res.data["nrc_name"] == "serviceNotSupported"

def test_dtc_snapshot_ids():
    """ pytest: test call for listing dtc snapshot ids from the ECU """
    raw = \
        '105A59030D150021C29A00211C4068201C406821C64A00210C4500210CD800' + \
        '210B3B00200B3B00210B4000200B4000210B4A00200B4A00210B4F00200B4F' + \
        '00210B4500210B5400210B5900210B5E00210B63002150605721D0640021'
    res = UdsResponse(raw)
    assert res.data["sid"] == "59"
    assert res.data["service"] == "ReadDTCInformation"
    assert res.data["count"] == 22
    snapshot_id0 = res.data["snapshot_ids"][0]
    assert snapshot_id0 == ('21','0D1500')

def test_dtc_extended_data_record():
    """ pytest: test parsing of extended data records """
    raw = \
        '102459060B4A00AF01FF020003FF04FF0500060007FF107F127F2000000000' + \
        '21000000003023'
    res = UdsResponse(raw)

    assert res.data["occ1"] == "FF"
    assert res.data["fdc10"] == "7F"
    assert res.data["ts20"] == "00000000"
    assert res.data["ts21"] == "00000000"
    assert res.data["si30"] == "23"

def test_extract_fields():
    """ pytest: test extract_fields helper function """
    regex_fields = [
        '.*(01)(?P<occ1>..)',
        '.*(02)(?P<occ2>..)',
        '.*(03)(?P<occ3>..)',
        '.*(04)(?P<occ4>..)',
        '.*(05)(?P<occ5>..)',
        '.*(06)(?P<occ6>..)',
        '.*(10)(?P<fdc10>..)',
        '.*(20)(?P<ts20>.{8})',
        '.*(21)(?P<ts21>.{8})',
        '.*(30)(?P<si30>..)'
    ]
    fields = extract_fields(
        '01fa02fb03fc04fd05fe06ff07aa10ab12ac20xxxxxxxx21yyyyyyyy30zz',
        regex_fields)
    assert "occ1" in fields
    assert fields["occ1"] == "fa"
    assert fields["ts20"] == "xxxxxxxx"
    assert fields["ts21"] == "yyyyyyyy"
    assert fields["si30"] == "zz"

def test_active_session():
    """ pytest: test mode/session state changes in response """
    response = UdsResponse("0462F18601000000")
    assert response.data['details']['mode'] == 1
    # set mode/session to 3 (extended) gives us actually a proper reply
    response = UdsResponse("065003001901F400")
    assert response.data['details']['mode'] == 3
