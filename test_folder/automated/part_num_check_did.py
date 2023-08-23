"""

"""

import time
from datetime import datetime
import sys
import logging
from os import listdir
import os.path as path_mod
import re

import odtb_conf
from supportfunctions.support_can import SupportCAN, CanParam, CanPayload, CanTestExtra
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_sec_acc import SupportSecurityAccess

from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_service10 import SupportService10
from supportfunctions.support_service11 import SupportService11
from supportfunctions.support_service22 import SupportService22
from supportfunctions.support_carcom import SupportCARCOM
from supportfunctions.support_file_io import SupportFileIO

from hilding.dut import Dut
from hilding.dut import DutTestError

SIO = SupportFileIO
SC = SupportCAN()
SUTE = SupportTestODTB2()
SSBL = SupportSBL()
SSA = SupportSecurityAccess()

PREC = SupportPrecondition()
SE10 = SupportService10()
SE11 = SupportService11()
SE22 = SupportService22()
SC_CARCOM = SupportCARCOM()

# Regular Expressions
RE_FILE_NAME = re.compile(r'(?P<file_name_sw_part_number>\d{8})\s*(?P<file_name_sw_version>\w+)')
RE_SW_PART_NUMBER = re.compile(r'\s*sw_part_number\s*=\s*"?(?P<sw_part_number>\w*)')
RE_SW_VERSION = re.compile(r'\s*sw_version\s*=\s*"?(?P<sw_version>\w*)')
RE_SW_PART_TYPE = re.compile(r'\s*sw_part_type\s*=\s*(?P<sw_part_type>\w*)')

def validate_vbf_name(infile, did_f12e):
    """
    action:
        Reads the vbf-files and compares the file name with the information in the header

    expected_result:
        Returns result of the validation
        True - If file_name match the information in the vbf file header
        False - If it doesn't match
	"""

    # Variables
    match_sw_part_number = False
    match_sw_version = False
    match_sw_part_type = False
    sw_part_number = None
    sw_version = None
    sw_part_type = None

    # Open file
    with open(infile, encoding="ascii", errors="surrogateescape") as vbf_file:
        # os.path is a module which helps splitting file and path (works with both
        # forward slashes (/) and backward slashes (\)
        file_name = path_mod.basename(infile)

        # Iterate line by line
        for line in vbf_file:
            # Break if we have all the information we need
            if sw_part_number and sw_version and sw_part_type:
                break
            # If we don't have a match, keep looking in each line
            if not match_sw_part_number:
                match_sw_part_number = RE_SW_PART_NUMBER.match(line)
            if not match_sw_version:
                match_sw_version = RE_SW_VERSION.match(line)
            if not match_sw_part_type:
                match_sw_part_type = RE_SW_PART_TYPE.match(line)

    # If we have all necessary info from the vbf file header
    if match_sw_part_number and match_sw_version and match_sw_part_type:
        sw_part_number = match_sw_part_number.group('sw_part_number')
        sw_version = match_sw_version.group('sw_version')
        sw_part_type = match_sw_part_type.group('sw_part_type')
        logging.info('\n----------------\nsw_part_number = %s\nsw_version = %s\nsw_part_type = %s',
                     sw_part_number, sw_version, sw_part_type)
    else:
        # Did not find the necessary header information to make the comparison
        logging.fatal('\nDid not find the necessary header information to make the comparison')
        return False

    # Compare
    retval = compare_part_number_and_version(sw_part_number, sw_version, file_name, did_f12e)
    return retval


def compare_part_number_and_version(sw_part_number, sw_version, file_name, did_f12e):
    """
    action:
        Splits the file name into part number and version and compares them with the
        part number and version from the file header (input parameters to this function)

    expected_result:
        True - If they match
        False - If they do not match
    """

    result = True
    match_file_name = RE_FILE_NAME.match(file_name)

    file_name_sw_part_number = None
    file_name_sw_version = None
    if match_file_name:
        file_name_sw_part_number = match_file_name.group('file_name_sw_part_number')
    if match_file_name:
        file_name_sw_version = match_file_name.group('file_name_sw_version')

    # Comparing part numbers
    if sw_part_number != file_name_sw_part_number:
        logging.fatal('\nPart numbers not matching.\nHeader: %s\nFile name: %s', sw_part_number,
                      file_name_sw_part_number)
        result = False
    # Comparing part number and did F12E
    if sw_part_number != did_f12e:
        logging.fatal('\nPart numbers not matching.\nHeader: %s\nDid F12E: %s', sw_part_number,
                      did_f12e)
    # Comparing versions
    if sw_version != file_name_sw_version:
        logging.fatal('\nVersions not matching.\nHeader: %s\nFile name: %s', sw_version,
                      file_name_sw_version)
        result = False
    return result


