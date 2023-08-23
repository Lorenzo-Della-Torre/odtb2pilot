#!/bin/bash

### TESTREPO and ODTBPROJ taken from environment variables
### token and pass created for tht repo
###TESTREPO=~/Repos/odtb2pilot
###ODTBPROJ=my_odtb_proj
###ODTBPROJ=MEP2_SPA2

echo
echo Start: generate_log_report script
echo parameter: TESTREPO: $TESTREPO
echo parameter: ODTBPROJ: $ODTBPROJ
export ODTBPROJPARAM=$TESTREPO/projects/$ODTBPROJ
echo ODTBPROJPARAM=$ODTBPROJPARAM

###export PYTHONPATH=$TESTREPO/:.
###export PYTHONPATH=$TESTREPO/projects/project_template:$PYTHONPATH
echo PYTHONPATH=$PYTHONPATH

###cd ~/testrun

# Copying files from Py_testenv to projects/odtb2/python/ where it can be found
#cp -u $TESTREPO/Py_testenv/*.py ~/projects/odtb2/python/

### GRPC catalog needed for using GRPC in Python scripts
#export PYTHONPATH=$HOME/projects/odtb2/python

# Generate testreport
echo
echo "Generate html-report for all scripts - Start"
echo "Take logs from: $TESTRUNREPO"
echo "outfile generated in: $TESTRUNREPO"
python3 $TESTREPO/projects/project_template/automated_testrun/logs_to_html.py --logs $TESTRUNREPO --reqcsv $ODTBPROJPARAM/req_bsw.csv --script_folder $TESTREPO/ --outfile $TESTRUNREPO/index.html --smoke_result $SMOKETESTRESULT
echo "Generate html-report for all scripts - Done"
