"""
project:  Hilding
author:   DHJELM (Daniel Hjelm)
date:     2020-12-09

Support function for importing sddb data and store it as python data
structures in <platform>/build/.
"""

import os
import sys
import codecs
import logging
import tempfile

from pathlib import Path
from pprint import pformat
from lxml import etree
from inflection import underscore


def get_platform_dir():
    """Get the selected platform directory (spa1 or spa2)"""
    platform_dir = os.getenv('ODTBPROJPARAM')
    if not platform_dir:
        sys.exit("You need to set the ODTBPROJPARAM. Exiting...")
    return platform_dir


def get_release_dir():
    """Get the release dir for the current platform"""
    dbpath = Path(get_platform_dir()).joinpath('release')
    if not dbpath.exists():
        sys.exit(f"{dbpath} directory is missing. Exiting...")
    return dbpath


def get_sddb_file():
    """Get the current sddb file from the release directory"""

    dbpath = get_release_dir()
    sddb_glob = dbpath.glob("*.sddb")
    try:
        sddb_file = next(sddb_glob)
    except StopIteration:
        sys.exit(f"Couldn't find any sddb files in {dbpath}. Exiting...")

    try:
        next(sddb_glob)
        logging.warning(
            "More than one sddb file in %s. "
            "%s was selected.", dbpath, sddb_file)
    except StopIteration:
        # all is good
        pass

    return sddb_file


def get_build_dir():
    """
    Get the path of the build where we will store the python data structures
    extracted from the sddb xml file
    """
    build_dir = Path(get_platform_dir()).joinpath('build')
    if not build_dir.exists():
        sys.exit(f"{build_dir} directory is missing. Existing...")
    return build_dir


def ecu_determination(root, type_str):
    """
    Checking in the tree and look for ECU type (HVBM or BECM)
    returns the corresponding search string
    """
    ecu_type_name = root.find('.//ECU').attrib['Name']
    software = './/ECU[@Name="%s"]/SWs/SW[@Type="%s"]' % (ecu_type_name, type_str)
    return software


SERVICE22 = './/Service[@ID="22"]/DataIdentifiers/DataIdentifier'


def extract_service22_dids(root, type_str):
    """
    From the etree root, extract the dids in the service 22 and prepend the key
    with "22".
    """
    service22_dids = {}
    logging.debug(root.attrib)

    # Determine which ECU the SDDB is for
    ecu = ecu_determination(root, type_str)
    logging.debug('\n ECU: %s\n', ecu)

    diagnostic_part_number = str()
    for ecu_app in root.findall(ecu):
        diag_part_num = ecu_app.attrib['DiagnosticPartNumber']
        diagnostic_part_number = diag_part_num.replace(" ", "_")

        for did in ecu_app.findall(SERVICE22):
            # did.attrib is a dict containing the info we need
            parent_id = "22"
            did_key = parent_id + did.attrib["ID"]
            service22_dids[did_key] = did.attrib
    return service22_dids, diagnostic_part_number


def extract_service22_response_items(root, type_str):
    """
    Get the response items from service 22.
    """
    # Determine which ECU the SDDB is for
    ecu = ecu_determination(root, type_str)
    logging.debug('\n ECU: %s\n', ecu)

    data_dict = {}
    for ecu_app in root.findall(ecu):
        logging.info('Name= %s', ecu_app.attrib["Name"])
        for did in ecu_app.findall(SERVICE22):
            # did.attrib is a dict containing the info we need
            logging.debug('%s', did.attrib["Name"])
            did_key = "22" + did.attrib["ID"] # 22 Is parent ID
            data_dict[did_key] = []

            for response_item in did.findall('.//ResponseItems/ResponseItem'):
                logging.debug('attrib = %s', response_item.attrib)
                logging.debug('Name = %s', response_item.attrib['Name'])

                # Makes a new dict with the response_item as a base
                resp_item = dict(response_item.attrib)

                # Adding the rest of the information
                for formula in response_item.findall('Formula'):
                    logging.debug('FORMULA = %s', formula.text)
                    resp_item['Formula'] = formula.text
                for unit in response_item.findall('Unit'):
                    logging.debug('UNIT = %s', unit.text)
                    resp_item['Unit'] = unit.text
                for compare_value in response_item.findall('CompareValue'):
                    logging.debug('COMPARE_VALUE = %s', compare_value.text)
                    resp_item['CompareValue'] = compare_value.text
                for software_label in response_item.findall('SoftwareLabel'):
                    logging.debug('SOFTWARE_LABEL = %s', software_label.text)
                    resp_item['SoftwareLabel'] = software_label.text
                data_dict[did_key].append(resp_item)
    return data_dict


