"""
    Test of support for GPIO, Arduino, I2c-board
"""
#from datetime import datetime
import time
#import glob #for getting catalog
import serial

#import os
#import sys


from gpiozero import LED

from supportfunctions.support_can import SupportCAN, CanParam
from supportfunctions.support_test_odtb2 import SupportTestODTB2
from supportfunctions.support_seeed_4relay_board import Support_Seeed_4Relay, Seeed

import odtb_conf

SC = SupportCAN()
SUTE = SupportTestODTB2()

# extra for using GPIO

# extra for using I2C relay board (SEEED)
SEEED = Support_Seeed_4Relay

# Relay card connected via USB/Arduino
# Baudrate won't matter as using USB
ser = serial.Serial("/dev/ttyACM0", 9600)

# ToDo: Possibility to register several Arduino extension
# try to register arduino interfaces
#for serinf in glob.glob('/dev/ttyAM*'):
#    ser = serial.Serial(serinf, 9600)
# ToDo: Read Arduino name & configuration
# ToDo: mapping to Signals
#    config_ardu_if(ser)

# map to raspberry GPIO-port:
Relay1 = LED(6)
Led1 = LED(12)
Led2 = LED(13)







# Now see what we're supposed to do next
def run():# pylint: disable=too-many-branches, too-many-statements, too-many-locals
    """
    Run - Call other functions from here
    """
    timeout = 0
    script_timeout = 0
    starttime = time.time()
    time_rec = time.time()
    #time_set = time.time()

    seeed: Seeed = {
        "NUM_RELAY_PORTS": 4,
        "DEVICE_ADDRESS": 0x20,
        "DEVICE_REG_MODE1": 0x06,
        "DEVICE_REG_DATA" : 0xff
    }

    network_stub = SC.connect_to_signalbroker(odtb_conf.ODTB2_DUT, odtb_conf.ODTB2_PORT)

    gpio_led1: CanParam = {"netstub": network_stub,
                           "send": "Led1",
                           "receive": "Led1",
                           "namespace": SC.nspace_lookup("RpiGPIO")
                          }
    SC.subscribe_signal(gpio_led1, timeout)
    #SC.subscribe_signal(network_stub, "Led1", "Led1", SC.nspace_lookup("RpiGPIO"), timeout)

    gpio_led2: CanParam = {"netstub": network_stub,
                           "send": "Led2",
                           "receive": "Led2",
                           "namespace": SC.nspace_lookup("RpiGPIO")
                          }
    SC.subscribe_signal(gpio_led2, timeout)
    #SC.subscribe_signal(network_stub, "Led2", "Led2", SC.nspace_lookup("RpiGPIO"), timeout)

    gpio_relais1: CanParam = {"netstub": network_stub,
                              "send": "Relay1",
                              "receive": "Relay1",
                              "namespace": SC.nspace_lookup("RpiGPIO")
                             }
    SC.subscribe_signal(gpio_relais1, timeout)
    #SC.subscribe_signal(network_stub, "Relay1", "Relay1", SC.nspace_lookup("RpiGPIO"), timeout)

    gpio_arduino: CanParam = {"netstub": network_stub,
                              "send": "Arduino_GPIO",
                              "receive": "Arduino_GPIO",
                              "namespace": SC.nspace_lookup("RpiGPIO")
                             }
    SC.subscribe_signal(gpio_arduino, timeout)

    gpio_i2c: CanParam = {"netstub": network_stub,
                          "send": "I2C_GPIO",
                          "receive": "I2C_GPIO",
                          "namespace": SC.nspace_lookup("RpiGPIO")
                         }
    SC.subscribe_signal(gpio_i2c, timeout)


