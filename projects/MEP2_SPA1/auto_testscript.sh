#!/bin/bash

### token and pass created for tht repo
    TESTREPO=~/Repos/odtb2pilot
	export PYTHONPATH=~/Repos/odtb2pilot/Py_testenv/:.
    echo variables used in testrun:
	echo TESTREPO: $TESTREPO
	echo PYTHONPATH: $PYTHONPATH
	echo PATH: $PATH

	cd ~/testrun
	[ ! -d VBF ] && mkdir VBF
	rm -f VBF/*
	cp ~/delivery/*.vbf VBF
	cp ~/SBL/*.vbf VBF

	[ ! -d VBF_Reqprod ] && mkdir VBF_Reqprod
	rm -f VBF_Reqprod/*
	cp $TESTREPO/autotest/VBF_Reqprod_SPA/* VBF_Reqprod

	[ ! -d parameters_yml ] && mkdir parameters_yml
	rm -f parameters_yml/*
	cp $TESTREPO/yml_parameter/MEP2_SPA1/* parameters_yml

	### Generate catalog for logfiles and list of scripts to run
	TESTRUN=$(date +Testrun_%Y%m%d_%H%M_BECM_BT)
	[ ! -d $TESTRUN ] && mkdir $TESTRUN
	echo "Results of testrun $TESTRUN:" >$TESTRUN\/Result.txt

	### collect all testscripts
	find $TESTREPO/test_cases  -name BSW_REQPROD_*.py >testscripts.lst
	find $TESTREPO/test_cases_old -name BSW_REQPROD_*.py >>testscripts.lst
	find $TESTREPO/manual_test -name BSW_REQPROD_*.py >>testscripts.lst

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