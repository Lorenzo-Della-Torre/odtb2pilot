"""
ECU software download

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""
from os import listdir
import logging
import traceback
import time

from hilding.dut import Dut

from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_sec_acc import SecAccessParam

SSBL = SupportSBL()

def load_vbf_files(dut):
    """Loads the rig specific VBF files found in rigs/<default-rig-name>/VBFs

    Args:
        dut (Dut): An instance of Dut

    Returns:
        boolean: True if vbfs were loaded successfully, otherwise False
    """
    logging.info("~~~~~~~~ Loading VBFs started ~~~~~~~~")
    vbfs = listdir(dut.conf.rig.vbf_path)

    paths_to_vbfs = [str(dut.conf.rig.vbf_path) + "/" + x for x in vbfs]

    if not paths_to_vbfs:
        logging.error("VBFs not found, expected in %s ... aborting", dut.conf.rig.vbf_path)
        return False

    result = SSBL.read_vbf_param(paths_to_vbfs)

    return result

def activate_sbl(dut):
    """Downloads and activates SBL on the ECU using supportfunction from support_SBL

    Args:
        dut (Dut): An instance of Dut

    Returns:
        boolean: Result from support_SBL.sbl_activation.
        Should be True if sbl is activated successfully,
        otherwise False
    """
    logging.info("~~~~~~~~ Activate SBL started ~~~~~~~~")

    # Setting up keys
    sa_keys: SecAccessParam = dut.conf.default_rig_config

    # Activate SBL
    result = SSBL.sbl_activation(dut,
                                 sa_keys)

    return result

def download_ess(dut):
    """Download the ESS file to the ECU

    Args:
        dut (Dut): An instance of Dut

    Returns:
        boolean: True if download software part was successful, otherwise False
    """

    if SSBL.get_ess_filename():
        logging.info("~~~~~~~~ Download ESS started ~~~~~~~~")

        purpose = "Download ESS"
        result = SSBL.sw_part_download(dut, SSBL.get_ess_filename(),
                                       purpose=purpose)

    else:
        result = True
        logging.info("ESS file not needed for this project, skipping...")

    return result

def download_application_and_data(dut):
    """Download the application to the ECU

    Args:
        dut (Dut): An instance of Dut

    Returns:
        boolean: True of download was successful, otherwise False
    """

    logging.info("~~~~~~~~ Download application and data started ~~~~~~~~")
    result = True
    purpose = "Download application and data"
    for vbf_file in SSBL.get_df_filenames():
        result = result and SSBL.sw_part_download(dut, vbf_file, purpose=purpose)

    return result

def check_complete_and_compatible(dut):
    """Run complete and compatible routine

    Args:
        dut (Dut): Instance of Dut

    Returns:
        boolean: Result of complete and compatible
    """
    logging.info("~~~~~~~~ Check Complete And Compatible started ~~~~~~~~")

    return SSBL.check_complete_compatible_routine(dut, stepno=1)

def software_download(dut):
    """The function that handles all the sub-steps when performing software download.
    This function will keep track of the progress and give error indications if a step fails

    Args:
        dut (Dut): An instance of Dut

    Returns:
        boolean: Result of software download
    """

    # Load vbfs
    vbf_result = load_vbf_files(dut)

    logging.info("~~~~~~ Step 1/5 of software download (loading vbfs) done."
    " Result: %s\n\n", vbf_result)

    if vbf_result is False:
        logging.error("Aborting software download due to problems when loading VBFs")
        return False

    # Activate sbl
    sbl_result = activate_sbl(dut)

    logging.info("Step 2/5 of software download (downloading and activating sbl) done."
    " Result: %s\n\n", sbl_result)

    if sbl_result is False:
        logging.error("Aborting software download due to problems when activating SBL")
        return False

    # # Download ess (if needed)
    # ess_result = download_ess(dut)

    # logging.info("Step 3/5 of software download (downloading ess) done. \
    #  Result: %s\n\n", ess_result)

    # if ess_result is False:
    #     logging.error("Aborting software download due to problems when downloading ESS")
    #     return False

    # Download application and data
    app_result = download_application_and_data(dut)

    logging.info("Step 4/5 of software download (downloading application and data) done."
    " Result: %s\n\n", app_result)

    if app_result is False:
        logging.error("Aborting software download due to problems when downloading application")
        return False

    # # Check Complete And Compatible
    # check_result = check_complete_and_compatible(dut)

    # logging.info("Step 5/5 of software download (Check Complete And Compatible) done."
    # " Result: %s\n\n", check_result)

    # if check_result is False:
    #     logging.error("Aborting software download due to problems when checking C & C")
    #     return False

    # Check that the ECU ends up in mode 1 (default session)
    dut.uds.ecu_reset_1101()
    time.sleep(5)
    uds_response = dut.uds.active_diag_session_f186()
    mode = uds_response.data['details'].get('mode')
    correct_mode = True
    if mode != 1:
        logging.error("Software download complete "
        "but ECU did not end up in mode 1 (default session), current mode is: %s", mode)
        correct_mode = False

    return correct_mode



def flash():
    """Flashes the ECU with VBF files found in the rigs folder.
    If the script is executed on a remote computer the remote computers VBF files will be used.
    If executed locally on a hilding the VBF files on that hilding will be used.
    """
    dut = Dut()
    start_time = dut.start()
    result = False
    try:
        dut.precondition(timeout=1800)
        result = dut.step(software_download, purpose="Perform software download")
    except: # pylint: disable=bare-except
        error = traceback.format_exc()
        logging.error("Software download failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    logging.info("ssssss")
    flash()




























# '''
# project:  HVBM basetech MEPII
# author:   jpiousmo (Jenefer Liban)
# date:     2021-11-11
# version:  1.0
# reqprod:  68172
# title:    Usage Mode data record
# purpose: >
#     To enable readout of the active Usage mode.

# description: >
#     If the ECU is a publisher or a subscriber on the
#     usage mode signal, a data record with identifier as specified in
#     the table below shall be implemented exactly as defined in
#     Carcom - Global Master Reference Database.

# details: >
#     Read the DID 'DD0A' in both default and extended session
#     and make sure that we get a positive response with the
#     DID(DD0A) in the response.
# '''

# from datetime import datetime
# import inspect
# import sys
# import logging
# import time
# from os import listdir
# import odtb_conf

# from hilding.dut import Dut
# from hilding.dut import DutTestError
# from hilding.uds import UdsEmptyResponse
# from supportfunctions.support_can import CanParam, SupportCAN
# from supportfunctions.support_service31 import SupportService31
# from supportfunctions.support_service27 import SupportService27
# from supportfunctions.support_SBL import SupportSBL
# from supportfunctions.support_sec_acc import SupportSecurityAccess
# from supportfunctions.support_precondition import SupportPrecondition
# from supportfunctions.support_file_io import SupportFileIO

# SC = SupportCAN()
# SE31 = SupportService31()
# SE27 = SupportService27()
# SSBL = SupportSBL()
# SSA = SupportSecurityAccess()
# PREC = SupportPrecondition()
# SIO = SupportFileIO

# def load_vbf_files(dut):
#     """
#     Loads the rig specific VBF files found in rigs/<default-rig-name>/VBFs
#     Args:
#         dut (Dut): An instance of Dut
#     Returns:
#         boolean: True if vbfs were loaded successfully, otherwise False
#     """
#     logging.info("Loading VBFs started")
#     vbfs = listdir(dut.conf.rig.vbf_path)