#    try:
#        process_loop(seeed)
#    except KeyboardInterrupt:
#        # tell the user what we're doing...
#        print("\nExiting application")
#        # turn off all of the relays
#        SEEED.relay_all_off(seeed)
#        # exit the application
#        sys.exit(0)


    while (script_timeout == 0) or (int(time.time() - starttime) < script_timeout):
        #if (len(SC.can_frames) != 0):
        #    print("len(can_frames) ", len(SC.can_frames), " frames: ", SC.can_frames)
        if len(SC.can_frames["I2C_GPIO"]) != 0:
            print("Time since last command: ", time.time()-time_rec)
            starttime = time.time()
            print("Frames received: ", len(SC.can_frames["I2C_GPIO"]),\
                  " ", SC.can_frames["I2C_GPIO"])
            #Ardu_val = int(SC.can_frames["I2C_GPIO"][0][2])
            #print("first value I2C_GPIO ", Ardu_val)
            #print("first value as hex       ", SC.can_frames["I2C_GPIO"][0][2][-4::])
            #if Ardu_val == 0 : Relay1.on()
            #elif Ardu_val == 1 : Relay1.off()
            #else : print ("value error Relay1 ", Ardu_val)
            time_rec = SC.can_frames["I2C_GPIO"][0][0]
            #if SC.can_frames["I2C_GPIO"][0][2][-4:-2] == '00':
            #    offs=-2
            #else:
            #    offs=-4
            #print("send to I2C-Card: Rx"+SC.can_frames["I2C_GPIO"][0][2])
            #print("send to I2C-Card: Rx"+SC.can_frames["I2C_GPIO"][0][2][offs::])
            print("send to I2C-Card: Rx"+SC.can_frames["I2C_GPIO"][0][2][-4::])
            relay_num = 1 + int(SC.can_frames["I2C_GPIO"][0][2][-2])
            print("I2C-Card: Relay no: ", relay_num)
            rel_off_on = SC.can_frames["I2C_GPIO"][0][2][-1]
            print("I2C-Card: Relay off/on: ", rel_off_on)
            if rel_off_on == '0':
                SEEED.relay_off(relay_num, seeed)
            else:
                SEEED.relay_on(relay_num, seeed)

            SC.can_frames["I2C_GPIO"].pop(0)
        if len(SC.can_frames["Arduino_GPIO"]) != 0:
            print("Time since last command: ", time.time()-time_rec)
            starttime = time.time()
            print("Frames received: ", len(SC.can_frames["Arduino_GPIO"]),\
                  " ", SC.can_frames["Arduino_GPIO"])
            #Ardu_val = int(SC.can_frames["Arduino_GPIO"][0][2])
            #print("first value Arduino_GPIO ", Ardu_val)
            #print("first value as hex       ", SC.can_frames["Arduino_GPIO"][0][2][-4::])
            #if Ardu_val == 0 : Relay1.on()
            #elif Ardu_val == 1 : Relay1.off()
            #else : print ("value error Relay1 ", Ardu_val)
            time_rec = SC.can_frames["Arduino_GPIO"][0][0]
            if SC.can_frames["Arduino_GPIO"][0][2][-4:-2] == '00':
                offs = -2
            else:
                offs = -4
            print("send to Arduino: Rx"+SC.can_frames["Arduino_GPIO"][0][2][offs::])
            ser.write(("Rx"+SC.can_frames["Arduino_GPIO"][0][2][offs::]+"\n").encode('ascii'))
            SC.can_frames["Arduino_GPIO"].pop(0)
        if len(SC.can_frames["Relay1"]) != 0:
            print("Time since last command: ", time.time()-time_rec)
            starttime = time.time()
            print("Frames received: ", len(SC.can_frames["Relay1"]),\
                  " ", SC.can_frames["Relay1"])
            time_rec = SC.can_frames["Relay1"][0][0]
            rel1_val = int(SC.can_frames["Relay1"][0][2])
            print("first value Relay1 ", rel1_val)
            if rel1_val == 0:
                Relay1.on()
            elif rel1_val == 1:
                Relay1.off()
            else:
                print("value error Relay1 ", rel1_val)
            SC.can_frames["Relay1"].pop(0)
        if len(SC.can_frames["Led1"]) != 0:
            starttime = time.time()
            #print ("frames received: ", len(SC.can_frames["Led1"]), " ", SC.can_frames["Led1"])
            time_rec = SC.can_frames["Led1"][0][0]
            led1_val = int(SC.can_frames["Led1"][0][2])
            print("first value Led1: ", int(led1_val))
            if led1_val == 0:
                Led1.off()
            elif led1_val == 1:
                Led1.on()
            else:
                print("value error Led1 ", led1_val)
            SC.can_frames["Led1"].pop(0)
        if len(SC.can_frames["Led2"]) != 0:
            starttime = time.time()
            #print ("frames Led2 received: ", len(SC.can_frames["Led2"]),\
            #       " ", SC.can_frames["Led2"])
            time_rec = SC.can_frames["Led2"][0][0]
            led2_val = int(SC.can_frames["Led2"][0][2])
            print("first value Led2: ", led2_val)
            if led2_val == 0:
                Led2.off()
            elif led2_val == 1:
                Led2.on()
            else:
                print("value error Led2 ", led2_val)
            SC.can_frames["Led2"].pop(0)
        if ser.inWaiting() > 0:
            time_set = time.time()
            ser_read = ser.read(ser.inWaiting())
            print("Time elapsed", time_set-time_rec, " Read from ser_buffer: ", ser_read)

if __name__ == "__main__":
    run()
