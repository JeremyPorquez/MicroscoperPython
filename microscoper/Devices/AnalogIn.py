import ctypes
import time
import os
import numpy as np
import PyDAQmx as pdmx
# import tifffile as tf
from threading import Thread
import multiprocessing
import Devices.TiffWriter as tf

from Math.Cython.CMath import updateArray, cupdateArray, nupdateArray, nmeanArray
from Devices.Sync import sync_parameters

def get_number_of_channels(channel='Dev1/ai0:2'):
    if 'ai' in channel : chType = 'ai'
    else : chType = 'ao'
    try :
        upper = int(channel[channel.find(":") + 1:])
        lower = int(channel[channel.find(chType)+2:channel.find(":")])
        number_of_channels = upper - lower + 1
    except :
        number_of_channels = 1
    return number_of_channels


class readProcess(multiprocessing.Process):
    def __init__(self,q=None,connection=None):
        super().__init__()
        self.q = q
        self.connection = connection

    def detectConnection(self):
        self.detectingConnection = True
        while self.detectingConnection :
            try : connection = self.connection.recv() #automatically waits for event
            except EOFError :
                self.detectingConnection = False
                break
            if type(connection) == type({}):
                if connection.get('channel') is not None : self.channel = connection.get('channel')
                if connection.get('voltage_min') is not None : self.voltage_min = connection.get('voltage_min')
                if connection.get('voltage_max') is not None : self.voltage_max = connection.get('voltage_max')
                if connection.get('clock_rate') is not None : self.clock_rate = connection.get('clock_rate')
                if connection.get('multiplier') is not None: self.multiplier = connection.get('multiplier')
                if connection.get('samples_to_read_per_channel') is not None :
                    self.samples_to_read_per_channel = connection.get('samples_to_read_per_channel')
                if connection.get('data_line_length') is not None :
                    self.data_line_length = connection.get('data_line_length')
                    self.data_line = np.zeros(self.data_line_length)
                if connection.get('number_of_channels') is not None :
                    self.number_of_channels = connection.get('number_of_channels')
                if connection.get('reading') is not None :
                    self.reading = connection.get('reading')
                if connection.get('detect connection') is not None :
                    self.detectingConnection = connection.get('detect connection')


            if self.reading :
                self.analog_input = pdmx.Task()
                self.analog_input.CreateAIVoltageChan(physicalChannel=self.channel,
                                                      nameToAssignToChannel="",
                                                      terminalConfig=pdmx.DAQmx_Val_Cfg_Default,
                                                      minVal=self.voltage_min,
                                                      maxVal=self.voltage_max,
                                                      units=pdmx.DAQmx_Val_Volts,
                                                      customScaleName=None)

                self.analog_input.CfgSampClkTiming(source="",
                                                   rate=self.clock_rate,
                                                   activeEdge=pdmx.DAQmx_Val_Rising,
                                                   sampleMode=pdmx.DAQmx_Val_ContSamps,
                                                   sampsPerChan=self.samples_to_read_per_channel)
                self.readThread = Thread(target=self.read)
                self.readThread.start()

    def run(self):
        self.reading = False
        self.detectConnectionThread = Thread(target=self.detectConnection)
        self.detectConnectionThread.start()

    def read(self):
        while self.reading:
            try :
                self.analog_input.ReadAnalogF64(
                    numSampsPerChan=self.samples_to_read_per_channel,
                    timeout=10,
                    fillMode=pdmx.DAQmx_Val_GroupByChannel,
                    readArray=self.data_line,
                    arraySizeInSamps=self.number_of_channels * self.samples_to_read_per_channel,
                    sampsPerChanRead=None,
                    reserved=None)
                self.q.put_nowait(self.data_line*self.multiplier)
                if self.q.qsize() > 20000:
                #     raise Exception('queue size greater than 50')
                    self.reading = False
                # time.sleep(0)
            except Exception as e:
                print(e)

            # print('\t',self.data_line[0])
        # try:
        ## empties queue if done
        while not self.q.empty():
            self.q.get()
        # with self.q:
        # self.q.clear()
        # except: pass
        self.analog_input.ClearTask()