def step_1(can_p: CanParam):
    """
    Teststep 1: Service22: F12E ECU Software Part Numbers
    """
    cpay: CanPayload = {"payload" : SC_CARCOM.can_m_send("ReadDataByIdentifier",
                                                         b'\xF1\x2E', b''),
                        "extra" : ''
                       }
    etp: CanTestExtra = {"step_no": 1,\
                         "purpose" : "Service22: F12E ECU Software Part Numbers",
                         "timeout" : 1,
                         "min_no_messages" : -1,
                         "max_no_messages" : -1
                        }

    result = SUTE.teststep(can_p, cpay, etp)
    logging.debug("Step%s, received frames: %s",
                  etp["step_no"], SC.can_frames[can_p["receive"]])
    logging.debug("Step%s, received messages: %s",
                  etp["step_no"], SC.can_messages[can_p["receive"]])
    if not len(SC.can_messages[can_p["receive"]]) == 0:
        logging.info('Read F12E: %s', SC.can_messages[can_p["receive"]])
        message = SC.can_messages[can_p["receive"]][0][2]
        pos1 = message.find('F12E')
        if not pos1 == -1:
            logging.info("ECU Software Part Numbers %s\n",
                         SUTE.pp_partnumber(message[pos1+6: pos1+20], message[pos1:pos1+4]))
            file_name_did = message[pos1+6: pos1+14]
        else:
            result = False
    else:
        logging.info("Could not read DID F12E)")
        result = False
    return result, file_name_did

def run():
    """
    Run - Call other functions from here
    """

    dut = Dut()
    # start logging
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)
    #logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.DEBUG)

    # where to connect to signal_broker
    platform=dut.conf.rigs[dut.conf.default_rig]['platform']
    can_p: CanParam = {
        'netstub': SC.connect_to_signalbroker(odtb_conf.ODTB2_DUT, odtb_conf.ODTB2_PORT),
        'send': dut.conf.platforms[platform]['signal_send'],
        'receive': dut.conf.platforms[platform]['signal_receive'],
        'namespace': dut.conf.platforms[platform]['namespace'],
        'signal_periodic': dut.conf.platforms[platform]['signal_periodic'],
        'signal_tester_preset': dut.conf.platforms[platform]['signal_tester_present'],
        'wakeup_frame': dut.conf.platforms[platform]['wakeup_frame'],
        'protocol': dut.conf.platforms[platform]['protocol'],
        'framelength_max': dut.conf.platforms[platform]['framelength_max'],
        'padding': dut.conf.platforms[platform]['padding']
        }
    #Read YML parameter for current function (get it from stack)
    SIO.parameter_adopt_teststep(can_p)

    logging.info("Testcase start: %s", datetime.now())
    starttime = time.time()
    logging.info("Time: %s \n", time.time())
    ############################################
    # precondition
    ############################################


    # read VBF param when testscript is s started, if empty take default param
    SSBL.get_vbf_files()
    timeout = 30
    result = PREC.precondition(can_p, timeout)

    #Init parameter for SecAccess Gen1 / Gen2
    platform=dut.conf.rigs[dut.conf.default_rig]['platform']

    if result:
        ############################################
        # teststeps
        ############################################

        # step 1:
        # action: Service22: F12E ECU Software Part Numbers
        # result: BECM sends requested IDs
        result, file_name_did = step_1(can_p)

        try:
            vbfs = listdir(dut.conf.rig.vbf_path)
            paths_to_vbfs = [str(dut.conf.rig.vbf_path) + "/" + x for x in vbfs]

            if not paths_to_vbfs:
                logging.error("VBFs not found, expected in %s ... aborting", dut.conf.rig.vbf_path)
                sys.exit()

            # A second result variabel because we want the other one to be False
            # until the end in case we get an exception.
            test_result = True

            # Creating generator for looping paths_to_vbfs while test result is True
            gen = (vbf for vbf in paths_to_vbfs if test_result and vbf.endswith('.vbf'))

            # Looping using the generator
            for vbf in gen:
                # Validating file names
                test_result = validate_vbf_name(vbf, file_name_did) and result

            result = test_result
        except DutTestError as error:
            logging.error("Test failed: %s", error)

    ############################################
    # postCondition
    ############################################

    logging.debug("\nTime: %s \n", time.time())
    logging.info("Testcase end: %s", datetime.now())
    logging.info("Time needed for testrun (seconds): %s", int(time.time() - starttime))

    logging.info("Do cleanup now...")
    logging.info("Stop all periodic signals sent")
    SC.stop_periodic_all()

    # deregister signals
    SC.unsubscribe_signals()
    # if threads should remain: try to stop them
    SC.thread_stop()

    logging.info("Test cleanup end: %s\n", datetime.now())

    if result:
        logging.info("Testcase result: PASSED")
    else:
        logging.info("Testcase result: FAILED")


if __name__ == '__main__':
    run()
