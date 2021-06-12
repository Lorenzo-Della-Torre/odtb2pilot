""" legacy configuration file for old scripts """
from hilding.settings import Settings

settings = Settings()

ODTB2_DUT = settings.rig.hostname
ODTB2_PORT = settings.rig.signal_broker_port
