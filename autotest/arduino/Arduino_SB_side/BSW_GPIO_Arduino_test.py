from datetime import datetime
import serial
import time

import os
import sys
import glob #for getting catalog

import odtb_conf

from support_can import SupportCAN, CanParam
SC = SupportCAN()

from support_test_odtb2 import SupportTestODTB2
SUTE = SupportTestODTB2()

# extra for using GPIO
from gpiozero import LED

# Baudrate won't matter as using USB
#ser = serial.Serial("/dev/ttyACM0", 9600)

Relais1=LED(6)
Led1=LED(12)
Led2=LED(13)
timeout = 0
script_timeout = 0


starttime = time.time()
time_rec = time.time()
time_set = time.time()

network_stub = SC.connect_to_signalbroker(odtb_conf.ODTB2_DUT, odtb_conf.ODTB2_PORT)

GPIO_Led1: CanParam = {"netstub": network_stub,
                       "send": "Led1",
                       "receive": "Led1",
                       "namespace": SC.nspace_lookup("RpiGPIO")
                      }
SC.subscribe_signal(GPIO_Led1, timeout)
#SC.subscribe_signal(network_stub, "Led1", "Led1", SC.nspace_lookup("RpiGPIO"), timeout)

GPIO_Led2: CanParam = {"netstub": network_stub,
                       "send": "Led2",
                       "receive": "Led2",
                       "namespace": SC.nspace_lookup("RpiGPIO")
                      }
SC.subscribe_signal(GPIO_Led2, timeout)
#SC.subscribe_signal(network_stub, "Led2", "Led2", SC.nspace_lookup("RpiGPIO"), timeout)

GPIO_Relais1: CanParam = {"netstub": network_stub,
                          "send": "Relais1",
                          "receive": "Relais1",
                          "namespace": SC.nspace_lookup("RpiGPIO")
                         }
SC.subscribe_signal(GPIO_Relais1, timeout)
#SC.subscribe_signal(network_stub, "Relais1", "Relais1", SC.nspace_lookup("RpiGPIO"), timeout)

GPIO_Arduino: CanParam = {"netstub": network_stub,
                          "send": "Arduino_GPIO",
                          "receive": "Arduino_GPIO",
                          "namespace": SC.nspace_lookup("RpiGPIO")
                         }
SC.subscribe_signal(GPIO_Arduino, timeout)
#SC.subscribe_signal(network_stub, "Arduino_GPIO", "Arduino_GPIO", SC.nspace_lookup("RpiGPIO"), timeout)

# try to register arduino interfaces
#for serinf in glob.glob('/dev/ttyAM*'):
#    ser = serial.Serial(serinf, 9600)
#try to config interface for arduino
#    config_ardu_if(ser)

while (script_timeout == 0) or (int(time.time() - starttime) < script_timeout):
    #if (len(SC.can_frames) != 0):
    #    print("len(can_frames) ", len(SC.can_frames), " frames: ", SC.can_frames)
    if (len(SC.can_frames["Arduino_GPIO"]) != 0):
        print ("Time since last command: ", time.time()-time_rec)
        starttime = time.time()
        print ("Frames received: ", len(SC.can_frames["Arduino_GPIO"]), " ", SC.can_frames["Arduino_GPIO"])
        #Ardu_val = int(SC.can_frames["Arduino_GPIO"][0][2])
        #print("first value Arduino_GPIO ", Ardu_val)
        #print("first value as hex       ", SC.can_frames["Arduino_GPIO"][0][2][-4::])
        #if Ardu_val == 0 : Relais1.on()
        #elif Ardu_val == 1 : Relais1.off()
        #else : print ("value error Relais1 ", Ardu_val)
        time_rec = SC.can_frames["Arduino_GPIO"][0][0]
        if (SC.can_frames["Arduino_GPIO"][0][2][-4:-2] == '00'): offs=-2
        else: offs=-4
        print("send to Arduino: Rx"+SC.can_frames["Arduino_GPIO"][0][2][offs::])
        #ser.write(("Rx"+SC.can_frames["Arduino_GPIO"][0][2][offs::]+"\n").encode('ascii'))
        SC.can_frames["Arduino_GPIO"].pop(0)
    if (len(SC.can_frames["Relais1"]) != 0):
        print ("Time since last command: ", time.time()-time_rec)
        starttime = time.time()
        print ("Frames received: ", len(SC.can_frames["Relais1"]), " ", SC.can_frames["Relais1"])
        time_rec = SC.can_frames["Relais1"][0][0]
        Rel1_val = int(SC.can_frames["Relais1"][0][2])
        print("first value Relais1 ", Rel1_val)
        if Rel1_val == 0 : Relais1.on()
        elif Rel1_val == 1 : Relais1.off()
        else : print ("value error Relais1 ", Rel1_val)
        SC.can_frames["Relais1"].pop(0)
    if (len(SC.can_frames["Led1"]) != 0):
        starttime=time.time()
        #print ("frames received: ", len(SC.can_frames["Led1"]), " ", SC.can_frames["Led1"])
        time_rec = SC.can_frames["Led1"][0][0]
        Led1_val = int(SC.can_frames["Led1"][0][2])
        print ("first value Led1: ", int(Led1_val))
        if Led1_val == 0 : Led1.off()
        elif Led1_val == 1 : Led1.on()
        else : print ("value error Led1 ", Led1_val)
        SC.can_frames["Led1"].pop(0)
    if (len(SC.can_frames["Led2"]) != 0):
        starttime=time.time()
        #print ("frames Led2 received: ", len(SC.can_frames["Led2"]), " ", SC.can_frames["Led2"])
        time_rec = SC.can_frames["Led2"][0][0]
        Led2_val = int(SC.can_frames["Led2"][0][2])
        print ("first value Led2: ", Led2_val)
        if Led2_val == 0: Led2.off()
        elif Led2_val == 1: Led2.on()
        else :print ("value error Led2 ", Led2_val)
        SC.can_frames["Led2"].pop(0)
#    if(ser.inWaiting() > 0):
#        time_set = time.time()
#        ser_read = ser.read(ser.inWaiting())
#        print ("Time elapsed", time_set-time_rec," Read from ser_buffer: ", ser_read)

