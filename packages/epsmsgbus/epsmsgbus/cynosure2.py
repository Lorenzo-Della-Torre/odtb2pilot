#!/bin/env python

"""
Create messages in JSON format and post these messages to Cynosure.
"""

# NOTE: See .\cynosure2.txt for message samples

import datetime
import http.client
import json
import logging
import pprint
import pytz
import time

from collections import deque

import epsmsgbus.core as core


# Globals ================================================================{{{1
log = logging.getLogger('epsmsgbus.cynosure2')

DEFAULT_SERVER = "core.messagebus.cynosure.volvocars.biz"
DEFAULT_VERSION =  "2.0.0"
DEFAULT_USE_MQ = True
DEFAULT_USE_DB = True


# Base classes for messages =============================================={{{1
class CynosureMessage(dict):
    """Base class for messages to Cynosure. Contains common functionality."""
    # These *must* be overriden by subclasses
    server = None
    version = None

    # List of optional fields in the message. Mandatory fields should
    # be specified in __init__()
    optional = []

    def __init__(self, **k):
        """Add optional fields given at instiation time."""
        for key in self.optional:
            if key in k:
                self[key] = k[key]

    def is_valid(self, data):
        """Data is valid if it's not None and has length > 0."""
        if data is None:
            # None is the same as empty
            return False
        try:
            # Strings, bytes, tuples, lists and mappings
            return len(data) > 0
        except:
            try:
                # Numbers and everything else that has a string representation
                return len(str(data)) > 0
            except:
                # Not possible to persist
                return False

    def post(self):
        """Push the message to cynosure."""
        # Use the class name as the message name
        post_message(self.server, self.version, self.__class__.__name__, self)

    def set_custom(self, **data):
        """Update/add custom fields."""
        self.set_object('custom', data)

    def set_object(self, name, data):
        """Update mapping, filter for valid data."""
        if self.is_valid(data):
            self.setdefault(name, {}).update({k: v for k, v in data.items() if self.is_valid(v)})

    def set_value(self, **data):
        """Set single value (if valid)."""
        for k, v in data.items():
            if self.is_valid(v):
                self[k] = v


class CynosureV2Message(CynosureMessage):
    """Base class for version 2.0 of Cynosure messages."""

    server = DEFAULT_SERVER
    version = DEFAULT_VERSION

    def set_sender(self, **data):
        """Set the 'sender' data block (unique for Cynosure V2)."""
        self.set_object('sender', data)

    def set_vendor(self, **data):
        """Set the 'vendor' data block (unique for Cynosure V2)."""
        self.set_object('vendor', data)


def qualify(namespace, instance):
    """Return qualified name (namespace + instance)."""
    return {'namespace': namespace, 'instance': instance}


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
        self['time'] = isoformat(zulu_time())


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
        self['time'] = isoformat(zulu_time())


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
        self['time'] = isoformat(zulu_time())


class TaskUpdated(TaskCreated):
    """Sent when test case / test step is finished."""
    # NOTE: Same structure as TaskCreated but needs unique name
    pass


# Observer objects that copy data from core objects to messages. =========={{{1

