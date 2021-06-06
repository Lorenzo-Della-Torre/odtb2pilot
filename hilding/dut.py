"""
Support device under test module
"""

import os
import re
import logging
import inspect
import json
import base64
import shutil
import hashlib
import posixpath
import ntpath
from glob import glob
from pathlib import Path
from datetime import datetime
from tempfile import TemporaryDirectory

import pytest
import grpc
import requests

from protogenerated.common_pb2 import Empty
from protogenerated.common_pb2 import NameSpace

from protogenerated.system_api_pb2_grpc import SystemServiceStub
from protogenerated.network_api_pb2_grpc import NetworkServiceStub

from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition
from hilding import analytics
from hilding.uds import Uds
from hilding.platform import get_platform
from hilding.platform import get_release_dir
from hilding.platform import get_parameters
from hilding.settings import Settings

# pylint: disable=no-member
import protogenerated.system_api_pb2
if hasattr(protogenerated.system_api_pb2, "License"):
    # pylint: disable=no-name-in-module,redefined-outer-name,import-outside-toplevel
    from protogenerated.system_api_pb2 import License
    from protogenerated.system_api_pb2 import LicenseStatus # pylint: disable=no-name-in-module
    from protogenerated.system_api_pb2 import FileDescription # pylint: disable=no-name-in-module
    from protogenerated.system_api_pb2 import FileUploadRequest # pylint: disable=no-name-in-module

class DutTestError(BaseException):
    """ Exception class for test errors """

def beamy_feature(func):
    """ Decorator to mark which functions require the beamy signal broker """
    def wrapper_beamy_feature(*args, **kwargs):
        if not hasattr(protogenerated.system_api_pb2, "License"):
            logging.error("you try to access %s, but it requires beamy broker "
                          "which is not supported", func.__name__)
            raise DutTestError
        func(*args, **kwargs)
    return wrapper_beamy_feature

def analytics_test_step(func):
    """ Decorator to add test step analytics """
    def wrapper_test_step(self, *args, **kwargs):
        if analytics.lack_testcases():
            return func(self, *args, **kwargs)

        # we can only add test steps if we have a testcase
        analytics.teststep_started(f"step{self.uds.step+1}")
        try:
            result = func(self, *args, **kwargs)
        except DutTestError as e:
            # maybe we should rename DutTestError to DutTestFailed instead
            analytics.teststep_ended("failed")
            raise e
        except Exception as e:
            analytics.teststep_ended("errored")
            raise e
        # if we don't get any exception the test has passed
        analytics.teststep_ended("passed")
        return result
    return wrapper_test_step


