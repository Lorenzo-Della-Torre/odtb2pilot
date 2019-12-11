Readme logs_to_html.py

This is instructions regarding how to run logs_to_html.py which visualizes the testresults in a generated hmtl-file.

Prerequisites
-------------
You need to have Python 3 installed.

As input you should have one or more folders with log_files, each folder can contain an arbitrary number of log-files.
You also need a csv-file with requirement specifications from Electra.

Today we have some sample-folders with sample log-files and the csv-file here:
\\Gotsnm5104.got.volvocars.net\proj\9413-SHR-VCC125200\ScriptInputData\HtmlVisualization

I would recommend copying them to your local folder where you plan to execute the logs_to_html script.

You also need the html-lib, either found here https://pypi.org/project/html/
or on our shared disk \\Gotsnm5104.got.volvocars.net\proj\9413-SHR-VCC125200\ScriptInputData\HtmlVisualization\html-1.16

This lib needs to be somewhere where your Environment Variable PYTHONPATH is pointing. Either you put it in one of your
PYTHONPATH folders, or you add the folder with HTLM-lib to your PYTONPATH. If you change the PYTHONPATH you have to
restart the computer for the changes to take effect.

Usage
-----
You execute the python script in your command prompt window.

usage: logs_to_html.py [-h] --logfolder REPORT_FOLDER [REPORT_FOLDER ...]
                       [--reqcsv REQ_CSV] [--outfile HTML_FILE]


Example: python logs_to_html.py --logfolder Testrun_20191118_1558_BECM_BT Testrun_20191118_1606_BECM_BT Testrun_20191118_9999_BECM_BT --reqcsv req_bsw.csv

Tip: Don't add --logfolder in front of all folders, it should only be infront of the first.

Result
------
If successful the result will be a file called: test.html
If double-clicked it will open in your web-browser.