def write(path, variable_name, data, mode):
    """ Writing python data structure to file """
    with open(path, mode) as file:
        logging.debug('Writing python data structure to %s', path)
        variable_name = "\n\n" + variable_name + " = "
        file.write(variable_name + str(data))


def quotify(string):
    """ Surround with single quotes """
    return '\'' + string + '\''


def process_did_content(root):
    """
    Go over the different sections of the sddb and extract the service 22 dids
    """
    pbl_dict, pbl_diag_part_num = extract_service22_dids(root, 'PBL')
    sbl_dict, sbl_diag_part_num = extract_service22_dids(root, 'SBL')
    app_dict, app_diag_part_num = extract_service22_dids(root, 'APP')
    data_dict = extract_service22_response_items(root, 'APP')

    # Write all information to file. First file mode should be w+ so we start
    # with empty file, then we append to that file.
    did_file = Path(get_build_dir()).joinpath('did.py')
    write(did_file, 'pbl_diag_part_num', quotify(pbl_diag_part_num), 'w')
    write(did_file, 'pbl_did_dict', pformat(pbl_dict), 'a')
    write(did_file, 'sbl_diag_part_num', quotify(sbl_diag_part_num), 'a')
    write(did_file, 'sbl_did_dict', pformat(sbl_dict), 'a')
    write(did_file, 'app_diag_part_num', quotify(app_diag_part_num), 'a')
    write(did_file, 'app_did_dict', pformat(app_dict), 'a')
    write(did_file, 'resp_item_dict', pformat(data_dict), 'a')


def extract_dtcs(root):
    """
    Extract DTCs and their respective snapshot diffinition from service 19
    """
    dtc_record = {}
    for dtc_node in root.find('.//Service[@ID="19"]/DTCS'):
        dtc = dict(dtc_node.attrib)
        try:
            dtc_id = dtc.pop('ID')
        except KeyError:
            sys.exit("ID is missing from DTC entry. Check XML data. Exiting...")
        dtc_id = dtc_id.replace('0x', '')
        dtc_record[dtc_id] = dtc

        snapshot_dids_list = []
        for snapshot_dids in dtc_node.find('.//SnapshotDIDs'):
            snapshot_dids_item = dict(snapshot_dids.attrib)
            did_ref = snapshot_dids.find('.//')
            snapshot_dids_item['DataIdentifierReference'] = dict(did_ref.attrib)
            snapshot_dids_list.append(snapshot_dids_item)
        dtc_record[dtc_id]['SnapshotDIDs'] = snapshot_dids_list
    return dtc_record


def extract_report_dtc(root):
    """ Get service 19 subfunctions and their response items """
    report_dtc = {}

    for report_dtc_node in root.find('.//Service[@ID="19"]/Subfunctions'):
        report_dtc_item = dict(report_dtc_node.attrib)
        try:
            report_dtc_id = report_dtc_item.pop('ID')
        except KeyError:
            sys.exit("ID is missing from DTC entry. Check XML data. Exiting...")
        report_dtc[report_dtc_id] = report_dtc_item

        response_item_list = []
        for response_item in report_dtc_node.findall('.//ResponseItems/ResponseItem'):
            response_item_list.append(dict(response_item.attrib))
        report_dtc[report_dtc_id]['ResponseItems'] = response_item_list

    return report_dtc


def process_dtc_content(root):
    """ Get DTCs and DTC reports and write it to the build file """
    dtc_dict = extract_dtcs(root)
    report_dtc = extract_report_dtc(root)

    dtc_file = Path(get_build_dir()).joinpath('dtc.py')
    write(dtc_file, 'sddb_dtcs', pformat(dtc_dict), 'w')
    write(dtc_file, 'sddb_report_dtc', pformat(report_dtc), 'a')


