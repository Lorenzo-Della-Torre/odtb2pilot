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
Create messages in JSON format and post these messages to Cynosure.


NOTE:
    This file is for message format 3, it reuses a lot of functionality from
    .\cynosure2.py
"""

# NOTE: See .\cynosure2.txt for message samples

import logging

import epsconfig
import epsmsgbus.core as core
import epsmsgbus.cynosure as cynosure
import epsmsgbus.cynosure2 as cynosure2
#import epsglobal # Not needed for Hilding
import os


# Globals ================================================================{{{1
paramConfig = epsconfig.config('parameter')
log = logging.getLogger('epsmsgbus.cynosure3')

DEFAULT_SERVER = "core.messagebus.cynosure.volvocars.biz"
DEFAULT_VERSION =  "3.0.0"


# Encoding ==============================================================={{{1
# Unfortunately some fields in cynosure do not accept common characters such as
NUMBERS            = "0123456789"
UPPERCASE_LETTERS  = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
LOWERCASE_LETTERS  = "abcdefghijklmnopqrstuvwxyz"
SPECIAL_CHARACTERS = "_/-"
ALLOWED_CHARACTERS = NUMBERS + UPPERCASE_LETTERS + LOWERCASE_LETTERS + SPECIAL_CHARACTERS

class CharMapping(dict):
    def __init__(self, k, replacechar=None):
        dict.__init__(self, k)
        self.replacechar = replacechar

    def __getitem__(self, item):
        if not item in self:
            return self.replacechar
        return dict.__getitem__(self, item)

TRANSLATION_TABLE = {ord(x): x for x in ALLOWED_CHARACTERS}


def cyno_encode(data):
    return data.translate(CharMapping(TRANSLATION_TABLE))


def cyno_decode(data):
    """In reality a no-op, there is no one-to-one decoding."""
    return data


# Base classes for messages =============================================={{{1
class CynosureV3Message(cynosure2.CynosureV2Message):
    """Base class for version 3.0 of Cynosure messages."""

    server = DEFAULT_SERVER
    version = DEFAULT_VERSION


def make_name(*a):
    """Convenience function for 'name' fields in Cynosure3.
    A name is a '/' delimited string, e.g.
       "MyProductName/MyActivityName/MyTaskName"
    """
    return '/'.join(a)


# Messages ==============================================================={{{1

# --- This is the basic message order
# ProductCreated               = Always sent to define a 'baseline'
# ActivityCreated              = Test suite started
#     TaskCreated              = Test case started
#          TaskCreated(parent) = Test step started (Task with parent task)
#          ...                   Will not post TaskUpdated, since test steps are
#          ...                   kept until testcase is finished.
#     TaskUpdated              = Test case ended
#     ...
# ActivityUpdated              = test suite ended


# NOTE: Conventions for products:
#   The messaging protocol defines two title fields, metadata.title and metadata.extendedTitle.
#
#   metadata.title should be the name of the baseline or repository depending on source type.
#   metadata.extendedTitle must conform to these principles:
#
#   | Integration levels    | Labeling principle                            | Labeling source             | Examples                                                                              |
#   | ==================    | ==================                            | ===============             | ========                                                                              |
#   | Unit                  | Product Module/Local label*                   | Module Structure            | - Vehicle Motion Management/vehiclemotionstate_service_Computing Infrastructure_dp-lp |
#   | Component (rim nodes) | ECU/local label                               | Module Structure            | - BMS/MyLabel                                                                         |
#   | SW Component (VCU)    | Product Module/CS-Layer/CS-module/Local label | Module Structure/CS modules | - Computing Infrastructure/Base/cs-core/MyLabel                                       |
#   |                       |                                               |                             | - Steering/HAL/hal-power-steering/MyLabel                                             |
#   | Domain                | DomainLabel/Local label                       | CI Framework                | - Body/MyLabel                                                                        |
#   | Complete              | Main branch                                   | CI Framework                | - SPA2 Main Integration                                                               |
#    * It's recommended that Local label contain CS-module id HP SW platform (CS-tool)
#
#   The messaging protocol allows tags, metadata.tags, which are used to build an organized structure in Victoria.
#
#   metadata.tags should include tags that conform to these principles:
#
#   | Product Type   | Tag principle                              | Examples                          |
#   | ============   | =============                              | ========                          |
#   | baseline       | category:ci-levels:component:<ecu-name>    | category:ci-levels:component:asdm |
#   | baseline       | category:ci-levels:domain:<domain-name>    | category:ci-levels:domain:body    |
#   | baseline       | category:ci-levels:complete:<program-name> | -                                 |
#   | source         | category:ecu:<ecu-name>                    | category:ecu:vcu                  |
#   | source (tools) | category:tools:<tools-group-name>          | category:tools:cii-tools          |
#
#   Note:
#   metadata.tags hidden can be used to hide/exclude prototypes and experimenting from being displayed by default.
#   Enable Show Hidden in Explore page will make it possible to find items with metadata.tags set to hidden.


class ProductCreated(CynosureV3Message):
    """ProductCreated message, sent in the beginning of each new test suite."""

    # These fields are optional, mandatory fields are part of the initialization.
    optional = ['productOf', 'createdBy', 'contact', 'version', 'title',
            'description', 'url', 'time', 'tags', 'metadata', 'custom',
            'vendor', 'sender', 'confidenceLevels']

    def __init__(self, productId, track=None, type_='baseline', **k):
        """Default type is 'baseline'."""
        super(ProductCreated, self).__init__(**k)
        self['type'] = type_
        self['productId'] = productId
        self['track'] = track
        self['time'] = cynosure.now()


class ActivityCreated(CynosureV3Message):
    """This message is sent at start of each test suite.

    For 'type':
        - 'default' requires a 'productId',
        - 'assembly' requires a list of 'productIds',
        - 'standalone' does not allow a 'productId', since it has no connection
           to products.

    NOTE! This is the 'default' type of Activity, for other types see_
    AssemblyActivityCreated and StandaloneActivityCreated.
    """

    optional = ['triggeredBy', 'version', 'allocatedTo', 'actions', 'estimatedDuration',
            'state', 'verdict', 'verdictInfo', 'metrics', 'logs', 'contact', 'title',
            'description', 'url', 'time', 'tickets', 'tags', 'custom', 'vendor', 'sender']

    def __init__(self, activityId, name, productId, type_='default', track=None, **k):
        """type and activityId are mandatory.
        NOTE:  For activities of type 'assembly', then productID should be a
               list of productIDs
        NOTE:  Identifying name of the activity.  In the case of a default type
               activity the name must be prefixed with the productId.namespace,
               e.g.  PSRC1234567/myawesomeactivity
        NOTE:  'track' is only mandatory for default activities.
        """
        self['type'] = type_
        if type_ == 'assembly':
            # For 'assembly', use  a list of products
            self['productIds'] = productId
        elif type_ == 'standalone':
            # No productId for 'standalone'
            pass
        else:
            # type_ == 'default'
            self['productId'] = productId
            self['track'] = track # Track is nullable, None is translated to 'null'
        self['activityId'] = activityId
        self['name'] = name
        self['time'] = cynosure.now()
        super(ActivityCreated, self).__init__(**k)


class ActivityUpdated(ActivityCreated):
    """Message sent when the test suite is finished."""
    # ActivityUpdated contains exactly the same fields as ActivityCreated, but
    # needs to have its own name.
    optional = ['allocatedTo', 'actions', 'estimatedDuration', 'state',
            'verdict', 'verdictInfo', 'metrics', 'logs', 'contact', 'title',
            'description', 'url', 'time', 'tickets', 'tags', 'custom',
            'vendor', 'sender']
    def __init__(self, activityId, **k):
        self['activityId'] = activityId
        self.add_optional(k)


class TaskCreated(CynosureV3Message):
    """Sent for each new test case or test step. The difference between test
    cases and test steps is that the 'parentTaskId' of test steps will point to
    the parent test case."""

    optional = ['parentTaskId', 'isParentTask', 'version', 'estimatedDuration',
            'state', 'verdict', 'verdictInfo', 'metrics', 'logs', 'contact',
            'title', 'description', 'url', 'time', 'tickets', 'tags', 'custom',
            'vendor', 'sender']

    def __init__(self, activityId, taskId, name, **k):
        """NOTE: The task name must be prefixed with the activity identifier:
            e.g PSRC1234567/myawesomeactivity/myawesometask."""
        super(TaskCreated, self).__init__(**k)
        self['activityId'] = activityId
        self['taskId'] = taskId
        self['name'] = name
        self['time'] = cynosure.now()


class TaskUpdated(TaskCreated):
    """Sent when test case / test step is finished."""
    optional = ['version', 'estimatedDuration', 'state', 'verdict',
            'verdictInfo', 'metrics', 'logs', 'contact', 'title',
            'description', 'url', 'time', 'tickets', 'tags', 'custom',
            'vendor', 'sender']
    def __init__(self, taskId, **k):
        self['taskId'] = taskId
        self.add_optional(k)


# Observer objects that copy data from core objects to messages. =========={{{1

class TestSuiteMessageObserver(core.Observer):
    """Observer for test suites, creates messages and uses handler to
    distribute the messages."""

    def __init__(self, handler, send_product=True):
        """Handler is of type 'MessageHandler'. Attributes of the
        MessageHandler will decide how the message is processed.
        If 'send_product' is False, then no ProductCreated message
        is sent, the activity will then instead be associated with
        a product that is configured in the TestsuiteDataAdapter."""
        self.handler = handler
        self.send_product = send_product
        self.paramsPosted = False
#        self.globalCtx = epsglobal.read() # Not needed for Hilding

    def notify_abort(self, observable):
        # TODO: What do we do here?!?
        pass

    def notify_start(self, observable):
        """Create start messages: 'ProductCreated' and 'ActivityCreated'."""
        productId = cynosure.qualify(namespace=cyno_encode(observable.metadata.product_name),
                instance=observable.metadata.product_id)
        if self.send_product:
            # The product ID was not supplied by the calling process (e.g. Jenkins pipeline)
            pcm = ProductCreated(productId=productId)
            self.handler.handle(pcm)
        acm = ActivityCreated(activityId=observable.id,
                name=self.get_activityname(observable),
                title=observable.name,
                productId=productId)
        if not self.paramsPosted and paramConfig.cynosure.post:
            self.paramsPosted = True
            acm.set_custom(EPSHIL_System_parameters=observable.metadata.execution_info.parameters)
        acm.set_custom(EPSHIL_ini_execution_time=cynosure.isoformat(observable.starttime))
        acm.set_value(state=observable.state.name)
        self.copy_data(observable, acm)
        self.handler.handle(acm)

    def notify_update(self, observable, data):
        msg = ActivityUpdated(activityId=observable.id)
        if not data:
            msg.set_custom(EPSHIL_ini_execution_time=cynosure.isoformat(observable.starttime))
        if not self.paramsPosted:
            if paramConfig.cynosure.post:
                self.paramsPosted = True
                msg.set_custom(EPSHIL_System_parameters=observable.metadata.execution_info.parameters)
#            msg.set_custom_for_updates(self.globalCtx._indata) # Not needed for Hilding
        
        self.copy_data(observable, msg)
        self.handler.handle(msg,data==None)

    def notify_finish(self, observable, verdict):
        """Create an 'ActivityUpdated' message."""
        v_info = observable.metadata.verdict_info
        verdict_info = cynosure.qualify_verdict(description=v_info.description,
                                                vtype=v_info.vtype,
                                                code=v_info.code,
                                                url=v_info.url,
                                                data=v_info.data)
                                                
        msg = ActivityUpdated(activityId=observable.id)
        msg.set_object('verdictInfo',verdict_info)
        self.copy_data(observable, msg)
        msg.set_custom(EPSHIL_ini_execution_time=cynosure.isoformat(observable.starttime))
        msg.set_custom(EPSHIL_end_execution_time=cynosure.isoformat(observable.endtime))
        msg.set_custom(EPSHIL_executionTime=cynosure.isotimediff(observable.starttime, observable.endtime))
        msg.set_value(state=observable.state.name)
        msg.set_value(verdict=observable.verdict.name)
        self.handler.handle(msg)

    def copy_data(self, o, m):
        """Copy data from the 'core.TestSuite' object to the message
        structure."""
        m.set_value(url=o.url)
        m.set_value(logs=o.logs)
        # Execution info
        e_info = o.metadata.execution_info
        m.set_custom(EPSHIL_Jenkins_JobId=e_info.name)
        m.set_custom(EPSHIL_System_executor=e_info.executor)
        m.set_custom(EPSHIL_System_project_AD_name=e_info.project)
        m.set_custom(EPSHIL_TestExecutionDescription=e_info.description)
        # Software info
        sw_info = o.metadata.software_info
        m.set_custom(EPSHIL_Baseline_Changeset=sw_info.changeset)
        m.set_custom(EPSHIL_Development_Baseline_Changeset=sw_info.inhousechangeset)
        m.set_custom(EPSHIL_GitHash=sw_info.githash)
        m.set_custom(EPSHIL_System_ECU=sw_info.ecu)
        m.set_custom(EPSHIL_System_platform=sw_info.platform)
        m.set_custom(EPSHIL_System_project=sw_info.vehicle_project)
        m.set_custom(EPSHIL_System_release_version=sw_info.version)
        m.set_custom(EPSHIL_System_series=sw_info.vehicle_series)
        # Test env info
        t_info = o.metadata.testenv_info
        # NOTE: Adding tag for rig (HIL)
        m.set_value(tags=["rig:{name}".format(name=t_info.name)])
        # The rest of testenv_info is stored in custom attributes.
        m.set_custom(EPSHIL_System_ipaddress=t_info.ipaddress)
        m.set_custom(EPSHIL_System_name=t_info.name)
        m.set_custom(EPSHIL_System_testequipment=t_info.testequipment)
        # Version info
        v_info = o.metadata.version_info
        m.set_custom(EPSHIL_System_repo_information=v_info)
        # Model info
        sim_info = o.metadata.simulation_info
        m.set_custom(EPSHIL_Model_CAN_database=sim_info.dbc)
        m.set_custom(EPSHIL_Model_ECU=sim_info.ecu)
        m.set_custom(EPSHIL_Model_branch=sim_info.branch)
        m.set_custom(EPSHIL_Model_id=sim_info.build_id)
        m.set_custom(EPSHIL_Model_project=sim_info.project)
        try:
            for i in o.metadata.others:
                m.set_custom_for_updates(i)
        except Exception as e:
            log.debug("Error trying to set runtime custom data : {}".format(e))
        # TODO: HIL Platform !!

    def get_activityname(self, o):
        # ProductName '/' ActivityName
        return cyno_encode(make_name(o.metadata.product_name, o.name))


class TestCaseMessageObserver(core.Observer):
    """Observer for test cases."""
    def __init__(self, handler):
        self.handler = handler

    def handle_message(self, observable, msg):
        """To be overridden for test steps, the 'observable' argument is not
        used here, but it is used in the 'TestStepMessageObserver'."""
        self.handler.handle(msg)

    def notify_abort(self, observable):
        # TODO: What do we do here?!?
        pass

    def notify_start(self, observable):
        """Create a 'TaskCreated' message."""
        msg = TaskCreated(activityId=self.get_activityid(observable),
                taskId=observable.id,
                name=self.get_taskname(observable),
                title=observable.name)
        self.copy_data(observable, msg)
        msg.set_value(isParentTask=True)
        msg.set_value(state=observable.state.name)
        msg.set_custom(EPSHIL_ini_execution_time=cynosure.isoformat(observable.starttime))
        self.handle_message(observable, msg)

    def notify_finish(self, observable, verdict):
        """Create a 'TaskUpdated' message with the verdicdt."""
        msg = TaskUpdated(taskId=observable.id)
        msg.set_custom(EPSHIL_ini_execution_time=cynosure.isoformat(observable.starttime))
        msg.set_custom(EPSHIL_end_execution_time=cynosure.isoformat(observable.endtime))
        msg.set_custom(EPSHIL_executionTime=cynosure.isotimediff(observable.starttime, observable.endtime))
        msg.set_value(state=observable.state.name)
        msg.set_value(verdict=observable.verdict.name)
        self.copy_data(observable, msg)
        self.handle_message(observable, msg)

    def copy_data(self, o, m):
        """Copy data from the 'core.TestCase' or 'core.TestStep' object to the
        message."""
        m.set_value(url=o.url)
        m.set_value(logs=o.logs)
        c_info = o.metadata.testcode_info
        # NOTE: Adding descriptions for test cases
        m.set_value(description=c_info.description)
        # NOTE: Adding contact for test cases
        # TODO: Check if "Author" really is what we want here.
        m.set_value(contact={'name': c_info.responsible or c_info.author})
        # Adding the rest as custom values
        m.set_custom(EPSHIL_author=c_info.author)
        m.set_custom(EPSHIL_description=c_info.description)
        m.set_custom(EPSHIL_creation_date=cynosure.isoformat(c_info.creationdate))
        m.set_custom(EPSHIL_modification_date=cynosure.isoformat(c_info.modificationdate))
        m.set_custom(EPSHIL_requirement=c_info.requirement)
        m.set_custom(EPSHIL_TCresponsible=c_info.responsible)

    def get_activityid(self, o):
        return o.parent.id

    def get_taskname(self, o):
        """Return ProductName/ActivityName/TaskName."""
        # ProductName '/' TestsuiteName '/' TestcaseName
        return cyno_encode(make_name(o.parent.metadata.product_name, o.parent.name, o.name))


class TestStepMessageObserver(TestCaseMessageObserver):
    """Observer for test steps. Two differences from test cases:
      1. The 'parentTaskId' is set to the identity of the test case.
      2. Test step messages are not handled directly, they are queued to avoid
         interrupting the test case flow (timing issues).
    """
    def handle_message(self, observable, msg):
        msg['parentTaskId'] = observable.parent.id
        self.handler.queue(msg)

    def notify_start(self, observable):
        """Skip start messages, send a TaskCreated message when test step is
        finished instead."""
        pass

    def notify_finish(self, observable, verdict):
        """Push a 'TaskCreated' message to the internal queue, with verdict."""
        msg = TaskCreated(activityId=self.get_activityid(observable),
                taskId=observable.id,
                name=self.get_taskname(observable),
                title=observable.name)
        msg.set_custom(EPSHIL_ini_execution_time=cynosure.isoformat(observable.starttime))
        msg.set_custom(EPSHIL_end_execution_time=cynosure.isoformat(observable.endtime))
        msg.set_custom(EPSHIL_executionTime=cynosure.isotimediff(observable.starttime, observable.endtime))
        msg.set_value(isParentTask=False)
        msg.set_value(state=observable.state.name)
        msg.set_value(verdict=observable.verdict.name)
        self.copy_data(observable, msg)
        self.handle_message(observable, msg)

    def get_activityid(self, o):
        return o.parent.parent.id

    def get_taskname(self, o):
        # ProductName '/' TestsuiteName '/' TestcaseName '/' TeststepName
        return cyno_encode(make_name(o.parent.parent.metadata.product_name, o.parent.parent.name, o.parent.name, o.name))


# modeline ==============================================================={{{1
# vim: set fdm=marker:
# eof
