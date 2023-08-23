#!/bin/bash
    export TESTREPO=~/Repos/odtb2pilot
### TESTREPO and ODTBPRO taken from environment variables
    ODTBPROJPARAM=$TESTREPO/projects/$ODTBPROJ
    echo export ODTBPROJPARAM=$ODTBPROJPARAM

### show environment variables used in automated testrun:
    echo Variables used in testrun:
    echo TESTREPO: $TESTREPO
    echo ODTBPROJPARAM $ODTBPROJPARAM
    echo PYTHONPATH: $PYTHONPATH
    echo PATH: $PATH
<< com
### VBF files update in $TESTREPO/projects/$ODTBPROJ
    [ ! -d $TESTREPO/projects/$ODTBPROJ/VBF ] && mkdir $TESTREPO/projects/$ODTBPROJ/VBF
    rm -f $TESTREPO/projects/$ODTBPROJ/VBF/*
    cp ~/delivery/*.vbf $TESTREPO/projects/$ODTBPROJ/VBF
    cp ~/SBL/*.vbf $TESTREPO/projects/$ODTBPROJ/VBF
com

### uncomment if VBF should be updated in local catalog:
###    [ ! -d VBF ] && mkdir VBF
###    rm -f VBF/*
###    cp ~/delivery/*.vbf VBF
###    cp ~/SBL/*.vbf VBF


### Generate catalog for logfiles and list of scripts to run
    TESTRUN=$(date +Testrun_%Y%m%d_%H%M_ECM_VBFs_download)
    [ ! -d $TESTRUN ] && mkdir $TESTRUN
    echo "Results of testrun $TESTRUN:" >$TESTRUN\/Result.txt

	# SWRS Testing
	python3 $TESTREPO/autotest/testcase_picker.py --txtfile $TESTREPO/projects/ecm_phev/vbf_download.txt --scriptfolder $TESTREPO/test_folder/automated > testscripts_auto.lst

    ### Run all testscripts found:
    while IFS= read -r line
    do
		echo "Origin: $line"
		echo $line | sed -E "s/(.*e_)([0-9]{3,}.*)(\.py)/python3 \1\2\3 >$TESTRUN\/e_\2.log/"
                script2run_log=$(echo $line | sed -E "s/(.*e_)([0-9]{3,}.*)(\.py)/e_\2.log/")
		echo $script2run_log
		script2run=$(echo $line | sed -E "s/(.*e_)([0-9]{3,}.*)(\.py)/e_\2.py/")
	        echo $script2run
       # echo "Set ECU to default"
#		python3 $TESTREPO/test_folder/on_the_fly_test/BSW_Set_ECU_to_default.py >/dev/null
        python3 $TESTREPO/manage.py run $script2run >$TESTRUN/$script2run_log
        ### add REQ_NR, scriptresult, filename to result
        req_tested=$(echo $line | sed -E "s/(.*?e_)([0-9]{3,})(_.*)/\2/")
        testresult=$(tail -1 $TESTRUN/$script2run_log | sed -E "s/(INFO dut Testcase result: )(.*)/\2/")
	#vbf=$(cat $TESTRUN/$script2run_log | sed -En "s/(INFO root Data)(.*vbf_list_ecm\/)(.*AA.vbf).*$/\3/p")
	vbf=$(cat $TESTRUN/$script2run_log | sed -En "s/(INFO root Data)(.*vbf_list_ecm\/)(.*AA.vbf).*$/\3/p")
	calid=$(cat $TESTRUN/$script2run_log | sed -En "s/(INFO root Cal ID)(.*)/\2/p")
	cvn=$(cat $TESTRUN/$script2run_log | sed -En "s/(INFO root CVN)(.*)/\2/p")
	engine=$(cat $TESTRUN/$script2run_log | sed -En "s/(INFO root Engine, Platform )(.*)/\2/p")
	pn=$(cat $TESTRUN/$script2run_log | sed -En "s/(INFO root Part number)(.*)/\2/p")
		echo "Requirement: $req_tested"
		echo "Testresult: $testresult"
		echo "Log: $script2run_log"
		echo "vbf: $vbf"
		echo "Cal ID: $calid"
		echo "CVN: $cvn"
		echo "Engine, Platform: $engine"
		echo "Part number: $pn"
        echo -e "$req_tested\n $testresult\n $script2run_log\n" >>$TESTRUN\/Result.txt
        echo -e "$vbf\n $calid\n $cvn\n $engine\n $pn\n" >>$TESTRUN\/list_elem.txt
	#python3 dict.py
    done <testscripts_auto.lst




    echo
    date "+Test done. Time: %Y%m%d %H%M" 
    date "+Test done. Time: %Y%m%d %H%M" >>$TESTRUN\/Result.txt
