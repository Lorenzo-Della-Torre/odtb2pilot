#!/bin/bash

### token and pass created for tht repo
    TESTREPO=~/Repos/odtb2pilot
    export ODTBPROJ=becm_p319
    echo export ODTBPROJ=becm_p319

    export ODTBPROJPARAM=$TESTREPO/projects/$ODTBPROJ/
    echo export ODTBPROJPARAM=$ODTBPROJPARAM

    export PYTHONPATH=$TESTREPO:.
    echo export PYTHONPATH=$PYTHONPATH

