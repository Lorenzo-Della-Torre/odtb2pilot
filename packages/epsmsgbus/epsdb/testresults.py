"""
/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

#!/bin/env python
"""
Print out test results to console.
"""

import argparse
import logging
import sys

import epsdb

from collections import namedtuple


QUERY = ("SELECT u.pkey, u.name, u.start_time, u.end_time, u.verdict as suite_result,"
        "u.status, u.ecu, t.name as testcase_name, t.verdict as tc_result,"
        "s.name as teststep_name, s.verdict as ts_result"
        " FROM testsuite_result u, testcase_result t, teststep_result s"
        " WHERE u.pkey = t.testsuite_result"
        "    AND s.testsuite_result = u.pkey"
        "    AND s.testcase_result = t.pkey"
        "    AND u.pkey IN (SELECT {top} pkey"
        "        FROM testsuite_result"
        "        {where}"
        "        ORDER BY start_time DESC)"
        " ORDER BY u.start_time DESC, t.start_time ASC, s.start_time ASC")
resultrec = namedtuple("result", ('uuuid', 'uname', 'ustart', 'uend', 'uverdict', 'ustatus', 'uecu',
    'tname', 'tverdict', 'sname', 'sverdict'))


class ResultPrinter(object):

    tsuite1_t = "[{0.ustatus}] {0.uverdict:<10} {0.uecu:<4}  {0.uname}"
    tsuite2_t = "    ({0.ustart}/{0.uend})"
    tsuite3_t = "    {0.uuuid}"
    tcase_t = "    [{1:03d}] {0.tverdict:<10} {0.tname}"
    tstep_t = "        [{2:03d}] {0.sverdict:<10} {0.sname}"

    def __init__(self, name=None, ecu=None, last=None, where=None, short=False):
        self.where = '' if where is None else where
        self.top = '' if last is None else 'TOP({})'.format(last)
        if not where:
            if not name is None:
                self.where = " name = '%s' " % name
            if not ecu is None:
                self.where +=  (" pkey IN (SELECT testsuite_result"
                                "          FROM runtime_data"
                                "          WHERE (attribute = 'system_ecu' AND value = '{0}')"
                                "                OR"
                                "                (attribute = 'model_ecu' AND value = '{0}' ))").format(ecu)
        if len(self.where) > 0:
            self.where = "WHERE {}".format(self.where)
        self.short = short

    def printout(self):
        tsuite = tcase = tstep = None
        tcasec = 1
        tstepc = 1
        with epsdb.DatabaseContext() as db:
            results = db.sql(QUERY.format(top=self.top, where=self.where)).fetchall()
            for result in results:
                z = []
                for col in result:
                    z.append(col)
                rec = resultrec(*z)
                if rec.uuuid != tsuite:
                    tcasec = 1
                    tstepc = 1
                    self.print_testsuite(rec)
                    self.print_runtimedata(db, rec.uuuid)
                    self.print_testcase(rec, tcasec)
                    self.print_teststep(rec, tcasec, tstepc)
                    tsuite = rec.uuuid
                    tcase = rec.tname
                    tstep = rec.sname
                elif rec.tname != tcase:
                    tcasec += 1
                    tstepc = 1
                    self.print_testcase(rec, tcasec)
                    self.print_teststep(rec, tcasec, tstepc)
                    tcase = rec.tname
                    tstep = rec.sname
                elif rec.sname != tstep:
                    tstepc += 1
                    self.print_teststep(rec, tcasec, tstepc)
                    tstep = rec.sname

    def print_runtimedata(self, db, uuid):
        if self.short:
            return
        results = db.sql('SELECT attribute, value FROM runtime_data WHERE testsuite_result = ?', uuid)
        for attr, val in results.fetchall():
            print("    ++  {} = {}".format(attr, val))

    def print_testsuite(self, rec):
        print(self.tsuite1_t.format(rec))
        print(self.tsuite2_t.format(rec))
        print(self.tsuite3_t.format(rec))

    def print_testcase(self, rec, tcnum):
        print(self.tcase_t.format(rec, tcnum))

    def print_teststep(self, rec, tcnum, tsnum):
        if self.short:
            return
        print(self.tstep_t.format(rec, tcnum, tsnum))


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description="Print out test results from database.")
    ap.add_argument('-d', '--debug', action="store_true", default=False, help="Print out debug messages.")
    ap.add_argument('-s', '--short', action="store_true", default=False, help="Skip printing test steps and runtime_data.")
    ap.add_argument('--name', help="Filter on test suite name.")
    ap.add_argument('--ecu', help="Filter on ecu name.")
    ap.add_argument('-l', '--last', type=int, help="Only show the last number of entries.")
    ap.add_argument('where', nargs="*", help="where statement.")
    args = ap.parse_args(sys.argv[1:])
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)
    ResultPrinter(name=args.name, ecu=args.ecu, last=args.last, where=' '.join(args.where), short=args.short).printout()

# eof
