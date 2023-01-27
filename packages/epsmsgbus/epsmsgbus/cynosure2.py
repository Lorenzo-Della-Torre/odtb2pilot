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
"""

# NOTE: See .\cynosure2.txt for message samples

import logging

import epsmsgbus.core as core
import epsmsgbus.cynosure as cynosure


# Globals ================================================================
log = logging.getLogger('epsmsgbus.cynosure2')

DEFAULT_SERVER = "core.messagebus.cynosure.volvocars.biz"
DEFAULT_VERSION =  "2.0.0"


# Base classes for messages ==============================================
class CynosureV2Message(cynosure.CynosureMessage):
    """Base class for version 2.0 of Cynosure messages."""

    server = DEFAULT_SERVER
    version = DEFAULT_VERSION

    def set_sender(self, **data):
        """Set the 'sender' data block (unique for Cynosure V2)."""
        self.set_object('sender', data)

    def set_vendor(self, **data):
        """Set the 'vendor' data block (unique for Cynosure V2)."""
        self.set_object('vendor', data)


# Messages ===============================================================

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


class ProductCreated(CynosureV2Message):
    """ProductCreated message, sent in the beginning of each new test suite."""

    # These fields are optional, mandator fields are part of the initialization.
    optional = ['productOf', 'producedBy', 'track', 'contact', 'title',
            'description', 'url', 'time', 'tags', 'custom', 'vendor', 'sender']

    def __init__(self, productId, type_='baseline', **k):
        """Default type is 'baseline'."""
        super(ProductCreated, self).__init__(**k)
        self['productId'] = productId
        self['type'] = type_
        self['time'] = cynosure.now()


class ActivityCreated(CynosureV2Message):
    """This message is sent at start of each test suite."""

    optional = ['productIds', 'parentActivityId', 'track', 'chainIdentifier',
            'triggeredBy', 'allocatedTo', 'requirements', 'environment',
            'runner', 'workspace', 'action', 'estimatedDuration',
            'queueTimeout', 'concurrencyLimit', 'tokens', 'flowId', 'state',
            'verdictMessage', 'fault', 'metrics', 'logs', 'contact', 'title',
            'description', 'url', 'time', 'tags', 'custom', 'vendor', 'sender']

    def __init__(self, activityId, **k):
        """activityId is mandatory."""
        super(ActivityCreated, self).__init__(**k)
        self['activityId'] = activityId
        self['time'] = cynosure.now()


class ActivityUpdated(ActivityCreated):
    """Message sent when the test suite is finished."""
    # ActivityUpdated contains exactly the same fields as ActivityCreated, but
    # needs to have its own name.
    pass


class TaskCreated(CynosureV2Message):
    """Sent for each new test case or test step. The difference between test
    cases and test steps is that the 'parentTaskId' of test steps will point to
    the parent test case."""

    optional = ['parentTaskId', 'state', 'verdict', 'verdictMessage', 'fault',
            'metrics', 'logs', 'contact', 'title', 'description', 'url',
            'time', 'tags', 'custom', 'vendor', 'sender']

    def __init__(self, activityId, taskId, **k):
        super(TaskCreated, self).__init__(**k)
        self['activityId'] = activityId
        self['taskId'] = taskId
        self['time'] = cynosure.now()


class TaskUpdated(TaskCreated):
    """Sent when test case / test step is finished."""
    # NOTE: Same structure as TaskCreated but needs unique name
    pass


# Observer objects that copy data from core objects to messages. ==========

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

    def notify_abort(self, observable):
        # TODO: What do we do here?!?
        pass

    def notify_start(self, observable):
        """Create start messages: 'ProductCreated' and 'ActivityCreated'."""
        productId = cynosure.qualify(namespace=observable.metadata.product_name,
                instance=observable.metadata.product_id)
        if self.send_product:
            # The product ID was not supplied by the calling process (e.g. Jenkins pipeline)
            pcm = ProductCreated(productId=productId)
            self.handler.handle(pcm)
        activityId = cynosure.qualify(namespace=observable.name, instance=observable.id)
        acm = ActivityCreated(activityId=activityId)
        acm.set_custom(EPSHIL_ini_execution_time=cynosure.isoformat(observable.starttime))
        acm.set_value(state=observable.state.name)
        self.copy_data(observable, acm)
        self.handler.handle(acm)

    def notify_finish(self, observable, verdict):
        """Create an 'ActivityUpdated' message."""
        activityId = cynosure.qualify(namespace=observable.name, instance=observable.id)
        msg = ActivityUpdated(activityId=activityId)
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
        productId = cynosure.qualify(namespace=o.metadata.product_name,
                instance=o.metadata.product_id)
        m['productIds'] = [productId]
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
        m.set_custom(EPSHIL_System_ipaddress=t_info.ipaddress)
        m.set_custom(EPSHIL_System_name=t_info.name)
        # Model info
        sim_info = o.metadata.simulation_info
        m.set_custom(EPSHIL_Model_CAN_database=sim_info.dbc)
        m.set_custom(EPSHIL_Model_ECU=sim_info.ecu)
        m.set_custom(EPSHIL_Model_branch=sim_info.branch)
        m.set_custom(EPSHIL_Model_id=sim_info.build_id)
        m.set_custom(EPSHIL_Model_project=sim_info.project)
        # TODO: HIL Platform !!


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
                taskId=cynosure.qualify(namespace=observable.name, instance=observable.id))
        self.copy_data(observable, msg)
        msg.set_value(state=observable.state.name)
        msg.set_custom(EPSHIL_ini_execution_time=cynosure.isoformat(observable.starttime))
        self.handle_message(observable, msg)

    def notify_finish(self, observable, verdict):
        """Create a 'TaskUpdated' message with the verdicdt."""
        msg = TaskUpdated(activityId=self.get_activityid(observable),
                taskId=cynosure.qualify(namespace=observable.name, instance=observable.id))
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
        m['productId'] = [self.get_productid(o)]
        m.set_value(url=o.url)
        m.set_value(logs=o.logs)
        c_info = o.metadata.testcode_info
        m.set_custom(EPSHIL_author=c_info.author)
        m.set_custom(EPSHIL_description=c_info.description)
        m.set_custom(EPSHIL_creation_date=cynosure.isoformat(c_info.creationdate))
        m.set_custom(EPSHIL_modification_date=cynosure.isoformat(c_info.modificationdate))
        m.set_custom(EPSHIL_requirement=c_info.requirement)
        m.set_custom(EPSHIL_TCresponsible=c_info.responsible)

    def get_activityid(self, o):
        return cynosure.qualify(namespace=o.parent.name, instance=o.parent.id)

    def get_productid(self, o):
        return cynosure.qualify(namespace=o.parent.metadata.product_name,
                instance=o.parent.metadata.product_id)


class TestStepMessageObserver(TestCaseMessageObserver):
    """Observer for test steps. Two differences from test cases:
      1. The 'parentTaskId' is set to the identity of the test case.
      2. Test step messages are not handled directly, they are queued to avoid
         interrupting the test case flow (timing issues).
    """
    def handle_message(self, observable, msg):
        msg['parentTaskId'] = cynosure.qualify(namespace=observable.parent.name,
                instance=observable.parent.id)
        self.handler.queue(msg)

    def notify_start(self, observable):
        """Skip start messages, send a TaskCreated message when test step is
        finished instead."""
        pass

    def notify_finish(self, observable, verdict):
        """Push a 'TaskCreated' message to the internal queue, with verdict."""
        msg = TaskCreated(activityId=self.get_activityid(observable),
                taskId=cynosure.qualify(namespace=observable.name, instance=observable.id))
        msg.set_custom(EPSHIL_ini_execution_time=cynosure.isoformat(observable.starttime))
        msg.set_custom(EPSHIL_end_execution_time=cynosure.isoformat(observable.endtime))
        msg.set_custom(EPSHIL_executionTime=cynosure.isotimediff(observable.starttime, observable.endtime))
        msg.set_value(state=observable.state.name)
        msg.set_value(verdict=observable.verdict.name)
        self.copy_data(observable, msg)
        self.handle_message(observable, msg)

    def get_activityid(self, o):
        return cynosure.qualify(namespace=o.parent.parent.name,
                instance=o.parent.parent.id)

    def get_productid(self, o):
        return cynosure.qualify(namespace=o.parent.parent.metadata.product_name,
                instance=o.parent.parent.metadata.product_id)


# modeline ===============================================================
# vim: set fdm=marker:
# eof
