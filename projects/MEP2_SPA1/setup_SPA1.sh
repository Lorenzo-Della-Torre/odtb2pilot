#!/bin/bash

### token and pass created for tht repo
    TESTREPO=~/Repos/odtb2pilot
    ODTBPROJ=MEP2_SPA1

    export ODTBPROJPARAM=$TESTREPO/projects/$ODTBPROJ/
    echo export ODTBPROJPARAM=$ODTBPROJPARAM

    export PYTHONPATH=~/Repos/odtb2pilot/:.
    echo export PYTHONPATH=$PYTHONPATH

