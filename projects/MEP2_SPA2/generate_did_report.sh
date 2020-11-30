#!/bin/bash

### TESTREPO and ODTBPROJ taken from environment variables
### token and pass created for tht repo
###TESTREPO=~/Repos/odtb2pilot
###ODTBPROJ=my_odtb_proj
###ODTBPROJ=MEP2_SPA2

export ODTBPROJPARAM=$TESTREPO/projects/$ODTBPATH
echo export ODTBPROJPARAM=$ODTBPROJPARAM

export PYTHONPATH=$TESTREPO/:.
export PYTHONPATH=$TESTREPO/projects/project_template:$PYTHONPATH
echo export PYTHONPATH=$PYTHONPATH

cd ~/testrun

#Not needed anymore
# Copying files from Py_testenv to projects/odtb2/python/ where it can be found
#cp -u $TESTREPO/Py_testenv/*.py ~/projects/odtb2/python/


# Generate DID report
# Needed for parse_sddb. At the moment it is simpler to provide the result from parse_sddb.
# Otherwise we need to change the startscript when we change sddb-file (or rename the file).
#pip3 install lxml
#sudo apt-get install libxml2-dev libxslt-dev
#python3 $TESTREPO/dids_from_sddb_checker/parse_sddb.py --sddb 32290001_AD.sddb

echo
echo "Generate did report - Start"
python3 $TESTREPO/projects/project_template/automated_testrun/dids_from_sddb_checker/dids_from_sddb_checker.py

# Copying the file containing testrun info from testrun to where logs_to_html.py can find it
# Not the prettiest solution, but will be fixed when we have the flat structure.
#cp -avr ~/testrun/output ~/Repos/odtb2pilot/dids_from_sddb_checker
echo "Generate did report - Done"
