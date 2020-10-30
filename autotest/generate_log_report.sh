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

# Generate testreport
echo
echo "Generate html-report for all scripts - Start"
python3 $TESTREPO/autotest/logs_to_html.py --logs ~/testrun --reqcsv ~/Repos/odtb2pilot/autotest/req_bsw.csv --script_folder ~/Repos/odtb2pilot/ --outfile index.html
echo "Generate html-report for all scripts - Done"