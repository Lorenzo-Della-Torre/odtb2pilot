#!/bin/bash

echo Test2
export PYTHONPATH=/home/ci/Repos/odtb2pilot/Py_testenv/:.

#Input 1 username Input 2 pass Input 3 Url to deliveryfile
[ ! -d "./delivery" ] && mkdir "delivery"

#remove remaining logs from older testruns if existing
rm -r ./testrun/Testrun_20*

cd delivery
rm -f *.vbf
rm -f *.zip
rm -f *.sddb
rm -f *.dbc

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
	unzip -p delivery.zip | busybox unzip - -j */DBCfiles/*.dbc
	echo "dbc File unzipped"
	unzip -p delivery.zip | busybox unzip - -j */Sddb/*.sddb
	echo "sddb File unzipped"

	cd ~/testrun
	. ./setup_MEP2.sh
	rm -f $TESTREPO/projects/$ODTBPROJ/VBF/*
	cp ~/delivery/*.vbf $TESTREPO/projects/$ODTBPROJ/VBF
	cp ~/SBL/*.vbf $TESTREPO/projects/$ODTBPROJ/VBF

	echo "All files in place, starting SWDL"
	python3 $TESTREPO/test_folder/on_the_fly_test/BSW_SWDL.py >BSW_SWDL_delivery.log
#start testrun of all testscripts in odtb2pilot repo
	echo "SW Download finished, starting tests"
	./start_testrun.sh
else
	echo "Error during download of SW from Artifactory. Terminating." >&2
	exit 1
fi
