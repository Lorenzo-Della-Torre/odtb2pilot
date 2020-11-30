#!/bin/bash

SERVICE="python3"
if pgrep -x "$SERVICE" >/dev/null
then
	echo "Can't start testrun: $SERVICE is already running"
else
	echo "Start automated testrun"

	### token and pass created for tht repo
	export TESTREPO=~/Repos/odtb2pilot
	export ODTBPROJ=MEP2_SPA1
        cd $TESTREPO
	git pull
	cd ~/testrun

	# Execute test scripts
###	./auto_testscript.sh
        $TESTREPO/projects/project_template/automated_testrun/auto_testscript.sh

	# Generate did report
###	$TESTREPO/projects/$ODTBPROJ/generate_did_report.sh
        $TESTREPO/projects/project_template/automated_testrun/generate_did_report.sh

	# Generate test stats plot graph
###	$TESTREPO/projects/$ODTBPROJ/generate_plot_graph.sh
        $TESTREPO/projects/project_template/automated_testrun/generate_plot_graph.sh

	# Generate log report
###	$TESTREPO/projects/$ODTBPROJ/generate_log_report.sh
        $TESTREPO/projects/project_template/automated_testrun/generate_log_report.sh
	
	echo
	echo "All scripts executed. All html reports generated"
fi