def extract_pbl_services(root):
    """ Get primary bootloader services"""
    # pylint: disable=bare-except
    pbl_services = {}
    for service in root.find('.//SW[@Type="PBL"]/Services', namespaces=None):
        # First get Service name and ID
        service_item = dict(service.attrib)
        service_item['Name'] = underscore(service_item['Name'])
        service_item['name'] = service_item.pop('Name')
        try:
            service_id = service_item.pop('ID')
        except:
            pass

        pbl_services[service_id] = service_item

        # Get the negative response codes
        nrc_lst = []
        try:
            for nrc in service.find('NegativeResponseCodes'):
                to_underscore = dict(nrc.attrib)
                to_underscore['Name'] = underscore(to_underscore['Name'])
                to_underscore['code'] = to_underscore.pop('Code')
                to_underscore['name'] = to_underscore.pop('Name')
                nrc_lst.append(to_underscore)

            pbl_services[service_id]['negative_response_code'] = nrc_lst

        except:
            logging.debug("PBL: Service (%s) does not have any NRC defined.", service_id)

        # Get subfunctions
        try:
            sub_fn_lst = []
            for sub_functions in service.find('Subfunctions'):
                to_underscore = dict(sub_functions.attrib)
                to_underscore['Name'] = underscore(to_underscore['Name'])
                to_underscore['id'] = to_underscore.pop('ID')
                to_underscore['name'] = to_underscore.pop('Name')

                # Not all subfunctions have the keys below, need to check for each subfunction.
                if 'delayTime' in to_underscore:
                    to_underscore['delay_time'] = to_underscore.pop('delayTime')
                    to_underscore['delay_time_on_boot'] = to_underscore.pop('delayTimeOnBoot')
                    to_underscore['number_of_attempts'] = to_underscore.pop('numberOfAttempts')

                sub_fn_lst.append(to_underscore)

                # Get sessions
                sess_lst = []
                for sessions in sub_functions.find('Sessions'):
                    to_underscore = dict(sessions.attrib)
                    to_underscore['Name'] = underscore(to_underscore['Name'])
                    to_underscore['id'] = to_underscore.pop('ID')
                    to_underscore['name'] = to_underscore.pop('Name')
                    to_underscore['p2server_max'] = to_underscore.pop('P2ServerMax')
                    to_underscore['p4server_max'] = to_underscore.pop('P4ServerMax')

                    sess_lst.append(to_underscore)

                pbl_services[service_id]['sessions'] = sess_lst
            pbl_services[service_id]['sub_functions'] = sub_fn_lst

        except:
            logging.debug("PBL: No subfunction in service (%s).", service_id)

    return pbl_services


def extract_sbl_services(root):
    """ Get secondary bootloader services """
    # pylint: disable=bare-except
    sbl_services = {}
    for service in root.find('.//SW[@Type="SBL"]/Services', namespaces=None):
        # First get Service name and ID
        service_item = dict(service.attrib)
        service_item['Name'] = underscore(service_item['Name'])
        service_item['name'] = service_item.pop('Name')
        try:
            service_id = service_item.pop('ID')
        except:
            pass

        sbl_services[service_id] = service_item

        # Get the negative response codes
        nrc_lst = []
        try:
            for nrc in service.find('NegativeResponseCodes'):
                to_underscore = dict(nrc.attrib)
                to_underscore['Name'] = underscore(to_underscore['Name'])
                to_underscore['code'] = to_underscore.pop('Code')
                to_underscore['name'] = to_underscore.pop('Name')
                nrc_lst.append(to_underscore)

            sbl_services[service_id]['negative_response_code'] = nrc_lst

        except:
            logging.debug("SBL: Service (%s) does not have any NRC defined.", service_id)

        # Get subfunctions
        try:
            sub_fn_lst = []
            for sub_functions in service.find('Subfunctions'):
                to_underscore = dict(sub_functions.attrib)
                to_underscore['Name'] = underscore(to_underscore['Name'])
                to_underscore['id'] = to_underscore.pop('ID')
                to_underscore['name'] = to_underscore.pop('Name')

                # Not all subfunctions have the keys below, need to check for each subfunction.
                if 'delayTime' in to_underscore:
                    to_underscore['delay_time'] = to_underscore.pop('delayTime')
                    to_underscore['delay_time_on_boot'] = to_underscore.pop('delayTimeOnBoot')
                    to_underscore['number_of_attempts'] = to_underscore.pop('numberOfAttempts')

                sub_fn_lst.append(to_underscore)

                # Get sessions
                sess_lst = []
                for sessions in sub_functions.find('Sessions'):
                    to_underscore = dict(sessions.attrib)
                    to_underscore['Name'] = underscore(to_underscore['Name'])
                    to_underscore['id'] = to_underscore.pop('ID')
                    to_underscore['name'] = to_underscore.pop('Name')
                    to_underscore['p2server_max'] = to_underscore.pop('P2ServerMax')
                    to_underscore['p4server_max'] = to_underscore.pop('P4ServerMax')

                    sess_lst.append(to_underscore)

                sbl_services[service_id]['sessions'] = sess_lst
            sbl_services[service_id]['sub_functions'] = sub_fn_lst

        except:
            logging.debug("SBL: No subfunction in service (%s).", service_id)

    return sbl_services


