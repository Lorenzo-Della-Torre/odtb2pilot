"""

/*********************************************************************************/



Copyright © 2022 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/
"""

import os
import re
import sys
import ntpath
import shutil
from tempfile import mkstemp



def replace(file_path, pattern, subst):
    #Create temp file
    fh, abs_path = mkstemp()
    with os.fdopen(fh,'w') as new_file:
        with open(file_path) as old_file:
            for line in old_file:
                new_file.write(line.replace(pattern, subst))
    #Copy the file permissions from the old file to the new file
    shutil.copymode(file_path, abs_path)
    #Remove original file
    os.remove(file_path)
    #Move new file
    shutil.move(abs_path, file_path)

def define_tests(test_list):
    """
    Get test scripts from a list file
    """

    with open(test_list) as testfile_list:
        test_files = []
        for line in testfile_list.readlines():
            stripped_line = line.strip()
            test_files.append(stripped_line)

    return test_files

def select_script(test_script):
    """
    Select the correct script that needs to be edited. Some scripts are displayed with different
    versions but only the lowest one must be edited.
    """
    # scripts starting with e_###, determine the digit where the version is displayed
    if ntpath.basename(test_script)[0] == "e":
        if re.search("MAIN_",test_script) is not None:
            version_digit = re.search("MAIN_",test_script).end()
        elif re.search("__",test_script) is not None:
            version_digit = re.search("__",test_script).end()
    # other scripts are displayed with a unique version
    else:
        return test_script

    version = int(test_script[version_digit])
    characters_list = list(test_script)

    # find the lower version existing in the folder
    test_script_to_try = test_script
    while version >= 0:
        
        # decrease version by 1 in the script path
        version -= 1
        characters_list[version_digit] = str(version)
        test_script_to_try = "".join(characters_list)

        # check if this version of the script exists
        if os.path.exists(test_script_to_try):
            test_script = test_script_to_try

    return test_script

def run_tests(dir_path,test_list):
    """
    Run all selected tests
    """

    sys.path.append(dir_path)
    sys.path.append(r'/home/pi/Repos/odtb2pilot')

    for line in test_list:
        # check if the line define a valid path
        if os.path.exists(line):

            # select correct script to use
            test_script = select_script(line)

            script_name = ntpath.basename(test_script)

            # copy scripts of interest in the temporary folder
            script_new_path = dir_path+"/"+script_name
            shutil.copyfile(test_script,script_new_path)

            # copy corresponding yml file if exists
            yml_file = os.path.splitext(test_script)[0]+".yml"
            if os.path.exists(yml_file):
                yml_copy = dir_path+"/"+os.path.splitext(script_name)[0]+".yml"
                shutil.copyfile(yml_file,yml_copy)

            # add print statement to the code to get the result of the entire script
            replace(script_new_path,"  run()","  print(run())")
            replace(script_new_path,"dut.postcondition(start_time, result)","dut.postcondition(start_time, result)\n        return result")

            # test current script
            script_under_test = __import__(os.path.splitext(script_name)[0])
            if not script_under_test.run():
                return False

    return True

def create_temp_dir(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

def delete_temp_dir(dir_path):
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)

def main():
    """
    Verify all smoke test scripts are passing
    """

    # temp folder path
    dir_path = r'/home/pi/Repos/odtb2pilot/projects/project_template/automated_testrun/test_folder'

    # get test scripts from the list
    test_list = "smoke_test_list.lst"
    test_list = define_tests(test_list)

    # run test scripts
    create_temp_dir(dir_path)
    result = run_tests(dir_path,test_list)
    delete_temp_dir(dir_path)

    return result

if __name__ == "__main__":
    print(main())
    