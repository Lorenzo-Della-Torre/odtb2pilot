"""
HTML did report generator
"""
import time
import logging
import platform
import traceback
from datetime import datetime
from collections import Counter
from pathlib import Path
from pprint import pformat

from jinja2 import Environment
from jinja2 import FileSystemLoader

from build import did

from hilding.dut import Dut
from hilding.uds import EicDid
from hilding.uds import IoSssDid
from hilding.uds import UdsEmptyResponse
from hilding.sddb import write
from hilding.sddb import quotify
from hilding import get_conf

log = logging.getLogger('did_report')


def get_ecu_content(dut: Dut):
    """ get data from the ecu """
    part_numbers_res = dut.uds.read_data_by_id_22(
        EicDid.complete_ecu_part_number_eda0)
    log.info(part_numbers_res)
    git_hash_res = dut.uds.read_data_by_id_22(
        IoSssDid.git_hash_f1f2)
    log.info(git_hash_res)
    write_to_testrun_data_file(git_hash_res, part_numbers_res)

    did_counter = Counter(
        passed=0,
        failed=0,
        conditions_not_correct=0,
        request_out_of_range=0
    )
    app_dids = []
    for did_id, _ in did.app_did_dict.items():
        details = get_did_details(dut, did_id, did_counter)
        if details:
            app_dids.append(details)
    dut.uds.set_mode(mode=2)
    pbl_dids = []
    for did_id, _ in did.pbl_did_dict.items():
        details = get_did_details(dut, did_id, did_counter)
        if details:
            pbl_dids.append(details)
    dut.uds.enter_sbl()
    sbl_dids = []
    for did_id, _ in did.sbl_did_dict.items():
        details = get_did_details(dut, did_id, did_counter)
        if details:
            sbl_dids.append(details)

    content = {}
    content['part_numbers'] = part_numbers_res.details
    content['git_hash'] = git_hash_res.details
    content['app_dids'] = app_dids
    content['pbl_dids'] = pbl_dids
    content['sbl_dids'] = sbl_dids
    content['did_counter'] = did_counter

    return content


def write_to_testrun_data_file(git_hash_res, part_numbers_res):
    """
    provide data in the build dir to the logs_to_html script

    due to this setup, the did_report always need to run before the
    logs_to_html script.
    """
    conf = get_conf()
    testrun_data_file = conf.rig.build_path.joinpath('testrun_data.py')
    git_hash = 'no git hash available'
    if 'response_items' in git_hash_res.details:
        response_items = git_hash_res.details['response_items']
        if len(response_items) > 0:
            first_response_item = response_items[0]
            if 'scaled_value' in first_response_item:
                git_hash = quotify(first_response_item['scaled_value'])

    write(testrun_data_file, "git_hash", git_hash, "w")
    eda0 = {}
    details = part_numbers_res.details
    for eda0_did in ['F120', 'F12A', 'F12B', 'F18C']:
        if eda0_did in details:
            value = details.get(eda0_did + '_valid', details[eda0_did])
            eda0[details[eda0_did + '_info']['name']] = value
    write(testrun_data_file, "eda0_dict", pformat(eda0), "a")


def get_did_details(dut, did_id, did_counter):
    """ get relevant did details as a dictionary """
    # give the ecu some time to get ready for the next did request
    time.sleep(2)
    try:
        res = dut.uds.read_data_by_id_22(bytes.fromhex(did_id))
    except UdsEmptyResponse:
        return None
    log.info(res)
    details = res.details
    details['did_called'] = did_id
    if 'nrc_name' in res.data:
        nrc_name = res.data['nrc_name']
        nrc = res.data['nrc']
        did_counter['failed'] += 1
        # maybe we should collect all negative response code names, not
        # just the two we have here
        if nrc_name == "requestOutOfRange":
            did_counter['request_out_of_range'] += 1
        elif nrc_name == "conditionsNotCorrect":
            did_counter['conditions_not_correct'] += 1
        details['error_message'] = f"Negative response: {nrc_name} ({nrc})"
        return details

    details['sid_match'] = 'sid' in res.data
    details['did_match'] = did_id == res.data.get('did')

    size_match = False
    if 'size' in res.details and 'item' in res.details:
        expected_size = int(res.details['size'])
        actual_size = len(res.details['item']) // 2 # two nibbles per byte
        if expected_size == actual_size:
            size_match = True
        else:
            details['error_message'] = \
                f"Size wrong. Expected {expected_size} but was {actual_size}"
    details['size_match'] = size_match

    did_counter['passed'] += 1
    return details


def create_report(content):
    """ create the report """
    style = ""
    templates = Path(__file__).parent.joinpath("templates")
    with open(templates.joinpath("style.css").resolve()) as style_css:
        style = style_css.read()

    content['style'] = style
    content['hostname'] = platform.node()
    content['report_generated'] = datetime.now().strftime("%Y-%m-%d %H:%M")
    content['sddb_app_diag_part_num'] = did.app_diag_part_num.replace('_', ' ')

    file_loader = FileSystemLoader([templates.resolve()])
    env = Environment(loader=file_loader)
    template = env.get_template('did_report.jinja')
    output = template.render(content=content)
    with open("did_report.html", "w") as f:
        f.write(output)


def did_report():
    """ did report """
    dut = Dut()
    start_time = dut.start()
    result = False
    try:
        dut.precondition(timeout=3600)
        content = get_ecu_content(dut)
        result = True
    except: # pylint: disable=bare-except
        error = traceback.format_exc()
        log.error("The did report failed: %s", error)
        content = dict(error=error)
    finally:
        create_report(content)
        dut.postcondition(start_time, result)
