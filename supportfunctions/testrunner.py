"""
testrunner
"""
import re
import logging
import sys
import importlib
from pathlib import Path

from pygit2 import Repository
from pyfzf.pyfzf import FzfPrompt

from supportfunctions import analytics
from supportfunctions.dvm import get_reqdata


def run_tests(test_files, use_db=False, use_mq=False):
    """
    run tests from list of tests and optionally log to message bus and/or db
    """
    analytics.messagehandler(use_db=use_db, use_mq=use_mq)
    analytics.testsuite_started()
    for test_file_py in test_files:
        req_test, reqdata, dut_is_imported = get_reqdata(test_file_py)

        if reqdata['reqprod'] and reqdata['title']:
            test_case_name = f"{reqdata['reqprod']}: {reqdata['title']}"
        else:
            # let's use the filename as the test case name for none dut tests
            test_case_name = test_file_py.name

        analytics.testcase_started(test_case_name)

        if not dut_is_imported:
            analytics.teststep_started("combined step")

        # this is a bit hacky, but let's keep it for now
        sys.argv = [str(test_file_py)]
        logging.debug(
            "overriding sys.argv to make test specific yaml files load: %s",
            sys.argv)

        spec = importlib.util.spec_from_file_location("req_test", test_file_py)
        req_test = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(req_test)
        req_test.run()

    analytics.testsuite_ended()

def get_automated_files(glob_pattern):
    """ use fzf to select tests to run """
    fzf = FzfPrompt()
    automated = Path('test_folder/automated')
    test_files = fzf.prompt(automated.glob(glob_pattern), "--multi")
    return [Path(p) for p in test_files]

def runner(args):
    """ test suite/case runner """
    if args.reqprod:
        test_files = get_automated_files(f"*{args.reqprod}*.py")
    else:
        # see if we can find a reqprod number in current branch (that is, if
        # the branch is named like req_60112 or BSW_REQPROD_60112)
        repo = Repository('.')
        branch_name_reqprod = re.findall(r'\d{5,6}', repo.head.shorthand)
        if branch_name_reqprod:
            for reqprod in branch_name_reqprod:
                test_files = get_automated_files(f"*{reqprod}*.py")
        else:
            # current git branch does not match so let's do a interactive fuzzy
            # select from all available automated tests
            test_files = get_automated_files("*.py")

    run_tests(test_files, args.use_db, args.use_mq)
