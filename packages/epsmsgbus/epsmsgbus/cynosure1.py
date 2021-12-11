/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



**********************************************************************************/


#!/bin/env python

"""
Create messages in JSON format and post these messages to Cynosure.
"""

import logging
from epsmsgbus import common

log = logging.getLogger('epscynosure')

try:
    TARGET
except NameError:
    TARGET = 'VCC-CI'


# Messages ==============================================================={{{1

# BaseLineCreated                 = "root" message
#    ActivityStarted              = Test suite started
#        TestSuiteStarted         = Test case started
#             TestcaseStarted     = Test step started
#             TestcaseFinished    = Test step ended
#             ...
#        TestSuiteFinished        = Test case ended
#        ...
#    ActivityFinished             = test suite ended

# CynosureMessage (base class for messages) ------------------------------{{{2
class CynosureV1Message(common.CynosureMessage):
    server = "cimb.volvocars.biz"
    version = "1.6.0"

    def __init__(self, **k):
        """Add optional fields given at instiation time."""
        super(CynosureV1Message, self).__init__(self, **k)
        if 'target' in self.optional and 'target' not in k:
            self['target'] = TARGET


# BaselineCreated --------------------------------------------------------{{{2
class BaselineCreated(CynosureV1Message):
    """This message is the "root" message and must always be sent."""

    revision = "exampleRevision"
    author_id = "somebody@somewhere.com"
    project = "exampleProject"
    type = "exampleType"
    baseline = "exampleBaseline"
    baseline_name = "exampleBaselineName"

    mandatory = ('revision', 'author_id', 'project', 'type', 'baseline', 'baseline_name')
    optional = ('projects', 'custom', 'input_chain_ids', 'url', 'event_id', 'logs', 'data_ref', 'id', 'target', 'event_time')

    def __init__(self, chain_id, **k):
        self['chain_id'] = chain_id
        CynosureMessage.__init__(self, **k)
        for attr in self.mandatory:
            if attr in k:
                self[attr] = k[attr]
            if not attr in self:
                # Use default values from the class itself
                self[attr] = getattr(self, attr)

    @classmethod
    def set_mandatory(cls, revision=None, author_id=None, project=None,
            type_=None, baseline=None, baseline_name=None):
        """The mandatory attributes must always be present."""
        if revision is not None:
            cls.revision = revision
        if author_id is not None:
            cls.author_id = author_id
        if project is not None:
            cls.project = project
        # type is reserved in Python...
        if type_ is not None:
            cls.type = type_
        if baseline is not None:
            cls.baseline = baseline
        if baseline_name is not None:
            cls.baseline_name = baseline_name


# ActivityStarted --------------------------------------------------------{{{2
class ActivityStarted(CynosureV1Message):
    # Start of test suite
    optional = ('custom', 'event_id', 'logs', 'target', 'time_override', 'url')

    def __init__(self, chain_id, name, **k):
        CynosureMessage.__init__(self, **k)
        self['chain_id'] = chain_id
        self['name'] = name

    def post(self):
        BaselineCreated(self['chain_id'], target=self['target'], event_time=zulu_time()).post()
        CynosureMessage.post(self)


# ActivityFinished -------------------------------------------------------{{{2
class ActivityFinished(CynosureV1Message):
    # End of test suite
    optional = ('custom', 'event_id', 'logs', 'target', 'time_override', 'url')

    def __init__(self, chain_id, name, status, **k):
        CynosureMessage.__init__(self, **k)
        self['chain_id'] = chain_id
        self['name'] = name
        self['status'] = status


# TestsuiteStarted -------------------------------------------------------{{{2
class TestsuiteStarted(CynosureV1Message):
    # Start of test case
    optional = ('custom', 'event_id', 'logs', 'tags', 'target', 'time_override', 'url')

    def __init__(self, chain_id, name, activity, **k):
        CynosureV1Message.__init__(self, **k)
        self['chain_id'] = chain_id
        self['name'] = name
        self['activity'] = activity


# TestsuiteFinished -------------------------------------------------------{{{2
class TestsuiteFinished(CynosureV1Message):
    # End of test case
    optional = ('custom', 'event_id', 'logs', 'tags', 'target', 'time_override', 'url')

    def __init__(self, chain_id, name, activity, status, **k):
        CynosureV1Message.__init__(self, **k)
        self['chain_id'] = chain_id
        self['name'] = name
        self['activity'] = activity
        self['status'] = status


