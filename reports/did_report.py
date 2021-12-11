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

from hilding.dut import Dut
from hilding.uds import EicDid
from hilding.uds import IoSssDid
from hilding.uds import UdsEmptyResponse
from hilding.uds import UdsError
from hilding.sddb import write
from hilding.sddb import quotify
from hilding.conf import Conf
from hilding import get_conf

log = logging.getLogger('did_report')

def add_details(dut, did_counter, did_dict, dids):
    for did_id, _ in did_dict.items():
        # Get DID details from ECU
        details = get_did_details(dut, did_id, did_counter, did_dict)
        if details:
            dids.append(details)


def get_ecu_content(dut: Dut):
    """ get data from the ecu """

    conf = get_conf()
    did = conf.rig.sddb_dids

    # Get all APP-dids from SDDB
    app_did_dict = did.get('app_did_dict', {})

    # Get data for testrun data file. This file is used for logs_to_html report
    part_numbers_res = dut.uds.read_data_by_id_22(
        EicDid.complete_ecu_part_number_eda0)
    write_to_testrun_data_file(part_numbers_res)

    # Counter. Keeping track of passed/failed
    did_counter = Counter(
        passed=0,
        failed=0,
        conditionsNotCorrect=0,
        requestOutOfRange=0,
        securityAccessDenied=0
    )

    app_dids = []
    pbl_dids = []
    sbl_dids = []

    try:
        # Application DIDs
        add_details(dut, did_counter, app_did_dict, app_dids)

        # PBL
        dut.uds.set_mode(mode=2)
        pbl_did_dict = did.get('pbl_did_dict', {})
        add_details(dut, did_counter, pbl_did_dict, pbl_dids)

        # SBL
        dut.uds.enter_sbl()
        sbl_did_dict = did.get('sbl_did_dict', {})
        add_details(dut, did_counter, sbl_did_dict, sbl_dids)

    except UdsError as error:
        log.error(error)

    content = {}
    content['platform'] = get_conf().rig.platform
    content['part_numbers'] = part_numbers_res.details
    content['app_dids'] = app_dids
    content['pbl_dids'] = pbl_dids
    content['sbl_dids'] = sbl_dids
    content['did_counter'] = did_counter

    return content


def write_to_testrun_data_file(part_numbers_res):
    """
    Provide data in the build dir to the logs_to_html script
    Due to this setup, the did_report always need to run before the
    logs_to_html script.
    """
    conf = get_conf()
    testrun_data_file = conf.rig.build_path.joinpath('testrun_data.py')
    eda0 = {}
    details = part_numbers_res.details
    for eda0_did in ['F120', 'F12A', 'F12B', 'F18C']:
        if eda0_did in details:
            value = details.get(eda0_did + '_valid', details[eda0_did])
            eda0[details[eda0_did + '_info']['name']] = value
    # Writes the eda0 dict to a 'testrun_data.py' file
    # pformat is used to make it look nicer and 'w' is for writing
    # This file is used by logs_to_html to present data from DID EDA0
    # in the report
    write(testrun_data_file, "eda0_dict", pformat(eda0), "w")


def get_did_details(dut, did_id, did_counter, did_dict):
    """ Get relevant did details as a dictionary """
    # give the ecu some time to get ready for the next did request
    time.sleep(2)
    try:
        res = dut.uds.read_data_by_id_22(bytes.fromhex(did_id))
    except UdsEmptyResponse:
        return None
    log.debug(res)
    details = res.details
    details['did_called'] = did_id

    # If we get a 7F errormessage we won't get the did-info in the UDS_Response
    # Name is empty if the did-info is missing and then we need to add it
    name = details.get('name', '')
    if not name:
        did_id_dict = did_dict.get(did_id, {})
        details['name'] = did_id_dict.get('name' ,'')

    # If something went wrong
    if 'nrc_name' in res.data:
        nrc_name = res.data['nrc_name']
        nrc = res.data['nrc']
        did_counter['failed'] += 1
        # We increase the counter for that particular error
        did_counter[nrc_name] += 1
        details['error_message'] = f"Negative response: {nrc_name} ({nrc})"
        return details

    details['sid_match'] = 'sid' in res.data
    details['did_match'] = did_id == res.data.get('did')

    size_match = False
    if 'size' in res.details and 'item' in res.details:
        expected_size = int(details['size'])
        response_items = details.get('response_items', None)

        if not response_items:
            return None

        payload = details.get('item','')
        actual_size = int(details.get('size','0'))
        sub_payload = response_items[0].get('sub_payload','')
        log.debug("---------------------------------------------")
        log.debug("DID: %s", did_id)
        log.debug("payload (item): %s", details.get('item',''))
        log.debug("sub_payload: %s", sub_payload)
        log.debug("Expected size: %s", expected_size)
        log.debug("Actual size: %s", actual_size)
        log.debug("---------------------------------------------")
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

    conf = get_conf()
    dids = conf.rig.sddb_dids
    app_diag_part_num = dids.get('app_diag_part_num', {})

    content['style'] = style
    content['hostname'] = platform.node()
    content['report_generated'] = datetime.now().strftime("%Y-%m-%d %H:%M")
    content['sddb_app_diag_part_num'] = app_diag_part_num.replace('_', ' ')

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
        dut.precondition(timeout=1800)
        content = get_ecu_content(dut)
        result = True
        create_report(content)
        dut.postcondition(start_time, result)
    except: # pylint: disable=bare-except
        error = traceback.format_exc()
        log.error("The did report failed: %s", error)
        content = dict(error=error)

