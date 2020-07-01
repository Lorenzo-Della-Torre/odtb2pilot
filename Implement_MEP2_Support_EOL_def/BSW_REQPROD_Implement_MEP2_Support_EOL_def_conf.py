#!/usr/bin/env python3

"""
Module containing the constant parameters used in BSW_REQPROD_Implement_MEP2_Support_EOL_def.py

 Date: 2020-02-12
 Author: Fredrik Jansson (fjansso8)
"""

# For each each DID, wait this time for the response. If you wait to short time you might not get
# the full message (payload). The unit is seconds. 2s should cover even the biggest payloads.
response_timeout = 2

# Test this amount of DIDs. Example: If equal to 10, the program will only test the first 10 DIDs.
# This is to speed up during testing.
# 500 should cover all DIDs
max_no_of_dids = 5 #400 #215 #155

# Reserve this time for the full script (seconds)
# 400 DIDs * 2s = 800s should cover all DIDs
script_timeout = max_no_of_dids * response_timeout + 15 #800
