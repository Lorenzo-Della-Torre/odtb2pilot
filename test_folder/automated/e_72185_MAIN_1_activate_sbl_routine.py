'''Import script - Inherited from older version of requirement'''

import logging
import sys

logging.basicConfig(format=' %(message)s', stream=sys.stdout, level=logging.INFO)

logging.info("Testcase result: Tested implicitly by all diagnostic tests,\
 e.g. by REQPROD 67170 (tested implicitly)")
