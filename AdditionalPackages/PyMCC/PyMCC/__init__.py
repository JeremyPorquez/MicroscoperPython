import time
import ctypes
import os
import sys

class Device(object):
    # See cbw.h from MCCdaq C support
    BIP5VOLTS = 0  # from -5 to 5 Volts
    BIP10VOLTS = 1
    UNI10VOLTS = 100
    UNI5VOLTS = 101     # 0 to 5 Volts
    UNI4VOLTS = 114     # 0 to 4 Volts
    UNI2PT5VOLTS = 102  # /* 0 to 2.5 Volts */
    UNI2VOLTS = 103  # /* 0 to 2 Volts */
    UNI1PT67VOLTS = 109  # /* 0 to 1.67 Volts */
    UNI1PT25VOLTS = 104  # /* 0 to 1.25 Volts */
    UNI1VOLTS = 105  # /* 0 to 1 Volt */
    UNIPT5VOLTS = 110  # /* 0 to .5 Volt */
    UNIPT25VOLTS = 111  # /* 0 to 0.25 Volt */
    UNIPT2VOLTS = 112  # /* 0 to .2 Volt */
    UNIPT1VOLTS = 106  # /* 0 to .1 Volt */
    UNIPT05VOLTS = 113  # /* 0 to .05 Volt */
    UNIPT02VOLTS = 108  # /* 0 to .02 Volt*/
    UNIPT01VOLTS = 107  # /* 0 to .01 Volt*/
    model = {
        "1208" : UNI4VOLTS,
        "3101" : UNI10VOLTS
    }

    def __init__(self,boardNumber=0,model="3101",name=''):
        self.name = name
        print("MCC Analog output model %s %s"%(model,name))
        if sys.maxsize > 2 ** 32:
            dllname = os.path.join(os.path.dirname(__file__), r'cbw64.dll')
        else:
            dllname = os.path.join(os.path.dirname(__file__), r'cbw32.dll')
        try :
            self.dll = ctypes.windll.LoadLibrary(dllname)
            self.deviceLoaded = True
        except :
            print("Cannot load %s"%dllname)
            print("Simulating dll")
            self.deviceLoaded = False
        self.gain = self.model[model]
        self.boardNumber = int(boardNumber)
        self.model = model
        self.voltage = None

    def get_voltage(self,channel=0):
        voltage = ctypes.c_float()
        voltage = ctypes.pointer(voltage)
        Options = 0
        if self.deviceLoaded:
            self.dll.cbVIn(self.boardNumber,channel,self.gain,voltage,Options)
            return voltage.contents.value
        else :
            return 0

    def set_voltage(self,voltage,channel=0):
        self.voltage = voltage
        voltage = ctypes.c_float(voltage)
        Options = 0
        if self.deviceLoaded:
            self.dll.cbVOut(self.boardNumber, channel, self.gain, voltage, Options)

    def get_digital_in(self,port=1):
        value = ctypes.pointer(ctypes.c_short())
        if self.model == "1208":
            PortType = 10 #FIRSTPORTA
        if self.model == "3101":
            PortType = 1
        direction = 2 #Digital out = 1, Digital in = 2
        if self.deviceLoaded:
            self.dll.cbDConfigPort(self.boardNumber, PortType, direction)
            self.dll.cbDBitIn(self.boardNumber, PortType, ctypes.c_int(port), value)
            return value.contents.value
        else:
            return 0

    def set_digital_out(self,value=0,port=1):
        if self.model == "1208":
            PortType = 10 #FIRSTPORTA
        if self.model == "3101":
            PortType = 1
        direction = 1 #Digital out = 1, Digital in = 2
        if self.deviceLoaded:
            self.dll.cbDConfigPort(self.boardNumber, PortType, direction)
            self.dll.cbDBitOut(self.boardNumber, PortType, ctypes.c_int(port), ctypes.c_short(value))

    def test_ao(self):
        '''
        Generates 0 and 0.1 Volts which cycles every two seconds.
        '''
        Gain = self.gain
        BoardNum = 0
        Chan = 0
        Options = 0
        while True:
            DataValue = ctypes.c_float(0.1)
            self.dll.cbVOut(BoardNum, Chan, Gain, DataValue, Options)
            print("Set voltage channel %i at %f"%(Chan,DataValue.value))
            time.sleep(2)
            DataValue = ctypes.c_float(0.0)
            self.dll.cbVOut(BoardNum, Chan, Gain, DataValue, Options)
            print("Set voltage channel %i at %f"%(Chan,DataValue.value))
            time.sleep(2)

    def test_dio(self):
        '''
        Generates TTL False and True which cycles every two seconds.
        '''

        if self.model == "1208":
            PortType = 10 #FIRSTPORTA
        if self.model == "3101":
            PortType = 1
        Direction = 1
        while True:
            print(self.dll.cbDConfigPort(self.boardNumber, PortType, Direction))
            print(self.dll.cbDBitOut(self.boardNumber, PortType, ctypes.c_int(1), ctypes.c_short(0)))
            print(self.dll.cbDBitOut(self.boardNumber, PortType, ctypes.c_int(2), ctypes.c_short(0)))
            time.sleep(2)
            print(self.dll.cbDBitOut(self.boardNumber, PortType, ctypes.c_int(1), ctypes.c_short(1)))
            print(self.dll.cbDBitOut(self.boardNumber, PortType, ctypes.c_int(2), ctypes.c_short(1)))
            time.sleep(2)

if __name__ == "__main__":
    device = Device(model="1208")
    device.test_ao()