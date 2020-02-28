Readme Implement_MEP2_Support_EOL

These are instructions regarding how to run:
 - parse_sddb.py
 - BSW_REQPROD_Implement_MEP2_Support_EOL_def.py
which visualizes the testresults in a generated hmtl-file.


Prerequisites
-------------
- You need to have Python 3 installed.
- A SDDB-file (an extract from Carcom II) which is matching the BECM you are going to test.
- If you already don't have it, then you need to install yattag, it generates HTML or XML in a pythonic way.
  pip install yattag


Config files
------------
	ODTB_conf.py
	------------
	For all testscripts we run, there is a config file in the "\Repo\odtb2pilot\Py_testenv" folder.
	It specifies the address which ODTB you are testing against.

	BSW_REQPROD_Implement_MEP2_Support_EOL_def_conf.py
	--------------------------------------------------
	Only affects BSW_REQPROD_Implement_MEP2_Support_EOL_def.py.
	It specifies "response_timeout" and how many DIDs you want to test. Usually you want to test
	all of the DIDs and then the value should be larger than the amount of DIDs.
	But when debugging the script it can be more efficient to only test a few.

	parameters.py
	-------------
	parameters.py is common for both "parse_sddb.py" and "BSW_REQPROD_Implement_MEP2_Support_EOL_def.py".
	It defines parameters used by both scripts.


Usage
-----
You execute the python scripts in your command prompt window.

	parse_sddb.py
	-------------
	First time you use a new SDDB-file you need to run the parse_sddb.py script, this script extracts
	the information we are interested in and put it as a dictionary in a file.

	Give the SDDB-file as an input parameter:
	Usage: parse_sddb.py [-h] --sddb SDDB
	Example: parse_sddb.py [-h] --sddb V331_2007_MP1_BECM_APL_20191114.sddb


	BSW_REQPROD_Implement_MEP2_Support_EOL_def.py
	---------------------------------------------
	This script is creating the HTML-report.

	No input parameters need to be given. It is all in the config files.
	Usage: BSW_REQPROD_Implement_MEP2_Support_EOL_def.py
	Example: BSW_REQPROD_Implement_MEP2_Support_EOL_def.py


Result
------
If successful the result will be a file called something like: result_report_31697094_AN.html.
31697094_AN is the diagnostic part number which is being tested.
If double-clicked it will open in your web-browser.