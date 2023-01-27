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
Utilities for MessageBus (3.0) and "Victoria".

 - Stop Activities/Tasks that have state ongoing because of bugs in our
   framework.
"""

import argparse
import logging
import os
import pprint
import sys

import epsmsgbus.cynosure as cynosure
import epsmsgbus.cynosure3 as cynosure3


log = logging.getLogger('epsmsgbus.victoria')
MYNAME, _ = os.path.splitext(os.path.basename(__file__))
__version__ = "{} v0.1".format(MYNAME)


def run_stop(msgtype, identity, sender=None, description=None, contact=None):
    """Send ActivityUpdated or TaskUpdated with verdict = 'aborted' and state = 'finished'."""
    if msgtype == 'activity':
        msg = cynosure3.ActivityUpdated(identity)
    elif msgtype == 'task':
        msg = cynosure3.TaskUpdated(identity)
    else:
        raise Exception("Unsupported message type '{}' in 'run_stop'.".format(msgtype))
    msg.set_value(verdict='aborted', state='finished')
    if not sender is None:
        s_type, s_value = sender.split(':', 1)
        msg.set_value(sender={s_type: s_value})
    if not description is None:
        msg.set_value(verdictInfo={'description': description})
    if not contact is None and contact:
        msg.set_value(contact=contact)
    log.debug('{} =>\n{}'.format(msg.__class__.__name__, pprint.pformat(msg)))
    return msg


def main(argv):
    """Parse command line arguments and perform actions."""
    ap = argparse.ArgumentParser(description="Send 'utility' messages on Cynosure 3.0 message bus to fix problems.")
    ap.add_argument("-d", "--debug", action="store_true", default=False, help="Printout debug messages.")
    ap.add_argument("-n", "--dry-run", action="store_true", default=False, help="Don't send any messages to the message bus (for test purposes).")
    ap.add_argument("-V", "--version", action="version", version=__version__, help="Printout version information and quit.")
    sp = ap.add_subparsers(dest="command", help="Use '<command> --help' to get more information.", description="Use any of the following subcommands:")
    p_stop = sp.add_parser("stop", help="Mark jobs as finished.", description="Stop activities or tasks by sending an ActivityUpdated or TaskUpdated message with status = 'finished' and verdict = 'aborted'.")
    p_stop.add_argument("msgtype", choices=("activity", "task"), nargs=1, help="Choose either 'activity' for test suites or 'task' for test cases or test steps.")
    p_stop.add_argument("identity", nargs=1, help="Identity that uniquely identifies the object.")
    p_stop.add_argument('--description', help="Description of the verdict [=verdictInfo], default is not send a verdict description.")
    p_stop.add_argument('--sender', default="application:epsmsgbus.{}".format(MYNAME), help="Sender 'type:id', used mostly for debug purposes, default is '%(default)s'.")
    p_cg = p_stop.add_argument_group(title='contact information', description="Optional contact information to be added to the message.")
    p_cg.add_argument('--contact-email', metavar='EMAIL', help="Contact email (e.g. 'fredrik.acosta@volvocars.com').")
    p_cg.add_argument('--contact-id', metavar='CDSID', help="Contact ID (e.g. 'facosta').")
    p_cg.add_argument('--contact-name', metavar='NAME', help="Contact name (e.g. 'Fredrik Acosta').")
    p_cg.add_argument('--contact-url', metavar='URL', help="Contact URL (e.g. 'https://mysite.volvocars.net/personal/facosta_volvocars_com/Blog/default.aspx').")
    args = ap.parse_args(argv)
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    if args.command == 'stop':
        mh = cynosure.messagehandler(use_db=False, use_mq=(not args.dry_run))
        if args.sender and ':' not in args.sender:
            ap.error("Sender must be given as 'type:id' (e.g. application:victoria.py)")
        contact = {}
        if args.contact_email:
            contact['email'] = args.contact_email
        if args.contact_id:
            contact['id'] = args.contact_id
        if args.contact_name:
            contact['name'] = args.contact_name
        if args.contact_url:
            contact['url'] = args.contact_url
        message = run_stop(args.msgtype[0], args.identity[0], description=args.description,
                sender=args.sender, contact=contact)
        log.info("Sending message")
        mh.handle(message)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main(sys.argv[1:])


# eof
