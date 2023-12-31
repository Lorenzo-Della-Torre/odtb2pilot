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

#!/bin/env python
"""
Implementation of adapters and observers for AutomationDesk
"""

import configparser
import importlib
import json
import logging
import os
import re
import warnings
import requests


import epsconfig
import epsmsgbus.core as core
import epsmsgbus.data as data
import epsmsgbus.cynosure as cynosure
import epsmsgbus.productid as productid_mod
import epsmsgbus.activityid as activityid_mod
import epsmsgbus.ci_logs as logs_mod
import epsplatform
import epssut
import epstasks
import epssvn
import string

try:
    import tam.core.main.tam_globalstates as tam_globalstates
except ImportError:
    warnings.warn("Could not import 'tam.core.main.tam_globalstates', are you running outside AutomationDesk?")
try:
    import tam.core.dialogs.tam_execconfigrc_dlg as tam_execconfigrc_dlg
except ImportError:
    warnings.warn("Could not import 'tam.core.dialogs.tam_execconfigrc_dlg', are you running outside AutomationDesk?")

restful_config = epsconfig.config('postconnect')
config = epsconfig.config('db')
if config.cynosure.major_version is None:
    raise ValueError("Cynosure major version is not configured!")
cynosure_msg = importlib.import_module('epsmsgbus.cynosure{}'.format(config.cynosure.major_version))


log = logging.getLogger('epsmsgbus.api_ad')


JENKINS_SETTINGS = os.path.join(os.environ['SYSTEMDRIVE'] + os.sep + 'Jenkins', 'settings.ini')


# Mapping of verdicts ===================================================={{{1

AUD_VERDICTS = {
    # AD        :  message bus
    'Passed'    : 'passed',
    'Error'     : 'errored',
    'Failed'    : 'failed',
    'Undefined' : 'unknown',
    'Executed'  : 'unknown',
}


# Exceptions ============================================================={{{1

class CheckFirstLastError(Exception):
    """The first/last check of test cases found something strange."""
    pass


class OutOfOrderError(Exception):
    """The out-of-order check failed. Two consecutive calls to start or end
    methods."""
    pass


# Adapters for data retrieval ============================================{{{1