#     paths_to_vbfs = [str(dut.conf.rig.vbf_path) + "/" + x for x in vbfs]

#     if not paths_to_vbfs:
#         logging.error("VBFs not found, expected in %s ... aborting", dut.conf.rig.vbf_path)
#         return False

#     result = SSBL.read_vbf_param(paths_to_vbfs)

#     return result

# def run():
#     """
#     DD0A verification in  Default and Ext Session
#     """
#     logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

#     can_p: CanParam = {
#         'netstub': SC.connect_to_signalbroker(odtb_conf.ODTB2_DUT, odtb_conf.ODTB2_PORT),
#         'send': "Vcu1ToBecmFront1DiagReqFrame",
#         'receive': "BecmToVcu1Front1DiagResFrame",
#         'namespace': SC.nspace_lookup("Front1CANCfg0")
#         }
#     #Read YML parameter for current function (get it from stack)
#     logging.debug("Read YML for %s", str(inspect.stack()[0][3]))
#     SIO.extract_parameter_yml(str(inspect.stack()[0][3]), can_p)


#     dut = Dut()
#     start_time = dut.start()

#     result = False
#     #err_list = []

#     #payload = b'\x14\x0B\x4A\x00'
#     #payload = b'\x22\xF1\x25'
#     #payload = b'\x10\x03'
#     #payload1 = b'\x10\x01'
#     #payload2 = b'\x11\x01'
#     payload4 = b'\x19\x02\x09'
#     #payload5 = b'\x31\x01\x02\x31'
#     #payload6 = b'\x31\x03\x40\x1C'
#     #payload = b'\x19\x02\x03'
#     #payload = b'\x27\x05\x00\x01\x00\x01\xa0\x27\x8d\x89\xda\x28\x64\x2e\x32\x64\xae\xf3\x59\xd1\x23\x79\xf8\x6b\x8c\xc7\x8b\xc2\x35\x66\xdf\x79\x4c\xbb\x28\xe7\x31\x9f\x64\x55\xba\x44\x23\x2e\x7f\xe4\x44\x48\xd9\xc2\x5a\x65\xba\xf3'

