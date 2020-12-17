#!/usr/bin/env python3

import logging
from argparse import ArgumentParser
from supportfunctions.support_sddb import parse_sddb_file

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    parser = ArgumentParser(
        description="Management commands for the odtb project"
    )
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser(
        "sddb", help="Generates/updates the platform specific "
        "dictionaries from the current release sddb file"
    )
    subparsers.add_parser(
        "check", help="Does various checks to ensure that your "
        "system is setup correctly"
    )
    args = parser.parse_args()
    if not args.command:
        parser.print_help()

    if args.command == 'sddb':
        logging.info("Start processing sddb file...")
        parse_sddb_file()
    elif args.command == 'check':
        logging.info("Check installation. To be implemented...")