# TestSuiteDataAdapter ---------------------------------------------------{{{2
class TestSuiteDataAdapter(data.TestSuiteDataAdapter):
    def __init__(self, audctx):
        self.audctx = audctx
        self.activityid = activityid_mod.get_activityid()
        self.name = self.get_activity_name()
        self.result_dir = os.path.basename(audctx._INFO_.ResultDirectory)
        self.result_name = audctx._INFO_.ResultName
        self._base_url = None
        self.is_ci = 'jenkins' in self.result_name.lower()
        self.productid = productid_mod.get_productid()
        self.path_info_data = logs_mod.get_logs_url()

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

    def clear_activity_id(self):
        activityid_mod.set_activityid()
    
    def get_product_name(self):
        """Prefixing with project name since Cynosure3 requires that the product name
        is at least 10 characters, which creates a problem in case the folder
        name is very short.
        NOTE: If the CI chain has supplied a product identity, then this is used
              instead. Note that self.producctid can be None
        """
        try:
            return self.productid['namespace']
        except:
            return '-'.join((self.audctx._INFO_.ProjectName, self.result_name))

    def get_product_id(self):
        try:
            return self.productid['instance']
        except:
            return self.result_dir

    def get_activity_name(self):
        try:
            return self.activityid['namespace']
        except Exception as e:
            log.info(e)
            return tam_globalstates.GlobalStates.ExecutionBlock.GetName()

    def get_activity_id(self):
        try:
            return self.activityid['instance']
        except:
            return None

    def get_execution_info(self):
        parameters = {}
        parameters['Parameters'] = core.recurse_container(self.audctx.Parameters)
        return data.ExecutionInfo(
                name=self.result_name,
                description=tam_execconfigrc_dlg.ExecutionConfiguration.Description,
                executor=os.environ.get('USERNAME', '<unknown>'),
                project=self.audctx._INFO_.ProjectName,
                parameters=parameters)

    def get_simulation_info(self):
        try:
            sdfinfo = epstasks.SDFInfo(self.audctx.ModelLinks.HIL.MAPortConfiguration['ApplicationPath'])
            modelinfo = epssut.ModelInfo(self.audctx, multi_processor=sdfinfo.is_multi_processor)
            return data.SimulationInfo(
                    build_id=modelinfo.build_id,
                    project=modelinfo.project,
                    ecu=modelinfo.ecu,
                    branch=modelinfo.branch,
                    dbc=modelinfo.dbc)
        except:
            return data.SimulationInfo()

    def get_software_info(self):
        ecu = project = series = version = platform = None
        json_data = {}
        if self.is_ci:
            # If we are running thru Jenkins, then we will have information such as
            # Git hash and build number for the software package.
            log.debug("Adding metadata for Continuous Integration.")
            try:
                with open(self.audctx.Parameters.MetadataInfo.GetAbsolutePath()) as json_in:
                    json_data = json.load(json_in)
            except Exception as e:
                log.debug("Could not open JSON file. [%s]" % e)
        else:
            log.debug("Not running in CI, not adding Git hash and build number.")
        githash = json_data.get('githash')
        changeset = json_data.get('changeset')
        inhousechangeset = json_data.get('inhousechangeset')
        try:
            ecu = self.audctx.Constants.Software.Versions.ECU
        except:
            log.debug("Not adding ECU to result (not found).")
        try:
            project = self.audctx.Constants.Software.Versions.Project
        except:
            log.debug("Not adding vehicle project to result (not found).")
        try:
            series = self.audctx.Constants.Software.Versions.Series
        except:
            log.debug("Not adding vehicle series to result (not found).")
        try:
            version = self.audctx.Constants.Software.Versions.ReleaseVersion
        except:
            log.debug("Not adding release version to result (not found).")
        try:
            platform = self.audctx.Constants.Software.Versions.Platform
        except:
            log.debug("Not adding platform to result (not found).")
        return data.SoftwareInfo(
                ecu=ecu,
                platform=platform,
                vehicle_project=project,
                vehicle_series=series,
                version=version,
                githash=githash,
                changeset=changeset,
                inhousechangeset=inhousechangeset)

    def get_testenv_info(self):
        hilinfo = get_hil_info()
        regex = re.compile(r"(?i)^\s*(HIL)*[\s#]*(?P<id>[a-z0-9]+)\s*$")
        m_r = regex.match(hilinfo.name)
        if m_r:
            hilname = "HIL {}".format(m_r.group('id').upper())
            testequipmentlist = get_connected_equipments(hilname)
        else:
            testequipmentlist = []
            log.warning(f"The HIL name: '{hilinfo.name}' (in HIL.cfg) is either missing or in wrong format 'HIL <id>'.")
        return data.TestEnvironmentinfo(
            name=hilinfo.name,
            description=hilinfo.description,
            platform=hilinfo.platform,
            ipaddress=hilinfo.ipaddress,
            testequipment=testequipmentlist)

    def get_version_info(self):
        repos = epsconfig.config('git').repos
        eps_lib_repo = epssvn.GitInfo(repos.EPSLib)
        test_repo = epssvn.GitInfo(string.Template(repos.TestcaseLib).substitute(USERPROFILE = 'C:'))
        return [{
                'name' : eps_lib_repo.root().split('\\')[-1],
                'path' : eps_lib_repo.root(),
                'revision' : eps_lib_repo.revision(),
                'local_modifications' : eps_lib_repo.has_checkouts(),
            },
            {
                'name' : test_repo.root().split('\\')[-1],
                'path' : test_repo.root(),
                'revision' : test_repo.revision(),
                'local_modifications' : test_repo.has_checkouts(),
            }]

    def get_result(self):
        if self.is_ci:
            return "{base}/artifactory/{repo}/{path}/{jobid}.zip!/{report}.pdf".format(
                    base=self.base_url,
                    repo=self.path_info_data['repo'],
                    path=self.path_info_data['basepath'],
                    jobid=self.result_name,
                    report=self.result_name)

    def get_logs(self):
        if self.is_ci:
            return [self.get_build_url() + 'consoleText']

    def get_url(self):
        if self.is_ci:
            return "{base}/artifactory/{repo}/{path}/{jobid}.zip".format(
                    base=self.base_url,
                    repo=self.path_info_data['repo'],
                    path=self.path_info_data['basepath'],
                    jobid=self.result_name)

    def get_build_url(self):
        if self.is_ci:
            return self.path_info_data['build_url']


    def get_other_info(self):
        return data.RunTimeInfo()


    def get_verdict_info(self, verdict, **dat):
        return data.VerdictInfo(description="Execution for Suite %s is %s" % (self.name,verdict),
                                vtype="environment",
                                url=self.get_result() if self.is_ci else None,
                                data=dat if self.is_ci else None)


