#!/bin/bash

echo Test2
export PYTHONPATH=/home/ci/Repos/odtb2pilot/Py_testenv/:.

#Input 1 username Input 2 pass Input 3 Url to deliveryfile
[ ! -d "./delivery" ] && mkdir "delivery"

rm -r ./testrun/Testrun_20*

cd delivery
rm -f *.vbf
rm -f *.zip

#curl -sS -u "$1" -o delivery.zip $3
curl -sS -u "$1:$2" -o delivery.zip $3

#echo curl direct to unzip
#unzip -p (curl -sS -u "$1:£2" $3) | busybox unzip - -j */output/[0-9]*.vbf
#unzip <(curl -sSf -u "$1:$2" $3) | busybox unzip - -j */output/[0-9]*.vbf


if [ $? -eq 0 ]
then
	echo "Delivery zip downloaded"
        unzip -p delivery.zip | busybox unzip - -j */output/[0-9]*.vbf
	echo "VBF Files unzipped"
        cd ~/testrun
        rm -f VBF/*
        cp ~/delivery/*.vbf VBF
        cp ~/SBL/*.vbf VBF

        cp -u ~/Repos/odtb2pilot/autotest/BSW_SWDL.py .
	echo "All files in place, starting SWDL"
        python3 BSW_SWDL.py >BSW_SWDL_delivery.log
#start testrun of all testscripts in odtb2pilot repo
	echo "SW Downloaded, starting tests"
        ./start_testrun.sh
else
	echo "Error during download of SW from Artifactory. Terminating." >&2
	exit 1
fi
