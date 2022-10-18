
import logging
import time
from hilding.dut import Dut
from hilding.dut import DutTestError
from hilding.conf import Conf
from supportfunctions.support_service27 import SupportService27
from supportfunctions.support_carcom import SupportCARCOM

CNF = Conf()
SE27 = SupportService27()
S_CARCOM = SupportCARCOM()


def step_1(dut: Dut):
    """
    action: Set to Programming Session and security access to ECU.
    expected_result: ECU is in programming session and security access is granted
    """
    dut.uds.set_mode(2)
    result = SE27.activate_security_access_fixedkey(dut, sa_keys=CNF.default_rig_config,
                                                    step_no=272, purpose="SecurityAccess")
    time.sleep(10)
    dut.uds.set_mode(1)
    dut.uds.set_mode(3)
    result1 = SE27.activate_security_access_fixedkey(dut, sa_keys=CNF.default_rig_config,
                                                    step_no=272, purpose="SecurityAccess")
    dut.uds.ecu_reset_1101()
    response_session = dut.uds.active_diag_session_f186()

    payload = S_CARCOM.can_m_send("ReadDTCInfoSnapshotRecordByDTCNumber",\
                                            b'\x0A\xA1\x00', b"\xFF")
    response = dut.uds.generic_ecu_call(payload)
    print("DTCCCCCCCCCCCCCCCCCCCCC", response)

    print("RRRRRRRRRRRRRRRRRRRRRRRRRRRR", result, result1, response_session.data['details']['mode'])
    if result and response_session.data['details']['mode'] == 1:
        logging.info("Security access granted in programming session")
        return True

    logging.error("Test Failed: Security access denied in programming session")
    return False


def run():
    dut = Dut()
    start_time = dut.start()
    result = False
    result_step = False
    try:
        dut.precondition(timeout=300)

        result_step = dut.step(step_1, purpose='Verify ECU')

        result = result_step

    except DutTestError as error:
        logging.error("Test failed: %s", error)
    finally:
        dut.postcondition(start_time, result)


if __name__ == '__main__':
    run()