# TestStepDataAdapter3 ----------------------------------------------------{{{2
class TestSuiteDataAdapter3(TestSuiteDataAdapter):
    """Variant of TestSuiteDataAdapter where the logs are no longer a list of
    URLs but instead a list of objects with three mandatory fields:
    'name', 'url', and 'type', as required by Cynosure 3."""

    def get_logs(self):
        """Override 'get_logs()' to add more info about each log."""
        return add_loginfo(super(TestSuiteDataAdapter3, self).get_logs())


# TestCaseDataAdapter -----------------------------------------------------{{{2
class TestCaseDataAdapter(data.TestCaseDataAdapter):
    def __init__(self, audctx, level):
        """Level is the context of the actual TESTCASE_TEMPLATE block."""
        self.audctx = audctx
        self.level = level
        self.name = level.BlockName
        self.result_name = audctx._INFO_.ResultName
        self.is_ci = 'jenkins' in self.result_name.lower()
        self._base_url = None
        self.path_info_data = logs_mod.get_logs_url()

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

    def get_logs(self):
        if self.is_ci:
            return ["{base}/artifactory/{repo}/{path}/{jobid}.zip!/{logfile}.log".format(
                    base=self.base_url,
                    repo=self.path_info_data['repo'],
                    path=self.path_info_data['basepath'],
                    jobid=self.result_name,
                    logfile=self.audctx._INFO_.SequencePath)]

    def get_testcode_info(self):
        return data.TestCodeInfo(
                author=self.level.Author.strip(),
                description=get_description(self.level),
                creationdate=cynosure.zulu_time(self.level.CreationDate),
                modificationdate=cynosure.zulu_time(self.level.ModificationDate),
                requirement=self.audctx.Requirement.strip(),
                responsible=self.audctx.Responsible.strip())


# TestCaseDataAdapter3 -----------------------------------------------------{{{2
class TestCaseDataAdapter3(TestCaseDataAdapter):
    """Variant of TestCaseDataAdapter where the logs are no longer a list of
    URLs but instead a list of objects with three mandatory fields:
    'name', 'url', and 'type', as required by Cynosure 3."""

    def get_logs(self):
        """Override 'get_logs()' to add more info about each log."""
        return add_loginfo(super(TestCaseDataAdapter3, self).get_logs())


# TestStepDataAdapter ----------------------------------------------------{{{2
class TestStepDataAdapter(data.TestStepDataAdapter):
    def __init__(self, audctx, level):
        self.level = level
        self.name = self.level.BlockName

    def get_testcode_info(self):
        return data.TestCodeInfo(
                author=self.level.Author.strip(),
                description=get_description(self.level),
                creationdate=cynosure.zulu_time(self.level.CreationDate),
                modificationdate=cynosure.zulu_time(self.level.ModificationDate))


