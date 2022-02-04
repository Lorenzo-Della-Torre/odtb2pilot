#!/bin/bash

### token and pass created for tht repo
    TESTREPO=~/Repos/odtb2pilot
    export TESTREPO=$TESTREPO
    export ODTBPROJ=MEP2_SPA2_SAGen2
    echo export ODTBPROJ=MEP2_SPA2_SAGen2

    export ODTBPROJPARAM=$TESTREPO/projects/$ODTBPROJ/
    echo export ODTBPROJPARAM=$ODTBPROJPARAM

### PYTHON needs to look in current catalog 
    export PYTHONPATH=$TESTREPO:.
    echo export PYTHONPATH=$PYTHONPATH

