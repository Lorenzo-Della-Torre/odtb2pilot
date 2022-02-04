#!/bin/bash

### token and pass created for tht repo
    TESTREPO=~/Repos/odtb2pilot
    export ODTBPROJ=hlcm_p519
    echo export ODTBPROJ=hlcm_p519

    export ODTBPROJPARAM=$TESTREPO/projects/$ODTBPROJ/
    echo export ODTBPROJPARAM=$ODTBPROJPARAM

### PYTHON needs to look in current catalog
    export PYTHONPATH=$TESTREPO:.
    echo export PYTHONPATH=$PYTHONPATH