# Update report header with message id ==================================={{{1
class ADReportObserver(core.Observer):
    def notify_abort(self, observable):
        pass

    def notify_start(self, observable):
        pass

    def notify_update(self, observable, data):
        pass

    def notify_finish(self, observable, verdict):
        """Add header item to the AutomationDesk report."""
        try:
            # TODO This is not nice, circular dependency...
            import vccepsautoaudroot as epsauto
            m = observable.metadata
            epsauto.add_report_node('EPSINFO', {'chain_id': '{}::{}'.format(
                m.product_name, m.product_id)})
        except Exception:
            log.debug("Failed to add chain id to report header.", exc_info=True)


# Helpers ================================================================{{{1
try:
    HIL_INFO
except NameError:
    HIL_INFO = None


class HILInfo(object):
    """Parse HIL configuration file and retrieve data."""
    def __init__(self):
        c = configparser.ConfigParser()
        c.read([epsplatform.DEFAULT_HIL_CONFIG, epsplatform.HIL_CONFIG])
        self.name = c.get('HIL', 'name')
        self.platform = c.get('HIL', 'platform')
        self.ipaddress = c.get('HIL', 'ipaddress')
        self.description = 'HIL simulator'


def add_loginfo(url_list):
    """Decorator to add more information to the 'logs' field that is needed for
    Cynosure 3."""
    if url_list is None:
        return None
    else:
        logs = []
        ix = 0
        for url in url_list:
            logs.append({
                'name': 'log%02d' % ix,
                'url': url,
                'type': 'text',
            })
            ix += 1
        return logs


def get_description(ctx):
    """Use InstanceDescription unless it's empty, in that case use
    TemplateDescription."""
    inst_desc = ctx.InstanceDescription.strip()
    return ctx.TemplateDescription.strip() if len(inst_desc) == 0 else inst_desc


def get_hil_info():
    """Return cached HILInfo object"""
    global HIL_INFO
    if HIL_INFO is None:
        HIL_INFO = HILInfo()
    return HIL_INFO


def get_connected_equipments(parent):
    url = restful_config.dest.api_url
    response = requests.get(url, json={"parents": parent}).json()
    idlist = []
    for equipment in response[parent]:
        if 'error' in equipment:
            log.warning(equipment['error'])
        else:
            idlist.append(f"{equipment['type']}: {equipment['name']} ({equipment['id']})")
    return idlist


def get_message_handler():
    """Return message handler object based on HILInfo.  We only want to send
    messages and save to database if we are running on a HIL computer."""
    hilinfo = get_hil_info()
    # If the name contains HIL or platform is MABX
    is_hil = 'hil' in hilinfo.name.lower() or 'mabx' in hilinfo.platform.lower()
    return cynosure.messagehandler(use_mq=is_hil, use_db=is_hil)


def map_verdict(aud_verdict):
    """Map from verdicts used by AutomationDesk to verdicts used by
    Cynosure."""
    return AUD_VERDICTS.get(aud_verdict, 'aborted')


# Integrity checks ======================================================={{{1
# NOTE: These tests are probably not enough, but will make it possible
# to partly recover from exceptions in the execution flow.

