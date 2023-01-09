from pathlib import Path
from pprint import pformat
from hilding import get_conf
from datetime import datetime
from hilding.sddb import write

def create_result_dir(fmt="%Y%m%d_%H%M"):
    """
    Create a result folder with negative result of smoke test
    """

    # create folder with date
    now = datetime.now().strftime(fmt)
    result_folder = Path(f"/home/pi/testrun/Testrun_{now}_BECM_BT")
    result_folder.mkdir(exist_ok=True)

    # add a failed result file
    with open(result_folder.joinpath("README.txt"),"w") as file:
        file.write("SMOKE TEST RESULT: FAILED")

def testrun_data_missing():
    """
    overwrite part numbers file. New one contains 'no data'
    """

    conf = get_conf()
    testrun_data_file = conf.rig.build_path.joinpath('testrun_data.py')
    eda0 = {}
    # DIDS to look for
    eda0_did_names = ["Application Diagnostic Database Part Number",
    "ECU Core Assembly Part Number","ECU Delivery Assembly Part Number",
    "ECU Serial Number"]

    # write file with no data for each part number
    for eda0_did in eda0_did_names:
        eda0[eda0_did] = "no data"
    write(testrun_data_file, "eda0_dict", pformat(eda0), "w")

def main():

    # create a result folder
    create_result_dir()

    # overwrite part numbers file
    testrun_data_missing()

if __name__ == "__main__":
    main()