class Dut:
    """ Device under test """
    # pylint: disable=too-many-instance-attributes
    def __init__(self, custom_yml_file=None):
        settings = Settings()
        self.dut_host = settings.hostname
        self.dut_port = settings.signal_broker_port
        self.channel = grpc.insecure_channel(f'{self.dut_host}:{self.dut_port}')
        self.network_stub = NetworkServiceStub(self.channel)
        self.system_stub = SystemServiceStub(self.channel)

        parameters = get_parameters(custom_yml_file)
        self.send = parameters["run"]["send"]
        self.receive = parameters["run"]["receive"]
        self.namespace = NameSpace(name="Front1CANCfg0")

        self.uds = Uds(self)

    def __getitem__(self, key):
        # Legacy subscript access to dut object for old code
        # Do not use this for new features!
        if key == "netstub":
            return self.network_stub
        if key == "send":
            return self.send
        if key == "receive":
            return self.receive
        if key == "namespace":
            return self.namespace
        raise KeyError(key)

    def precondition(self, timeout=30):
        """ run preconditions and start heartbeat """
        return SupportPrecondition().precondition(self, timeout)

    def postcondition(self, start_time, result):
        """ run postconditions and change to mode 1 """
        return SupportPostcondition().postcondition(self, start_time, result)

    def start(self):
        """ log the current time and return a timestamp """
        start_time = datetime.now()
        timestamp = start_time.timestamp()
        logging.info("Running test on: %s:%s", self.dut_host, self.dut_port)
        logging.info("Testcase start: %s", start_time)
        logging.info("Time: %s \n", timestamp)
        return timestamp

    @analytics_test_step
    def step(self, func, *args, purpose="", **kwargs):
        """ add test step """
        self.uds.step += 1
        self.uds.purpose = purpose
        if inspect.ismethod(func):
            # step should also works with class methods and not just functions.
            # e.g. dut.step(dut.uds.set_mode, 2)
            return func(*args, **kwargs)
        return func(self, *args, **kwargs)

    @beamy_feature
    def check_licence(self):
        """ check the beamy check_licence with beamylabs """
        # pylint: disable=no-member
        status = self.system_stub.GetLicenseInfo(Empty()).status
        assert status == LicenseStatus.VALID, \
            "Check your license, status is: %d" % status

    @beamy_feature
    def reload_configuration(self):
        """
        Reload the signal broker configuration

        This need to be done after a configuration upload
        """
        request = Empty()
        response = self.system_stub.ReloadConfiguration(request, timeout=60000)
        logging.info(response)

    @beamy_feature
    def upload_file(self, path, dest_path):
        """ Upload configuration file to the beamy signal broker """
        sha256 = get_sha256(path)
        logging.info(sha256)
        with open(path, "rb") as f:
            # make sure path is unix style (necessary for windows, and does no harm
            # on linux)
            upload_iterator = generate_data(
                f, dest_path.replace(ntpath.sep, posixpath.sep), 1000000, sha256)
        response = self.system_stub.UploadFile(upload_iterator)
        logging.info("uploaded: %s %s", path, response)

    @beamy_feature
    def upload_folder(self, folder):
        """ Upload configuration folder to the beamy signal broker """
        files = [y for x in os.walk(folder)
                 for y in glob(os.path.join(x[0], '*'))
                 if not os.path.isdir(y)]
        for f in files:
            self.upload_file(f, f.replace(folder, ""))

    @beamy_feature
    def request_license(self, id_value=None):
        """
        re-request a license. By default uses the same email (requestId) as
        before. hash will be found in your mailbox
        """
        # pylint: disable=no-member
        if id_value is None:
            id_value = self.system_stub.GetLicenseInfo(Empty()).requestId
            assert id_value.encode("utf-8") != '', \
                "no old id avaliable, provide your email"
        request_machine_id = \
            self.system_stub.GetLicenseInfo(Empty()).requestMachineId
        body = {
            "id": id_value.encode("utf-8"),
            "machine_id": json.loads(request_machine_id)
        }
        resp_request = requests.post(
            'https://www.beamylabs.com/requestlicense',
            json = {"licensejsonb64": base64.b64encode(json.dumps(body))}
        )

        # pylint: disable=no-member
        assert resp_request.status_code == requests.codes.ok, \
            "Response code not ok, code: %d" % (resp_request.status_code)
        logging.info("License requested check your mail: %s", id_value)


    @beamy_feature
    def download_and_install_license(self, hash_without_dashes, id_value=None):
        """
        using your hash, upload your license (remove the dashes) use the same
        email (requestId) address as before
        """
        if id_value is None:
            # pylint: disable=no-member
            id_value = self.system_stub.GetLicenseInfo(Empty()).requestId
            assert id_value.encode("utf-8") != '', \
                "no old id avaliable, provide your email"
        resp_fetch = requests.post(
            'https://www.beamylabs.com/fetchlicense',
            json = {"id": id_value, "hash": hash_without_dashes}
        )

        # pylint: disable=no-member
        assert resp_fetch.status_code == requests.codes.ok, \
            "Response code not ok, code: %d" % (resp_fetch.status_code)
        license_info = resp_fetch.json()
        license_bytes = license_info['license_data'].encode('utf-8')

        # you agree to license and conditions found here
        # https://www.beamylabs.com/license/
        self.system_stub.SetLicense(
            License(termsAgreement = True, data = license_bytes)
        )


    @beamy_feature
    def reconfigure_broker(
            self, pattern="", replace="",
            can0_dbc_file='SPA3010_ConfigurationsSPA3_Front1CANCfg_180615_Prototype.dbc',
            can1_dbc_file='SPA3230_ConfigurationsCMAVolvo2_RMSCANCfg_181214_.dbc'):

        """
        Modify the signal broker configuration

        This build a new configuration directory and uploads it to the beamy
        signal broker. Once that done, it also issues a reload_configuration to
        finally activate the new configuation.

        Remember to set it back to default once you are done as it affects
        subsequent tests and users
        """
        dbpath = get_release_dir()

        with TemporaryDirectory() as tmpdirname:
            config_dir = Path(tmpdirname)
            config_can = config_dir.joinpath("can")
            config_can.mkdir()


            with open(dbpath.joinpath(can0_dbc_file), "r") as from_dbc_file:
                with open(config_can.joinpath(can0_dbc_file), "w") as to_dbc_file:
                    for line in from_dbc_file:
                        # see if regex matches
                        if pattern:
                            line = re.sub(pattern, replace, line)
                        to_dbc_file.write(line)

            interfaces["chains"][0]["dbc_file"] = \
                str(Path("can").joinpath(can0_dbc_file))

            shutil.copy(dbpath.joinpath(can1_dbc_file), config_can)
            interfaces["chains"][1]["dbc_file"] =  \
                str(Path("can").joinpath(can1_dbc_file))

            with open(config_dir.joinpath("interfaces.json"), "w") as f:
                json.dump(interfaces, f, indent=4)

            self.upload_folder(tmpdirname)
            self.reload_configuration()