class TestSuiteMessageObserver(core.Observer):
    """Observer for test suites, creates messages and uses handler to
    distribute the messages."""

    def __init__(self, handler):
        """Handler is of type 'MessageHandler'. Attributes of the
        MessageHandler will decide how the message is processed."""
        self.handler = handler

    def notify_abort(self, observable):
        # TODO: What do we do here?!?
        pass

    def notify_start(self, observable):
        """Create start messages: 'ProductCreated' and 'ActivityCreated'."""
        productId = qualify(namespace=observable.metadata.product_name,
                instance=observable.metadata.product_id)
        pcm = ProductCreated(productId=productId)
        self.handler.handle(pcm)
        activityId = qualify(namespace=observable.name, instance=observable.id)
        acm = ActivityCreated(activityId=activityId)
        acm.set_custom(EPSHIL_ini_execution_time=isoformat(observable.starttime))
        self.copy_data(observable, acm)
        self.handler.handle(acm)

    def notify_finish(self, observable, verdict):
        """Create an 'ActivityUpdated' message."""
        activityId = qualify(namespace=observable.name, instance=observable.id)
        msg = ActivityUpdated(activityId=activityId)
        self.copy_data(observable, msg)
        msg.set_custom(EPSHIL_ini_execution_time=isoformat(observable.starttime))
        msg.set_custom(EPSHIL_end_execution_time=isoformat(observable.endtime))
        msg.set_custom(EPSHIL_executionTime=isotimediff(observable.starttime, observable.endtime))
        msg.set_value(verdict=observable.verdict.name)
        self.handler.handle(msg)

    def copy_data(self, o, m):
        """Copy data from the 'core.TestSuite' object to the message
        structure."""
        productId = qualify(namespace=o.metadata.product_name,
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
                taskId=qualify(namespace=observable.name, instance=observable.id))
        self.copy_data(observable, msg)
        msg.set_custom(EPSHIL_ini_execution_time=isoformat(observable.starttime))
        self.handle_message(observable, msg)

    def notify_finish(self, observable, verdict):
        """Create a 'TaskUpdated' message with the verdicdt."""
        msg = TaskUpdated(activityId=self.get_activityid(observable),
                taskId=qualify(namespace=observable.name, instance=observable.id))
        msg.set_custom(EPSHIL_ini_execution_time=isoformat(observable.starttime))
        msg.set_custom(EPSHIL_end_execution_time=isoformat(observable.endtime))
        msg.set_custom(EPSHIL_executionTime=isotimediff(observable.starttime, observable.endtime))
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
        m.set_custom(EPSHIL_creation_date=isoformat(c_info.creationdate))
        m.set_custom(EPSHIL_modification_date=isoformat(c_info.modificationdate))
        m.set_custom(EPSHIL_requirement=c_info.requirement)
        m.set_custom(EPSHIL_TCresponsible=c_info.responsible)

    def get_activityid(self, o):
        return qualify(namespace=o.parent.name, instance=o.parent.id)

    def get_productid(self, o):
        return qualify(namespace=o.parent.metadata.product_name,
                instance=o.parent.metadata.product_id)


class TestStepMessageObserver(TestCaseMessageObserver):
    """Observer for test steps. Two differences from test cases:
      1. The 'parentTaskId' is set to the identity of the test case.
      2. Test step messages are not handled directly, they are queued to avoid
         interrupting the test case flow (timing issues).
    """
    def handle_message(self, observable, msg):
        msg['parentTaskId'] = qualify(namespace=observable.parent.name,
                instance=observable.parent.id)
        self.handler.queue(msg)

    def notify_start(self, observable):
        """Skip start messages, send a TaskCreated message when test step is
        finished instead."""
        pass

    def notify_finish(self, observable, verdict):
        """Push a 'TaskCreated' message to the internal queue, with verdict."""
        msg = TaskCreated(activityId=self.get_activityid(observable),
                taskId=qualify(namespace=observable.name, instance=observable.id))
        msg.set_custom(EPSHIL_ini_execution_time=isoformat(observable.starttime))
        msg.set_custom(EPSHIL_end_execution_time=isoformat(observable.endtime))
        msg.set_custom(EPSHIL_executionTime=isotimediff(observable.starttime, observable.endtime))
        msg.set_value(verdict=observable.verdict.name)
        self.copy_data(observable, msg)
        self.handle_message(observable, msg)

    def get_activityid(self, o):
        return qualify(namespace=o.parent.parent.name,
                instance=o.parent.parent.id)

    def get_productid(self, o):
        return qualify(namespace=o.parent.parent.metadata.product_name,
                instance=o.parent.parent.metadata.product_id)