# TestcaseStarted ---------------------------------------------------------{{{2
class TestcaseStarted(CynosureV1Message):
    # Start of test step
    optional = ('custom', 'event_id', 'logs', 'tags', 'target', 'testsuite_name', 'time_override', 'url')

    def __init__(self, chain_id, name, activity, **k):
        CynosureV1Message.__init__(self, **k)
        self['chain_id'] = chain_id
        self['name'] = name
        self['activity'] = activity


# TestcaseFinished --------------------------------------------------------{{{2
class TestcaseFinished(CynosureV1Message):
    # End of test step
    optional = ('custom', 'event_id', 'logs', 'tags', 'target', 'testsuite_name', 'time_override', 'url')

    def __init__(self, chain_id, name, activity, status, **k):
        CynosureV1Message.__init__(self, **k)
        self['chain_id'] = chain_id
        self['name'] = name
        self['activity'] = activity
        self['status'] = status


# Classes that hold information for suites, test cases, test steps ======={{{1

class BaseLevel(object):
    """To avoid defining the set() method in subclasses."""
    def __init__(self):
        self.custom = {}

    def set(self, **k):
        self.custom.update(k)
        return self


class TestSuite(BaseLevel):
    # This is a TEST SUITE even though we use ActivityStarted and
    # ActivityFinished.
    def __init__(self, chain_id, name):
        super(TestSuite, self).__init__()
        self.chain_id = chain_id
        self.name = name
        self._testsuite = None
        self.status = Status('skipped')

    def notify(self, status):
        self.status = max(self.status, Status(status))

    def post_started(self):
        asm = ActivityStarted(
                chain_id=self.chain_id,
                name=self.name,
                time_override=zulu_time())
        asm.set_custom(**self.custom)
        asm.post()

    def post_finished(self):
        afm = ActivityFinished(
                chain_id=self.chain_id,
                name=self.name,
                status=self.status.name,
                time_override=zulu_time())
        afm.post()

    def testsuite(self, name=None):
        if name is not None:
            self._testsuite = TestSuite(
                    parent=self,
                    chain_id=self.chain_id,
                    name=name,
                    activity=self.name)
        return self._testsuite


class TestCase(BaseLevel):
    # This is a TEST CASE even though we use TestsuiteStarted and
    # TestsuiteFinished.
    def __init__(self, parent, chain_id, name, activity):
        super(TestCase, self).__init__()
        self.parent = parent
        self.chain_id = chain_id
        self.name = name
        self.activity = activity
        self._teststep = None

    def post_started(self):
        tssm = TestsuiteStarted(
                chain_id=self.chain_id,
                name=self.name,
                activity=self.activity,
                time_override=zulu_time())
        tssm.set_custom(**self.custom)
        tssm.post()
        return tssm

    def post_finished(self, status):
        self.parent.notify(status)
        tsfm = TestsuiteFinished(
                chain_id=self.chain_id,
                name=self.name,
                activity=self.activity,
                status=status,
                time_override=zulu_time())
        tsfm.post()
        return tsfm

    def teststep(self, name=None):
        if name is not None:
            self._teststep = TestStep(
                    chain_id=self.chain_id,
                    name=name,
                    activity=self.activity,
                    testsuite_name=self.name)
        return self._teststep


class TestStep(BaseLevel):
    # This is a TEST STEP even though we use TestcaseStarted and
    # TestcaseFinished
    def __init__(self, chain_id, name, activity, testsuite_name):
        super(TestStep, self).__init__()
        self.chain_id = chain_id
        self.name = name
        self.activity = activity
        self.testsuite_name = testsuite_name

    def post_started(self):
        tcsm = TestcaseStarted(
                chain_id=self.chain_id,
                name=self.name,
                activity=self.activity,
                testsuite_name=self.testsuite_name,
                time_override=zulu_time())
        tcsm.set_custom(**self.custom)
        tcsm.post()
        return tcsm

    def post_finished(self, status):
        tcsm = TestcaseFinished(
                chain_id=self.chain_id,
                name=self.name,
                activity=self.activity,
                testsuite_name=self.testsuite_name,
                status=status,
                time_override=zulu_time())
        tcsm.post()
        return tcsm


# Functions =============================================================={{{1

try:
    ACTIVITY
except NameError:
    ACTIVITY = Activity('UnknownActivity', 'UnknownActivityName')


def activity(chain_id=None, name=None):
    global ACTIVITY
    if chain_id is not None:
        ACTIVITY = Activity(chain_id, name)
    return ACTIVITY


def use_sandbox(use_sandbox):
    global TARGET
    if use_sandbox:
        TARGET = 'VCC-CI-Sandbox'
    else:
        TARGET = 'VCC-CI'

# eof
