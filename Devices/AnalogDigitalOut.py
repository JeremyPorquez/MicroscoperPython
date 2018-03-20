import ctypes
import os, sys
import numpy as np
import PyDAQmx as pdmx
import Math
import time

from Devices.Sync import sync_parameters


class Analog_output(object):
    number_of_channels = 0
    data = None

    fill_fraction = 0.5
    max_timebase_frequency = 20e6
    timeout = 10
    trigger = "/Dev1/ai/StartTrigger"

    voltage_max = 10
    voltage_min = -10
    waveform = "sawtooth"
    samples_written = ctypes.c_int32()
    writing = False

    def __init__(self, channels="Dev1/ao0:1", resolution=(50,50),line_dwell_time=2,fill_fraction=0.5,hwbuffer=8192,
                 verbose=False,trigger="/Dev1/ai/StartTrigger"):
        self.channels = channels
        self.x_pixels,self.y_pixels = resolution
        self.msline = line_dwell_time
        self.fill_fraction = fill_fraction
        self.trigger = trigger
        self.analog_output = pdmx.Task()
        self.hwbuffer = hwbuffer
        self.verbose = verbose
        self.running = False
        self.get_number_of_channels()
        if self.verbose: print("Initializing analog output channel/s : %s" % self.channels)
        self.__calculate_sync()
        self.analog_output = pdmx.Task()

        self.analog_output.CreateAOVoltageChan(physicalChannel=self.channels,
                                               nameToAssignToChannel="",
                                               minVal=self.voltage_min,
                                               maxVal=self.voltage_max,
                                               units=pdmx.DAQmx_Val_Volts,
                                               customScaleName=None)
        self.analog_output.CfgSampClkTiming(source="",
                                            rate=int(self.clock_rate),
                                            activeEdge=pdmx.DAQmx_Val_Rising,
                                            sampleMode=pdmx.DAQmx_Val_ContSamps,
                                            sampsPerChan=1)
        self.analog_output.CfgDigEdgeStartTrig(triggerSource=self.trigger,  ##DOESN'T rely on trigger?
                                               triggerEdge=pdmx.DAQmx_Val_Rising
                                               )
        if self.verbose: print("%s initialized." % self.channels)

    def __calculate_sync(self):
        parameters = sync_parameters(resolution=(self.x_pixels,self.y_pixels),
                                     line_dwell_time=self.msline,
                                     fill_fraction=self.fill_fraction,
                                     max_timebase_frequency=self.max_timebase_frequency,
                                     maxbuffer=self.hwbuffer)
        self.x_pixels_total = parameters.x_pixels_total
        self.x_pixels_flyback = parameters.x_pixels_flyback

        self.clock_rate = parameters.write_clock_rate
        self.samples_per_pixel = parameters.samples_per_pixel
        self.samples_to_write_per_channel = parameters.samples_to_write_per_channel
        self.samples_trash = parameters.samples_trash
        self.divisor = parameters.divisorG
        # if 'point' in self.scanType.lower():
        #     self.samples_to_write_per_channel = 1

    def init(self):
        pass

    def get_number_of_channels(self):
        i = self.channels.find("ao") + 2
        j = self.channels.find(":")
        if j == -1:
            self.number_of_channels = 1
        else:
            lower = int(self.channels[i:j])
            upper = int(self.channels[j+1])
            self.number_of_channels = upper-lower+1
        return self.number_of_channels

    def set_data(self,data):
        self.data = np.array(data)

    def start(self):
        if self.data is None :
            print("No numpy array in the form of np.array([data_x,data_y]) given.\n"
                  " Data can be set using ao.set_data(np.array([data_x,data_y])). \n"
                  " Creating default sawtooth waveform instead.")
            data_x = 3 * np.tile(Math.sawtooth(self.x_pixels_total, repeat_per_point=1), self.y_pixels)
            data_y = -3 * Math.sawtooth(self.y_pixels, repeat_per_point=self.x_pixels_total) + 1.5
            self.data = np.array([data_x, data_y])
        if self.verbose:
            print("Write data length : %i" % self.samples_to_write_per_channel)
            print("Write trash samples : %i" % self.samples_trash)
            print("Write rate : %f" % self.clock_rate)
            print("Galvo timebase divisor : %i" % self.divisor)
        self.analog_output.WriteAnalogF64(
            numSampsPerChan=self.samples_to_write_per_channel,
            autoStart=False,
            timeout=self.timeout,
            dataLayout=pdmx.DAQmx_Val_GroupByChannel,
            writeArray=self.data,  # (ctypes.c_float*32)(),#self.data_x,
            sampsPerChanWritten=pdmx.byref(self.samples_written),
            reserved=None)

        self.analog_output.StartTask()
        if self.verbose: print("Analog output waiting for trigger.")
        self.running = True

    def stop(self):
        self.running = False
        self.analog_output.StopTask()
        if self.verbose: print("Stopping analog output.")

    def clear(self):
        self.stop()
        if self.verbose: print('Clearing analog output task.')
        self.analog_output.ClearTask()

class AnalogDigital_output_MCC(object):
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
            dllname = os.path.join(os.path.dirname(__file__), r'dlls\cbw64.dll')
        else:
            dllname = os.path.join(os.path.dirname(__file__), r'dlls\cbw32.dll')
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

class Digital_output(object):
    def __init__(self,channel = "Dev1/port0/line7"):
        self.channel = channel
        self.digital_output = pdmx.Task()
        try :
            self.digital_output.CreateDOChan(channel, "", pdmx.DAQmx_Val_ChanForAllLines)
            self.digital_output.StartTask()
            self.deviceLoaded = True
        except :
            print("NI digital output cannot be created")
            self.deviceLoaded = False

    def write(self,data=np.array([255],dtype=np.uint8),samples_per_channel=1,timeout=10,auto_start=1):
        if self.deviceLoaded:
            self.digital_output.WriteDigitalU8(samples_per_channel,
                                               auto_start,
                                               timeout,
                                               pdmx.DAQmx_Val_GroupByChannel,
                                               data,
                                               None,
                                               None)
    def close(self):
        if self.deviceLoaded:
            self.digital_output.StopTask()