# Post messages on queue (and call database API) ========================={{{1
class MessageHandler(object):
    def __init__(self, use_mq=False, use_db=False):
        self.use_mq = use_mq
        self.use_db = use_db
        self.internal_queue = deque()

    def handle(self, msg):
        while True:
            try:
                qm = self.internal_queue.popleft()
            except IndexError:
                break
            log.debug("Handling deferred message of type {} from queue.".format(qm.__class__.__name__))
            self._handle(qm)
        log.debug("Handling message of type {}.".format(msg.__class__.__name__))
        self._handle(msg)

    def queue(self, msg):
        self.internal_queue.append(msg)
        log.debug('Queueing {} message for later processing [{} messages].'.format(msg.__class__.__name__, len(self.internal_queue)))

    def _handle(self, msg):
        if self.use_mq:
            msg.post()
        else:
            log.debug("Not pushing any messages, not enabled.")
        if self.use_db:
            try:
                import epsdb
                epsdb.store_message(msg)
            except Exception as e:
                log.info("Failed saving to database.")
                log.info(e)
                log.debug("TRACE", exc_info=True)


try:
    MESSAGE_HANDLER
except NameError:
    MESSAGE_HANDLER = MessageHandler(use_mq=DEFAULT_USE_MQ, use_db=DEFAULT_USE_DB)


def messagehandler(use_db=None, use_mq=None):
    if use_db is not None:
        MESSAGE_HANDLER.use_db = bool(use_db)
    if use_mq is not None:
        MESSAGE_HANDLER.use_mq = bool(use_mq)
    return MESSAGE_HANDLER


def post_message(server, version, messagetype, data):
    """Called from message objects."""
    log.debug("--> START {} MESSAGE".format(messagetype))
    log.debug(pprint.pformat(data))
    log.debug("<-- END {} MESSAGE".format(messagetype))
    headers = {"accept": "application/json", "content-type": "application/json"}
    path = "/api/{version}/{messagetype}".format(version=version, messagetype=messagetype)
    try:
        conn = http.client.HTTPConnection(server)
        conn.request("POST", path, json.dumps(data) if data else None, headers)
        response = conn.getresponse()
        log.debug("Reponse: {} {}".format(response.status, response.reason))
        conn.close()
    except Exception as e:
        log.error('Connection error pushing message to Cynosure, reason :: "%s"' % e)
        log.debug("TRACE", exc_info=True)


# Date / Time utilities =================================================={{{1

# TODO: Fix time zone for China, so data from PDF HIL testing will have correct
# time stamps!!
LOCAL_TZ = pytz.timezone("Europe/Stockholm")
UTC_TZ = pytz.timezone("UTC")


def isoformat(dt):
    """Format datatime object according to Cynosure specification, which is
    basically ISO 8601 time format with added 'Z' timezone."""
    return None if dt is None else dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def isotimediff(t1, t2):
    """Calculated time delta between t1 and t2 and format according to ISO
    8601."""
    if t1 == t2:
        return "PT0S"
    td = max(t1, t2) - min(t1, t2)
    L = ['P']
    if td.days > 0:
        L.append("{}D".format(td.days))
    L.append('T')
    mm, ss = divmod(td.seconds, 60)
    ss += round(td.microseconds * 1E-6, 6)
    hh, mm = divmod(mm, 60)
    if hh > 0:
        L.append("{}H".format(hh))
    if mm > 0:
        L.append("{}M".format(mm))
    if ss > 0:
        L.append("{}S".format(ss))
    return ''.join(L)


def zulu_time(timestamp=None):
    """Return formatted string with 'timestamp' in UTC-time (Zulu time). If
    'timestamp' is None then use current time."""

    if timestamp is None:
        dt = datetime.datetime.utcnow()
    else:
        # NOTE: readouts using AutomationDesk's API will return timestamps as
        # 'struct_time' objects, that's why we convert using time.mktime()
        dt = datetime.datetime.fromtimestamp(time.mktime(timestamp), LOCAL_TZ).astimezone(UTC_TZ)
    return dt


# modeline ==============================================================={{{1
# vim: set fdm=marker:
# eof
