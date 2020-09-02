#!/bin/bash

### token and pass created for tht repo
TESTREPO=~/Repos/odtb2pilot
cd $TESTREPO
cd ~/testrun

### GRPC catalog needed for using GRPC in Python scripts
export PYTHONPATH=$HOME/projects/odtb2/python

# Generate DID report
# Needed for parse_sddb. At the moment it is simpler to provide the result from parse_sddb.
# Otherwise we need to change the startscript when we change sddb-file (or rename the file).
#pip3 install lxml
#sudo apt-get install libxml2-dev libxslt-dev
#python3 $TESTREPO/dids_from_sddb_checker/parse_sddb.py --sddb 32290001_AD.sddb
echo
echo "Generate did report - Start"
python3 $TESTREPO/dids_from_sddb_checker/dids_from_sddb_checker.py
echo "Generate did report - Done"