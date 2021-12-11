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
Command line utilities for database API.
"""

import argparse
import glob
import json
import logging
import os
import sys

from . import core


log = logging.getLogger('epsdb.main')


def main(argv=None):
    """Parse arguments and store messages from JSON files."""
    if argv is None:
        argv = sys.argv[1:]
    logging.basicConfig(level=logging.INFO)
    ap = argparse.ArgumentParser(prog="epsdb", description="Store data from Cynosure messages in the database or perform administrative tasks.")
    ap.add_argument("-d", "--debug", action="store_true", default=False, help="Print out debug messages.")
    cg = ap.add_argument_group("Connection options")
    cg.add_argument("--database-type", choices=("MSSQL", "SQLITE"), help="Database type.")
    cg.add_argument("--database-connect", help="Database connection strings.")
    tg = ap.add_argument_group("Diagnostics")
    tg.add_argument("--connection-test", action="store_true", default=False, help="Check that the database connection is OK.")
    tg.add_argument("--check-config", action="store_true", default=False, help="Print out the current database configuration and leave.")
    dg = ap.add_argument_group("Create/Drop tables in SQLite database")
    dgg = dg.add_mutually_exclusive_group()
    dgg.add_argument("--init", action="store_true", default=False, help="Initialize the SQLite database with tables and catalog data.")
    dgg.add_argument("--drop", action="store_true", default=False, help="Drop all tables. Warning, be careful! All existing data will be destroyed.")
    ap.add_argument("files", nargs="*", help="Data file(s) in JSON format to read and store.")
    args = ap.parse_args(argv)
    if args.debug:
        log.setLevel(logging.DEBUG)
    if args.database_type:
        core.set_config(dbtype=args.database_type)
    if args.database_connect:
        core.set_config(connstr=[args.database_connect])
    if args.connection_test:
        with core.DatabaseContext() as db:
            try:
                db.sql("SELECT count(*) FROM testcase_result")
                log.info("Connection test succeed.")
            except Exception as e:
                log.error(e)
                log.debug("TRACE", exc_info=True)
                raise
    if args.check_config:
        print("Enabled        : {}".format(core.CONFIG.enabled))
        print("Database type  : {}".format(core.CONFIG.dbtype))
        print("Connect strings:")
        i = 1
        for item in core.CONFIG.connstr:
            print(' - {:>2d} : "{}"'.format(i, item))
            i += 1
    if core.CONFIG.dbtype == 'SQLITE':
        dbfile = ''.join(core.CONFIG.connstr)
        if args.init:
            if os.path.exists(dbfile):
                log.error("The database file '%s' already exists, aborting.", dbfile)
                sys.exit(2)
            else:
                log.debug("Creating database in file '%s'.", dbfile)
                core.init()
        elif args.drop:
            ans = None
            while ans not in  ('y', 'n'):
                ans = input("All data in '%s' will be destroyed. Do you really wnat to continue? [y/N]" % dbfile)
                ans = ans.lower()
            if ans == 'y':
                log.info("Dropping tables")
                core.admin().drop_tables()
                log.info("Finished")
            else:
                log.info("Aborted on user's request.")
    else:
        log.error("Administrative tasks are only allowed for SQLite databases.")
    if args.files:
        for filearg in args.files:
            for filename in glob.glob(filearg):
                with open(filename) as fp:
                    store_message(json.loads(fp.read()))


# __main__ ==============================================================={{{1
if __name__ == '__main__':
    main()


# modeline ==============================================================={{{1
# vim: set fdm=marker:
# eof
