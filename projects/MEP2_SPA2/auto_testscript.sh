#!/bin/bash

### token and pass created for that repo
    TESTREPO=~/Repos/odtb2pilot
### adopt ODTBPROJ to fit your local project setting
###    ODTBPROJ=my_odtb_proj
    ODTBPROJ=MEP2_SPA2
    ODTBPROJPARAM=$TESTREPO/projects/$ODTBPROJ
    echo export ODTBPROJPARAM=$ODTBPROJPARAM

    ###export PYTHONPATH=$TESTREPO/:.
    ###export PYTHONPATH=$TESTREPO/projects/project_template:$PYTHONPATH
    export PYTHONPATH=$TESTREPO:$ODTBPROJPARAM:.
    echo export PYTHONPATH=$PYTHONPATH

### show environment variables used in automated testrun:
    echo Variables used in testrun:
    echo TESTREPO: $TESTREPO
    echo ODTBPROJPARAM $ODTBPROJPARAM
    echo PYTHONPATH: $PYTHONPATH
    echo PATH: $PATH

### VBF files update in $TESTREPO/projects/$ODTBPROJ
    [ ! -d $TESTREPO/projects/$ODTBPROJ/VBF && mkdir $TESTREPO/projects/$ODTBPROJ/VBF
    rm -f $TESTREPO/projects/$ODTBPROJ/VBF/*
    cp ~/delivery/*.vbf $TESTREPO/projects/$ODTBPROJ/VBF
    cp ~/SBL/*.vbf $TESTREPO/projects/$ODTBPROJ/VBF


### uncomment if VBF should be updated in local catalog:
###    [ ! -d VBF ] && mkdir VBF
###    rm -f VBF/*
###    cp ~/delivery/*.vbf VBF
###    cp ~/SBL/*.vbf VBF


### Generate catalog for logfiles and list of scripts to run
    TESTRUN=$(date +Testrun_%Y%m%d_%H%M_BECM_BT)
    [ ! -d $TESTRUN ] && mkdir $TESTRUN
    echo "Results of testrun $TESTRUN:" >$TESTRUN\/Result.txt

### collect all testscript, chose subcatalog separately or all existing:
###    find $TESTREPO/test_folder/automated/ -name BSW_REQPROD_*.py >testscripts.lst
###    find $TESTREPO/test_folder/manual/ -name BSW_REQPROD_*.py >>testscripts.lst
###    find $TESTREPO/test_folder/not_applicable/ -name BSW_REQPROD_*.py >>testscripts.lst
    find $TESTREPO/test_folder/ -name BSW_REQPROD_*.py >testscripts.lst

    ### Run all testscripts found:
    while IFS= read -r line
    do
        echo $line | sed -E "s/(.*BSW_REQPROD)(.*)(\.py)/python3 \1\2\3 >$TESTRUN\/BSW_REQPROD\2.log/"
        script2run_log=$(echo $line | sed -E "s/(.*BSW_REQPROD)(.*)(\.py)/BSW_REQPROD\2.log/")
        python3 $TESTREPO/autotest/BSW_ECU_restore_SWDL.py
        python3 $line >$TESTRUN/$script2run_log
        ### add REQ_NR, scriptresult, filename to result
        req_tested=$(echo $line | sed -E "s/(.*BSW_REQPROD_)([0-9]*)(_.*)/\2/")
        testresult=$(tail -1 $TESTRUN/$script2run_log | sed -E "s/(Testcase result: )(.*)/\2/")
        #echo "$req_tested $testresult $script2run_log"
        echo "$req_tested $testresult $script2run_log" >>$TESTRUN\/Result.txt
    done <testscripts.lst

    echo
    date "+Test done. Time: %Y%m%d %H%M" 
    date "+Test done. Time: %Y%m%d %H%M" >>$TESTRUN\/Result.txt