# Check if test case is first or last ------------------------------------{{{2
class CheckFirstLast(object):
    """Check if a test case is first or last in a sequence.

    If the test case is first, then we trigger 'testsuite_started()',
    if the test case is last, then we trigger 'testsuite_ended()'.

    The first test case will check if a 'lock' file is present, if its not
    present then we will create it..
     * If the file is present, then we assume that we are not first.
     * The first test case will count the number of test cases in the
       testsuite.
     * Each test case will decrease this test case counter.
     * When the counter is back at zero, then we assume that we are the last
       test case in the test suite.

    The class also checks if a call to 'is_first_testcase()' is followed by
    a call to 'is_last_testcase()'.

    If this is not the case, then something must have gone wrong (an Exception).
    In this case an error flag is set and the calling code can try to fix
    the messages.
    """
    lockfile_name = '.eps_lock'

    def __init__(self):
        self.counter = 0

    def is_first(self, audctx):
        """This method is called whenever a test case starts."""
        lockfile = os.path.join(audctx._INFO_.ResultDirectory, self.lockfile_name)
        if os.path.exists(lockfile):
            self.counter -= 1
            if self.counter < 0:
                raise CheckFirstLastError("counter was {}. Never expected to go below zero.".format(self.counter))
            return False
        log.debug("Creating {}".format(lockfile))
        with open(lockfile, 'w'):
            pass
        self.count_testcases()
        return True

    def is_last(self):
        return self.counter < 2

    def count_testcases(self):
        self.counter = self._count_tc(tam_globalstates.GlobalStates.ExecutionBlock, 0)
        log.debug("Found {} test case{} in the test suite.".format(self.counter, "s" if self.counter > 1 else ''))
        return self.counter

    def _count_tc(self, e, c):
        if e.IsDSFolder():
            for child in e.GetChildren():
                c = self._count_tc(child, c)
        elif not e.IsDSResultObject() and not e.IsDSDataObject() and e.GetEnableMode():
            c += 1
        return c


try:
    CHECK_FIRST_LAST
except NameError:
    CHECK_FIRST_LAST = CheckFirstLast()


def testcase_is_first(audctx):
    try:
        return CHECK_FIRST_LAST.is_first(audctx)
    except CheckFirstLastError as e:
        log.error(e)
        log.debug("TRACE", exc_info=True)


def testcase_is_last():
    return CHECK_FIRST_LAST.is_last()


# Check for out-of-order problems ----------------------------------------{{{2
class OutOfOrderCheck(object):
    def __init__(self, level_name):
        self.expect_start = True
        self.level_name = level_name

    def start(self):
        try:
            if not self.expect_start:
                # (N-1) : [pre-start-check]
                # (N-1) : [start-check]
                # (N-1) : [execution]        X *Exception* somewhere here
                # (N-1) : [end-check]        X  -"- (or here)
                # (N-1) : [post-end-check]   X  -"- (or here)
                # (N)   : [pre-start-check]  X  -"- (or here)
                # (N)   : [start-check]       <-- We are here
                raise OutOfOrderError("Previous {} ended abnormally and was started but not ended.".format(self.level_name))
        finally:
            self.expect_start = False

    def end(self, update=False):
        try:
            if self.expect_start:
                # (N-1) : [pre-start-check]
                # (N-1) : [start-check]
                # (N-1) : [execution]
                # (N-1) : [end-check]
                # (N-1) : [post-end-check]   X *Exception* somewhere here
                # (N)   : [pre-start-check]  X  -"- (or here)
                # (N)   : [start-check]      X  -"- (or here)
                # (N)   : [execution]        X  -"- (or here)
                # (N)   : [end-check]         <-- We are here
                raise OutOfOrderError("This {} ended abnormally. Previous test case ended but this testcase was never started.".format(self.level_name))
        finally:
            self.expect_start = True if not update else self.expect_start


# Test suite -------------------------------------------------------------{{{2
try:
    TESTSUITE_ORDER
except NameError:
    TESTSUITE_ORDER = OutOfOrderCheck('test suite')


def testsuite_check_start():
    TESTSUITE_ORDER.start()


def testsuite_check_end(Update=False):
    TESTSUITE_ORDER.end(Update)
        

# Test case --------------------------------------------------------------{{{2
try:
    TESTCASE_ORDER
except NameError:
    TESTCASE_ORDER = OutOfOrderCheck('test case')


def testcase_check_start():
    TESTCASE_ORDER.start()


def testcase_check_end():
    TESTCASE_ORDER.end()


# Test step --------------------------------------------------------------{{{2
try:
    TESTSTEP_ORDER
