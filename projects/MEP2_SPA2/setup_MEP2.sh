#!/bin/bash

### token and pass created for tht repo
	TESTREPO=~/Repos/odtb2pilot
	ODTBPROJ=MEP2_SPA2

	export ODTBPROJPARAM=$TESTREPO/projects/$ODTBPROJ/
	echo export ODTBPROJPARAM=$ODTBPROJPARAM

	export PYTHONPATH=~/Repos/odtb2pilot/Py_testenv/:.

	export PYTHONPATH=$TESTREPO/projects/$ODTBPROJ:$PYTHONPATH
	export PYTHONPATH=$TESTREPO/projects/$ODTBPROJ/generated:$PYTHONPATH

