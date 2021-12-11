"""
Analytics configuration
"""
import platform

class Analytics:
    """ analytics configuration class """
    def __init__(self, rig):
        self.rig = rig
        self.analytics = self.rig.conf.selected_rig_dict.get('analytics', {})

    # pylint: disable=missing-function-docstring
    @property
    def test_suite_name(self):
        return self.analytics.get('test_suite_name', 'Hilding user test suite')

    @property
    def test_suite_identifier(self):
        return self.analytics.get('test_suite_identifier', '1.0.2')

    @property
    def test_suite_description(self):
        return self.analytics.get('test_suite_description', 'Test case runner')

    @property
    def executor(self):
        return self.analytics.get('executor', 'Hilding')

    @property
    def project(self):
        return self.analytics.get('project', 'UNKNOWN')

    @property
    def platform(self):
        return self.analytics.get('platform', 'UNKNOWN')

    @property
    def branch(self):
        return self.analytics.get('branch', 'UNKNOWN')

    @property
    def ecu(self):
        return self.analytics.get('ecu', 'UNKNOWN')

    @property
    def dbc(self):
        return self.analytics.get('dbc', 'UNKNOWN')

    @property
    def vehicle_project(self):
        return self.analytics.get('vehicle_project', 'UNKNOWN')

    @property
    def vehicle_series(self):
        return self.analytics.get('vehicle_series', 'UNKNOWN')

    @property
    def sw_version(self):
        return self.analytics.get('sw_version', 'UNKNOWN')

    @property
    def sw_githash(self):
        return self.analytics.get('sw_githash', 'UNKNOWN')

    @property
    def sw_changeset(self):
        return self.analytics.get('sw_changeset', 'UNKNOWN')

    @property
    def sw_inhousechangeset(self):
        return self.analytics.get('sw_inhousechangeset', 'UNKNOWN')

    @property
    def testenv_info_name(self):
        return self.analytics.get('testenv_info_name', platform.node())

    @property
    def testenv_info_description(self):
        return self.analytics.get('testenv_info_description', 'Hilding test rig')

    @property
    def testenv_info_platform(self):
        return self.analytics.get('testenv_info_platform', 'Hilding')
