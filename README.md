# ODTB2Pilot

Pilot to test if Signalbroker can be used for automated test of BECM module on
basetech level (Autosar). The communication to BECM is done via CAN using
Raspberry and CanCase2. The CAN interface on Raspberry is accessed using
SignalBroker. Testscripts are done using Python and GRPC supplied by
Signalbroker.

Hardware used is Raspberry Pi3, CanCase2, BECM module including CVTN, CMS and
ODTB2.

Software used: Signalbroker (from gitlab/github/dockerhub) and Python 3.7 (or
later). 

This documentation assumes that the reader has at least basic understanding of:
 - CAN bus communication - https://en.wikipedia.org/wiki/CAN_bus
 - UDS - https://en.wikipedia.org/wiki/Unified_Diagnostic_Services
 - Python - https://docs.python.org/3/
 - Autosar - https://www.autosar.org/
 - Linux command line
 - SSH - https://www.raspberrypi.org/documentation/remote-access/ssh/
 - SSH on windows 10 - https://www.raspberrypi.org/documentation/remote-access/ssh/windows10.md

## Documentation

 - [docs/setup.md](docs/setup.md)
 - [docs/writing-tests.md](docs/writing-tests.md)
 - [docs/dvm-generator.md](docs/dvm-generator.md)
 - [docs/unittests.md](docs/unittests.md)

