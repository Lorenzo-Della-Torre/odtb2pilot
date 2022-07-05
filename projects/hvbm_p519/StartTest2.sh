#!/bin/bash

echo StartTest2
export PYTHONPATH=/home/ci/Repos/odtb2pilot/Py_testenv/:.

#Input 1 username Input 2 pass Input 3 Url to deliveryfile
[ ! -d "./delivery" ] && mkdir "delivery"

#remove remaining logs from older testruns if existing
rm -r ./testrun/Testrun_20*

echo "------- Removing files ---------"
cd delivery
rm -f *.vbf
rm -f *.zip
rm -f *.sddb
rm -f *.dbc

echo "--------- Extracting files -----------"
curl -sS -u ":$1" -o delivery.zip $2

#echo curl direct to unzip
#unzip -p (curl -sS -u "$1:£2" $3) | busybox unzip - -j */output/[0-9]*.vbf
#unzip <(curl -sSf -u "$1:$2" $3) | busybox unzip - -j */output/[0-9]*.vbf


if [ $? -eq 0 ]
then
	echo "Delivery zip downloaded"
	unzip -j delivery.zip vbf/[0-9]*.vbf
	echo "VBF Files unzipped"
	unzip -j delivery.zip dbc/*.dbc
	echo "dbc File unzipped"
	unzip -j delivery.zip sddb/*.sddb
	echo "sddb File unzipped"
	unzip -j delivery.zip doc/version.txt
	echo "version.txt File unzipped"

	cd ~/testrun

	echo "----------- Setting variables ---------"
	. ./setup_MEP2.sh

	echo "----------- Updating the rig: copying vbf, dbc, sddb ---------"
	python3 $TESTREPO/manage.py rigs --update

	echo "----------- Parsing sddb ---------"
	python3 $TESTREPO/manage.py sddb

	echo "------------ All files in place, starting SWDL ---------"
	python3 $TESTREPO/manage.py flash

	echo "------------ SW Download finished, starting tests ---------"
	./start_testrun.sh
else
	echo "Error during download of SW from Artifactory. Terminating." >&2
	exit 1
fi
