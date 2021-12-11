# Testscript Hilding MEPII
# project:  BECM basetech MEPII
# author:   J-ASSAR1 (Joel Assarsson)
# date:     2020-12-08
# version:  1.0
# reqprod:  76123

"""
General:        REQPROD 76123 / MAIN ; 2
Title:          DiagnosticSessionControl (10)
Purpose:        -
Description:    See DVM
"""

import time
from datetime import datetime
import sys
import logging
import inspect

import odtb_conf
from supportfunctions.support_can           import SupportCAN, CanPayload, CanParam,\
                                                    CanTestExtra, PerParam
from supportfunctions.support_test_odtb2    import SupportTestODTB2
from supportfunctions.support_carcom        import SupportCARCOM
from supportfunctions.support_file_io       import SupportFileIO

from supportfunctions.support_precondition  import SupportPrecondition
from supportfunctions.support_postcondition import SupportPostcondition
from supportfunctions.support_service10     import SupportService10
from supportfunctions.support_service22     import SupportService22

SIO         = SupportFileIO
SC          = SupportCAN()
SUTE        = SupportTestODTB2()
SC_CARCOM   = SupportCARCOM()
PREC        = SupportPrecondition()
POST        = SupportPostcondition()
SE10        = SupportService10()
SE22        = SupportService22()

def step_1(can_p):
    """
    Teststep 1: Send signal vehicle velocity < 3km/h
    """
    stepno = 1
    purpose = "Send signal vehicle velocity < 3km/h"
    SUTE.print_test_purpose(stepno, purpose)

    can_p_ex: PerParam = {
        "name" : 'VehSpdLgtSafe',
        "send" : True,
        "id" : "VCU1Front1Fr06",
        "frame" : b'\x80\xd5\x00\x00\x00\x00\x00\x00',
        "nspace" : can_p["namespace"].name,
        "intervall" : 0.015,
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), can_p_ex)

    SC.start_periodic(can_p["netstub"], can_p_ex)


def step_4(can_p):
    """
    Teststep 4: Request session change to Mode 3
    """
    etp: CanTestExtra = {
        "step_no" : 4,
        "purpose" : "Request session change to Mode 3 while car moving.\
                    BECM should acknowledge within 50ms and then change mode",
        "timeout" : 0.001,
        "min_no_messages" : -1,
        "max_no_messages" : -1
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)
    cpay: CanPayload = {
        "payload": SC_CARCOM.can_m_send("DiagnosticSessionControl",
                                        b'\x03', b''),
        "extra": ''
        }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), cpay)
    sleep_time = 0.03
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), sleep_time)
    allowed_time = 0.05
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), allowed_time)

    result = False
    SC.clear_all_can_frames()
    SC.clear_all_can_messages()
    time.sleep(1)

    time_1 = datetime.now()
    SC.t_send_signal_can_mf(can_p, cpay, True, 0x00)
    time.sleep(sleep_time)
    SC.update_can_messages(can_p)
    time_2 = datetime.now()

    time.sleep(1)
    delta_t = time_2-time_1
    can_reply = SC.can_frames[can_p["receive"]]
    logging.info(can_reply)
    logging.info("Time 1: %s\n Time 2: %s\n Time D: %s", time_1, time_2, delta_t)
    if delta_t.total_seconds() < allowed_time:
        result = True

    result = result and SUTE.test_message(can_reply, "5003")
    if result:
        logging.info("DiagnosticSessionControl acknowleged within time limits")

    time.sleep(3)
    result = result and SE22.read_did_f186(can_p, dsession=b'\x03')
    return result


def step_6(can_p):
    """
    Teststep 6: Send signal vehicle velocity > 3km/h
    """
    stepno = 6
    purpose = "Send signal vehicle velocity > 3km/h"
    SUTE.print_test_purpose(stepno, purpose)

    can_p_ex: PerParam = {
        "name" : 'VehSpdLgtSafe',
        "send" : True,
        "id" : "VCU1Front1Fr06",
        "frame" : b'\x80\xd6\x00\x00\x00\x00\x00\x00',
        "nspace" : can_p["namespace"].name,
        "intervall" : 0.015,
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), can_p_ex)

    SC.set_periodic(can_p_ex)


def step_7(can_p):
    """
    Teststep 7: Request session change to Mode 2 while car moving,
    session should remain in Mode 1.
    """
    etp: CanTestExtra = {
        "step_no" : 7,
        "purpose" : "Request session change to Mode2 while car moving",
        "timeout" : 3,
        "min_no_messages" : -1,
        "max_no_messages" : -1
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), etp)
    result = SE10.diagnostic_session_control(can_p, etp, b'\x02')

    time.sleep(3)
    result = result and SE22.read_did_f186(can_p, dsession=b'\x01')
    return result


def run():
    """
    Run - Call other functions from here
    """
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

    can_p: CanParam = {
        "netstub" : SC.connect_to_signalbroker(odtb_conf.ODTB2_DUT, odtb_conf.ODTB2_PORT),
        "send" : "Vcu1ToBecmFront1DiagReqFrame",
        "receive" : "BecmToVcu1Front1DiagResFrame",
        "namespace" : SC.nspace_lookup("Front1CANCfg0")
    }
    SIO.extract_parameter_yml(str(inspect.stack()[0][3]), can_p)

    logging.info("Testcase start: %s", datetime.now())
    starttime = time.time()
    logging.info("Time: %s \n", time.time())

    ############################################
    # precondition
    ############################################
    timeout = 30
    result = PREC.precondition(can_p, timeout)

    if result:
        ############################################
        # teststeps
        ############################################
        # step1:
        # action: Send signal vehicle velocity < 3km/h
        # result:
        step_1(can_p)
        time.sleep(2)

        # step2:
        # action: Change to programming session
        # result: Mode changed normally
        result = result and SE10.diagnostic_session_control_mode2(can_p, 2)
        time.sleep(3)
        result = result and SE22.read_did_f186(can_p, dsession=b'\x02')

        # step3:
        # action: Change to default session
        # result: Mode changed normally
        result = result and SE10.diagnostic_session_control_mode1(can_p, 3)
        time.sleep(3)
        result = result and SE22.read_did_f186(can_p, dsession=b'\x01')

        # step4:
        # action: Change to extended session
        # result: BECM acknowledges mode change within 50 ms.
        result = result and step_4(can_p)

        # step5:
        # action: Change to default session
        # result: Mode changed normally
        result = result and SE10.diagnostic_session_control_mode1(can_p, 5)
        time.sleep(3)
        result = result and SE22.read_did_f186(can_p, dsession=b'\x01')

        # step6:
        # action: Send signal vehicle velocity > 3km/h
        # result: BECM responds positively.
        step_6(can_p)
        time.sleep(2)

        # step7:
        # action: Request session change to Mode2 while car moving
        # result: No mode change
        result = result and step_7(can_p)

    ############################################
    # postCondition
    ############################################

    POST.postcondition(can_p, starttime, result)

if __name__ == '__main__':
    run()
