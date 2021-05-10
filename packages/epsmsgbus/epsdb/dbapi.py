#!/bin/env python

"""
This is the public part of the database API.
"""

import json
import logging

from . import core

# Only give access to these functions and classes.
__all__ = ['store_message', 'admin', 'DatabaseContext']


log = logging.getLogger('epsdb')


admin = core.admin
DatabaseContext = core.DatabaseContext


def store_message(message):
    """Store data [in JSON or a mapping (dict)]."""
    if core.CONFIG.enabled:
        try:
            data = json.loads(message) if isinstance(message, str) else message
            core.store_data(data)
        except Exception as e:
            log.error("Problem saving to database [%s]." % e)
            log.debug("TRACE", exc_info=True)
    else:
        log.debug("Saving to database is disabled.")


# modeline ==============================================================={{{1
# vim: set fdm=marker:
# eof
