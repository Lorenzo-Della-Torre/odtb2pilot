#!/bin/bash

### token and pass created for tht repo
	TESTREPO=~/Repos/odtb2pilot
	ODTBPROJ=MEP2_SPA1

	export ODTBPROJPARAM=$TESTREPO/projects/$ODTBPROJ/
	echo export ODTBPROJPARAM=$ODTBPROJPARAM

        export PYTHONPATH=~/Repos/odtb2pilot/:.
###     export PYTHONPATH=~/Repos/odtb2pilot/supportfunctions/:.

        export PYTHONPATH=$TESTREPO/projects/project_template:$PYTHONPATH
###        export PYTHONPATH=$TESTREPO/projects/$ODTBPROJ:$PYTHONPATH
###        export PYTHONPATH=$TESTREPO/projects/project_template/protogenerated:$PYTHONPATH
        echo export PYTHONPATH=$PYTHONPATH

