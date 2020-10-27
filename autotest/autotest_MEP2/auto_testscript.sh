#!/bin/bash

### token and pass created for tht repo
    TESTREPO=~/Repos/odtb2pilot

	cd ~/testrun
	[ ! -d VBF ] && mkdir VBF
	rm -f VBF/*
	cp ~/delivery/*.vbf VBF

	[ ! -d VBF_Reqprod ] && mkdir VBF_Reqprod
	rm -f VBF_Reqprod/*
	cp $TESTREPO/autotest/VBF_Reqprod_MEP2/* VBF_Reqprod

	[ ! -d parameters_yml ] && mkdir parameters_yml
	rm -f parameters_yml/*
	cp $TESTREPO/yml_parameter/MEP2_SPA2/* parameters_yml

	### GRPC catalog needed for using GRPC in Python scripts
	# set PYTHONPATH in .bashrc
	# export PYTHONPATH=/home/ci/Repos/odtb2pilot/Py_testenv/:.
	#old: export PYTHONPATH=$HOME/projects/odtb2/python

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
