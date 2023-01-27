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
Common definitions and functions for Cynosure 2 and Cynosure 3
"""

import datetime
import http.client
import json
import logging
import pprint
import pytz
import time

from collections import deque


# Globals ================================================================{{{1
log = logging.getLogger('epsmsgbus.cynosure')

DEFAULT_CONFIG = 'db'
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
        self.add_optional(k)

    def add_optional(self, k):
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
        self.set_custom_for_updates(data)

    def set_custom_for_updates(self, data):
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


def qualify(namespace, instance):
    """Return qualified name (namespace + instance)."""
    return {'namespace': namespace, 'instance': instance}

def qualify_verdict(description, code=None, vtype=None, url=None, data=None):
    return {'description' : description, 'code' : code, 'type' : vtype, 'url' : url, 'data' : data}
    
# Post messages on queue (and call database API) ========================={{{1
class MessageHandler(object):
    def __init__(self, use_mq=False, use_db=False):
        self.use_mq = use_mq
        self.use_db = use_db
        self.internal_queue = deque()

    def handle(self, msg, share_activity=None):
        while True:
            try:
                qm = self.internal_queue.popleft()
            except IndexError:
                break
            log.debug("Handling deferred message of type {} from queue.".format(qm.__class__.__name__))
            self._handle(qm,share_activity)
        log.debug("Handling message of type {}.".format(msg.__class__.__name__))
        self._handle(msg,share_activity)

    def queue(self, msg):
        self.internal_queue.append(msg)
        log.debug('Queueing {} message for later processing [{} messages].'.format(msg.__class__.__name__, len(self.internal_queue)))

    def _handle(self, msg, share_activity):
        if self.use_mq:
            msg.post()
        else:
            log.debug("Not pushing any messages, not enabled.")
        if self.use_db:
            try:
                import epsdb
                epsdb.store_message(msg, share_activity)
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
        log.debug("TRACE Response text {}".format(str(response.read(), 'utf8')))
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


def now():
    """Return time stamp in string format accepted by Cynosure."""
    return isoformat(zulu_time())


# modeline ==============================================================={{{1
# vim: set fdm=marker:
# eof
