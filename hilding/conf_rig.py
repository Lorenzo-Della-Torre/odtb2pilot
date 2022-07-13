"""
Handle rig configuration

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""
import importlib
from supportfunctions.support_sec_acc import SecAccessParam

from hilding.conf_analytics import Analytics
#SSA = SupportSecurityAccess()

class Rig:
    """ hilding rig management """
    def __init__(self, conf):
        self.conf = conf
        self.analytics = Analytics(self)
        self.__sddb_module_cache = {}

    def __str__(self):
        __str = f"Rig({self.user}@{self.hostname}):\n"
        composite_attr = [
            'sddb_dids',
            'sddb_dtcs',
            'sddb_services',
        ]
        for attr in dir(self):
            if hasattr(Rig, attr) and isinstance(getattr(Rig, attr), property):
                if attr in composite_attr:
                    __str += f"{attr}: <contains {len(getattr(self, attr))} " \
                             f"items>\n"
                else:
                    __str += f"{attr}: {getattr(self, attr)}\n"
        return __str

    @property
    def hostname(self):
        """ conf hostname """
        return self.conf.selected_rig_dict.get('hostname')

    @property
    def user(self):
        """ conf user """
        return self.conf.selected_rig_dict.get('user', 'pi')

    @property
    def platform(self):
        """ conf platform """
        return self.conf.selected_rig_dict.get('platform')

    @property
    def signal_broker_port(self):
        """ conf signal broker port number """
        return str(self.conf.selected_rig_dict.get('signal_broker_port', 50051))

    @property
    def sa_keys(self):
        """ conf platform fixed key or local fixed key override """
        platform_data = self.conf.platforms.get(self.platform, {})
        platform_sa_keys : SecAccessParam = {
            "SecAcc_Gen": platform_data.get("SecAcc_Gen"),
            "fixed_key": platform_data.get("fixed_key"),
            "auth_key": platform_data.get("auth_key"),
            "proof_key": platform_data.get("proof_key")
        }
        return self.conf.selected_rig_dict.get("sa_keys", platform_sa_keys)

    @property
    def signal_send(self):
        """ conf platform signal send """
        platform_data = self.conf.platforms.get(self.platform, {})
        platform_signal_send = platform_data.get("signal_send")
        return self.conf.selected_rig_dict.get(
            "signal_send", platform_signal_send)

    @property
    def signal_receive(self):
        """ conf platform signal receive """
        platform_data = self.conf.platforms.get(self.platform, {})
        platform_signal_receive = platform_data.get("signal_receive")
        return self.conf.selected_rig_dict.get(
            "signal_receive", platform_signal_receive)

    @property
    def signal_periodic(self):
        """ conf platform signal periodic """
        platform_data = self.conf.platforms.get(self.platform, {})
        platform_signal_periodic = platform_data.get("signal_periodic")
        return self.conf.selected_rig_dict.get(
            "signal_periodic", platform_signal_periodic)

    @property
    def signal_tester_present(self):
        """ conf platform signal tester present """
        platform_data = self.conf.platforms.get(self.platform, {})
        platform_signal_tester_present = platform_data.get("signal_tester_present")
        return self.conf.selected_rig_dict.get(
            "signal_tester_present", platform_signal_tester_present)

    @property
    def namespace(self):
        """ conf platform signal tester present """
        platform_data = self.conf.platforms.get(self.platform, {})
        platform_namespace = platform_data.get("namespace")
        return self.conf.selected_rig_dict.get(
            "namespace", platform_namespace)


    @property
    def wakeup_frame(self):
        """ conf platform wakeup frame """
        platform_data = self.conf.platforms.get(self.platform, {})
        platform_wakeup_frame = platform_data.get("wakeup_frame", "")
        return self.conf.selected_rig_dict.get(
            "wakeup_frame", platform_wakeup_frame)

    @property
    def rig_path(self):
        """ get the path to the selected rig """
        rigs = self.conf.hilding_root.joinpath("rigs")
        return ensure_exists(rigs.joinpath(self.conf.selected_rig))

    @property
    def vbf_path(self):
        """ get the path to the vbf dir for the selected rig """
        return ensure_exists(self.rig_path.joinpath("vbf"))

    @property
    def sddb_path(self):
        """ get the path to the sddb dir for the selected rig """
        return ensure_exists(self.rig_path.joinpath("sddb"))

    @property
    def dbc_path(self):
        """ get the path to the dbc dir for the selected rig """
        return ensure_exists(self.rig_path.joinpath("dbc"))

    @property
    def build_path(self):
        """ get the path to the build dir for the selected rig """
        return ensure_exists(self.rig_path.joinpath("build"))

    @property
    def sddb_dids(self):
        """ get sddb did content """
        return self.__get_sddb("dids")

    @property
    def sddb_dtcs(self):
        """ get sddb dtc content """
        return self.__get_sddb("dtcs")

    @property
    def sddb_services(self):
        """ get sddb services content """
        return self.__get_sddb("services")

    def __get_sddb(self, content: str):
        """
        accessor method to get one of the generated sddb modules
        (e.g.  "dids", "dtcs", "services")
        """
        if not content in self.__sddb_module_cache:
            sddb_file = self.build_path.joinpath(f"sddb_{content}.py")
            if not sddb_file.exists():
                raise ModuleNotFoundError(f"The {sddb_file} file does not exist")
            sddb_module = get_module(sddb_file)
            self.__sddb_module_cache[content] = {
                k:v for k,v in vars(sddb_module).items()
                if not k.startswith('__')}
        return self.__sddb_module_cache[content]

    def get_testrun_data(self):
        """ accessor method to get get_testrun_data module """
        testrun_data_file = self.build_path.joinpath("testrun_data.py")
        if not testrun_data_file.exists():
            raise ModuleNotFoundError("The testrun_data.py file does not exist")

        testrun_data_module = get_module(testrun_data_file)
        testrun_data = {
            k:v for k,v in vars(testrun_data_module).items()
            if not k.startswith('__')}
        return testrun_data


def ensure_exists(path):
    """ create directory if it does not exists """
    path.mkdir(exist_ok=True)
    return path

def get_module(module_filename):
    """ load module from file and return module object """
    spec = importlib.util.spec_from_file_location("spec", module_filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
