""" legacy configuration file for old scripts """
from hilding import get_conf

ODTB2_DUT = get_conf().rig.hostname
ODTB2_PORT = get_conf().rig.signal_broker_port
