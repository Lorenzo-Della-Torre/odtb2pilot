'''
Implicitly tested script

Tested implicitly by REQPROD XXXXX
'''


import logging
import sys

logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

#<This comment should be removed> The try-except is only required if the imported test script is
#not yet implemented
try:
	from e_XXXXX_... import run
except ModuleNotFoundError as err:
	logging.error("The test that is used to test this requirement can't be found: %s found", err)

if __name__ == '__main__':
    run()
