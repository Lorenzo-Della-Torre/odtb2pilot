#!/usr/bin/env python3

""" Move files from hierach folder structure to new flat structure """

import shutil
import os
import re
from neo4j import GraphDatabase

SRC_FOLDER = "test_cases"
DEST_FOLDER = "test_folder"

NEO4J = False

def neo_funz(py_files):
    """ add script file to db, and link it to REQPROD (if any) """
    # Diclaimer: This is hacking, we lack full info in the files in order to link
    #    testcases to acutual REQPRODs (true of 2020-10-14)

    uri = "bolt://localhost:7687"
    driver = GraphDatabase.driver(uri, auth=("neo4j", "1234"))
    RELATION = "verify"
    re_reqprod = re.compile(r'.*BSW_REQPROD_([0-9]*)_.*')

    def create_pynode(tx, name):
        print(name)
        tx.run(f"MERGE (a:Testcase {{ name: '{name}', repo: 'odtb2' }})")

    def create_pyrel(tx, node, rel, othernode):
        tx.run(f"MATCH (a:Testcase {{name: '{node}'}})\nMATCH (b:REQPROD {{ID: '{othernode}'}})\nMERGE (a)-[r:{rel}]->(b)")

    for filename in py_files:
        shortname_tmp = filename.split('/')[-1]
        shortname = shortname_tmp.split('\\')[-1]
        with driver.session() as session:
            session.write_transaction(create_pynode, shortname)
            print(f"file is {shortname}")
        req_match = re_reqprod.match(shortname)
        if req_match:
            with driver.session() as session:
                # get the REQPROD id from the file name and then add a relation
                req_id = req_match.group(1)
                session.write_transaction(create_pyrel, shortname, RELATION, req_id)
                print(f"reqprod is {req_match.group(1)}")


    driver.close()

def move_subfiles_to_flat(src_folder, dest_folder):
    """ Find and move all python files from given parent directory """
    cnt = 0
    listOfFiles = []
    for root, dirs, files in os.walk(src_folder):
        listOfFiles += [os.path.join(root, file) for file in files if file.endswith(".py")]
    print(f'list of files: {listOfFiles}')

    for full_path in listOfFiles:
        shutil.move(full_path, DEST_FOLDER)
        #continue
    # add to the graph db here instead; it will be cool.
    if NEO4J:
        neo_funz(listOfFiles)


if __name__ == "__main__":
    # Boilerplate to launch the main function with the command line arguments.
    move_subfiles_to_flat(SRC_FOLDER, DEST_FOLDER)
