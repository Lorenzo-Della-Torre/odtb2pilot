#!/bin/bash

### token and pass created for tht repo
    TESTREPO=~/Repos/odtb2pilot
    export ODTBPROJ=hvbm_p519_sa1
    echo export ODTBPROJ=hvbm_p519_sa1

    export ODTBPROJPARAM=$TESTREPO/projects/$ODTBPROJ/
    echo export ODTBPROJPARAM=$ODTBPROJPARAM

### PYTHON needs to look in current catalog 
    export PYTHONPATH=$TESTREPO:.
    echo export PYTHONPATH=$PYTHONPATH

