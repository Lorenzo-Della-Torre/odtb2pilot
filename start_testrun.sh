#!/bin/bash

### token and pass created for tht repo
TESTREPO=~/Repos/testbranch/odtb2pilot
cd $TESTREPO
git pull
cd ~/testrun

cp -u $TESTREPO/Py_testenv/*.py ~/projects/signalbroker/doc/grpc/grpc_python/

### GRPC catalog needed for using GRPC in Python scripts
export PYTHONPATH=$HOME/projects/signalbroker/doc/grpc/grpc_python

### Generate catalog for logfiles and list of scripts to run
TESTRUN=$(date +Testrun_%Y%m%d_%H%M_BECM_BT)
mkdir $TESTRUN
echo "Results of testrun $TESTRUN:" >$TESTRUN\/Result.txt

### collect all testscripts
find $TESTREPO/test_cases -name BSW_REQPROD_*.py >testscripts.lst
find $TESTREPO/test_cases_old -name BSW_REQPROD_*.py >>testscripts.lst

#sed -E 's/(.*BSW_REQPROD)(.*)(\.py)/python3 \1\2\3 >BSW_REQPROD\2.log/' testscripts.lst >all_scripts.sh
# chmod 755 all_scripts.sh
# ./all_scripts.sh

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

$TESTREPO/autotest/logs_to_html.py --logfolder testrun/Testrun_20200702_0359_BECM_BT --reqcsv $TESTREPO/autotest/req_bsw.csv

echo "ToDo:"
echo "Tests done...parse logfiles for PASS/FAILED"
echo "add results for implicitly tested requirements"
echo "handle requirements verified by several test(scripts)"
echo "handle requirements verified manually"
echo ""
#echo "Test done." >>$TESTRUN\/Result.txt
date "+Test done. Time: %Y%m%d %H%M" >>$TESTRUN\/Result.txt
date "+Test done. Time: %Y%m%d %H%M" >>$TESTRUN\/Result.txt

