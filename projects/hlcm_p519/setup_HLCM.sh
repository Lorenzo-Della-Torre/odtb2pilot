#!/bin/bash

### token and pass created for tht repo
    TESTREPO=~/Repos/odtb2pilot
    export ODTBPROJ=MEP2_HLCM
    echo export ODTBPROJ=MEP2_HLCM

    export ODTBPROJPARAM=$TESTREPO/projects/$ODTBPROJ/
    echo export ODTBPROJPARAM=$ODTBPROJPARAM

### PYTHON needs to look in current catalog 
    export PYTHONPATH=$TESTREPO:.
    echo export PYTHONPATH=$PYTHONPATH

