"""
testrunner

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""
import re
import logging
import sys
import importlib
import traceback
from datetime import datetime
from pathlib import Path
import yaml

from iterfzf import iterfzf

from hilding import analytics
from hilding.reset_ecu import reset_and_flash_ecu
from hilding.uds import UdsEmptyResponse

from autotest.blacklisted_tests_handler import add_to_result, create_logs, get_dictionary_from_yml
#from supportfunctions.support_relay import Relay


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
        r'(?P<file_name>[a-zA-Z0-9_]*).py-->' +
        r'(?P<tool>[a-zA-Z]*)_(?P<reqprod>\d+)_(?P<variant_revision>[a-zA-Z0-9_]*)$', test_file_py)
    if not reqprod_match:
        sys.exit(f"Got a test with an incorrect format {test_file_py}")
    return reqprod_match.groupdict()


def get_test_case_name(test_file_py):
    """ parse file name and compose test case name """
    t = parse_test_file_name(test_file_py)
    # it might seem a bit silly to basically recreate the filename again, but
    # let's keep it like this until we have settled on a good way to name our
    # testcases using epsmsgbus and epsdb
    return f"{t['tool']}_{t['reqprod']}_{t['variant_revision']}"


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
    log_file = test_res_dir.joinpath(Path(test_file_py.replace(".py-->", "--_--"))
                                                            .with_suffix('.log').name)
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
    except UdsEmptyResponse:
        log.error("Aborting the test.........")
    except Exception as e: # pylint: disable=broad-except
        log.critical("Testcase failed:\n%s", e)
        verdict = "errored"
        log.error("An exception was hit while running the ecutest: \n%s",
                  traceback.format_exc())
        # should probably be logged as ERRORED in Result.txt
    return verdict


def run_test_and_parse_log_to_result(test_file_py, result_file):
    """ create a test specific log, run the test, and parse the result """
    log.info("Running: %s", Path(test_file_py).name)
    log_file, log_file_handler = configure_log_file_handler(test_file_py)
    verdict = run_test(Path(test_file_py.split("-->")[0]))
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
                                                 "Tested in dSpace HIL",
                                                 "Modified VBF needed",
                                                 "SecOC not implemented",
                                                 "MANUAL",
                                                 "For diagnostic responsible",
                                                 "For application teams",
                                                 "This is a design requirement",
                                                 "This requirement needs a deviation",
                                                 "Excluded",
                                                 "Tested implicitly")):
                    verdict = "unknown"
                else:
                    verdict = "errored"

        entry = parse_test_file_name(test_file_py)
        requirement = f"{entry['tool']}_{entry['reqprod']}_{entry['variant_revision']}"
        # append to result file
        with open(result_file, mode='a') as result_file_handle:
            result_file_handle.write(f"{requirement} {hilding_verdict} {log_file.name}\n")
        log.info("%s done: hilding_verdict = %s", entry['reqprod'], hilding_verdict)

    return verdict


def run_reset_between():
    """
    this is to make sure that each test are not affected by the previous test
    """
    # run the reset test script
    try:
        reset_and_flash_ecu()
    except Exception as e: # pylint: disable=broad-except
        logging.critical("Run reset between scripts failed. Reason : \n%s", e)

def add_testsuite_endtime(result_file):
    """ at the end of the Results.txt file we add the end time"""
    with open(result_file, mode='a') as result_file_handle:
        now = datetime.now().strftime("%Y%m%d %H%M")
        result_file_handle.write(f"Test done. Time: {now}\n")

def global_verdict_file(result_file):
    """ Create a file that specify the global verdict
        This file is only used by the ci
    """
    with open(result_file) as file:
        lines = [line.rstrip() for line in file]
    global_verdict = "PASSED"

    # check all verdicts in Result.txt file
    for req in lines:
        verdict = req.split()[1]
        if verdict != "PASSED":
            # result is failed if anything but PASSED
            global_verdict = "FAILED"
            break
    filename = "global_verdict_"+global_verdict+".txt"
    # create the empty txt file
    open(result_file.parent.absolute().joinpath(filename),'a').close()

def run_tests(test_files):
    """ run tests without saving any results """
    for test_file_py in test_files:
        run_test(test_file_py)


def run_tests_and_save_results(test_files, result_dir, use_db=False, use_mq=False,
                               reset_between=False):
    """
    run tests from list of tests and save to message bus and/or db
    """

    analytics.messagehandler(use_db=use_db, use_mq=use_mq)
    analytics.testsuite_started()

    configure_progress_log(result_dir)

    for test_file_py in test_files:
        if reset_between:
            run_reset_between()

        test_case_name = get_test_case_name(test_file_py)
        analytics.testcase_started(test_case_name)
        verdict = run_test_and_parse_log_to_result(test_file_py, result_dir.joinpath('Result.txt'))
        analytics.testcase_ended(verdict)

    analytics.testsuite_ended()


def get_ecutest_files(file_dict, reqprod):
    """ use fzf to select tests to run """
    files = []
    ecutest_dir = Path(__file__).parent.parent.joinpath("test_folder")
    for key, value in file_dict.items():
        files_temp = [str(f) for f in ecutest_dir.glob(f"*/*{key}.py")]
        if len(files_temp) != 0:
            files.append(files_temp[0]+ "----->"+value)

    if reqprod.endswith(".py"):
        test_files = [str(f) for f in ecutest_dir.glob(f"*/*{reqprod}")]
    elif len(files) == 1:
        test_files = files
    else:
        test_files = iterfzf(files, multi=True)

    # If the file is not found in the mapping file,
    # search the keyword in the test_folder folder.
    if not test_files:
        file_name_fragment = reqprod.rstrip('.py')
        test_files = get_testfiles_generic(f"*/*{file_name_fragment}*.py")
        return test_files

    return [Path(p.split("----->")[0]) for p in test_files]


def get_testfiles_generic(glob_pattern):
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

    logging.debug(args)
    if args.reqprod:
        file_name_list = script_picker(args.reqprod)
        test_files = get_ecutest_files(file_name_list, args.reqprod)
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
                test_files = get_testfiles_generic(f"*/*{reqprod}*.py")
        else:
            # current git branch does not match so let's do a interactive fuzzy
            # select from all available automated tests
            test_files = get_testfiles_generic("*/*.py")

    if args.save_result:
        run_tests_and_save_results(
            test_files, args.use_db, args.use_mq, args.reset_between)
    else:
        run_tests(test_files)


def nightly(args):
    """This function runs the nightly tests.
    The list that is used to pick tests in passed as an argument to this function.
    The every line in the list might contain a path to a test or data about a
    black listed requirement.

    The list must have the following structure:

    <path_to_script>
    <path_to_script>
    <path_to_script>
    --Category1--
    <info_about_requirement_of_type_category1>
    <info_about_requirement_of_type_category1>
    --Category2--
    <info_about_requirement_of_type_category2>

    Args:
        args (list): A list containing paths and data about black listed requirements
    """

    test_res_dir = get_test_res_dir()
    result_file = test_res_dir.joinpath('Result.txt')
    with open(args.testfile_list) as testfile_list:
        test_files = []
        blacklisted_reqprods = {}
        # This will keep track of what category of reqs. we are currently
        # dealing with (NA, Implicit, etc.)
        current_category = ""
        # Read from yml file what categories we have in the current default project
        if get_dictionary_from_yml() is not None:
            existing_categories = get_dictionary_from_yml().keys()
        else:
            existing_categories = {}
        for line in testfile_list.readlines():
            stripped_line = line.strip()
            if stripped_line in existing_categories:
                current_category = stripped_line
                blacklisted_reqprods[current_category] = {}
            elif current_category == "":
                test_files.append(stripped_line)
            else:
                split_line = stripped_line.split("|", maxsplit=1)
                reqprod_id = split_line[0]
                info = split_line[1]
                blacklisted_reqprods[current_category][reqprod_id] = info

    add_to_result(blacklisted_reqprods, result_file)
    create_logs(blacklisted_reqprods, test_res_dir)

    run_tests_and_save_results(
        test_files, test_res_dir, args.use_db, args.use_mq, reset_between=True)

    add_testsuite_endtime(result_file)
    # create an empty txt file with the global verdict as name
    global_verdict_file(result_file)

def relay(relay_state):
    """ Trigger relay """
#    rel = Relay()
#    success = 0
#    if relay_state == "on":
#        success = rel.ecu_on()
#    elif relay_state == "off":
#        success = rel.ecu_off()
#    elif relay_state == "reset":
#        logging.info("Waiting 5 seconds between ECU OFF and ON")
#        success = rel.ecu_off()
#        time.sleep(5)
#        success = success and rel.ecu_on()
#    elif relay_state == "toggle":
#        success = rel.toggle_power()
#    else:
#        logging.error(" ** Relay command not correct **")
#        logging.error(" ** Please use on/off/reset/toggle only **")
#
#    if success == 1:
#        logging.info("Success")
#    else:
#        logging.info("Not Success")
    logging.info("relay support currently under development")
    logging.info("wanted to set relay to state: %s", relay_state)

def script_picker(reqprod):
    """
    This function returns the script name from the script mapping
    file by taking the reqprod ID as input.
    """

    script = {}
    with open('req_script_mapping.yml') as mapping_file:
        mapping_dict = yaml.safe_load(mapping_file)

    for key, value in mapping_dict.items():
        if reqprod in value:
            for req in value.split(" "):
                if reqprod in req:
                    script[key] = req

    return script
