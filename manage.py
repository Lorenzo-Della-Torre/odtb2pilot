#!/usr/bin/env python3
""" manage.py: Management commands for the ODTB project """

import sys
import logging
from argparse import ArgumentParser
from pathlib import Path

from supportfunctions.support_sddb import parse_sddb_file
from supportfunctions.support_sddb import get_platform_dir
from supportfunctions.support_sddb import get_sddb_file
from supportfunctions.dvm import create_dvm

def check_install():
    """ Make sure that the installation is setup and configured properly """

    logging.info("Checking installation:")

    # test that odtb_conf.py is in the python path.
    try:
        import odtb_conf # pylint: disable=import-outside-toplevel
    except ModuleNotFoundError as error:
        logging.error("Could not import odtb_conf.py: %s", error)
        logging.error(
            "Add the path of the adequate odtb_conf.py to your PYTHONPATH")
        sys.exit()

    logging.info("Configured broker:")

    try:
        dut = odtb_conf.ODTB2_DUT
    except AttributeError as error:
        sys.exit(error)
    logging.info("Device under test (DUT): %s", dut)

    try:
        port = odtb_conf.ODTB2_PORT
    except AttributeError as error:
        sys.exit(error)
    logging.info("DUT port: %s", port)

    # implicitlly also check that ODTBPROJPARAM is set
    platform_dir = get_platform_dir()

    vbf_dir = Path(platform_dir).joinpath("VBF")
    if not vbf_dir.exists():
        sys.exit(f"Can't find VBF directory in {vbf_dir}")

    vbf_files = vbf_dir.glob("*.vbf")
    try:
        next(vbf_files)
    except StopIteration:
        logging.error("Can not locate any vbf fiels in %s", vbf_dir)

    # have a release directory or link
    get_sddb_file()

    # build files have been created
    build_dir = Path(platform_dir).joinpath("build")
    if not build_dir.exists():
        sys.exit(f"Could not locate release directory in {build_dir}")

    for build_file in ['did.py', 'dtc.py']:
        if not build_dir.joinpath(build_file).exists():
            logging.error("Could not locate %s in %s.", build_file, build_dir)
            sys.exit("Run ./manage.py sddb")

    try:
        from build import did # pylint: disable=import-outside-toplevel
    except ModuleNotFoundError as error:
        sys.exit(error)

    logging.info("Build data from SDDB file contains the following:")
    logging.info("PBL diagnostic part number: %s", did.pbl_diag_part_num)
    logging.info("SBL diagnostic part number: %s", did.sbl_diag_part_num)
    logging.info("App diagnostic part number: %s", did.app_diag_part_num)

    logging.info("Everything seems fine.")


if __name__ == "__main__":
    logging.basicConfig(
        format='%(levelname)s %(message)s', stream=sys.stdout,
        level=logging.INFO)
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
    dvm_parser = subparsers.add_parser(
        "dvm", help="generate a new dvm document from the test script"
    )
    dvm_parser.add_argument('test_script')

    args = parser.parse_args()
    if not args.command:
        parser.print_help()

    if args.command == 'sddb':
        logging.info("Start processing sddb file...")
        parse_sddb_file()
    elif args.command == 'check':
        check_install()
    elif args.command == 'dvm':
        create_dvm(args.test_script)
