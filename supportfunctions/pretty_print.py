"""

/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE:
This file contains material that is confidential and confidential to Volvo Cars and/or
other developers. No license is granted under any intellectual or industrial property
rights of Volvo Cars except as may be provided in an agreement with Volvo Cars.
Any unauthorized copying or distribution of content from this file is prohibited.



/*********************************************************************************/

Support function to handle pretty print of a DID
"""

import time
import logging

def __get_spaces(name : str, max_item_length):
    """Function used to get correct layout in the print.
    It adds to correct amount of spaces so that the string "name" + spaces
    are 50 chars long.

    If name is longer than 46 chars only the first 46 will be shown

    Args:
        name (str): Input string, only used to know how many spaces that are needed
        max_item_length (optional) (int): The maximum allowed length of a response_items name.
        Everything after this length will be cut out

    Returns:
        string: string containing 43-len(name) spaces and one delimiter "|" in index
        [number_of_spaces - 4]
    """
    number_of_spaces = max_item_length - len(name) + 4
    ret_string = ""
    for i in range(number_of_spaces):
        if i == number_of_spaces - 4:
            ret_string += "|"
        else:
            ret_string += " "
    return ret_string

def __uds_response_2_string(uds_response, max_item_length = 55):
    """
    This function takes an instance of the class UdsResponse and turns in into
    a good looking string.

    Args:
        uds_response (UdsResponse): An instance of the class UdsReponse
        max_item_length (optional) (int): The maximum allowed length of a response_items name.
        Everything after this length will be cut out

    Returns:
        string: A string containing all the response items found in uds_response
        formated in a good way.
    """
    try:
        response_items = uds_response.details["response_items"]

        #First two lines in the pretty print
        ret_string = "Name"
        for _ in range(max_item_length-4):
            ret_string += " "
        ret_string += "| Value \n"
        for _ in range(max_item_length):
            ret_string += "-"
        ret_string += "|------------- \n"

        #If this part in unclear, try printing response_items to understand its structure.
        for response_item in response_items:
            response_name = response_item['name']
            if len(response_name) > max_item_length:
                response_name = response_name[0:max_item_length]
            ret_string += response_name\
                + __get_spaces(response_name, max_item_length)\
                + str(response_item['scaled_value'])\
                + "\n"

    except KeyError as err:
        logging.info("DID not read successfully %s", err)
        return "DID not read successfully \n UdsResponse: \n" + str(uds_response)


    return ret_string

def get_did_pretty_print(dut, did : str):
    """Function used to get a pretty printed string from did id "did"
    The result will be returned once

    Args:
        dut (Dut): An instance of the class Dut
        did (str): did id

    Returns:
        string: Pretty looking string with data from did with id "did"
    """
    res = dut.uds.read_data_by_id_22(bytes.fromhex(did))
    ret = __uds_response_2_string(res)
    return ret

def subscribe_to_did(dut, did : str, duration = 60):
    """This function will print the response for did with id "did" for duration amount of seconds.

    Args:
        dut (Dut): An instance of the class Dut
        did (str): did id
        duration (int, optional): For how many seconds should the result be printed?
        Defaults to 60.
    """

    start_time = time.time()

    logging.disable(level = "INFO")

    while time.time() - start_time < duration:
        res = dut.uds.read_data_by_id_22(bytes.fromhex(did))
        ret = __uds_response_2_string(res)
        print(ret)
