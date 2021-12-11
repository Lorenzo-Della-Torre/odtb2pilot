"""
/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

"""
A draft of a script to execute the testcase picker result
WIP!
"""
import sys
import logging
import argparse
import runpy
import testcase_picker

# Logging has different levels: DEBUG, INFO, WARNING, ERROR, and CRITICAL
# Set the level you want to have printout in the console.
logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)
LOGGER = logging.getLogger(__name__)

def parse_some_args():
    """Get the command line input, using the defined flags."""
    parser = argparse.ArgumentParser(description='Picks the desired testscripts from a selection')
    parser.add_argument("--swrs",
                        help="Elektra rif export, xml-file. SWRS file with requirements which "\
                        "should be tested.",
                        type=str,
                        action='store',
                        dest='swrs')
    parser.add_argument("--txt_file",
                        help="Textfile with list of files which should be tested",
                        type=str,
                        action='store',
                        dest='txt_file')
    parser.add_argument("--scripts",
                        help="List of files which should be tested",
                        type=str,
                        action='append',
                        dest='scripts')
    parser.add_argument("--script_folder",
                        help="Folder where the scripts are located",
                        type=str,
                        action='store',
                        dest='script_folder',
                        default='./')
    ret_args = parser.parse_args()
    return ret_args


def main(margs):
    """ Main function """
    included, _ = testcase_picker.execute(margs.swrs,
                                          margs.txt_file,
                                          margs.scripts,
                                          margs.script_folder)
    LOGGER.info('############################################')

    for file in included:
        LOGGER.info('')
        LOGGER.info('')
        LOGGER.info('%s', file)
        runpy.run_path(file, run_name='__main__')


if __name__ == "__main__":
    # Boilerplate to launch the main function with the command line arguments.
    ARGS = parse_some_args()
    main(ARGS)
