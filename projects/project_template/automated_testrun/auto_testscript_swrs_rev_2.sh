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


### Generate catalog for logfiles and list of scripts to run
    TESTRUN=$(date +Testrun_%Y%m%d_%H%M_BECM_BT)
    [ ! -d $TESTRUN ] && mkdir $TESTRUN
    echo "Results of testrun $TESTRUN:" >$TESTRUN\/Result.txt

	# For smoketest (Cherrypicked scripts)
	#python3 $TESTREPO/autotest/testcase_picker.py --txtfile $TESTREPO/autotest/smoke_test.txt --script_folder $TESTREPO/test_folder > testscripts_auto.lst
	
	# SWRS Testing
	python3 $TESTREPO/autotest/testcase_picker.py --swrs NOTE-SWRS-33754905-01-2.xml --scriptfolder $TESTREPO/test_folder > testscripts_auto.lst

    ### Run all testscripts found:
    while IFS= read -r line
    do
		echo "###############################################################"
		echo "Origin: $line"
		echo $line | sed -E "s/(.*e_)([0-9]{3,}.*)(\.py)/python3 \1\2\3 >$TESTRUN\/e_\2.log/"
        script2run_log=$(echo $line | sed -E "s/(.*e_)([0-9]{3,}.*)(\.py)/e_\2.log/")
		echo $script2run_log
		echo "###############################################################"
        python3 $TESTREPO/test_folder/on_the_fly_test/BSW_Set_ECU_to_default.py
        python3 $line >$TESTRUN/$script2run_log
        ### add REQ_NR, scriptresult, filename to result
        req_tested=$(echo $line | sed -E "s/(.*?e_)([0-9]{3,})(_.*)/\2/")
        testresult=$(tail -1 $TESTRUN/$script2run_log | sed -E "s/(Testcase result: )(.*)/\2/")
  		echo "###############################################################"
		echo "Requirement: $req_tested"
		echo "Testresult: $testresult"
		echo "Log: $script2run_log"
		echo "###############################################################"
        echo "$req_tested $testresult $script2run_log" >>$TESTRUN\/Result.txt
    done <testscripts_auto.lst


    echo
    date "+Test done. Time: %Y%m%d %H%M" 
    date "+Test done. Time: %Y%m%d %H%M" >>$TESTRUN\/Result.txt
