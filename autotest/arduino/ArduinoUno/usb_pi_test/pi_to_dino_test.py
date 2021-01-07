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
				