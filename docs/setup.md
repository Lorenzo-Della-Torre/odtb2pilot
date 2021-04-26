
## Setup

### Naming

In order to keep track of all the instances of Hilding we need to keep the naming consistent.

Only lower case letters are allowed. For rigs that are used for a specific
project, use the following naming scheme:

```
<project-name>-<ecu-type>-pi<number>
```

Example project rig host names:
 - p519-hvbm-pi1
 - p319-becm-pi1
 - p519-hlcm-pi1
 - p519-ed-ihfa-pi1

For rigs that are used by a specific ART:

```
<art-name>-pi<number>
```

Example ART rig host names:
 - bsw-pi1
 - eps-pi1


### Configuring the software on the raspberry pi

Clone this repository. If you are setting up a Raspberry Pi for CI, then you
probably want to use "Deploy Token" with read access. Otherwise, use your CDSID
credentials.

Next step is to get all dependencies:

```shell
  sudo apt install libxslt-dev unixodbc-dev tdsodbc
  pip3 install -r requirements.txt
```

And let's build libgit2 from source:
```shell
  wget https://github.com/libgit2/libgit2/releases/download/v1.1.0/libgit2-1.1.0.tar.gz
  tar xzf libgit2-1.1.0.tar.gz
  cd libgit2-1.1.0/
  cmake .
  make
  sudo make install
```

NOTE: `<platform>` has to be replaced with the name of the platform that you are
using in the text below (for example: MEP2_SPA1, MEP2_SPA2, or MEP2_HLCM). The
same goes for all other instances of angle brackets.

Copy `projects/odtb_conf-TEMPLATE.py` to `projects/<platform>/odtb_conf.py`.

Remember to set the address and port to the rig you will use.

```
ODTB2_DUT = '<hostname>'
ODTB2_PORT = '<port>'
```

Make sure that you have a release in the folder `projects/<platform>/release/`
containing at least a .sddb file, but also .dbc files to support more advanced
features of the platform.

You also need VBF files for the platform you want to test in the
`projects/<platform>/VBF/` directory.

In `projects/\<platform\>/` you will find a file called `setup_<platform>.py` that
contains the basic environment variables that you need to have set.

Test your installation by running the following command: `./manage.py check`

Now you are good to go if you are on your own PC. For setting up a rig, then a
few more steps are needed.

### Extra steps for rig setup

Only for rigs (i.e. computer connected to the device under test):

 * Set host name, so clients can connect to the rig
 * Define and enable interfaces (e.g. CAN)
 * Install Docker
 * Update `interfaces.json`and place it in `sb_docker/configuration` with e.g.
   links to CAN-db in `sb_docker/configuration/can`
 * Run `sb_starter.sh`
 * Make sure that the SignalBroker image is running (and add it to sysctl so it
   starts in case of reboot)

One way to ensure that communication is working properly is to connect a
CANalyzer CANcase and listen for the traffic, when starting a script from rig
computer.

#### Details about setting up SignalBroker image

The image we are using as of Feb 2021, must be restarted in order to get any
updates in `interfaces.json` and files that are referred to.

Check that the SignalBroker is running with command `docker ps -a` where
`STATUS` shall be `Up`.

