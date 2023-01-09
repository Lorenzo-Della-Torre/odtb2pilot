#!/bin/bash

SERVICE="python3"
if pgrep -x "$SERVICE" >/dev/null
then
    echo "Can't start testrun: $SERVICE is already running"
else
    echo "Start automated testrun"

    ### token and pass created for tht repo
    export TESTREPO=~/Repos/odtb2pilot
	export ODTBPROJ=hvbm_p519
	export ODTBPROJPARAM=$TESTREPO/projects/$ODTBPROJ
	export PYTHONPATH=$TESTREPO:$ODTBPROJPARAM:.
    export AUTOTESTRUN=$TESTREPO/projects/project_template/automated_testrun
    export TESTRUNREPO=~/testrun

    cd $TESTREPO

    echo "------------- Git pull ------------"
    git pull

    cd $AUTOTESTRUN

    echo "----------- Run smoke test -----------"
    SMOKETESTRESULT=$(python3 smoke_test.py)

    if [ $SMOKETESTRESULT == "True" ]
    then
        echo "smoke test passed"
        auto_testscript_swrs_rev_5_analytics.sh

        echo "----------- Generate did report ---------"
        python3 $TESTREPO/manage.py did_report

        # plot graph not working. waiting to be fixed
        ##echo "----------- Generate test stats plot graph ---------"
        ##$AUTOTESTRUN/generate_plot_graph.sh
    else
        # if python flow is aborted in smoke test, smoke test result != False
        SMOKETESTRESULT="False"
        echo "smoke test failed"
        # create a result test folder and format data for report
        python3 create_no_results_dir.py
    fi

    echo "----------- Generate log report ---------"
    export SMOKETESTRESULT
    sh ./generate_log_report.sh
    
    echo
    echo "All scripts executed. All html reports generated"
fi