except NameError:
    TESTSTEP_ORDER = OutOfOrderCheck('test suite')


def teststep_check_start():
    TESTSTEP_ORDER.start()


def teststep_check_end():
    TESTSTEP_ORDER.end()


# Interface to AutomationDesk ============================================{{{1

# Test suite -------------------------------------------------------------{{{2
def testsuite_started(audctx):
    """Called at start of test suite."""
    try:
        testsuite_check_start()
    except OutOfOrderError:
        # Previous test suite was never ended, send message that it was aborted.
        core.testsuite().abort()

    if config.cynosure.major_version > 2:
        tsda = TestSuiteDataAdapter3(audctx)
    else:
        tsda = TestSuiteDataAdapter(audctx)
    # If no product was given via Jenkins
    send_product = (tsda.productid is None)
    ts = core.testsuite(tsda.name, tsda.get_activity_id())
    ts.register(data.TestSuiteDataObserver(tsda))
    ts.register(cynosure_msg.TestSuiteMessageObserver(get_message_handler(), send_product=send_product))
    ts.register(ADReportObserver())
    ts.start()

def testsuite_updated(data):
    """Called during execution of test suite."""
    try:
        testsuite_check_end(True)
    except OutOfOrderError:
        # This test suite was never startedm
        core.testsuite().abort()
    else:
        core.testsuite().update(data)


def testsuite_ended():
    """Called at end of test suite."""
    try:
        testsuite_check_end()
    except OutOfOrderError:
        # This test suite was never startedm
        core.testsuite().abort()
    else:
        core.testsuite().finish()


# Test case --------------------------------------------------------------{{{2
def testcase_started(audctx, level):
    """Called at start of test case."""
    try:
        testcase_check_start()
    except OutOfOrderError as e:
        # Previous test case was never ended, send message that it was aborted.
        core.testsuite().testcase().abort()

    try:
        if testcase_is_first(audctx):
            testsuite_started(audctx)
    except CheckFirstLastError as e:
        # TODO: Don't know what to do here.
        log.error(e)
        log.debug("TRACE", exc_info=True)

    if config.cynosure.major_version > 2:
        tcda = TestCaseDataAdapter3(audctx, level)
    else:
        tcda = TestCaseDataAdapter(audctx, level)
    tc = core.testsuite().testcase(tcda.name) #TODO: identifier
    tc.register(data.TestCaseDataObserver(tcda))
    tc.register(cynosure_msg.TestCaseMessageObserver(get_message_handler()))
    tc.start()


def testcase_ended(verdict):
    """Called at end of test case. The verdict needs to be mapped to something
    that Cynosure accepts."""
    try:
        testcase_check_end()
    except OutOfOrderError:
        # This test case was never started, send message that it was aborted.
        core.testsuite().testcase().abort()
    else:
        core.testsuite().testcase().finish(map_verdict(verdict))
    if testcase_is_last():
        testsuite_ended()


# Test step --------------------------------------------------------------{{{2
def teststep_started(audctx, level):
    """Called at start of test step."""
    try:
        teststep_check_start()
    except OutOfOrderError:
        # Previous test step was never ended, send message that it was aborted.
        core.testsuite().testcase().teststep().abort()
    tssda = TestStepDataAdapter(audctx, level)
    tss = core.testsuite().testcase().teststep(tssda.name) #TODO: identifier
    tss.register(data.TestStepDataObserver(tssda))
    tss.register(cynosure_msg.TestStepMessageObserver(get_message_handler()))
    tss.start()


def teststep_ended(verdict):
    """Called at end of test step. The verdict needs to be mapped."""
    try:
        teststep_check_end()
    except OutOfOrderError:
        # This test step was never started, send message that it was aborted.
        core.testsuite().testcase().teststep().abort()
    else:
        core.testsuite().testcase().teststep().finish(map_verdict(verdict))


# EOF
