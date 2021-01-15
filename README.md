# ODTB2Pilot

Pilot to test if Signalbroker can be used for automated test of BECM module on basetech level (Autosar).
The communication to BECM is done via CAN using Raspberry and CanCase2.
The CAN interface on Raspberry is accessed using SignalBroker.
Testscripts are done using Python and GRPC supplied by Signalbroker.

Hardware used is Raspberry Pi3, CanCase2, BECM module including CVTN, CMS and ODTB2.

Software used: CSP/Signalbroker (from gitlab) and Python 3.7 (or later). 


## Setup

  sudo apt install libxslt-dev
  pip3 install -r requirements.txt
