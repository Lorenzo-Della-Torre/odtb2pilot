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

	# Execute test scripts
	./auto_testscript.sh
	
	# Generate log report
	./generate_log_report.sh
	
	# Generate did report
	./generate_did_report.sh

	echo
	echo "All scripts executed. All html reports generated"
fi