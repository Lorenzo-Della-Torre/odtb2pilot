#!/bin/bash

SERVICE="python3"
if pgrep -x "$SERVICE" >/dev/null
then
	echo "Can't start testrun: $SERVICE is already running"
else
	echo "Start automated testrun"

### token and pass created for tht repo
	TESTREPO=~/Repos/odtb2pilot
	cd $TESTREPO
	git pull
	cd ~/testrun

	cp -u $TESTREPO/Py_testenv/*.py ~/projects/odtb2/python/

	### GRPC catalog needed for using GRPC in Python scripts
	export PYTHONPATH=$HOME/projects/odtb2/python

	### Generate catalog for logfiles and list of scripts to run
	TESTRUN=$(date +Testrun_%Y%m%d_%H%M_BECM_BT)
	mkdir $TESTRUN
	echo "Results of testrun $TESTRUN:" >$TESTRUN\/Result.txt

	### collect all testscripts
	#find $TESTREPO/testscripts -name BSW_REQPROD_*.py >testscripts.lst
	find $TESTREPO/test_cases  -name BSW_REQPROD_*.py >testscripts.lst
	find $TESTREPO/test_cases_old -name BSW_REQPROD_*.py >>testscripts.lst
	find $TESTREPO/manual_test -name BSW_REQPROD_*.py >>testscripts.lst


	#sed -E 's/(.*BSW_REQPROD)(.*)(\.py)/python3 \1\2\3 >BSW_REQPROD\2.log/' testscripts.lst >all_scripts.sh
	# chmod 755 all_scripts.sh
	# ./all_scripts.sh

	# Needed for parse_sddb. At the moment it is simpler to provide the result from parse_sddb.
	# Otherwise we need to change the startscript when we change sddb-file (or rename the file).
	#pip3 install lxml
	#sudo apt-get install libxml2-dev libxslt-dev
	#python3 $TESTREPO/dids_from_sddb_checker/parse_sddb.py --sddb 32290001_AD.sddb
	echo "Start generate did report"
	python3 $TESTREPO/dids_from_sddb_checker/dids_from_sddb_checker.py
	echo "Generate did report done"

	### Run all testscripts found:
	while IFS= read -r line
	do
		echo $line | sed -E "s/(.*BSW_REQPROD)(.*)(\.py)/python3 \1\2\3 >$TESTRUN\/BSW_REQPROD\2.log/"
		script2run_log=$(echo $line | sed -E "s/(.*BSW_REQPROD)(.*)(\.py)/BSW_REQPROD\2.log/")
		python3 $line >$TESTRUN/$script2run_log
	### add REQ_NR, scriptresult, filename to result
		req_tested=$(echo $line | sed -E "s/(.*BSW_REQPROD_)([0-9]*)(_.*)/\2/")
		testresult=$(tail -1 $TESTRUN/$script2run_log | sed -E "s/(Testcase result: )(.*)/\2/")
		echo "$req_tested $testresult $script2run_log"
		echo "$req_tested $testresult $script2run_log" >>$TESTRUN\/Result.txt
	done <testscripts.lst

	# Generate testreport
	python3 $TESTREPO/autotest/logs_to_html.py --logs ~/testrun --reqcsv ~/Repos/odtb2pilot/autotest/req_bsw.csv --script_folder ~/Repos/odtb2pilot/ --outfile index.html

    echo
	echo "ToDo:"
	echo "Tests done...parse logfiles for PASS/FAILED"
	echo "add results for implicitly tested requirements"
	echo "handle requirements verified by several test(scripts)"
	echo "handle requirements verified manually"
	echo ""
	#echo "Test done." >>$TESTRUN\/Result.txt
	date "+Test done. Time: %Y%m%d %H%M" 
	date "+Test done. Time: %Y%m%d %H%M" >>$TESTRUN\/Result.txt
fi