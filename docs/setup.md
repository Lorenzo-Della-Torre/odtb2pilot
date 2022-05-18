## Setup

### Naming

In order to keep track of all the instances of Hilding we need to keep the naming consistent.

Only lower case letters are allowed. For rigs that are used for a specific
project, use the following naming scheme:

```
<ecu-name>-<vehicle-project>-pi<number>
```

Example project rig host names:
 - hvbm_p519_sa1-pi1
 - becm_p319-pi1
 - hlcm_p519-pi1
 - ihfa_v436-pi1

For rigs that are used by a specific ART:

```
<art-name>-pi<number>
```

Example ART rig host names:
 - bsw-pi1
 - eps-pi1

## Setting up SSH keys locally and on remote

If you are on windows use Powershell as administrator and add ssh according to
the instructions you find here:
https://jcutrer.com/windows/install-openssh-on-windows10

run (only once):
  ssh-keygen

and accept the defaults. There is no need to set any password for the key.

Copy content of id_rsa.pub and add it to ~/.ssh/authorized_keys on the
remote raspberry pi (or on the same host if you are configuring a raspberry pi
rig).

Now connect to the raspberry pi and you should not need to enter the password
since you are already authenticated.
for example:
  ssh pi@bsw-piX.dhcp.nordic.volocars.net

run:
  ./manage.py rigs --update


and all the vbf, dbf, and sddb files will be copied over to the rigs/<rigname>/
directories.

Note: make sure that you connect with ssh to the host first so that the host
gets added to the .ssh/knows_hosts file.

To make using ssh more convenient add a config file with the rigs that you
typically use (in ~/.ssh/config):

        Host pX
          Hostname bsw-piX.dhcp.nordic.volvocars.net
          User ci

Then you can directly connect to the rig with the user 'ci' as follows: ssh pX


### Configuring the software on the raspberry pi

Clone this repository. If you are setting up a Raspberry Pi for CI, then you
probably want to use "Deploy Token" with read access. Otherwise, use your CDSID
credentials.

Next step is to get all dependencies:

```shell
  sudo apt update # you might need to update url, have a look at https://pimylifeup.com/raspbian-repository-mirror/
  sudo apt upgrade
  sudo apt install libxslt-dev unixodbc-dev tdsodbc libopenjp2-7 sqlite3 fzf
  pip3 install -r requirements.txt
```

Make sure you run the pip3 install in the Hilding root directory (odtb2pilot or
whatever you've called it) to include the packeges/epsmsgbus as well.

### Enabling analytics on Hilding

configure conf_local.yml...

rigs:
    p6ci:
        hostname: bsw-pi6.dhcp.nordic.volvocars.net
        platform: becm_p319
        user: ci
        analytics:
            project: V331
            platform: V331
            ecu: BECM
            dbc: SPA3010_ConfigurationsSPA3_Front1CANCfg_180615_Prototype
            vehicle_project: V331

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


#### Optional feature: git support for the test runner

As a tester we tend to work on many different tests and switch back and forth
between different branches. Most of the time we name our branches with
something including the reqprod number (e.g. req_12345). manage.py has support
for directly running the right script from the current branch name if you have
the python package `pygit2` installed.

Just run
```
  python manage.py run
```
and if we are on the branch `req_12345` manage.py will automatically select any
scripts in the `test_folder/automated` directory that contains `12345`. This
can be quite convenient; especially for reviewers that frequently switches from
one branch to another.

Currently on raspberry pi we need to build libgit2 manually from source as it
is now:
```shell
  sudo apt install cmake
  mkdir ~/software
  cd ~/software
  wget --no-check-certificate https://github.com/libgit2/libgit2/releases/download/v1.1.0/libgit2-1.1.0.tar.gz
  tar xzf libgit2-1.1.0.tar.gz
  cd libgit2-1.1.0/
  cmake .
  make
  sudo make install
```
