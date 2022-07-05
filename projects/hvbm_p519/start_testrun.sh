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
    echo TESTREPO: $TESTREPO
    echo ODTBPROJ: $ODTBPROJ
    echo ODTBPROJPARAM: $ODTBPROJPARAM
    echo PYTHONPATH: $PYTHONPATH
    
    cd $TESTREPO

    echo "------------- Git pull ------------"
    git pull

    echo "------------- Install packages ------------"
    pip3 install -r requirements.txt

    cd ~/testrun
    $TESTREPO/projects/project_template/automated_testrun/auto_testscript_swrs_rev_5_analytics.sh

    echo "----------- Generate did report ---------"
    python3 $TESTREPO/manage.py did_report

    echo "----------- Generate test stats plot graph ---------"
    $TESTREPO/projects/project_template/automated_testrun/generate_plot_graph.sh

    echo "----------- Generate log report ---------"
    $TESTREPO/projects/project_template/automated_testrun/generate_log_report.sh
    
    echo
    echo "All scripts executed. All html reports generated"
fi

