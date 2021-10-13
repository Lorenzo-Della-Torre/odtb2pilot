'''
Implicitly tested script

Tested implicitly by REQPROD 486686
'''

import logging
import sys

logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

try:
    from \
    e_486686_MAIN_0_security_log_authentication_key_detection_of_non_programmed_production_keys\
    import run
except ModuleNotFoundError as err:
    logging.error("The test that is used to test this requirement can't be found: %s found", err)

if __name__ == '__main__':
    run()
