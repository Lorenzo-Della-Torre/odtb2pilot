#!/bin/bash

### token and pass created for tht repo
    TESTREPO=~/Repos/odtb2pilot
    ODTBPROJ=MEP2_SPA2

    export ODTBPROJPARAM=$TESTREPO/projects/$ODTBPROJ/
    echo export ODTBPROJPARAM=$ODTBPROJPARAM

### PYTHON needs to look in current catalog 
    export PYTHONPATH=~/Repos/odtb2pilot/:.
    echo export PYTHONPATH=$PYTHONPATH

