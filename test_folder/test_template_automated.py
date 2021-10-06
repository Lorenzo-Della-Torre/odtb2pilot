"""
reqprod: XXXXXX (Ex. 74109)
version: Y (Ex. 2)
title: <Insert Reqprod title> (Ex. Allowed diagnostic services)
purpose: >
	<Insert text found in purpose field>

	(Ex. Define which diagnostic services to allow. Ensure all suppliers uses the
	same diagnostic services as well as preventing supplier from using not
	not allowed diagnostic services.)

description: >
	<Insert text found under the "box">

	(Ex. The ECU shall only support the diagnostic services specified in the
	requirement sections from Volvo Car Corporation.)

details:
	<Write your own description of the test>

	(Ex. Read which serives are defined in the sddb file.
	If the service is not defined, send the request to the ECU and
	expect a negative response.

	The time for last frame sent to first frame received is measured
	for each undefined service and compared against P2Server_max.

	According to REQPROD 74140 the ECU shall use P2Server_max as P4Server_max
	as the timing parameterfor a negative response for diagnostic
	services not supported by the ECU.)
"""
import logging

from hilding.dut import Dut
from hilding.dut import DutTestError

def step_1():
	"""
	action:
		<Write a description of the test step>

		(Ex. Check if True equals 1, in that case the test is a success.)

	expected_result:
		<What is the expected result?>

		(Ex. Excpected that True = False)
	"""

	#Add test code
	#Ex:

	if True == 1:
		return True
	return False


def run():
	"""
	Run - Call other functions from here

	This information should be removed before submitting the test:

	There are different ways of writing tests.

	One of them is to set the result variables init. value
	to False. Then later to True if all steps in the try bracket
	succeeds.

	Another is to utilise the return value from the step function in some way.

	Feel free to write the test however you like as long as the correct
	value is sent to postcondition in the end.
	"""
	dut = Dut()

	start_time = dut.start()
	result = False
	try:
		# Communication with ECU lasts 60 seconds.
		dut.precondition(timeout=60)

		# Start with application since default session is active.
		dut.step(step_1, purpose='This is just a dummystep used in this template')

		result = True
	except DutTestError as error:
		logging.error("Test failed: %s", error)
	finally:
		dut.postcondition(start_time, result)

if __name__ == '__main__':
	run()
