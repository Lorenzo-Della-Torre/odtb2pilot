"""
Analytics configuration
"""
import platform

class Analytics:
    """ analytics configuration class """
    def __init__(self, rig):
        self.rig = rig
        self.config = self.rig.settings.selected_rig_dict.get('analytics', {})

    # pylint: disable=missing-function-docstring
    @property
    def test_suite_name(self):
        return self.config.get('test_suite_name', 'Hilding user test suite')

    @property
    def test_suite_identifier(self):
        return self.config.get('test_suite_identifier', '1.0.2')

    @property
    def test_suite_description(self):
        return self.config.get('test_suite_description', 'Test case runner')

    @property
    def executor(self):
        return self.config.get('executor', 'Hilding')

    @property
    def project(self):
        return self.config.get('project', 'UNKNOWN')

    @property
    def platform(self):
        return self.config.get('platform', 'UNKNOWN')

    @property
    def branch(self):
        return self.config.get('branch', 'UNKNOWN')

    @property
    def ecu(self):
        return self.config.get('ecu', 'UNKNOWN')

    @property
    def dbc(self):
        return self.config.get('dbc', 'UNKNOWN')

    @property
    def vehicle_project(self):
        return self.config.get('vehicle_project', 'UNKNOWN')

    @property
    def vehicle_series(self):
        return self.config.get('vehicle_series', 'UNKNOWN')

    @property
    def sw_version(self):
        return self.config.get('sw_version', 'UNKNOWN')

    @property
    def sw_githash(self):
        return self.config.get('sw_githash', 'UNKNOWN')

    @property
    def sw_changeset(self):
        return self.config.get('sw_changeset', 'UNKNOWN')

    @property
    def sw_inhousechangeset(self):
        return self.config.get('sw_inhousechangeset', 'UNKNOWN')

    @property
    def testenv_info_name(self):
        return self.config.get('testenv_info_name', platform.node())

    @property
    def testenv_info_description(self):
        return self.config.get('testenv_info_description', 'Hilding test rig')

    @property
    def testenv_info_platform(self):
        return self.config.get('testenv_info_platform', 'Hilding')
