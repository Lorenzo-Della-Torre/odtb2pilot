#!/bin/bash

### token and pass created for tht repo
TESTREPO=~/Repos/odtb2pilot
cd $TESTREPO
cd ~/testrun

### GRPC catalog needed for using GRPC in Python scripts
export PYTHONPATH=$HOME/projects/odtb2/python

# Generate testreport
python3 $TESTREPO/autotest/logs_to_html.py --logs ~/testrun --reqcsv ~/Repos/odtb2pilot/autotest/req_bsw.csv --script_folder ~/Repos/odtb2pilot/ --outfile index.html