#!/bin/bash

### token and pass created for tht repo
TESTREPO=~/Repos/odtb2pilot
###ODTBPROJ=my_odtb_proj
ODTBPROJ=MEP2_SPA1

export ODTBPROJPATH=$TESTREPO/projects/$ODTBPATH
echo export ODTBPROJPARAM=$ODTBPROJPARAM

export PYTHONPATH=$TESTREPO/:.
export PYTHONPATH=$TESTREPO/projects/project_template:$PYTHONPATH
echo export PYTHONPATH=$PYTHONPATH

cd ~/testrun

# Copying files from Py_testenv to projects/odtb2/python/ where it can be found
#cp -u $TESTREPO/Py_testenv/*.py ~/projects/odtb2/python/

### GRPC catalog needed for using GRPC in Python scripts
#export PYTHONPATH=$HOME/projects/odtb2/python

# Generate testreport
echo
echo "Generate html-report for all scripts - Start"
python3 $TESTREPO/projects/project_templates/automated_testrun/logs_to_html.py --logs ~/testrun --reqcsv $TESTREPO/autotest/req_bsw.csv --script_folder $TESTREPO/ --outfile index.html
echo "Generate html-report for all scripts - Done"
