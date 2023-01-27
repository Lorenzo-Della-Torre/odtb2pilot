"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

Get or Set server repo and path for Cynosure messages

When running CI, there could be three artifactory servers where the zip package comes from: 
It could be ARA, LTS or CI2. The logs and related information from the execution is uploaded to the same
server for future analysis. 

Cynosure messages have fields for logs and url. This information in victoria is very easy to read, and there is an 
hyperlink related to it to download the results from the execution. 

This is a simple interface to save all artifactory related information in order to be accessible  when the fields 
in the message bus needs to be filled in. It is the only way to communicate two independent systems (ci_runner with
Jenkins information and message bus with info about AutomationDesk execution)

In case the server info is not provided (ex. running from HILTest pipeline where is not need to provide a zip package), 
the server will be ci2.
""" 

import json
import logging
import epsci
import os

log = logging.getLogger('epsmsgbus.ci_logs')

DEFAULT_LOGSID_FILENAME = os.path.abspath(os.path.join(os.path.dirname(__file__),
        "..", "..", "..", "log", "msgbuslogs.tmp"))

def get_logs_url(filename=DEFAULT_LOGSID_FILENAME):
    ''' Get info about server, repo and path where the package zip from CI comes from
    
    :param filename: json file where information about server is saved
    :type filename: file

    :rtype: dict
    :return: Json data with server, repo and base path if the file msgbuslogs.tmp exists.None if the file is empty, not readable, 
    or non-existing.
    '''
    try:
        with open(filename) as fp:
            log.debug(f"Getting log info paths from '{filename}'.")
            return json.load(fp)
    except:
        pass

def set_logs_url(base_url, repo=None, basepath=None, filename=DEFAULT_LOGSID_FILENAME):
    '''Save path information about where to upload logs into a JSON file.

    :param base_url: server
    :type base_url: string
    
    :param repo: repo in artifactory server
    :type repo: string

    :param basepath: path inside repo to complete the whole url
    :type basepath: string

    :rtype: dict
    :return filename: json file where information about server will be saved
    '''
    
    config_name = 'artifactory'
    log.debug(f"Setting baseurl='{base_url}', repo='{repo}', basepath='{basepath}' to '{filename}'")
    repo, basepath, base = epsci.get_repo_path(base_url, config_name, repo, basepath)
    try:
        os.unlink(filename)
    except:
        pass
    try:
        with open(filename, 'w') as fp:
            json.dump({'base_url' : 'https://'+ base,
                'repo': repo,
                'basepath' : basepath,
                'build_url' : os.environ['BUILD_URL'],
                }, fp)            
    except:
        try:
            os.unlink(filename)
        except:
            pass
