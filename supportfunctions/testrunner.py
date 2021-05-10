"""
testrunner
"""
import re
import logging
import sys
import importlib
import traceback
from datetime import datetime
from pathlib import Path

from iterfzf import iterfzf

from supportfunctions import analytics
from supportfunctions.dvm import get_reqdata

import test_folder.on_the_fly_test.BSW_Set_ECU_to_default as set_ecu_to_default

log = logging.getLogger('testrunner')

# this need to be fixed
# pylint: disable=too-many-locals, too-many-branches, too-many-statements
def run_tests(
        test_files, use_db=False, use_mq=False, save_result=False,
        reset_between=False):
    """
    run tests from list of tests and optionally log to message bus and/or db
    """
    if save_result:
        analytics.messagehandler(use_db=use_db, use_mq=use_mq)
        analytics.testsuite_started()

        now = datetime.now().strftime("%Y%m%d_%H%M")
        test_res_dir = Path(f"Testrun_{now}_BECM_BT")
        test_res_dir.mkdir(exist_ok=True)
        result_file = test_res_dir.joinpath('Result.txt')

        progress_handler = logging.FileHandler(test_res_dir.joinpath('progress.log'))
        progress_handler.setLevel(logging.CRITICAL)
        progress_handler.setFormatter(logging.Formatter(
            "%(levelname)s %(asctime)s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"))
        logging.getLogger('').addHandler(progress_handler)

    for test_file_py in test_files:
        req_test, reqdata, dut_is_imported = get_reqdata(test_file_py)

        log.critical("Running: %s", test_file_py.name)

        if reqdata['reqprod'] and reqdata['title']:
            test_case_name = f"{reqdata['reqprod']}: {reqdata['title']}"
        else:
            # let's use the filename as the test case name for none dut tests
            test_case_name = test_file_py.name

        combine_steps = not dut_is_imported
        if save_result:
            analytics.testcase_started(test_case_name)
            if combine_steps:
                analytics.teststep_started("combined step")


        if reset_between:
            # this is a bit hacky, but let's keep it for now
            sys.argv = [set_ecu_to_default.__file__]

            # run the reset test script
            try:
                set_ecu_to_default.run()
            except Exception as e: # pylint: disable=broad-except
                logging.critical(
                    "Set ecu to default failed:\n%s", e)
                sys.exit("If we can't reset the ecu, we can't reply on the "
                         "test being correct. Exiting...")

        if save_result:
            log_file = test_res_dir.joinpath(test_file_py.with_suffix('.log').name)
            log_file_handler = logging.FileHandler(log_file)
            log_file_handler.setFormatter(logging.Formatter(" %(message)s"))
            log_file_handler.setLevel(logging.INFO)
            logging.getLogger('').addHandler(log_file_handler)

        # this is a bit hacky, but let's keep it for now
        sys.argv = [str(test_file_py)]
        log.debug(
            "overriding sys.argv to make test specific yaml files load: %s",
            sys.argv)

        spec = importlib.util.spec_from_file_location("req_test", test_file_py)
        req_test = importlib.util.module_from_spec(spec)

        epsmsgbus_testcase_verdict = "unknown"
        try:
            spec.loader.exec_module(req_test)
            req_test.run()
        except Exception as e: # pylint: disable=broad-except
            log.critical("Testcase failed:\n%s", e)
            epsmsgbus_testcase_verdict = "errored"
            log.error("An exception was hit while running the hwtest: \n%s",
                      traceback.format_exc())
            # this should probably be logged as an ERRORED in the result file

        if save_result:
            logging.root.removeHandler(log_file_handler)

            reqprod_match = re.search(r'^e_(\d{5,6})_', test_file_py.name)
            if not reqprod_match:
                sys.exit("Got a test with an incorrect format {test_file_py}")
            reqprod = reqprod_match.group(1)

            # open log file and check for result
            with open(log_file) as log_file_handle:
                # to emulate the bash script that we are replacing we add
                # this to the result file if there is no result. We might
                # want to consider adding an ERRORED state instead, but
                # that will have to come later
                hilding_verdict = ""
                for line in log_file_handle.readlines():
                    match = re.search(r'Testcase result: (.*)', line)
                    if match:
                        hilding_verdict = match.group(1)
                        if hilding_verdict == "PASSED":
                            epsmsgbus_testcase_verdict = "passed"
                        elif hilding_verdict == "FAILED":
                            epsmsgbus_testcase_verdict = "failed"
                        else:
                            epsmsgbus_testcase_verdict = "errored"

                # append to result file
                with open(result_file, mode='a') as result_file_handle:
                    result_file_handle.write(f"{reqprod} {hilding_verdict} {log_file.name}\n")

                log.critical("%s done: hilding_verdict = %s", reqprod, hilding_verdict)

        if save_result:
            if combine_steps:
                analytics.teststep_ended(epsmsgbus_testcase_verdict)
            analytics.testcase_ended(epsmsgbus_testcase_verdict, combine_steps)

    if save_result:
        analytics.testsuite_ended()

        with open(result_file, mode='a') as result_file_handle:
            now = datetime.now().strftime("%Y%m%d %H%M")
            result_file_handle.write(f"Test done. Time: {now}")


def get_automated_files(glob_pattern):
    """ use fzf to select tests to run """
    automated = Path('test_folder/automated')
    files = [str(f) for f in automated.glob(glob_pattern)]
    test_files = iterfzf(files, multi=True)
    return [Path(p) for p in test_files]


def runner(args):
    """ test suite/case runner """
    if args.reqprod:
        test_files = get_automated_files(f"*{args.reqprod}*.py")
    else:
        # see if we can find a reqprod number in current branch (that is, if
        # the branch is named like req_60112 or BSW_REQPROD_60112)
        branch_name_reqprod = None
        try:
            # pylint: disable=import-outside-toplevel
            from pygit2 import Repository
            repo = Repository('.')
            branch_name_reqprod = re.findall(r'\d{5,6}', repo.head.shorthand)
        except ImportError:
            pass

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
