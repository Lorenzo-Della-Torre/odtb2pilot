/*********************************************************************************/



Copyright © 2021 Volvo Car Corporation. All rights reserved.



NOTICE: This file contains material that is confidential and confidential to Volvo Cars and/or other developers. No license is granted under any intellectual or industrial property rights of Volvo Cars except as may be provided in an agreement with Volvo Cars. Any unauthorized copying or distribution of content from this file is prohibited.



**********************************************************************************/


#!/usr/bin/env python
import serial

port = "/dev/ttyACM0"
rate = 9600

s1 = serial.Serial(port,rate)
s1.flushInput()

comp_list=["Flash complete\r\n","Hello Pi 3, This is Arduino UNO...\r\n"]
while True:
	if s1.inWaiting()>0:
		inputValue = s1.readline()
		print(inputValue)
		if inputValue in comp_list:
			try:
				n = input("Set Arduino flash times:")
				s1.write('%d'%n)
			except:
				print("Input error, please input a number")
				s1.write('0')
				