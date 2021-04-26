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

### VBF files update in $TESTREPO/projects/$ODTBPROJ
    [ ! -d $TESTREPO/projects/$ODTBPROJ/VBF ] && mkdir $TESTREPO/projects/$ODTBPROJ/VBF
    rm -f $TESTREPO/projects/$ODTBPROJ/VBF/*
    cp ~/delivery/*.vbf $TESTREPO/projects/$ODTBPROJ/VBF
    cp ~/SBL/*.vbf $TESTREPO/projects/$ODTBPROJ/VBF


### uncomment if VBF should be updated in local catalog:
###    [ ! -d VBF ] && mkdir VBF
###    rm -f VBF/*
###    cp ~/delivery/*.vbf VBF
###    cp ~/SBL/*.vbf VBF

# SWRS Testing
python3 $TESTREPO/autotest/testcase_picker.py --swrs NOTE-SWRS-33754905-01-5.xml --scriptfolder $TESTREPO/test_folder > testscripts_auto.lst

python3 $TESTREPO/manage.py nightly testscripts_auto.lst

date "+Test done. Time: %Y%m%d %H%M" 
