#!/bin/bash

### TESTREPO and ODTBPRO taken from environment variables
    ODTBPROJPARAM=$TESTREPO/projects/$ODTBPROJ
    echo export ODTBPROJPARAM=$ODTBPROJPARAM

### show environment variables used in automated testrun:
    echo Variables used in testrun:
    echo TESTREPO: $TESTREPO
    echo ODTBPROJPARAM $ODTBPROJPARAM
    echo PYTHONPATH: $PYTHONPATH
    echo PATH: $PATH

# SWRS Testing
echo "----------- Testcase picker using SWRS Rev 5 ------------"
python3 $TESTREPO/autotest/testcase_picker.py --swrs NOTE-SWRS-33754905-01-5.xml --scriptfolder $TESTREPO/test_folder > testscripts_auto.lst

echo "----------- Executing scripts from list created by Testcase picker -----------"
python3 $TESTREPO/manage.py nightly --use-db testscripts_auto.lst

date "+Test done. Time: %Y%m%d %H%M" 
