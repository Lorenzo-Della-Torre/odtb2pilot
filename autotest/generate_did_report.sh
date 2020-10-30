#!/bin/bash

### token and pass created for tht repo
TESTREPO=~/Repos/odtb2pilot
PYTHONPATH=~/Repos/odtb2pilot/Py_testenv/:.
cd $TESTREPO
cd ~/testrun

# Copying files from Py_testenv to projects/odtb2/python/ where it can be found
cp -u $TESTREPO/Py_testenv/*.py ~/projects/odtb2/python/

### GRPC catalog needed for using GRPC in Python scripts
#export PYTHONPATH=$HOME/projects/odtb2/python

# Generate DID report
# Needed for parse_sddb. At the moment it is simpler to provide the result from parse_sddb.
# Otherwise we need to change the startscript when we change sddb-file (or rename the file).
#pip3 install lxml
#sudo apt-get install libxml2-dev libxslt-dev
#python3 $TESTREPO/dids_from_sddb_checker/parse_sddb.py --sddb 32290001_AD.sddb
echo
echo "Generate did report - Start"
python3 $TESTREPO/dids_from_sddb_checker/dids_from_sddb_checker.py

# Copying the file containing testrun info from testrun to where logs_to_html.py can find it
# Not the prettiest solution, but will be fixed when we have the flat structure.
cp -avr ~/testrun/output ~/Repos/odtb2pilot/dids_from_sddb_checker
echo "Generate did report - Done"