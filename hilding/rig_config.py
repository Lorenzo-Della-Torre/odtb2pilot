"""
Handle rig configuration
"""
import importlib
from hilding.analytics_config import Analytics

class Rig:
    """ hilding rig management """
    def __init__(self, settings):
        self.settings = settings
        self.analytics = Analytics(self)
        self.__sddb_module_cache = {}

    @property
    def hostname(self):
        """ settings hostname """
        return self.settings.selected_rig_dict.get('hostname')

    @property
    def user(self):
        """ settings user """
        return self.settings.selected_rig_dict.get('user', 'pi')

    @property
    def platform(self):
        """ settings platform """
        return self.settings.selected_rig_dict.get('platform')

    @property
    def signal_broker_port(self):
        """ settings signal broker port number """
        return str(self.settings.selected_rig_dict.get('signal_broker_port', 50051))

    @property
    def fixed_key(self):
        """ settings platform fixed key """
        platform_data = self.settings.settings.get(self.platform, {})
        return platform_data.get("fixed_key", "0102030405")

    @property
    def default_signal_send(self):
        """ settings platform default signal send """
        platform_data = self.settings.settings.get(self.platform, {})
        return platform_data.get("default_signal_send")

    @property
    def default_signal_receive(self):
        """ settings platform default signal receive """
        platform_data = self.settings.settings.get(self.platform, {})
        return platform_data.get("default_signal_receive")

    @property
    def rig_path(self):
        """ get the path to the default rig """
        rigs = self.settings.hilding_root.joinpath("rigs")
        return ensure_exists(rigs.joinpath(self.settings.default_rig))

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