def get_dut_custom():
    """
    Create a dut with a custom parameters file that has the same name as the
    caller (most commonly the name of the test file)
    """
    frame_info = inspect.stack()[1]
    filename = Path(frame_info.filename)
    return Dut(custom_yml_file=os.path.basename(filename.with_suffix(".yml")))


def get_sha256(filename):
    """ Helper function for the file upload process """
    with open(filename,"rb") as f:
        byte_string = f.read() # read entire file as bytes
    readable_hash = hashlib.sha256(byte_string).hexdigest()
    return readable_hash

@beamy_feature
def generate_data(filename, dest_path, chunk_size, sha256):
    """ Helper function for making sure the file upload works on windows """
    # 20000 as in infinity
    for x in range(0, 20000):
        if x == 0:
            file_description = FileDescription(sha256 = sha256, path = dest_path)
            yield FileUploadRequest(fileDescription = file_description)
        else:
            buf = filename.read(chunk_size)
            if not buf:
                break
            yield FileUploadRequest(chunk = buf)


interfaces = {
    'default_namespace': 'Front1CANCfg0',
    'chains': [
        {
            'type': 'can',
            'namespace': 'Front1CANCfg0',
            'device_name': 'can0',
            'dbc_file': ''
        },
        {
            'type': 'can',
            'namespace': 'BecmRmsCanFr1',
            'device_name': 'can1',
            'dbc_file': ''
        },
        {
            'type': 'virtual', 'namespace': 'RpiGPIO', 'device_name': 'virtual'
        }
    ],
    'gateway': {'tcp_socket_port': 4040, 'gateway_pid': 'gateway_pid'},
    'auto_config_boot_server': {
        'port': 4000, 'server_pid': 'auto_config_boot_server_pid'
    },
    'reflectors': [],
    'support_dut_test_config': 'yes'
}



##################################
# Pytest unit tests starts here
##################################

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

    status = dut.system_stub.GetLicenseInfo(Empty()).status
    assert status == LicenseStatus.VALID, \
        "Check your license, status is: %d" % status


def test_upload_folder():
    """ pytest: testing upload_folder """
    dut = Dut()
    dut.reconfigure_broker(
        "BO_ 1875 HvbmdpToHvbmUdsDiagRequestFrame : 8 HVBMdp",
        "BO_ 1875 HvbmdpToHvbmUdsDiagRequestFrame : 7 HVBMdp"
    )


def test_get_platform():
    """ pytest: testing get_platform """
    old_odtbproj = os.getenv("ODTBPROJ")

    os.environ["ODTBPROJ"] = "MEP2_SPA1"
    assert get_platform() == "spa1"
    os.environ["ODTBPROJ"] = "MEP2_SPA2"
    assert get_platform() == "spa2"
    os.environ["ODTBPROJ"] = "MEP2_HLCM"
    assert get_platform() == "hlcm"
    os.environ["ODTBPROJ"] = "MEP2_ED_IFHA"
    assert get_platform() == "ed_ifha"
    os.environ["ODTBPROJ"] = ""
    with pytest.raises(EnvironmentError, match=r".*not set"):
        get_platform()
    os.environ["ODTBPROJ"] = "NONESENSE"
    with pytest.raises(EnvironmentError, match=r"Unknown ODTBPROJ.*"):
        get_platform()

    os.environ["ODTBPROJ"] = old_odtbproj


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
    with pytest.raises(FileNotFoundError, match=r"Could not find .*support_dut.yml"):
        get_dut_custom()
