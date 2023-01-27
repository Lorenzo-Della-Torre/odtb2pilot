#!/bin/env python

"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

Get or set activityId for Cynosure messages.

Normally when we run test cases we will create the following structure:

    Product       - a dummy product of type baseline
    Activity      - representing the test execution (Test Suite)
        Task      - results and info on test case level
           Task   - subtask with results and info on test step level.

When we run test cases in a CI-chain it may be desirable to reuse a product
that has already been sent by one of the calling processes in the CI-chain.

This file is a very simple interface.

If the environment variables
    ACTIVITY_NAME  (the suite name)
    ACTIVITY_ID   (contains the instance part of the product identity)
are present, then they will be written to a temporary JSON file.

Examples:
    ACTIVITY_ID=Ifa3416293acf315390987ae94b16f0195ad96526
    ACTIVITY_NAME=PBSL15BF417E/TestSuiteName

NOTE: It's important that this file is overwritten in case there is no
      ACTIVITYID !

The code that creates Cynosure messages can then query if the product id has
been persisted to disk, then it means that the calling process already has sent
the product.
"""
import argparse
import json
import logging
import os
import pprint
import sys
import uuid
import epsmsgbus.productid as productid_mod

log = logging.getLogger('epsmsgbus.activityid')

DEFAULT_ACTIVITYID_FILENAME = os.path.abspath(os.path.join(os.path.dirname(__file__),
        "..", "..", "..", "log", "activityid.tmp"))


def get_activityid(filename=DEFAULT_ACTIVITYID_FILENAME):
    ''' Return product info structure if the file productinfo.tmp exists.
    Returns None if the file is empty, not readable, or non-existing.
    
    :param filename: json file where information about activity is saved
    :type filename: file

    :rtype: dict
    :return: Json data with activity info if the file activityid.tmp exists.None if the file is empty, 
    not readable, or non-existing.

    '''
    try:
        with open(filename) as fp:
            log.debug(f"Getting product identity from '{filename}'.")
            return json.load(fp)
    except:
        pass


def set_activityid(filename=DEFAULT_ACTIVITYID_FILENAME, namespace=None, instance=None):
    ''' Save product identity from the environment to a JSON file. The
    'namespace' and 'instance' parameters are primarily for unittesting.
    
    :param filename: json file name where information about server is saved
    :type filename: str

    :param namespace: activity name
    :type namespace: str

    :param instance: activity id
    :type instance: str
    '''

    try:
        with open(filename, 'w') as fp:
            log.debug(f"Writing activity identity to '{filename}'.")
            prod_name = productid_mod.get_productid()['namespace']
            activity = os.environ['ACTIVITY_NAME']
            # IF we get an exception here, nothing will be written
            # Just first item on left is removed since it is the product. The rest is activity name
            json.dump({
                'namespace': activity.replace(prod_name+'/', "") if namespace is None else namespace,
                'instance': os.environ['ACTIVITY_ID'] if instance is None else instance,
            }, fp)
    except:
        # In there was no product identity, then make sure that old entries
        # in the file are removed!!
        try:
            os.unlink(filename)
        except:
            pass


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    ap = argparse.ArgumentParser(description="Show or write values from the productid file used by Cynosure", epilog=__doc__)
    ap.add_argument("-f", "--filename", default=DEFAULT_ACTIVITYID_FILENAME, help="Use this file for persisting values, default is '%(default)s'.")
    rg = ap.add_argument_group('show values')
    rg.add_argument("-r", "--raw", action="store_true", default=False, help="Show the raw values.")
    wg = ap.add_argument_group('write values')
    wg.add_argument('-e', '--environment', action="store_true", default=False, help="Write data from environment $ACTIVITY_ID and $ACTIVITY_NAME.")
    wg.add_argument("-i", "--instance", help="Activity instance (e.g. 'Ifa3416293acf315390987ae94b16f0195ad96526').")
    wg.add_argument("-n", "--namespace", help="Suite Name (namespace) (e.g. 'PBSL15BF417E').")
    args = ap.parse_args(sys.argv[1:])
    if (args.instance and not args.namespace) or (not args.instance and args.namespace):
        ap.error("Both 'instance' and 'namespace' are needed.")
    if args.instance or args.environment:
        if args.environment:
            set_activityid(filename=args.filename)
        else:
            set_activityid(filename=args.filename, namespace=args.namespace, instance=args.instance)
    else:
        activityId = get_activityid(args.filename)
        if activityId is None:
            print(f"The file '{args.filename}' was empty or non-existing.")
        else:
            if args.raw:
                print(activityId)
            else:
                print((f"# contents of '{args.filename}\n"
                    "---\n"
                    f"namespace : {activityId['namespace']}\n"
                    f"instance  : {activityId['instance']}\n"
                    "..."))

# eof
