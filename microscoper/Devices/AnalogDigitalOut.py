import ctypes
import os, sys
import numpy as np

try:
    import PyDAQmx as pdmx
except:
    print("PyDAQmx import failed. Simulating PyDAQmx.")
    import Devices.FakePyDAQmx as pdmx
import time

from microscoper.Devices.Sync import sync_parameters


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

    def __init__(self, channels="Dev1/ao0:1", resolution=50, line_dwell_time=2, fill_fraction=0.5, hwbuffer=8192,
                 verbose=False, trigger="/Dev1/ai/StartTrigger"):
        self.channels = channels
        self.x_pixels, self.y_pixels = resolution, resolution
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
        parameters = sync_parameters(resolution=(self.x_pixels, self.y_pixels),
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
            upper = int(self.channels[j + 1])
            self.number_of_channels = upper - lower + 1
        return self.number_of_channels

    def set_data(self, data):
        self.data = np.array(data)

    def start(self):
        if self.data is None:
            print("No numpy array in the form of np.array([data_x,data_y]) given.\n"
                  " Data can be set using ao.set_data(np.array([data_x,data_y])). \n"
                  " Creating default sawtooth waveform instead.")
            data_x = 3 * np.tile(sawtooth(self.x_pixels_total, repeat_per_point=1), self.y_pixels)
            data_y = -3 * sawtooth(self.y_pixels, repeat_per_point=self.x_pixels_total) + 1.5
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

    def sawtooth(pixels=50, repeat_per_point=1):
        dx = 1 / (pixels - 1)
        result = []
        for i in range(0, pixels):
            for j in range(0, repeat_per_point):
                result.append(i * dx)
        result = np.array(result)
        return result

    def generateRasterScan(amplitude=16, x_pixels=256, y_pixels=256, x_flyback=128, offset=[0, 0]):
        x_pixels_total = x_pixels + x_flyback
        x_axis_raw = generateAxisScan(amplitude, x_pixels, offset[0])
        x_axis_flyback = generateFlyback(amplitude, x_pixels, x_flyback, offset[0])
        data_x = np.tile(np.concatenate((x_axis_flyback, x_axis_raw)), y_pixels)
        data_y = - amplitude * sawtooth(y_pixels, repeat_per_point=x_pixels_total) + amplitude / 2 + offset[1]
        data_x[data_x < -10] = -10
        data_x[data_x > 10] = 10
        data_y[data_y < -10] = -10
        data_y[data_y > 10] = 10
        print('X xcanning from %.2f to %.2f' % (np.min(data_x), np.max(data_x)))
        print('Y xcanning from %.2f to %.2f' % (np.min(data_y), np.max(data_y)))
        return np.array([data_x, data_y])


class Digital_output(object):
    def __init__(self, channel="Dev1/port0/line7"):
        self.channel = channel
        self.digital_output = pdmx.Task()
        try:
            self.digital_output.CreateDOChan(channel, "", pdmx.DAQmx_Val_ChanForAllLines)
            self.digital_output.StartTask()
            self.deviceLoaded = True
        except:
            print("NI digital output cannot be created")
            self.deviceLoaded = False

    def write(self, data=np.array([255], dtype=np.uint8), samples_per_channel=1, timeout=10, auto_start=1):
        if self.deviceLoaded:
            self.digital_output.WriteDigitalU8(samples_per_channel,
                                               auto_start,
                                               timeout,
                                               pdmx.DAQmx_Val_GroupByChannel,
                                               data,
                                               None,
                                               None)

    def high(self):
        self.write(np.array([255], dtype=np.uint8))

    def low(self):
        self.write(np.array([0], dtype=np.uint8))

    def close(self):
        if self.deviceLoaded:
            self.digital_output.StopTask()
