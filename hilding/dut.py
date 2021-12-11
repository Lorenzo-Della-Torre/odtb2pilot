/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



**********************************************************************************/


"""
Support device under test module
"""

import os
import re
import time
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
import yaml

import grpc
import requests

from protogenerated.common_pb2 import Empty
from protogenerated.common_pb2 import NameSpace

from protogenerated.system_api_pb2_grpc import SystemServiceStub
from protogenerated.network_api_pb2_grpc import NetworkServiceStub

from supportfunctions.support_can import SupportCAN
from supportfunctions.support_can import CanParam
from supportfunctions.support_can import PerParam
from supportfunctions.support_can import CanMFParam
from supportfunctions.support_service3e import SupportService3e
from hilding.uds import Uds
from hilding.uds import EicDid
from hilding.uds import IoVmsDid
from hilding import analytics
from hilding import get_conf

# pylint: disable=no-member
import protogenerated.system_api_pb2
if hasattr(protogenerated.system_api_pb2, "License"):
    # pylint: disable=no-name-in-module,redefined-outer-name,import-outside-toplevel
    from protogenerated.system_api_pb2 import License
    from protogenerated.system_api_pb2 import LicenseStatus # pylint: disable=no-name-in-module
    from protogenerated.system_api_pb2 import FileDescription # pylint: disable=no-name-in-module
    from protogenerated.system_api_pb2 import FileUploadRequest # pylint: disable=no-name-in-module


log = logging.getLogger('dut')


class DutTestError(BaseException):
    """ Exception class for test errors """

