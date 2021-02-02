# ODTB2Pilot

Pilot to test if Signalbroker can be used for automated test of BECM module on basetech level (Autosar).
The communication to BECM is done via CAN using Raspberry and CanCase2.
The CAN interface on Raspberry is accessed using SignalBroker.
Testscripts are done using Python and GRPC supplied by Signalbroker.

Hardware used is Raspberry Pi3, CanCase2, BECM module including CVTN, CMS and ODTB2.

Software used: Signalbroker (from gitlab/github/dockerhub) and Python 3.7 (or later). 


## Setup
Clone this repository. If you are setting up a Raspberry Pi for CI, then you probably want to use "Deploy Token" with read access. Otherwise, use your CDSID credentials.

Next step is to get all dependencies:

```shell
  sudo apt install libxslt-dev
  pip3 install -r requirements.txt
```

Remember to set the address to the rig you will use, in `odtb2_conf.py`!

Now you are good to go if you are on your own PC. For setting up a rig, then a few more steps are needed.

### Extra steps for rig setup
Only for rigs (i.e. computer connected to the device under test)

*  Set host name, so clients can connect to the rig
*  Define and enable interfaces (eg CAN)
*  Install Docker and Docker Compose
*  Run `sb_starter.sh`
*  Update `interfaces.json`and place it in `sb_docker/configuration` with e.g. links to CAN-db in `sb_docker/configuration/can`
*  Make sure that the SignalBroker image is running (and add it to sysctl so it starts in case of reboot)

One way to ensure that communication is working properly is to connect a CANalyzer CANcase and listen for the traffic, when starting a script from rig computer.
