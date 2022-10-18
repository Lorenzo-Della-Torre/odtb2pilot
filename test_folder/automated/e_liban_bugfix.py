from datetime import datetime
import inspect
import sys
import logging
import time
from os import listdir
import odtb_conf

from hilding.dut import Dut
from hilding.dut import DutTestError
from hilding.uds import UdsEmptyResponse
from supportfunctions.support_can import CanParam, SupportCAN
from supportfunctions.support_service31 import SupportService31
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_SBL import SupportSBL
from supportfunctions.support_sec_acc import SupportSecurityAccess
from supportfunctions.support_precondition import SupportPrecondition
from supportfunctions.support_file_io import SupportFileIO

SC = SupportCAN()
SE31 = SupportService31()
SE27 = SupportService27()
SSBL = SupportSBL()
SSA = SupportSecurityAccess()
PREC = SupportPrecondition()
SIO = SupportFileIO


def run():
    """
    DD0A verification in  Default and Ext Session
    """
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

    can_p: CanParam = {
        'netstub': SC.connect_to_signalbroker(odtb_conf.ODTB2_DUT, odtb_conf.ODTB2_PORT),
        'send': "Vcu1ToBecmFront1DiagReqFrame",
        'receive': "BecmToVcu1Front1DiagResFrame",
        'namespace': SC.nspace_lookup("Front1CANCfg0")
        }
    #Read YML parameter for current function (get it from stack)
    logging.debug("Read YML for %s", str(inspect.stack()[0][3]))
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), can_p)


    dut = Dut()
    start_time = dut.start()

    result = False
    #err_list = []

    try:
        # Communication with ECU lasts 30 seconds.
        #dut.precondition(timeout=100000)
        dut.precondition(timeout=30)

        #set mode
        dut.uds.set_mode(3)
        time.sleep(6)

        print("================================================Unlock start================================================")

        SSA.set_keys(dut.conf.default_rig_config)

        #define security level 
        SSA.set_level_key(5)

        #prepare payload for request seed
        payload = SSA.prepare_client_request_seed()

        #corrupt any required byte
        # payload[7] = 0x00

        #send request key payload
        response = dut.uds.generic_ecu_call(payload)
        logging.info("------Send request key response: ", response)

        #process seed
        SSA.process_server_response_seed(bytearray.fromhex(response.raw[4:]))

        #prepare key payload
        payload = SSA.prepare_client_send_key()
        #corrupt key payload
        #payload[1] = 0x06
        logging.info("------Prepare key payload: ", payload)

        #send key
        response = dut.uds.generic_ecu_call(payload)
        logging.info("------Send key response: ", response)

        #process received key response
        result = SSA.process_server_response_key(bytearray.fromhex(response.raw[6:(6+4)]))
        logging.info("------process received key response: ", result)

        print("================================================End================================================")
        result = True

    except DutTestError as error:
        logging.error("Test failed: %s", error)
        endtime = datetime.now().timestamp()
        logging.info("Total time run is : ")
        logging.info(endtime-start_time)
    finally:
        dut.postcondition(start_time, result)

if __name__ == '__main__':
    run()
