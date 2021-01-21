#!/usr/bin/env python3

# Date: 2021-01-13
# Authors: Fredrik Jansson (fjansso8)

"""
Startscript to generate did_report
Usage: python3 generate_did_report.py --SDDB sddb_file
Output: html file with the did_report
"""

import argparse
import logging
import sys
import parse_sddb
import dids_from_sddb_checker


def parse_some_args():
    """Get the command line input, using the defined flags."""
    parser = argparse.ArgumentParser(description='-')
    parser.add_argument("--SDDB", help="input sddb xml file", type=str, action='store',
                        dest='sddb_file', required=True,)
    ret_args = parser.parse_args()
    return ret_args


def main(margs):
    """Call other functions from here"""
    logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

    logging.info("Parsing SDDB-file: %s", margs.sddb_file)
    parsed_sddb = parse_sddb.execute(margs.sddb_file)

    logging.info("Generate did report - Start")
    dids_from_sddb_checker.execute(parsed_sddb)
    logging.info("Generate did report - Done")


if __name__ == "__main__":
    # Boilerplate to launch the main function with the command line arguments.
    ARGS = parse_some_args()
    main(ARGS)