def beamy_feature(func):
    """ Decorator to mark which functions require the beamy signal broker """
    def wrapper_beamy_feature(*args, **kwargs):
        if not hasattr(protogenerated.system_api_pb2, "License"):
            log.error("you try to access %s, but it requires beamy broker "
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
    def __init__(self):
        self.conf = get_conf()
        self.channel = grpc.insecure_channel(
            f'{self.conf.rig.hostname}:'
            f'{self.conf.rig.signal_broker_port}')
        self.network_stub = NetworkServiceStub(self.channel)
        self.system_stub = SystemServiceStub(self.channel)
        self.namespace = NameSpace(name="Front1CANCfg0")
        self.protocol = 'can'
        self.framelength_max = 8
        self.padding = True
        self.uds = Uds(self)

    def __getitem__(self, key):# pylint: disable=too-many-return-statements
        # Legacy subscript access to dut object for old code
        # Do not use this for new features!
        if key == "netstub":
            return self.network_stub
        if key == "send":
            return self.conf.rig.signal_send
        if key == "receive":
            return self.conf.rig.signal_receive
        if key == "namespace":
            return self.namespace
        if key == 'protocol':
            return self.protocol
        if key == 'framelength_max':
            return self.framelength_max
        if key == 'padding':
            return self.padding
        raise KeyError(key)

    def precondition(self, timeout=30):
        """Run preconditions and start heartbeat

        Args:
            timeout (int, optional): Decides for how long the test is allowed to run.
            Defaults to 30.
        """

        self.uds.step = 100
        # start heartbeat, repeat every 0.8 second
        heartbeat_param: PerParam = {
            "name" : "Heartbeat",
            "send" : True,
            "id" : self.conf.rig.signal_periodic,
            "nspace" : self.namespace.name,
            "protocol" : "can",
            "framelength_max" : 8,
            "padding" : True,
            "frame" : bytes.fromhex(self.conf.rig.wakeup_frame),
            "intervall" : 0.4
            }
        log.debug("heartbeat_param %s", heartbeat_param)

        iso_tp = SupportCAN()

        # start heartbeat, repeat every x second
        iso_tp.start_heartbeat(self.network_stub, heartbeat_param)

        # start testerpresent without reply
        tp_name = self.conf.rig.signal_tester_present
        SupportService3e.start_periodic_tp_zero_suppress_prmib(self, tp_name)

        # record signal we send as well
        iso_tp.subscribe_signal(self, timeout)
        log.debug("precondition can_p2 %s", self)

        # record signal we send as well. Do notice the reverse order of the
        # send and receive signals!
        can_p2: CanParam = {"netstub": self.network_stub,
                            "send": self.conf.rig.signal_receive,
                            "receive": self.conf.rig.signal_send,
                            "namespace": self.namespace,
                            "protocol": self.protocol,
                            "framelength_max": self.framelength_max,
                            "padding" : self.padding
                           }
        iso_tp.subscribe_signal(can_p2, timeout)

        # do not generate FC frames for signals we generated:
        time.sleep(1)
        can_mf: CanMFParam = {
            "block_size": 0,
            "separation_time": 0,
            "frame_control_delay": 10,
            "frame_control_flag": 48,
            "frame_control_auto": False
            }
        iso_tp.change_mf_fc(can_p2["receive"], can_mf)

        log.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Precondition started~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")

        res = self.uds.read_data_by_id_22(EicDid.complete_ecu_part_number_eda0)
        log.info("Precondition eda0: %s\n", res)

        res = self.uds.read_data_by_id_22(IoVmsDid.pbl_software_part_num_f125)
        log.info("Precondition f125: %s\n", res)
        self.uds.step = 0

    def postcondition(self, start_time, result):
        """Run postconditions and change to mode 1

        Args:
            start_time (float): Used to calculate time needed for test
            result (boolean): Result of the test script
        """
        log.info("")
        log.info("~~~~Postcondition: Display current mode/session, change to mode1 (default)~~~~")
        self.uds.step = 200
        res_mode = self.uds.active_diag_session_f186()
        log.info("Current mode/session: %s", res_mode.details["mode"])

        self.uds.set_mode(1)
        if self.uds.mode != 1:
            DutTestError("Could not set the ECU to mode 1 (default)")

        log.debug("\nTime: %s \n", time.time())
        log.info("Testcase end: %s", datetime.now())
        log.info("Time needed for testrun (seconds): %s", int(time.time() - start_time))

        log.info("Do cleanup now...")
        log.info("Stop all periodic signals sent")

        iso_tp = SupportCAN()
        iso_tp.stop_periodic_all()

        # deregister signals
        iso_tp.unsubscribe_signals()

        # if threads should remain: try to stop them
        iso_tp.thread_stop()

        log.info("Test cleanup end: %s\n", datetime.now())

        if result:
            log.info("Testcase result: PASSED")
        else:
            log.info("Testcase result: FAILED")

    def start(self):
        """Log the current time and return a timestamp

        Returns:
            float: Current time
        """

        start_time = datetime.now()
        timestamp = start_time.timestamp()
        log.info("Running test on: %s:%s",
                     self.conf.rig.hostname,
                     self.conf.rig.signal_broker_port)
        log.info("Testcase start: %s", start_time)
        log.info("Time: %s \n", timestamp)
        return timestamp

    @analytics_test_step
    def step(self, func, *args, purpose="", **kwargs):
        """Add a test step. This method runs the function func with arguments *args and **kwargs.

        This method also increase the value of step

        Args:
            func (function): A function or method that should be run in the step
            purpose (str, optional): The purpose will be added to the log. Defaults to "".

        Returns:
            any: This method will return whatever is returned by func
        """
        self.uds.step += 1

        logging.info("")
        logging.info("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Step %s started~~~~~~~~~~~~~~~~~~~~~~~~~~~~~",
        self.uds.step)
        logging.info("Purpose: %s", purpose)

        self.uds.purpose = purpose
        if inspect.ismethod(func):
            # step should also works with class methods and not just functions.
            # e.g. dut.step(dut.uds.set_mode, 2)
            return func(*args, **kwargs)
        return func(self, *args, **kwargs)

    @beamy_feature
    def check_licence(self):
        """
        Check the beamy check_license with beamylabs
        """
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
        log.info(response)

    @beamy_feature
    def upload_file(self, path, dest_path):
        """
        Upload configuration file to the beamy signal broker
        """
        sha256 = get_sha256(path)
        log.info(sha256)
        with open(path, "rb") as f:
            # make sure path is unix style (necessary for windows, and does no harm
            # on linux)
            upload_iterator = generate_data(
                f, dest_path.replace(ntpath.sep, posixpath.sep), 1000000, sha256)
        response = self.system_stub.UploadFile(upload_iterator)
        log.info("uploaded: %s %s", path, response)

    @beamy_feature
    def upload_folder(self, folder):
        """
        Upload configuration folder to the beamy signal broker
        """
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
        log.info("License requested check your mail: %s", id_value)


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
        finally activate the new configuration.

        Remember to set it back to default once you are done as it affects
        subsequent tests and users
        """
        dbpath = get_conf().rig.dbc_path

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

    def get_platform_yml_parameters(self, test_filename_py):
        """Get test_filename_<platform>.yml file from the same directory as the
        main test if you really want to add external parameters to the test

        usage example:
            parameters = dut.get_platform_yml_parameters(__file__)
            dut.send = parameters["send"]

        Args:
            test_filename_py (string):

        Raises:
            DutTestError: If platform is not currently supported

        Returns:
            any: Parameters from yml-file
        """
        test_filename = Path(test_filename_py).with_suffix("")
        platform = self.conf.rig.platform
        test_filename_platform_yml = Path(f"{test_filename}_{platform}.yml")
        if not test_filename_platform_yml.exists():
            raise DutTestError(
                f"Your platform is not supported for this test. Please add "
                f"{test_filename_platform_yml} in the same directory as the test")
        with open(test_filename_platform_yml) as yml:
            parameters = yaml.safe_load(yml)
        return parameters




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
}#
