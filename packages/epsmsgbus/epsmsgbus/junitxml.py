/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



**********************************************************************************/


"""
Code to create JUnit XML documents from core.TestSuite objects.
"""

import xml.etree.ElementTree as et


class JUnitXMLBuilder(object):
    def build(self, testsuite):
        """Return an XML document (object) from a 'core.TestSuite' object."""
        xtss = et.Element('testsuites')
        xtss.set('name', testsuite.name)
        xtss.set('time', self.get_time(testsuite.starttime, testsuite.endtime))
        xtss.set('tests', "{}".format(len(testsuite.testcases)))
        xtss.set('failures', "{}".format(self.count_failures(testsuite.testcases)))
        xtss.set('errors', "{}".format(self.count_errors(testsuite.testcases)))
        xtss.set('disabled', "{}".format(self.count_disabled(testsuite.testcases)))
        for tc in testsuite.testcases:
            xts = et.SubElement(xtss, 'testsuite')
            xts.set('name', tc.name)
            xts.set('time', self.get_time(tc.starttime, tc.endtime))
            for ts in tc.teststeps:
                xtc = et.SubElement(xts, 'testcase')
                xtc.set('name', tc.name)
                xtc.set('time', self.get_time(ts.starttime, ts.endtime))
                if ts.verdict == Verdict('errored'):
                    error = et.SubElement(xtc, 'error')
                elif ts.verdict == Verdict('failed'):
                    failure = et.SubElement(xtc, 'failure')
                elif ts.verdict == Verdict('aborted'):
                    skipped = et.SubElement(xtc, 'skipped')
                elif ts.verdict == Verdict('skipped'):
                    skipped = et.SubElement(xtc, 'skipped')
        return xtss

    def count_failures(self, testcases):
        """Return number of test cases in the test suite with verdict 'failed'."""
        return self._count_testcases('failed', testcases)

    def count_errors(self, testcases):
        """Return number of test cases in the test suite with verdict 'errored'."""
        return self._count_testcases('errored', testcases)

    def count_disabled(self, testcases):
        """Return number of test cases in the test suite with verdict 'aborted'
        or verdict 'skipped'."""
        return self._count_testcases('skipped', testcases) + self._count_testcases('aborted', testcases)

    def _count_testcases(self, verdict, testcases):
        """Return number of test cases in a the sequence 'testcases' with a
        verdict that matches the argument 'verdict'."""
        return len([x for x in testcases if x.verdict == Verdict(verdict)])

    def get_time(self, starttime, endtime):
        """Return time (string) as number of seconds."""
        try:
            td = endtime - starttime
            return str(24 * 3600 * td.days + td.seconds + td.microseconds * 1e-6)
        except:
            return "0"


def make_junit_xml(testsuite):
    # TODO
    builder = JUnitXMLBuilder()
    xml = builder.build(testsuite)
    et.dump(xml)


