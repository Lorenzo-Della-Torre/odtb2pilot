Readme for testcase_picker.py

This is instructions regarding how to run testcase_picker.py which picks
the desired testscripts from a selection and return them as a list.



Prerequisites
-------------


Usage
-----
You execute the python script in your command prompt window.

usage: testcase_picker.py [-h] [--swrs SWRS] [--txt_file TXT_FILE] [--scripts SCRIPTS] [--script_folder SCRIPT_FOLDER]

Picks the desired testscripts from a selection

optional arguments:
  -h, --help            			show this help message and exit
  --swrs SWRS           			Elektra rif export, xml-file. SWRS file with requirements which should be tested.
  --txtfile TXT_FILE	   			Textfile with list of files which should be tested
  --scripts SCRIPTS     			List of files which should be tested
  --scriptfolder SCRIPT_FOLDER		Folder where the scripts are located

**Examples**
Using SWRS as input:
python testcase_picker.py --swrs ..\Repo\odtb2pilot\autotest\NOTE-SWRS-33754905-01-2.xml
						  --scriptfolder ..\Repo\odtb2pilot\test_folder\automated

Using textfile as input:
python testcase_picker.py --txtfile ..\Repo\odtb2pilot\test_folder\automated\smoke_test.txt
						  --scriptfolder ..\Repo\odtb2pilot\test_folder\automated

Using argument as input:
python testcase_picker.py --scripts BSW_REQPROD_52287_S3Server_timer_timeout_in_SBL_1_1_part.py
						  --scripts e_53913_-_1_ECUs_with_multiple_networks_P319.py
						  --scriptfolder ..\Repo\odtb2pilot\test_folder\automated

Using only --scriptfolder
python testcase_picker.py --scriptfolder ..\Repo\odtb2pilot\test_folder


** It is also possible to execute these functions from another script, like below. **
def main(margs):
    """ Main function """
    included, excluded = testcase_picker.execute(margs.swrs, margs.txt_file, margs.scripts, margs.script_folder)

** The arguments to that script should be the same as it is in testcase_picker. **
Example. If you have a script called starter.py: **
python starter.py --txtfile ..\Repo\odtb2pilot\test_folder\automated\smoke_test.txt
                  --scriptfolder ..\Repo\odtb2pilot\test_folder
