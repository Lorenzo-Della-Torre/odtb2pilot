"""
testrunner
"""
import re
import logging
import sys
import importlib
from datetime import datetime
from pathlib import Path

from pygit2 import Repository
from pyfzf.pyfzf import FzfPrompt

from supportfunctions import analytics
from supportfunctions.dvm import get_reqdata

from test_folder.on_the_fly_test.BSW_Set_ECU_to_default import run as set_ecu_to_default

# this need to be fixed
# pylint: disable=too-many-locals, too-many-branches, too-many-statements
def run_tests(
        test_files, use_db=False, use_mq=False, save_result=False,
        reset_between=False):
    """
    run tests from list of tests and optionally log to message bus and/or db
    """
    analytics.messagehandler(use_db=use_db, use_mq=use_mq)
    analytics.testsuite_started()

    if save_result:
        now = datetime.now().strftime("%Y%m%d_%H%M")
        test_res_dir = Path(f"Testrun_{now}_BECM_BT")
        test_res_dir.mkdir(exist_ok=True)
        result_file = test_res_dir.joinpath('Result.txt')

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

        if reset_between:
            # run a reset test script
            set_ecu_to_default()

        if save_result:
            log_file = test_res_dir.joinpath(test_file_py.with_suffix('.log').name)
            log_file_handler = logging.FileHandler(log_file)
            log_file_handler.setFormatter(logging.Formatter(" %(message)s"))
            log_file_handler.setLevel(logging.INFO)
            logging.root.addHandler(log_file_handler)

        spec = importlib.util.spec_from_file_location("req_test", test_file_py)
        req_test = importlib.util.module_from_spec(spec)

        try:
            spec.loader.exec_module(req_test)
            req_test.run()
        except: # pylint: disable=bare-except
            logging.critical("Testcase failed: %s", sys.exc_info()[0])
            analytics.testcase_ended("errored", combine_steps=(not dut_is_imported))
            # this should probably be logged as an ERRORED in the result file

        if save_result:
            logging.root.removeHandler(log_file_handler)

            reqprod_match = re.search(r'^e_(\d{5,6})_', test_file_py.name)
            if not reqprod_match:
                sys.exit("Got a test with an incorrect format {test_file_py}")
            reqprod = reqprod_match.group(1)

            # open log file and check for result
            with open(log_file) as log_file_handle:
                for line in log_file_handle.readlines():
                    match = re.search(r'Testcase result: (.*)', line)

                # to emulated the bash script that we are replacing we add
                # this to the result file if there is no result. We might
                # want to consider adding an ERRORED state instead, but
                # that will have to come later
                result = ""
                if match:
                    result = match.group(1)

                # append to result file
                with open(result_file, mode='a') as result_file_handle:
                    result_file_handle.write(f"{reqprod} {result} {log_file.name}\n")

    if save_result:
        with open(result_file, mode='a') as result_file_handle:
            now = datetime.now().strftime("%Y%m%d %H%M")
            result_file_handle.write(f"Test done. Time: {now}")

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

    run_tests(
        test_files, args.use_db, args.use_mq, args.save_result,
        args.reset_between)

def nightly(args):
    """ run the nighly test from list """
    with open(args.testfile_list) as testfile_list:
        test_files = [Path(t.strip()) for t in testfile_list.readlines()]
        run_tests(
            test_files, args.use_db, args.use_mq, save_result=True,
            reset_between=True)