def extract_app_services(root):
    """
    Get application services
        Default session
        Extended session
    """
    # pylint: disable=bare-except
    app_services = {}
    for service in root.find('.//SW[@Type="APP"]/Services', namespaces=None):
        # First get Service name and ID
        service_item = dict(service.attrib)
        service_item['Name'] = underscore(service_item['Name'])
        service_item['name'] = service_item.pop('Name')
        try:
            service_id = service_item.pop('ID')
        except:
            pass

        app_services[service_id] = service_item

        # Get the negative response codes
        nrc_lst = []
        try:
            for nrc in service.find('NegativeResponseCodes'):
                to_underscore = dict(nrc.attrib)
                to_underscore['Name'] = underscore(to_underscore['Name'])
                to_underscore['code'] = to_underscore.pop('Code')
                to_underscore['name'] = to_underscore.pop('Name')
                nrc_lst.append(to_underscore)

            app_services[service_id]['negative_response_code'] = nrc_lst

        except:
            logging.debug("APP: Service (%s) does not have any NRC defined.", service_id)

        # Get subfunctions
        try:
            sub_fn_lst = []
            for sub_functions in service.find('Subfunctions'):
                to_underscore = dict(sub_functions.attrib)
                to_underscore['Name'] = underscore(to_underscore['Name'])
                to_underscore['id'] = to_underscore.pop('ID')
                to_underscore['name'] = to_underscore.pop('Name')

                # Not all subfunctions have the keys below, need to check for each subfunction.
                if 'delayTime' in to_underscore:
                    to_underscore['delay_time'] = to_underscore.pop('delayTime')
                    to_underscore['delay_time_on_boot'] = to_underscore.pop('delayTimeOnBoot')
                    to_underscore['number_of_attempts'] = to_underscore.pop('numberOfAttempts')

                sub_fn_lst.append(to_underscore)

                # Get sessions
                sess_lst = []
                for sessions in sub_functions.find('Sessions'):
                    to_underscore = dict(sessions.attrib)
                    to_underscore['Name'] = underscore(to_underscore['Name'])
                    to_underscore['id'] = to_underscore.pop('ID')
                    to_underscore['name'] = to_underscore.pop('Name')
                    to_underscore['p2server_max'] = to_underscore.pop('P2ServerMax')
                    to_underscore['p4server_max'] = to_underscore.pop('P4ServerMax')

                    sess_lst.append(to_underscore)

                app_services[service_id]['sessions'] = sess_lst
            app_services[service_id]['sub_functions'] = sub_fn_lst

        except:
            logging.debug("APP: No subfunction in service (%s).", service_id)

    return app_services


def extract_defined_services(root):
    """
    Extract services which are defined in the different software levels.
    Programming session which includes:
        Primary bootloader
        Secondary bootloader

    Application includes:
        Default session
        ExtendedDiagnostic session
    """
    pbl_services = extract_pbl_services(root)
    sbl_services = extract_sbl_services(root)
    app_services = extract_app_services(root)

    return pbl_services, sbl_services, app_services


def process_service_content(root):
    """ Get services for each software level and write to file. """
    pbl_services, sbl_services, app_services = extract_defined_services(root)

    service_file = Path(get_build_dir()).joinpath('services.py')
    write(service_file, 'pbl', pformat(pbl_services), 'w')
    write(service_file, 'sbl', pformat(sbl_services), 'a')
    write(service_file, 'app', pformat(app_services), 'a')

    logging.info("Services for primary bootloader, secondary bootloader, and application " \
                 "has been saved at:\n %s", service_file)


def parse_sddb_file():
    """
    Convert and parse the sddb file and trigger the processing of it's content
    """
    sddb_file = get_sddb_file()

    # the carcom sddb export seems to be in latin1 format and lxml.etree can't
    # handle it so let's convert the file first
    with tempfile.TemporaryFile(mode='w+') as tf:
        with open(sddb_file, 'r', encoding='latin1') as f:

            # remove that pesky BOM at the beginning of the file if it exists
            line = f.readline()
            line = line.replace(codecs.BOM_UTF8.decode('latin1'), '')
            tf.write(line)

            # read the rest of the file
            for line in f:
                line = line.replace('°C', 'degC')
                line = line.replace('µC', 'uC')
                line = line.replace(u'\xa0', u' ') #non-breaking space
                tf.write(line)

        logging.info("Parse sddb file")
        tf.seek(0)
        tree = etree.parse(tf) # pylint: disable=c-extension-no-member

    root = tree.getroot()
    logging.debug(root.attrib)

    process_did_content(root)
    process_dtc_content(root)
    process_service_content(root)