class Analog_input(object):
    # Create task
    '''
    1. Set channel
    2. Set clock_rate
    3. Set samples to read per channel
    4. Set voltage min and max
    5. Set data length'''

    samples_read = ctypes.c_int32()
    data_line_length = 1000

    samples_to_read_per_channel = 1000  # -1 Read all available samples, 1000 default
    voltage_min = -10
    voltage_max = 10
    timeout = 10
    max_timebase_frequency = 20e6

    def __init__(self, parent=None, inputChannels = "Dev1/ai0:3", polarityWidgets = None):
        # super().__init__()
        self.cwd = os.path.basename(os.path.realpath(__file__))
        self.parent = parent
        os.chdir("Devices")

        self.polarityWidgets = None
        if polarityWidgets is not None:
            self.polarityWidgets = polarityWidgets

        self.dataQ = multiprocessing.Manager().Queue()

        self.parentConnectionReader, self.childConnectionReader = multiprocessing.Pipe()
        self.readProcess = readProcess(q=self.dataQ,
                                     connection=self.childConnectionReader)
        self.readProcess.daemon = True
        self.readProcess.start()

        self.numberOfChannels = get_number_of_channels(inputChannels)
        # self.initializeProcessors(self.numberOfChannels)

        self.x_pixels = None
        self.y_pixels = None
        self.x_pixel_location = 0

        self.trigger = None
        self.tolerance = 0.1
        self.reading = False

        self.get_image()

    def get_data(self):
        return self.samples_buffer

    def get_image(self):
        if (self.y_pixels is not None) and (self.x_pixels is not None):
            self.imageData = np.zeros((self.numberOfChannels, self.y_pixels, self.x_pixels))
        else :
            self.y_pixels, self.x_pixels = 50,50
            self.imageData = np.zeros((self.numberOfChannels, self.y_pixels, self.x_pixels))
        return self.imageData

    def init(self,channel="Dev1/ai0",resolution=(50,50),line_dwell_time=2.,fill_fraction=0.5,hwbuffer=8192,
             verbose=False,save=False,saveFilename='',saveFileIndex='',xAxis='',metadata='',waitForLastFrame=False,
             singleFrameScan=False,framesToAverage=1,dataMaximums=None,dataMinimums=None):

        self.channel = channel
        self.numberOfChannels = get_number_of_channels(channel)
        self.x_pixels, self.y_pixels = resolution
        self.msline = line_dwell_time
        self.fill_fraction = fill_fraction
        self.hwbuffer = hwbuffer
        self.verbose = verbose
        self.save = save
        self.saveFilename = saveFilename
        self.saveFileIndex = saveFileIndex
        self.metadata = metadata
        self.waitForLastFrame = waitForLastFrame
        self.singleFrameScan = singleFrameScan
        self.xAxis = xAxis
        self.framesToAverage = int(framesToAverage)
        self.framesDisplayed = 0
        self.lastFrameScan = False
        self.reading = False
        self.csvFileLoaded = False
        self.forcedStop = False
        self.atTheLastFrame = False
        # self.atTheLastFrame = [False for i in range(self.numberOfChannels)]

        if dataMaximums is None :
            self.dataMaximums = [1]*self.numberOfChannels
        else :
            self.dataMaximums = dataMaximums

        if dataMinimums is None :
            self.dataMinimums = [1]*self.numberOfChannels
        else :
            self.dataMinimums = dataMinimums

        if self.saveFilename is not '':
            self.saveFilename = self.saveFilename.replace('tiff', '')
            self.saveFilename = self.saveFilename.replace('tif', '')

        if self.verbose: print("Initializing analog input channel : %s" % self.channel)

        self.__calculate_sync()

        self.imageData = np.zeros((self.numberOfChannels, self.y_pixels, self.x_pixels))

        self.imageArrays = np.zeros((self.framesToAverage,self.numberOfChannels,self.y_pixels,self.x_pixels))

        self.intensities = [[] for i in range(0, self.numberOfChannels)]
        self.intensitiesIndex = [[] for i in range(0, self.numberOfChannels)]
        if self.verbose: print("%s initialized." % self.channel)

        self.__saveFileHeader()
        self.__saveFileIndex()
        self.y_pixel_location = 0
        self.framesGrabbed = 0
        self.framesSkipped = 0
        self.parentConnectionReader.send({'channel':self.channel,
                                          'voltage_min':self.voltage_min,
                                          'voltage_max':self.voltage_max,
                                          'clock_rate':self.clock_rate,
                                          'samples_to_read_per_channel':self.samples_to_read_per_channel,
                                          'data_line_length':self.data_line_length,
                                          'number_of_channels':self.numberOfChannels,
                                          'multiplier':10000})

        # self.initializeProcessorsParameters()


    def start(self):
        print('start')
        if self.verbose:
            print("\tData length :\t\t\t%i" % self.data_line_length)
            print("\tSamples per pixel :\t\t%i" % self.samples_per_pixel)
            print("\tSamples to read per channel :\t%i" % self.samples_to_read_per_channel)
            print("\tTrash samples :\t\t\t%i" % self.samples_trash)
            print("\tRead rate :\t\t\t%f" % self.clock_rate)
            print("\tDetector timebase divisor :\t\t%i" % self.divisor)

        self.startTime = time.time()
        self.reading = True

        self.parentConnectionReader.send({'reading' : True})

        Thread(target=self.calculateDisplay).start()
        Thread(target=self.displayData).start()

    def stop(self):
        self.forcedStop = True
        if self.verbose: print("Stopping analog input.")
        if not self.waitForLastFrame:
            self.reading = False
            self.parentConnectionReader.send({'reading' : False})
        else :
            self.lastFrameScan = True

    def clear(self):
        self.stop()
        if self.verbose: print('Clearing analog input task.')
        if self.waitForLastFrame:
            while self.reading : #soft stops
                time.sleep(0.1)
                pass
        self.reading = False
        # self.stopProcessors()
        self.parentConnectionReader.send({'reading' : False})

    def terminate(self):
        self.parentConnectionReader.send({'detect connection' : False})

    def calculateDisplay(self):
        while self.reading :
            for frame in range(0, self.framesToAverage):
                data_line = self.dataQ.get()

            ## from here is inserted code

                for channel in range(self.numberOfChannels):
                    channel_offset = channel * self.samples_to_read_per_channel_per_line
                    start = channel_offset + self.samples_trash
                    end = channel_offset + self.samples_to_read_per_channel_per_line
                    trimmedDataLine = data_line[start:end]
                    if self.polarityWidgets[channel].isChecked():
                        trimmedDataLine = -trimmedDataLine

                    nupdateArray(self.imageArrays[frame,channel], trimmedDataLine, self.samples_per_pixel, self.x_pixels,
                                 self.y_pixel_location)

                    self.imageData[channel] = nmeanArray(self.imageArrays[:,channel,...])

                    # self.imageData[channel] = np.mean(self.imageArrays[:,channel,...],axis=0)

                self.y_pixel_location += 1

                if (self.y_pixel_location >= self.y_pixels):
                    self.y_pixel_location = 0
                    if (frame == self.framesToAverage - 1):
                        self.framesGrabbed += 1
                        self.atTheLastFrame = True


    def setNumberOfChannels(self,channel):
        self.numberOfChannels = get_number_of_channels(channel)

    def displayData(self):
        while self.reading:
            if self.atTheLastFrame:
                for channel in range(self.numberOfChannels):
                    # Calculate intensity of image at given channel
                    intensity = np.average(self.imageData[channel])
                    self.intensities[channel].append(intensity)
                        # Calculate the intensity x-axis
                    index = self.xAxis[-1]()  # index 0 is time index by default, -1 is last index eg. Raman from [Time, Stage, Raman]
                    self.intensitiesIndex[channel].append(index)
                    if self.save:
                        self.saveImage(channel)


                if self.save :
                    self.saveCSV()
                if self.singleFrameScan:
                    self.reading = False
                if self.lastFrameScan:
                    self.reading = False
                self.atTheLastFrame = False
            else:
                time.sleep(0.001)


    def __calculate_sync(self):

        parameters = sync_parameters(resolution=(self.x_pixels,self.y_pixels),
                                     line_dwell_time=self.msline,
                                     fill_fraction=self.fill_fraction,
                                     max_timebase_frequency=self.max_timebase_frequency,
                                     maxbuffer=self.hwbuffer,
                                     number_of_channels=self.numberOfChannels)

        self.clock_rate = parameters.read_clock_rate
        self.samples_per_pixel = parameters.samples_per_pixel
        self.samples_to_read_total_per_line = parameters.samples_to_read_per_channel_per_line
        self.samples_to_read_per_channel_per_line = parameters.samples_to_read_per_channel_per_line
        self.samples_to_read_per_channel = parameters.samples_to_read_per_channel
        self.samples_trash = parameters.samples_trash
        self.data_line = parameters.data_line
        self.divisor = parameters.divisorD
        self.data_line_length = len(self.data_line)

    def __getElapsedTime(self):
        return (time.time() - self.startTime)

    def __saveFileHeader(self):
        fileName = "{}/intensity.csv".format(self.saveFilename)
        if self.save and not (os.path.exists(fileName)):
            with open(fileName, 'a') as f:
                if not self.waitForLastFrame:
                    f.write('Time,X,')
                else :
                    f.write('Time,X,Raman,')
                channelHeaderString = ''
                for i in range(self.numberOfChannels):
                    channelHeaderString += 'Channel%i,'%i
                f.write(channelHeaderString)
                f.write('\n')

    def __saveFileIndex(self):
        '''
        Adds time index to the csv file when saving is enabled
        return: None
        '''
        # if self.saveFilename is not '':
        ## if 'default' in self.scanType.lower():
        if not self.waitForLastFrame: ## todo : temporary measure
            self.xAxis = [self.__getElapsedTime]
        else :
            saveIndices = []
            saveIndices.append(self.__getElapsedTime)
            try :
                for xAxis in self.xAxis :
                    saveIndices.append(xAxis)
            except :
                saveIndices.append(self.xAxis)
            self.xAxis = saveIndices

    def saveImage(self,channel):
        # Recalibrated image intensities to maximimze dynamic range
        recalibratedImage = self.imageData[channel].copy()
        # if 'point' not in self.scanType.lower():
        recalibratedImage -= self.dataMinimums[channel]
        divisor = self.dataMaximums[channel] - self.dataMinimums[channel]
        if self.dataMaximums[channel] == self.dataMinimums[channel]:
            divisor = self.dataMinimums[channel] + 0.0001
        recalibratedImage = recalibratedImage * 65535. / divisor
        recalibratedImage[recalibratedImage > 65535] = 65535
        recalibratedImage[recalibratedImage < 0] = 0
        recalibratedImage = np.array(recalibratedImage, dtype=np.uint16)

        # Save image
        def save_image():
            saveImage = recalibratedImage
            while True:
                try:
                    tf.imsave("{}/ch{}.tiff".format(self.saveFilename, channel), saveImage, pages=self.framesGrabbed)
                    # tf.imsave("%s_%s_ch%i.tiff" % (self.saveFilename, self.saveFileIndex, channel),
                    #           saveImage,append=True,metadata=self.metadata)
                except Exception as e:
                    print("Error in Analog_input.saveImage() : %s" % e)
                    pass
                    # tf.imsave("%s_%s_ch%i.tiff" % (self.saveFilename, self.saveFileIndex, channel),
                    #           saveImage, append=True, metadata=self.metadata)
                    # continue
                break
        save_image()
        # Thread(target=save_image).start()

    def saveCSV(self):
        for channel in range(self.numberOfChannels):
        # Save CSV
            def save_csv():
                if self.saveFilename is not '':
                    # if all(len(i) == len(self.intensities[0]) for i in self.intensities):
                    with open("{}/intensity.csv".format(self.saveFilename), 'a') as f:
                        for xAxis in self.xAxis:
                            # print(self.xAxis)
                            # print(self.xAxis[0]())
                            # print(self.xAxis[1]())
                            print(xAxis())
                            f.write('{:.5f},'.format(xAxis()))
                        for j in range(0, self.numberOfChannels):
                            f.write("%.5f," % (self.intensities[j][-1]))
                            # f.write("%.5f," % (self.intensities[channel][-1]))
                        f.write("\n")

        Thread(target=save_csv).start()

