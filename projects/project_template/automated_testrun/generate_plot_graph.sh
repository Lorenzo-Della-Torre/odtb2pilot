#!/bin/bash

### token and pass created for tht repo
###TESTREPO=~/Repos/odtb2pilot
###cd $TESTREPO
###cd ~/testrun

# Generate test stats plot graph
echo "Generate test stats plot graph - Start"
python3 $TESTREPO/autotest/local_stats_plot.py --resultfolder . --outplot stats_plot
echo "Generate test stats plot graph - Done"