#     try:
#         # Communication with ECU lasts 30 seconds.
#         dut.precondition(timeout=100000)
#         #time.sleep(10)
#         #PREC.precondition(can_p, 30)

#         #dut.uds.set_mode(2)

#         # dut.uds.ecu_reset_1101()

#         # dut.uds.set_mode(3)

#         # SSA.set_level_key(1)

#         # SE27.activate_security_access_fixedkey(dut,dut.conf.default_rig_config)


#         #SSA.set_level_key(1)

#         #SE27.activate_security_access_fixedkey(dut,dut.conf.default_rig_config)

#         #sample code starts
#         #print("Libannnnnnnnnnn===============================================")
#         #print(payload)

#         # while(1):
#         #     try:
#         #         print("Sequence start===============================================")
#         #         code = 1
#         #         print(dut.uds.generic_ecu_call(payload1).raw)
#         #         code = 2
#         #         print(dut.uds.generic_ecu_call(payload1).raw)
#         #         code = 3
#         #         print(dut.uds.generic_ecu_call(payload2).raw)
#         #         code = 4
#         #         print(dut.uds.generic_ecu_call(payload4).raw)
#         #         code = 5
#         #         print(dut.uds.generic_ecu_call(payload5).raw)
#         #         code = 6
#         #         print(dut.uds.generic_ecu_call(payload).raw)
#         #         code = 7
#         print(dut.uds.generic_ecu_call(payload4))
#         #         code = 8
#         #         print(dut.uds.generic_ecu_call(payload5).raw)
#         #         code = 9
#         #         print(dut.uds.generic_ecu_call(payload1).raw)
#         #         code = 10
#         #         print(dut.uds.generic_ecu_call(payload4).raw)
#         #         code = 11
#         #         print(dut.uds.generic_ecu_call(payload5).raw)
#         #         code = 12
#         #         logging.info(err_list)
#         #         print("Sequence end===============================================")
#         #     except UdsEmptyResponse:
#         #         logging.error("No response from ECU")
#         #         err_list.append(code)
#         #         if len(err_list) > 50:
#         #             raise DutTestError("Continuously no response from ECU")
#         #         pass

#         # dut.uds.set_mode(3)

#         # SSA.set_level_key(5)

#         # SE27.activate_security_access_fixedkey(dut,dut.conf.default_rig_config)

#         # response = dut.uds.generic_ecu_call(payload5)

#         # logging.info(response)


#         # response = dut.uds.generic_ecu_call(payload6)

#         # logging.info(response)

#         # dut.uds.set_mode(1)
#         # dut.uds.set_mode(2)

#         # SSA.set_keys(dut.conf.default_rig_config)
#         # SSA.set_level_key(25)
#         # payload = SSA.prepare_client_request_seed()
    
#         # response = dut.uds.generic_ecu_call(payload)
#         # logging.info(response)

#         # SSA.process_server_response_seed(bytearray.fromhex(response.raw[4:]))

#         # payload = SSA.prepare_client_send_key()

#         # logging.info(payload)

#         #response = dut.uds.generic_ecu_call(payload2)

#         #logging.info(response)

#         # result = SSA.process_server_response_key(bytearray.fromhex(response.raw[6:(6+4)]))

#         # logging.info(result)

#         #SE27.activate_security_access_fixedkey(dut,dut.conf.default_rig_config)
#         #logging.info(SSBL.get_sbl_filename())

#         #load_vbf_files(dut)

#         #SSBL.sbl_activation(dut, sa_keys=dut.conf.default_rig_config)

#         #SE31.routinecontrol_requestsid_complete_compatible(dut)
#         #dut.uds.read_data_by_id_22(payload)
        

#         # time.sleep(5)

#         # print(dut.conf.rig.signal_send)
#         # print(dut.conf.rig.signal_receive)


#         print("Libannnnnnnnnnn================================================")
#         result = True

#     except DutTestError as error:
#         logging.error("Test failed: %s", error)
#         endtime = datetime.now().timestamp()
#         logging.info("Total time run is : ")
#         logging.info(endtime-start_time)
#     finally:
#         dut.postcondition(start_time, result)

# if __name__ == '__main__':
#     run()
