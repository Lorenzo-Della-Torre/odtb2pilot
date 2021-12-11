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

from hilding import analytics
from hilding.reset_ecu import reset_and_flash_ecu



log = logging.getLogger('testrunner')


def get_test_res_dir(fmt="%Y%m%d_%H%M"):
    """
    get test result directory for storing logs and Result.txt

    can be called be called multiple time, but will always return a directory
    based on the first invocation
    """
    global _TEST_RES_DIR # pylint: disable=global-statement
    if not _TEST_RES_DIR:
        now = datetime.now().strftime(fmt)
        _TEST_RES_DIR = Path(f"Testrun_{now}_BECM_BT")
        _TEST_RES_DIR.mkdir(exist_ok=True)
    return _TEST_RES_DIR
_TEST_RES_DIR = None


def configure_progress_log(test_res_dir):
    """ this log can be used to view the progress of the test suite """
    progress_handler = logging.FileHandler(test_res_dir.joinpath('progress.log'))
    progress_handler.setLevel(logging.INFO)
    progress_handler.setFormatter(logging.Formatter(
        "%(levelname)s %(asctime)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"))
    logging.getLogger('testrunner').addHandler(progress_handler)


def parse_test_file_name(test_file_py):
    """ return a dictionary with reqprod, variant, revision, and description """
    reqprod_match = re.search(
        r'^e_(?P<reqprod>\d+)_(?P<variant>[a-zA-Z]*)_' +
        r'(?P<revision>\d+)_(?P<description>.*).py$', test_file_py.name)
    if not reqprod_match:
        sys.exit(f"Got a test with an incorrect format {test_file_py}")
    return reqprod_match.groupdict()


def get_test_case_name(test_file_py):
    """ parse file name and compose test case name """
    t = parse_test_file_name(test_file_py)
    # it might seem a bit silly to basically recreate the filename again, but
    # let's keep it like this until we have settled on a good way to name our
    # testcases using epsmsgbus and epsdb
    return f"e_{t['reqprod']}_{t['variant']}_{t['revision']}_{t['description']}"


def fake_argv_filename(test_file_py):
    """
    this is a bit hacky, but let's keep it for now as we rely on it.
    better would be to remove the dependence on .yml file based monkey
    patching
    """
    sys.argv = [str(test_file_py)]
    log.debug(
        "overriding sys.argv to make test specific yaml files load: %s",
        sys.argv)


def configure_log_file_handler(test_file_py):
    """ configure log file handler """
    test_res_dir = get_test_res_dir()
    log_file = test_res_dir.joinpath(test_file_py.with_suffix('.log').name)
    log_file_handler = logging.FileHandler(log_file)
    log_file_handler.setFormatter(logging.Formatter(" %(message)s"))
    log_file_handler.setLevel(logging.INFO)
    logging.getLogger('').addHandler(log_file_handler)
    return log_file, log_file_handler


def run_test(test_file_py):
    """
    run the test module and catch any exceptions in order for the test suite to
    continue with faulty test
    """
    fake_argv_filename(test_file_py)
    spec = importlib.util.spec_from_file_location("req_test", test_file_py)
    module = importlib.util.module_from_spec(spec)
    verdict = "unknown"
    try:
        spec.loader.exec_module(module)
        if 'run' in dir(module):
            module.run()
    except Exception as e: # pylint: disable=broad-except
        log.critical("Testcase failed:\n%s", e)
        verdict = "errored"
        log.error("An exception was hit while running the ecutest: \n%s",
                  traceback.format_exc())
        # should probably be logged as ERRORED in Result.txt
    return verdict


def run_test_and_parse_log_to_result(test_file_py, result_file):
    """ create a test specific log, run the test, and parse the result """
    log.info("Running: %s", test_file_py.name)
    log_file, log_file_handler = configure_log_file_handler(test_file_py)
    verdict = run_test(test_file_py)
    logging.root.removeHandler(log_file_handler)
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
                    verdict = "passed"
                elif hilding_verdict == "FAILED":
                    verdict = "failed"
                elif hilding_verdict.startswith(("Not applicable",
                                                 "To be inspected",
                                                 "Tested implicitly")):
                    verdict = "unknown"
                else:
                    verdict = "errored"

        reqprod = parse_test_file_name(test_file_py)['reqprod']
        # append to result file
        with open(result_file, mode='a') as result_file_handle:
            result_file_handle.write(f"{reqprod} {hilding_verdict} {log_file.name}\n")
        log.info("%s done: hilding_verdict = %s", reqprod, hilding_verdict)

    return verdict


def run_reset_between():
    """
    this is to make sure that each test are not affected by the previous test
    """
    # run the reset test script
    try:
        reset_and_flash_ecu()
    except Exception as e: # pylint: disable=broad-except
        logging.critical(
            "Set ecu to default failed:\n%s", e)
        sys.exit("If we can't reset the ecu, we can't reply on the "
                 "test being correct. Exiting...")


def add_testsuite_endtime(result_file):
    """ at the end of the Results.txt file we add the end time"""
    with open(result_file, mode='a') as result_file_handle:
        now = datetime.now().strftime("%Y%m%d %H%M")
        result_file_handle.write(f"Test done. Time: {now}\n")


def run_tests(test_files):
    """ run tests without saving any results """
    for test_file_py in test_files:
        run_test(test_file_py)


def run_tests_and_save_results(test_files, use_db=False, use_mq=False,
                               reset_between=False):
    """
    run tests from list of tests and save to message bus and/or db
    """

    analytics.messagehandler(use_db=use_db, use_mq=use_mq)
    analytics.testsuite_started()

    test_res_dir = get_test_res_dir()
    result_file = test_res_dir.joinpath('Result.txt')
    configure_progress_log(test_res_dir)

    for test_file_py in test_files:
        if reset_between:
            run_reset_between()

        test_case_name = get_test_case_name(test_file_py)
        analytics.testcase_started(test_case_name)
        verdict = run_test_and_parse_log_to_result(test_file_py, result_file)
        analytics.testcase_ended(verdict)

    analytics.testsuite_ended()
    add_testsuite_endtime(result_file)


def get_ecutest_files(glob_pattern):
    """ use fzf to select tests to run """
    ecutest_dir = Path(__file__).parent.parent.joinpath("test_folder")
    files = [str(f) for f in ecutest_dir.glob(glob_pattern)]
    test_files = iterfzf(files, multi=True)
    if not test_files:
        sys.exit(f"ecutest selection was terminated or\n"
                 f"{glob_pattern} couldn't be found in {ecutest_dir}")
    return [Path(p) for p in test_files]


def runner(args):
    """ test suite/case runner """
    if args.reqprod:
        file_name_fragment = args.reqprod.rstrip('.py')
        test_files = get_ecutest_files(f"*/*{file_name_fragment}*.py")
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
                test_files = get_ecutest_files(f"*/*{reqprod}*.py")
        else:
            # current git branch does not match so let's do a interactive fuzzy
            # select from all available automated tests
            test_files = get_ecutest_files("*/*.py")

    if args.save_result:
        run_tests_and_save_results(
            test_files, args.use_db, args.use_mq, args.reset_between)
    else:
        run_tests(test_files)


def nightly(args):
    """ run the nighly test from list """
    with open(args.testfile_list) as testfile_list:
        test_files = [Path(t.strip()) for t in testfile_list.readlines()]
        run_tests_and_save_results(
            test_files, args.use_db, args.use_mq, reset_between=True)
