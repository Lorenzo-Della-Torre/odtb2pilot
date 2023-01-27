"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

import os

import epsmsgbus.productid as productid_mod
import epsmsgbus.activityid as activity_mod
import epsmsgbus.ci_logs as logs_mod
import epsmsgbus.cynosure as cynosure
import epsmsgbus

import configparser
import logging

log = logging.getLogger('api_runner')


JENKINS_SETTINGS = os.path.join(os.environ['SYSTEMDRIVE'] + os.sep + 'Jenkins', 'settings.ini')

class TestSuiteDataAdapter(epsmsgbus.TestSuiteDataAdapter):
    """
    Data adapter class for a testsuite
    """
    def __init__(self, config):
        """
        Constructor for test suite data adapter
        """
        self.config = config
        if not productid_mod.get_productid():
            productname = str(config.project_name) + '-' + str(config.result_name)
            productid = config.result_name + str(cynosure.now())
            os.environ['PRODUCTID_NAMESPACE'] = productname
            os.environ['PRODUCTID_INSTANCE'] = str(productid)
            productid_mod.set_productid()
        else:
            prodid = productid_mod.get_productid()
            productname = prodid['namespace']
            productid = prodid['instance']
        self.name = productname
        self.id = productid
        self.jobid = config.result_name
        self.activityid = activity_mod.get_activityid()
        self.productid = productid_mod.get_productid()
        self.path_info_data = logs_mod.get_logs_url()
        self._base_url = None

    @property
    def base_url(self):
        if self._base_url is None:
            try:
                return self.path_info_data['base_url']
            except:
                c = configparser.ConfigParser()
                c.read([JENKINS_SETTINGS])
                return c.get('Artifactory', 'base_url')
        return self._base_url

            # OPTIONAL fields ----------------------------------------------------{{{3
    def get_product_name(self):
        """Return product name."""
        return self.name

    def get_product_id(self):
        """Return product ID. This is Cynosure specific and should be similar
        to the activity id (or maybe even the same)."""
        return self.id

    def get_execution_info(self):
        """Return information about the test execution itself."""
        return epsmsgbus.ExecutionInfo(
                name=self.jobid,
                executor= os.environ.get('USERNAME', '<unknown>'),
                project=self.config.project_name)

    def get_software_info(self):
        """Return information about the software under test."""
        info = self.config.project_name.split('_')
        return epsmsgbus.SoftwareInfo(
                ecu=info[2],
                platform=info[1],
                vehicle_project=info[0])

    def get_logs(self):
        if 'jenkins' in self.config.result_name.lower():
            return [self.path_info_data['build_url'] + 'consoleText']

    def get_result(self):
        pass
        """Return URL to the test report."""
        result_name = self.config.result_name
        return "{base}/artifactory/{repo}/{path}/{jobid}.zip!/{report}.pdf".format(
                    base=self.base_url,
                    repo=self.path_info_data['repo'],
                    path=self.path_info_data['basepath'],
                    jobid=result_name,
                    report=result_name)

    def get_verdict_info(self, verdict, **data):
        log.info("DATA sample: {} type {}".format(data, type(data)))
        return epsmsgbus.VerdictInfo(
            description="Execution for Suite %s is %s" % (self.name,verdict),
            vtype="environment",
            url=self.get_result(),
            data=data)

    def clear_activity_id(self):
        os.environ.pop('ACTIVITY_NAME', None)
        activity_mod.set_activityid()

    def get_activity_name(self):
        try:
            return self.activityid['namespace']
        except Exception as e:
            log.info(e)
            
    def get_activity_id(self):
        try:
            return self.activityid['instance']
        except:
            return activity_mod.get_activityid()

class TestCaseDataAdapter(epsmsgbus.TestCaseDataAdapter):
    """Adapter for metadata from test cases and test steps. Only 'get_taskid()'
    is mandatory."""
    def __init__(self, name):
        self.name = name
        self.parent = activity_mod.get_activityid()

    def get_testcode_info(self):
        """Return informatino about the test case itself (author, requirment,
        modification date, etc)."""
        return epsmsgbus.TestCodeInfo(
                author='',
                description='Executed from ci_runner',
                creationdate=None,
                modificationdate=None,
                requirement='',
                responsible='')

def testsuite_started(config):
        adapter = TestSuiteDataAdapter(config)
        name = config.folder.split('.')[-1]
        epsmsgbus.testsuite_started(adapter, name, use_db=False)
        if not activity_mod.get_activityid():
            os.environ['ACTIVITY_NAME'] = name
            os.environ['ACTIVITY_ID'] = str(epsmsgbus.core.CURRENT_TESTSUITE.id)
            activity_mod.set_activityid()

def testsuite_ended():
        epsmsgbus.testsuite_ended()

def testcase_started(name):
        adapter = TestCaseDataAdapter(name)
        epsmsgbus.testcase_started(adapter, name)

def testcase_ended(verdict):
        epsmsgbus.testcase_ended(verdict)