def xtest(array,newdata,samples,x,yloc):
    timeNow = time.time()
    for i in range(x):
        updateArray(array,newdata,samples,x,yloc)
    now = time.time() - timeNow
    print('xtest ', now)
    return now

def xtestc(array,newdata,samples,x,yloc):
    timeNow = time.time()
    for i in range(x):
        cupdateArray(array,newdata,samples,x,yloc)
    now = time.time() - timeNow
    print('xtestc ', now)
    return now

def xtestnc(array,newdata,samples,x,yloc):
    timeNow = time.time()

    #array[yloc] = np.mean(newdata.reshape(-1, samples), 1)
    nupdateArray(array,newdata,samples,x,yloc)

    now = time.time() - timeNow
    print('xtestn ', now)
    return now

if __name__ == "__main__":
    xys = [(50,50,25),(500,500,10)]
    for (x,y,samples) in xys :
        array = np.random.random((x,y))
        arrayx = array.copy()
        newdata = np.random.random(x*samples)
        yloc = 0

        xtestc(array,newdata,samples,x,yloc)
        xtest(array, newdata, samples, x, yloc)
        xtestnc(array, newdata, samples, x, yloc)

    pass
    # import os
    # print(os.getcwd())
    # dll = ctypes.WinDLL("dlls/nilvaiu.dll")