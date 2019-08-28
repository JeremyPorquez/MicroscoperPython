'''Contains library required to access StellarNet Spectrometer'''

import configparser
import os
import pandas as pd
import time
import struct
import matplotlib.pyplot as plt
from PyQt5 import QtCore, QtWidgets, QtGui
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationToolbar
from threading import Thread
from multiprocessing.pool import ThreadPool
from scipy.optimize import curve_fit
from matplotlib.figure import Figure
import numpy as np
from Network.Connections import clientObject
from Gui.Spectrometer_gui import Ui_Spectrometer
from Math import gaussianFunction



class PyStellarNet(object):
    dll = ''
    device_count = 0
    default_directory = os.path.dirname(os.path.realpath(__file__))
    directory = r'C:\Program Files\StellarNet\SpectraWiz'
    directory = default_directory
    integration_time = 10 ## milliseconds
    critical_error = False
    scans_to_average = 1
    smoothing = 0
    temperature_compensation = False
    deviceLoaded = False

    detector_type = {
        '1': 2047,
        '5': 511,
        '6': 1023
    }


    def __init__(self, verbose=True):
        self.SNLoadSpectraWizDLL(verbose=verbose)
        self.SNSpectraWizInit(verbose=verbose)
        self.SNGet_devicecount(verbose=verbose)
        self.calibration = []

        for channel in range(1,self.device_count+1):
            self.calibration.append(np.ones(2051))
        self.SNSet_integration_time(10)
        self.SNSet_digitizer_clockrate(3)
        self.SNGet_all_wavelengths()

    def SNClose(self,verbose=True):
        if self.deviceLoaded :
            self.dll.SWDclose()
        if verbose == True : print("Spectrometer connection halted.")

    def SNLoadSpectraWizDLL(self,dllDirectory=r'C:\Program Files\StellarNet\SpectraWiz',verbose=True):
        try :
            os.chdir(dllDirectory)
            self.dll = ctypes.WinDLL('Swdll.dll')
            self.deviceLoaded = True
        except : self.deviceLoaded = False
        if verbose == True : print("Spectrometer DLL loaded")

    def SNGet_devicecount(self,verbose=True):
        if self.deviceLoaded:
            self.device_count = self.dll.SWDdevcnt() #get number of devices
        else :
            self.device_count = 0
        if verbose == True : print("Number of spectrometers : %i" %self.device_count)
        return self.device_count

    def SNGet_coefficients(self,channel):
        # self.init(verbose=False) ## prevents crashing

        self.SNSet_integration_time(10)
        self.SNUpdate(1,0,0)
        time.sleep(0.1)
        self.SNScan(channel)
        time.sleep(0.1)
        eaddress = [ctypes.c_int16(int(i, 16)) for i in ['80', 'A0', 'C0', 'E0']]
        ee = (ctypes.c_uint8*32)() ## create C variable ee which contains ascii codes for spectrometer coefficients
        for i in range(0,32):
            ee[i] = 0
        ee = ctypes.pointer(ee) ## makes ee a pointer
        c = []
        for i in eaddress:
            time.sleep(0.1)
            self.dll.SWDeeRead(channel,i,ee)
            c.append(bytes(ee[0]))

        coefficients = []
        special_indicator = []

        for i in range(0,len(c)):
            coefficients.append(float(c[i][:31]))
            try : special_indicator.append(int(c[i][31:]))
            except : special_indicator.append(int(0))

        ## special_indicator[0] is the detector specifier
        ## 1 : first 2047 elements are important
        ## 5 : first 511 elements are important
        ## 6 : first 1024 elements are important

        return coefficients,special_indicator[0]

    def SNGet_wavelengths(self,channel):
        # self.init(verbose=False)                    ## prevents from crashing
        c,d = self.SNGet_coefficients(channel)
        c[0] /= 2
        c[1] /= 4
        c[2] /= 1
        c[3] /= 8
        wavelengths = []
        for i in range(0,2051):
            wavelengths.append(c[3] * i ** 3 + c[1] * i ** 2 + c[0] * i + c[2])
        # wavelengths = wavelengths[:self.detector_type[str(d)]]
        # wavelengths = wavelengths[:self.detector_type[str(d)]]
        return np.array(wavelengths)

    def SNGet_all_wavelengths(self):
        self.wavelengths = []
        for channel in range(1,self.device_count+1):
            self.wavelengths.append(self.SNGet_wavelengths(channel))
        return self.wavelengths

    def SNScan(self,channel):
        ''' Returns intensity values *2051 array size'''
        length = 2051  # 2051
        if self.deviceLoaded:
            buffer = (ctypes.c_float * length)()
            for i in range(0,length):
                buffer[i] = ctypes.c_float(0)
            buffer = ctypes.pointer(buffer)

            status = 1

            while status == 1:
                # print('status = 1')
                # time.sleep(self.integration_time/1000)
                # time.sleep(10. / 1000)
                status = self.dll.SWDscanLV(channel,buffer)
                time.sleep(0.01)
            if status > 2:
                print("critical error in SWDScanLV call to swdll.dll")
                self.critical_error = True

            buffer = bytes(buffer[0])

            intensities = []
            for i in range(0,length):
                value = buffer[i*4:i*4+4]
                value = struct.unpack('f',value)
                intensities.append(value)

            intensities = np.reshape(intensities, len(intensities))
        else :
            intensities = np.zeros(length)
        return intensities

    def SNSet_integration_time(self,rate):
        self.integration_time = rate
        if self.deviceLoaded :
            return self.dll.SWDrate(ctypes.c_int32(rate))

    def SNSet_digitizer_clockrate(self,rate=3):
        if self.deviceLoaded :
            return self.dll.SWDxtrate(ctypes.c_int32(rate))

    def SNSpectraWizInit(self, verbose=True):
        if self.deviceLoaded :
            self.dll.SWDinit()
            if verbose == True: print("Spectrometer initialized.")

    def SNUpdate(self,scans_to_average=1,smoothing=0,temperature_compensation=False):
        '''
        Scans To Avg = N
        Smoothing = 0..N
        Temperature Compensation = T/F'''
        self.scans_to_average = scans_to_average
        self.smoothing = smoothing
        self.temperature_compensation = temperature_compensation
        temperature_compensation = int(temperature_compensation)
        if self.deviceLoaded:
            return self.dll.SWDupdate(ctypes.c_int32(scans_to_average),ctypes.c_int32(smoothing),ctypes.c_int32(temperature_compensation))

    def SNBasic_scan(self):
        wavelengths = self.SNGet_wavelengths(1)
        self.SNSet_integration_time(10)
        self.SNSet_digitizer_clockrate(3)
        self.SNUpdate(1, 0, False)
        intensities = self.SNScan(1)
        plt.plot(wavelengths[:511], intensities[:511])
        plt.ylabel("Counts")
        plt.xlabel("Wavelength (nm)")
        plt.show()

class MplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        fig.subplots_adjust(left=0.15, bottom=0.15, right=0.95, top=0.95, wspace=0, hspace=0)
        self.axes = fig.add_subplot(111)
        self.compute_initial_figure()
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def compute_initial_figure(self):
        pass

class SpectrometerWidget(MplCanvas, PyStellarNet):
    """A canvas that updates itself every second with a new plot."""
    class Signal(QtCore.QObject):
        scanInit = QtCore.pyqtSignal()
        scanDone = QtCore.pyqtSignal()

    scanDone = False

    def __init__(self, parentWindow = None, parentLayout = None, connection = None, *args, **kwargs):
        # MplCanvas.__init__(self, *args, **kwargs)
        MplCanvas.__init__(self,parentWindow,*args,**kwargs)
        if parentLayout is not None :
            self.layout = parentLayout
            self.layout.addWidget(self)
        PyStellarNet.__init__(self)

        if self.device_count < 1:
            self.simulateDevice = True
            self.device_count = 3
            print('Simulating device')
            self.wavelengths = [[] for i in range(self.device_count)]

            for i in range(self.device_count):
                self.wavelengths[i] = np.arange(400,1200,0.5)
        else:
            self.simulateDevice = False

        self.frequencies = [[] for i in range(self.device_count)]
        self.mpl_connect('button_press_event', self.onClick)

        # CoreSpectrometer.__init__(self)
        self.xdata,self.ydata = None, None #for fitting
        self.RamanOffset = 12500

        self.SNSet_integration_time(10)
        self.SNUpdate(1,0,False)

        self.scanThread = None
        self.scanning = False
        self.autoscale = False
        self.showFitData = False
        self.realTimeFit = False
        self.fitting = False
        self.popt, self.pcov = None, None
        self.mode = "Spectrometer"

        self.currentYmax = 0

        if connection is not None:
            self.connection = connection

        self.data = [[] for i in range(0, self.device_count)]
        self.background = [np.zeros(2051) for i in range(0, self.device_count)]
        self.backgroundLoaded = False
        self.intensities = [[] for i in range(0, self.device_count)]
        self.fitData = [[] for i in range(0, self.device_count)]
        self.deviceScanEnable = [True for i in range(self.device_count)]
        self.stitchChannel = [0, 0]
        self.stitchWavelength = 900
        self.stitchData = 0, 0
        self.stitch = False
        self.plots = []
        self.fits = []
        self.frequencies = []
        for i in range(self.device_count):
            self.frequencies.append(1.e7 / self.wavelengths[i] - self.RamanOffset)
            self.plots.append(self.axes.plot([])[0])
            self.fits.append(self.axes.plot([])[0])
        self.plots.append(self.axes.plot([])[0])

        self.fitInfo = self.axes.text(0.3,0.9,'',transform=self.axes.transAxes)

        self.signal = self.Signal()
        self.signal.scanDone.connect(lambda : self.setScanStatus(True))
        self.signal.scanInit.connect(lambda : self.setScanStatus(False))

    def onClick(self,event):
        if (event.button == 3) & ((event.xdata is not None) & (event.ydata is not None)):
            # print('button=%d, x=%d, y=%d, xdata=%f, ydata=%f' %
            #       (event.button, event.x, event.y, event.xdata, event.ydata))
            self.xdata = event.xdata
            self.ydata = event.ydata

        if self.realTimeFit:
            self.fit(plotIndex=self.plotIndex)

    def compute_initial_figure(self, xlabel="Wavelength (nm)", ylabel="Intensity (a.u.)",
                               xlim = [350,1600],
                               ylim = [-1000,66000]):
        self.axes.set_xlabel(xlabel)
        self.axes.set_ylabel(ylabel)
        self.axes.set_xlim(xlim)
        self.axes.set_ylim(ylim)

    def get_xy(self,event):
        self.x,self.y = event.xdata,event.ydata
        # print("%.2f %.2f"%(event.xdata,event.ydata))
        return self.x,self.y
        # print('you pressed', event.xdata, event.ydata)
        # .statusBar().showMessage("All hail matplotlib!", 2000)

    def scan(self, background_subtract=False):

        # Simulate data if there's no spectrometer
        self.signal.scanInit.emit()
        if self.mode == "Raman":
            x = self.frequencies
        elif self.mode == "Spectrometer":
            x = self.wavelengths
        if not self.simulateDevice :
            #get the intensity values for each channel
            for i, scan in enumerate(self.deviceScanEnable):
                if scan:
                # init_time = time.time()
                    self.intensities[i] = self.SNScan(i+1)
                # elapsed_time = time.time() - init_time
                # print("Device %i , Elapsed time %.3f" % (channel, elapsed_time,))

            # For each channel, get the wavelengths and restructure into (wavelength, intensity)
                    if background_subtract:
                        intensity = self.intensities[i]*self.calibration[i] - self.background[i]
                        self.data[i] = x[i], intensity
                    else:
                        self.intensities[i] *= self.calibration[i]
                        self.data[i] = x[i], self.intensities[i]
                else:
                    self.data[i] = [], []

        else :
            for i, scan in enumerate(self.deviceScanEnable):
                # self.wavelengths[i] = [np.arange(400,1000,0.5)]
                if scan:
                    x0 = 600 + 200 * i + np.random.random()
                    sigma = 10 + 10 * i

                    A = 30000+10000*i + np.random.random()*10
                    self.intensities[i] = gaussianFunction(self.wavelengths[0],
                                                           A=A,x0=x0,sigma=sigma)
                    if self.mode == 'Raman':
                        x0 = 1.e7/x0 - self.RamanOffset
                        sigma = 100 + 100 * i


                    self.data[i] = x[i], self.intensities[i]
                else:
                    self.data[i] = [], []

        if self.stitch:
            x1 = np.array(self.wavelengths[self.stitchChannel[0]])
            x2 = np.array(self.wavelengths[self.stitchChannel[1]])
            x1 = x1[x1 <= self.stitchWavelength]
            x2 = x2[x2 > self.stitchWavelength]
            y1 = self.data[self.stitchChannel[0]][1][:len(x1)]
            y2 = self.data[self.stitchChannel[1]][1][-len(x2):]
            x_stitch = np.concatenate([x1, x2])
            x = x_stitch
            if self.mode == 'Raman':
                x = 1.e7/x_stitch - self.RamanOffset
            y = np.concatenate([y1, y2])
            self.stitchData = x,y


        if self.autoscale:
            if self.currentYmax < np.max(self.intensities):
                self.currentYmax = np.max(self.intensities)
                self.axes.set_ylim(0,self.currentYmax)

        self.signal.scanDone.emit()
        if self.data is not None:
            return self.data




    def startContinuousScan(self):
        def threadscan():
            while self.scanning:
                # try :
                time.sleep(self.integration_time / 1000.)
                self.scan(background_subtract=self.backgroundLoaded)
                self.plot()
                # except Exception as e:
                #     print(e)

        if self.scanThread is not None :
            if self.scanThread.is_alive() :
                self.stopContinuousScan()
        self.scanning = True
        self.scanThread = Thread(target=threadscan)
        # self.scanThread.daemon = True
        self.scanThread.start()

    def stopContinuousScan(self):
        self.realTimeFit = False
        self.scanning = False
        if self.scanThread is not None :
            while self.scanThread.is_alive():
                time.sleep(0.1)
            self.scanThread = None

    def fit(self, plotIndex = None,sigma=20):
        if plotIndex is not None:
            self.plotIndex = plotIndex

        if self.data is not None:


            if self.xdata is None:
                self.xdata = 400
            if self.ydata is None:
                self.ydata = 400

            p0g = [self.ydata, self.xdata, sigma]
            try :
                self.popt, self.pcov = curve_fit(gaussianFunction, self.data[self.plotIndex][0], self.data[self.plotIndex][1], p0g)
                # print("A : %.3f \t x : %.3f \t sigma = %.3f"%(self.popt[0],self.popt[1],self.popt[2]))
                FWHM = 2.355*self.popt[2]
                # FWHM = self.popt[1]
                if self.showFitData:
                    if self.mode == 'Spectrometer':
                        units = 'nm'
                    else :
                        units = 'cm$^{-1}$'
                    self.fitInfo.set_text(r'x=%.2f y=%.2f FWHM=%.1f %s'%(self.popt[1],self.popt[0],FWHM,units))

                if self.device_count > 0:
                    fitData = gaussianFunction(self.data[self.plotIndex][0],*self.popt)
                    # self.fitData[self.plotIndex] = self.data[self.plotIndex][0],fitData
                    self.fitData[0] = self.data[self.plotIndex][0], fitData

                    if self.plots.__len__() < (self.device_count + self.fitData.__len__()):
                        self.plots.append(self.axes.plot([])[0])
            except Exception as e :
                print(e)

            if self.scanning == False:
                try : self.plot()
                except : print('Error occured in fit')

    def hideFit(self):
        self.showFitData = False
        self.fitInfo.set_text('')
        for i in range(0, self.device_count):
            self.fits[i].set_data([], [])

    def showFit(self):
        self.showFitData = True

    def setFit(self):
        if self.showFitData:
            self.hideFit()
        else:
            self.showFit()

    def enableRealTimeFit(self,plotIndex):
        self.plotIndex = plotIndex
        self.realTimeFit = True

    def disableRealTimeFit(self):
        self.realTimeFit = False

    def plot(self):
        if self.realTimeFit :
            self.fit()
        for i in range(0, self.device_count):
            self.plots[i].set_data(self.data[i])
            if self.showFitData:
            # if self.fitData[i].__len__() > 0: #makes sure fit data is present
                # self.fits[i].set_data(self.fitData[i]) ## show all fits
                self.fits[i].set_data(self.fitData[0])
        if self.stitch:
            if self.deviceScanEnable[self.stitchChannel[0]] &  self.deviceScanEnable[self.stitchChannel[1]]:
                self.plots[-1].set_data(self.stitchData)
        else:
            self.plots[-1].set_data([0,0])

        self.draw()

    def yscale(self):
        self.autoscale = False
        maximum = 0
        for index, enabled in enumerate(self.deviceScanEnable):
            if enabled:
                intensities = self.intensities[index]
                if max(intensities) > maximum :
                    maximum = max(intensities)
        if maximum == 0: maximum = 1000
        self.axes.set_ylim(0, maximum)
        self.draw()

    def setSpectrometerMode(self):
        self.mode = "Spectrometer"
        # for i in range(0, self.device_count):
        #     self.wavelengths[i] = 1.e7/(self.wavelengths[i]+self.RamanOffset)
        self.compute_initial_figure(xlim=[350, 1600])


    def setRamanMode(self):

        self.mode = "Raman"

        if self.xdata is not None:
            self.xdata = 1.e7 / self.xdata - self.RamanOffset

        for i in range(self.device_count):
            # self.wavelengths[i] = 1.e7/self.wavelengths[i] - self.RamanOffset
            self.frequencies[i] = 1.e7 / self.wavelengths[i] - self.RamanOffset

        self.compute_initial_figure(xlabel=r"Wavenumber (cm$^{-1}$)",xlim=[-4000,1000])

    def setScanStatus(self,status=False):
        self.scanDone = status
        if self.connection is not None:
            self.connection.connectionIsBusy = not status
        else:
            self.connectionIsBusy = not status

class Spectrometer():
    class Signal(SpectrometerWidget.Signal):
        close = QtCore.pyqtSignal()
        appInit = QtCore.pyqtSignal()
        appLoaded = QtCore.pyqtSignal()

    def __checkExists(self):
        handle = ctypes.windll.user32.FindWindowW(None, "Spectrometer 2017")
        if handle != 0:
            ctypes.windll.user32.ShowWindow(handle, 10)
            exit(0)

    def __init__(self):
        self.connection = clientObject(parent=self)
        self.signal = self.Signal()
        self.signal.appInit.emit()

        self.ui = Ui_Spectrometer()
        self.mainWindow = CustomMainWindow()
        self.mainWindow.setWindowIcon(QtGui.QIcon('Gui/spectrometer.ico'))
        self.ui.setupUi(self.mainWindow) #Setups the user interface

        self.cwd = os.path.dirname(os.path.realpath(__file__))
        self.spectrometer = SpectrometerWidget(parentWindow=self.mainWindow,
                                               parentLayout=self.ui.SpectrometerHandle,
                                               connection = self.connection)

        self.spectrometer.mpl_connect('motion_notify_event', self.update_statusBar)


        self.spectrometer.navi_toolbar = NavigationToolbar(self.spectrometer, self.mainWindow)
        self.ui.SpectrometerHandle.addWidget(self.spectrometer.navi_toolbar)


        self.calibration_files = [[] for i in range(0,self.spectrometer.device_count)]
        self.ini_file = self.cwd + '\\Spectrometer.ini'
        self.load_ini()
        self.getWavelengths()
        self.calibrateEnable = False
        self.fileLoaded = None
        self.savingContinuously = False

        # LOAD DEFAULTS
        self.ui.integration_time_spinbox.setValue(self.integration_time)
        self.ui.scans_to_average_spinbox.setValue(self.scans_to_average)
        self.ui.smoothing_spinbox.setValue(self.smoothing)
        self.ui.stitchWavelength_spinbox.setValue(self.spectrometer.stitchWavelength)
        self.__set_integration_time()
        self.__set_scans_to_average()
        self.__set_smoothing()

        self.plotList = ['Plot %i'%i for i in range(1,self.spectrometer.device_count+1)]
        self.setupButtonActions()
        self.setupSpinBoxes()
        self.setupMenuItems()
        self.setupComboBoxes()
        self.setupKeyPress()

        # INITIATE APPLICATION
        self.mainWindow.signal.close.connect(self.fileQuit)

        self.mainWindow.show()
        self.mainWindow.setWindowTitle("Spectrometer 2017")
        screen = QtWidgets.QDesktopWidget().screenGeometry()
        self.mainWindow.move(screen.width()-751, 0)
        self.mainWindow.activateWindow()

        self.setScan()
        self.connection.autoConnect(self.connectionPort)
        self.signal.close.connect(self.fileQuit)
        self.signal.appLoaded.emit()

    def setupButtonActions(self):
        self.ui.acqbackgroundButton.clicked.connect(self.get_background)
        self.ui.backgroundButton.clicked.connect(self.set_background)
        self.ui.autoscaleButton.clicked.connect(self.set_autoscale)
        self.ui.resetScaleButton.clicked.connect(self.set_resetscale)
        # self.ui.stopScanButton.clicked.connect(self.spectrometer.stopContinuousScan)
        self.ui.setScanButton.clicked.connect(self.setScan)
        self.ui.yScaleButton.clicked.connect(self.set_yscale)
        self.ui.saveButton.clicked.connect(lambda : self.save())
        self.ui.saveContinuouslyButton.clicked.connect(lambda : self.start_autosave())
        self.ui.fitButton.clicked.connect(self.fitPlots)
        self.ui.showFitButton.clicked.connect(self.setFit)
        self.ui.calibratedButton.clicked.connect(lambda: Thread(target=self.calibrate).start())
        self.ui.ch1CheckBoxWidget.clicked.connect(self.checkScanDevices)
        self.ui.ch2CheckBoxWidget.clicked.connect(self.checkScanDevices)
        self.ui.ch3CheckBoxWidget.clicked.connect(self.checkScanDevices)
        self.ui.stitchCheckBoxWidget.clicked.connect(self.checkScanDevices)
        self.ui.stitchWavelength_spinbox.valueChanged.connect(self.checkScanDevices)

    def setupKeyPress(self):
        def keyPress(event):
            if event.key() == QtCore.Qt.Key_Enter or event.key() == QtCore.Qt.Key_Return:
                wasScanning = False
                if self.spectrometer.scanning:
                    wasScanning = True
                    self.stopContinuousScan()
                time.sleep(0.1)
                self.__set_integration_time()
                self.__set_scans_to_average()
                self.__set_smoothing()
                time.sleep(0.1)
                if wasScanning:
                    self.spectrometer.startContinuousScan()

        self.mainWindow.signal.keyPress.connect(keyPress)

    def setupSpinBoxes(self):
        pass
        # self.ui.integration_time_spinbox.valueChanged.connect(self.__set_integration_time)
        # self.ui.scans_to_average_spinbox.valueChanged.connect(self.__set_scans_to_average)
        # self.ui.smoothing_spinbox.valueChanged.connect(self.__set_smoothing)

    def setupMenuItems(self):
        self.ui.action_Quit.triggered.connect(self.mainWindow.close)
        self.ui.action_Save.triggered.connect(self.save)
        self.ui.action_Load_Calibration_Files.triggered.connect(self.getCalibrationFiles)
        self.ui.actionRaman_Mode.triggered.connect(self.spectrometer.setRamanMode)
        self.ui.actionSpectrometer_Mode.triggered.connect(self.spectrometer.setSpectrometerMode)
        self.ui.action_Set_laser_wavelength.triggered.connect(self.setLaserWavelength)
        self.ui.actionConnect.triggered.connect(self.connection.startClientConnection)
        self.ui.actionDisconnect.triggered.connect(self.connection.stopClientConnection)

    def setupComboBoxes(self):
        self.ui.plotNumberComboBox.clear()
        self.ui.plotNumberComboBox.addItems(self.plotList)

    def checkScanDevices(self):
        self.spectrometer.deviceScanEnable[0] = self.ui.ch1CheckBoxWidget.isChecked()
        self.spectrometer.deviceScanEnable[1] = self.ui.ch2CheckBoxWidget.isChecked()
        self.spectrometer.deviceScanEnable[2] = self.ui.ch3CheckBoxWidget.isChecked()
        self.spectrometer.stitch = self.ui.stitchCheckBoxWidget.isChecked()
        self.spectrometer.stitchWavelength = self.ui.stitchWavelength_spinbox.value()

    def get_background(self):
        wasFitting = False
        wasScanning = False

        if self.spectrometer.scanning:
            wasScanning = True
            self.stopContinuousScan()

        if self.spectrometer.showFitData:
            wasFitting = True
            self.hideFit()

        # else:
        #     restartScan = False
        # time.sleep(1)

        self.zero_background()
        dir = self.cwd + "\\Background\\"
        if not os.path.exists(dir):
            os.makedirs(dir)
        if self.calibrateEnable :
            self.calibrateOff()
        self.spectrometer.scan()
        for i in range(1,self.spectrometer.device_count+1):
            intensity = self.spectrometer.intensities[i-1]
            wavelength = self.spectrometer.wavelengths[i-1]
            data = pd.DataFrame(intensity,columns=['Counts'],index=wavelength)
            data.index.name = 'Wavelength (nm)'
            data.to_csv(dir + 'background_ch%i_i%i.csv'%(i,self.integration_time))
            self.spectrometer.background[i - 1] = intensity
            print('created : ' + dir + 'background_ch%i_i%i.csv'%(i,self.integration_time))

        self.load_background()

        if self.calibrateEnable :
            self.calibrateOn()

        if wasFitting:
            self.spectrometer.showFit()

        if wasScanning:
            self.spectrometer.startContinuousScan()



        # Thread(target=get_background).start()

    def set_background(self):
        if not self.spectrometer.simulateDevice :
            if not self.spectrometer.backgroundLoaded:
                self.load_background()
            else:
                self.zero_background()

    def load_background(self):
        dir = self.cwd + "\\Background\\"
        for i in range(1, self.spectrometer.device_count + 1):
            filename = dir + 'background_ch%i_i%i.csv' % (i, self.integration_time)
            if os.path.exists(filename):
                data = pd.read_csv(filename)
                self.spectrometer.background[i - 1] = data.Counts.values
                print('loaded :' + filename)
                self.spectrometer.backgroundLoaded = True
                self.ui.backgroundButton.setText("Unload background")
            else:
                print('No %s exists. Take background data.' % filename)
                self.spectrometer.backgroundLoaded = False
                self.ui.backgroundButton.setText("Load background")

    def zero_background(self):
        if self.spectrometer.backgroundLoaded:
            for i in range(0, self.spectrometer.device_count):
                self.spectrometer.background[i] = np.zeros(2051)
            self.ui.backgroundButton.setText("Load background")
            self.spectrometer.backgroundLoaded = False

    def calibrateOn(self):
        for i in range(0, self.spectrometer.device_count):
            if self.calibration_files[i] is '':
                absolutePath = QtWidgets.QFileDialog.getOpenFileName(directory=self.cwd)[0]
                relativePath = self.cwd
                self.calibration_files[i] = os.path.relpath(absolutePath, relativePath)
            if self.calibration_files[i] is '':
                break
            calibrationFileDirectory = os.path.join(self.cwd,self.calibration_files[i])
            cf = pd.read_csv(calibrationFileDirectory, index_col=0, names=['Y'])
            self.spectrometer.calibration[i] = cf['Y'].values

    def calibrateOff(self):
        for i in range(0, self.spectrometer.device_count):
            self.spectrometer.calibration[i] = np.ones(2051)

    def calibrate(self):
        self.calibrateEnable = not self.calibrateEnable
        if self.calibrateEnable :
            self.calibrateOn()
            self.ui.calibratedButton.setText("Unload calibration")
        else:
            self.calibrateOff()
            self.ui.calibratedButton.setText("Load calibration")

    def getCalibrationFiles(self):
        for i in range(0, self.spectrometer.device_count):
            absolutePath = QtWidgets.QFileDialog.getOpenFileName(directory=self.cwd)[0]
            relativePath = self.cwd
            self.calibration_files[i] = os.path.relpath(absolutePath,relativePath)

    def getWavelengths(self):
        return self.spectrometer.wavelengths

    def fitPlots(self):
        if self.ui.fitButton.text() == "Fit":
            self.ui.fitButton.setText("Stop Fit")
            self.ui.showFitButton.setEnabled(True)
            self.spectrometer.fit(plotIndex = self.ui.plotNumberComboBox.currentIndex())
            self.showFit()
            self.spectrometer.enableRealTimeFit(plotIndex=self.ui.plotNumberComboBox.currentIndex())
        else :
            self.ui.fitButton.setText("Fit")
            self.ui.showFitButton.setEnabled(False)
            self.spectrometer.enableRealTimeFit(plotIndex=self.ui.plotNumberComboBox.currentIndex())

    def setScan(self):
        if self.spectrometer.scanning == False:
            self.startContinuousScan()
        else:
            self.stopContinuousScan()

    def startContinuousScan(self):
        self.spectrometer.startContinuousScan()
        self.ui.setScanButton.setText("Stop scan")

    def stopContinuousScan(self):
        self.spectrometer.stopContinuousScan()
        self.ui.setScanButton.setText("Start scan")

    def scan(self,background_subtract=False):
        self.spectrometer.scan(background_subtract)

    def plotNumberValueChange(self):
        pass

    def showFit(self):
        self.spectrometer.showFit()
        self.ui.showFitButton.setText("Hide Fit")

    def hideFit(self):
        self.spectrometer.hideFit()
        self.ui.showFitButton.setText("Show Fit")

    def stopFit(self):
        if self.spectrometer.showFitData :
            self.setFit()

    def setFit(self):
        if self.spectrometer.showFitData :
            self.ui.showFitButton.setText("Hide Fit")
        else :
            self.ui.showFitButton.setText("Show Fit")
        self.spectrometer.setFit()
        self.spectrometer.disableRealTimeFit()


    def scan(self):
        self.spectrometer.scan()

    def plot(self,background_subtract=False):
        self.spectrometer.plot(background_subtract)

    def start_autosave(self, delay=5):

        if not self.savingContinuously:
            if not hasattr(self,'filename'):
                self.filename = None

            if self.filename is None:
                self.filename, self.saveextension = \
                    QtWidgets.QFileDialog.getSaveFileName(options=QtWidgets.QFileDialog.DontConfirmOverwrite)

            if self.filename != '':
                 self.ui.saveContinuouslyButton.setText("Stop saving")
                 self.savingContinuously = True

                 def autosave(delay=60):
                     dt = 0.1
                     time_elapsed = 0
                     total_time_elapsed = 0
                     while self.savingContinuously:
                         self.save(filename=self.filename,label='{}'.format(total_time_elapsed,'%.3f'),append=True)
                         time.sleep(dt)
                         time_elapsed += dt
                         total_time_elapsed += dt
                         if time_elapsed > delay:
                             time_elapsed = 0

                 Thread(target=autosave,args=(delay,)).start()

        else:
            self.ui.saveContinuouslyButton.setText("Save Continuously")
            self.savingContinuously = False




    def save(self, filename = None, label = 'Intensity', append = False):

        self.filename = filename

        ### get filename
        if self.filename is None :
            self.filename,self.saveextension = \
                QtWidgets.QFileDialog.getSaveFileName(options=QtWidgets.QFileDialog.DontConfirmOverwrite)

        if self.filename is not '':
            csvFileExists = []
            for i, save in enumerate(self.spectrometer.plots):
                csvFilename = "%s_%i.csv" % (self.filename, i)
                exists = os.path.exists(csvFilename)
                csvFileExists.append(exists)
            fileExists = exists #a temporary measure

            # Initiates
            if fileExists :
                if not self.fileLoaded:
                    self.dataFrames = []
                    df = pd.ExcelFile(self.filename)
                    for i, save in enumerate(self.spectrometer.plots):
                        if save:
                            sheetName = 'Spectrometer %i' % i
                            dataFrame = df.parse(sheetName,index_col=0)
                            self.dataFrames.append(dataFrame)
                    self.fileLoaded = True
                    print('writer book set')
            else : #if file doesn't exist create blank dataframes
                self.dataFrames = []
                for i, save in enumerate(self.spectrometer.plots):
                    # if save:
                    dataFrame = pd.DataFrame()
                    dataFrame['Wavelength'] = self.spectrometer.plots[i]._x
                    dataFrame.set_index('Wavelength', inplace=True)
                    self.dataFrames.append(dataFrame)
                self.fileLoaded = True


            #Use excel writer to write DataFrame of spectrometer data in different sheets

            for i,dataFrame in enumerate(self.dataFrames):
                dataFrame[label] = self.spectrometer.plots[i]._y
                # sheetName = 'Spectrometer %i' % i ## disabled in preference for csv
                # dataFrame.to_excel(self.writer, sheet_name=sheetName) ## disabled in preference for csv
                csvFilename = "%s_%i.csv"%(self.filename,i)
                dataFrame.to_csv(csvFilename)


    def set_autoscale(self):
        self.spectrometer.autoscale = not self.spectrometer.autoscale
        if self.spectrometer.autoscale :
            self.ui.autoscaleButton.setText("Disable autoscale")
        else :
            self.ui.autoscaleButton.setText("Autoscale")

    def setLaserWavelength(self):
        laserWavelength, accept = QtWidgets.QInputDialog.getText(self,
                                                 "Input Dialog : ",
                                                 "Set laser wavelength : ")
        if accept :
            try :
                self.RamanOffset = 1.e7/float(laserWavelength)
            except :
                pass
        if self.spectrometer.mode == "Spectrometer": self.spectrometer.setSpectrometerMode()
        if self.spectrometer.mode == "Raman": self.spectrometer.setRamanMode()

    def set_resetscale(self):
        if self.spectrometer.mode == "Raman":
            self.spectrometer.compute_initial_figure(xlabel = r"Wavenumber (cm$^{-1}$)",
                                                     ylabel = "Intensity (a.u.)",
                                                     xlim = [-4000, 300],
                                                     ylim = [0,65535])
        else:
            self.spectrometer.compute_initial_figure()

    def set_yscale(self):
        self.spectrometer.yscale()

    def start_scan(self):
        self.spectrometer.startContinuousScan()

    def stop_scan(self):
        self.spectrometer.stopContinuousScan()

    def fileQuit(self):
        print('Quitting')
        self.spectrometer.disableRealTimeFit()
        self.spectrometer.stopContinuousScan()
        self.connection.stopClientConnection()
        self.save_ini()


    def load_ini(self):
        config = configparser.ConfigParser()

        def make_default_ini():
            config['Settings'] = {}
            config['Settings']['Integration time'] = '10'
            config['Settings']['Scans to average'] = '1'
            config['Settings']['Smoothing'] = '0'
            config['Settings']['Temperature compensation'] = 'False'
            config['Settings']['Port'] = '10121'
            config['Settings']['Stitch Channel 1'] = '1'
            config['Settings']['Stitch Channel 2'] = '2'
            config['Settings']['Stitch Wavelength'] = '900'
            config['Background'] = {}


            config['Calibration'] = {}

            config['Calibration']['Channel 0'] = 'Devices\Spectrometer\Calibration\bc.csv'
            config['Calibration']['Channel 1'] = 'Devices\Spectrometer\Calibration\bw.csv'
            config['Calibration']['Channel 2'] = 'Devices\Spectrometer\Calibration\ds.csv'

            with open(self.ini_file, 'w') as configfile:
                config.write(configfile)

        def read_ini():
            config.read(self.ini_file)
            self.integration_time = int(config['Settings']['Integration time'])
            self.scans_to_average = int(config['Settings']['Scans to average'])
            self.smoothing = int(config['Settings']['Smoothing'])
            self.temperature_compensation = bool(config['Settings']['Temperature compensation'])
            self.spectrometer.SNSet_integration_time(self.integration_time)
            self.spectrometer.SNUpdate(self.scans_to_average,
                                       self.smoothing,
                                       self.temperature_compensation)
            self.connectionPort = int(config['Settings']['Port'])
            for i in range(0,self.spectrometer.device_count):
                self.calibration_files[i] = config['Calibration']['Channel %i'%i]
            self.spectrometer.stitchChannel[0] = int(config['Settings']['Stitch Channel 1'])
            self.spectrometer.stitchChannel[1] = int(config['Settings']['Stitch Channel 2'])
            self.spectrometer.stitchWavelength = int(config['Settings']['Stitch Wavelength'])

        try :
            read_ini()
        except :
            make_default_ini()
            read_ini()

    def save_ini(self):
        config = configparser.ConfigParser()
        config['Settings'] = {}
        config['Settings']['Integration time'] = str(self.ui.integration_time_spinbox.value())
        config['Settings']['Scans to average'] = str(self.ui.scans_to_average_spinbox.value())
        config['Settings']['Smoothing'] = str(self.ui.smoothing_spinbox.value())
        config['Settings']['Temperature compensation'] = 'False'
        config['Settings']['Port'] = str(self.connectionPort)
        config['Settings']['Stitch Channel 1'] = str(self.spectrometer.stitchChannel[0])
        config['Settings']['Stitch Channel 2'] = str(self.spectrometer.stitchChannel[1])
        config['Settings']['Stitch Wavelength'] = str(self.spectrometer.stitchWavelength)
        config['Background'] = {}

        config['Calibration'] = {}
        for i in range(0,self.spectrometer.device_count):
            config['Calibration']['Channel %i'%i] = self.calibration_files[i]

        with open(self.ini_file, 'w') as configfile:
            config.write(configfile)

    def update_statusBar(self,event):
        if not event.inaxes:
            return
        x,y = self.spectrometer.get_xy(event)

    def About(self):
        QtWidgets.QMessageBox.about(self, "About",
                                    """SpectraWiz Spectrometer code by : Jeremy Porquez"""
                                )
    def endScript(self):
        if self.ui.setScanButton.text() == "Stop scan":
            self.stopContinuousScan()
        else:
            self.startContinuousScan()

        if self.ui.fitButton.text() == "Stop Fit":
            self.stopFit()
        else:
            self.fitPlots()


    def __spectro_set(self,func, a):
        self.scanning = False
        time.sleep(0.1)
        try:
            func(*a)
        except:
            func(a)
        time.sleep(0.1)
        self.scanning = True

    def __set_scans_to_average(self):
        scans_to_average = int(self.ui.scans_to_average_spinbox.text())
        if scans_to_average > 0:
            self.scans_to_average = scans_to_average
            self.__spectro_set(self.spectrometer.SNUpdate,
                        (scans_to_average, self.smoothing, self.temperature_compensation))
        else:
            self.ui.scans_to_average_spinbox.setSpecialValueText("1")

    def __set_smoothing(self):
        smoothing = int(self.ui.smoothing_spinbox.text())
        if smoothing >= 0:
            self.smoothing = smoothing
            self.__spectro_set(self.spectrometer.SNUpdate, (
                self.scans_to_average, self.smoothing, self.temperature_compensation))

    def __set_integration_time(self):
        wasScanning = False
        if self.spectrometer.scanning:
            wasScanning = True
            self.stopContinuousScan()
        integration_time = int(self.ui.integration_time_spinbox.value())
        # self.ui.integration_time_spinbox.setValue(integration_time)

        if integration_time >= 10:
            # wasScanning = self.spectrometer.scanning
            # if self.spectrometer.scanning :
            #     self.spectrometer.scanning = False
            # time.sleep(self.integration_time/1000)
            self.integration_time = integration_time
            self.spectrometer.SNSet_integration_time(self.integration_time)
            # if wasScanning:
            #     self.spectrometer.startContinuousScan()
        # else:
        #     self.ui.integration_time_spinbox.setValue(10)
        #     self.integration_time = 10
        #     self.spectrometer.SNSet_integration_time(self.integration_time)
        if wasScanning:
            self.startContinuousScan()

class CustomMainWindow(QtWidgets.QMainWindow):

    class Signal(QtCore.QObject):
        close = QtCore.pyqtSignal()
        keyPress = QtCore.pyqtSignal(QtCore.QEvent)

    def __init__(self):
        super().__init__()
        self.signal = self.Signal()

    def closeEvent(self, event):
        self.signal.close.emit()
        super().closeEvent(event)
        event.accept()

    def keyPressEvent(self, event):
        self.signal.keyPress.emit(event)
        super().keyPressEvent(event)


# class Spectrometer_ExampleApp(CustomMainWindow):
#     def __init__(self):
#         # QtWidgets.QMainWindow.__init__(self)
#         super().__init__()
#         self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
#         self.setWindowTitle("application main window")
#
#         self.file_menu = QtWidgets.QMenu('&File', self)
#         self.file_menu.addAction('&Quit', self.fileQuit,
#                                  QtCore.Qt.CTRL + QtCore.Qt.Key_Q)
#         self.menuBar().addMenu(self.file_menu)
#
#         self.help_menu = QtWidgets.QMenu('&Help', self)
#         self.menuBar().addSeparator()
#         self.menuBar().addMenu(self.help_menu)
#
#         self.help_menu.addAction('&About', self.about)
#         self.main_widget = QtWidgets.QWidget(self)
#         self.main_widget.setFocus()
#         self.setCentralWidget(self.main_widget)
#
#         self.l = QtWidgets.QGridLayout(self.main_widget)
#
#         self.fig_add_spectrometer()
#
#     def fig_add_spectrometer(self):
#         self.dc = SpectrometerWidget(self.main_widget, width=500, height=400, dpi=100)
#         self.dc.mpl_connect('motion_notify_event', self.update_statusBar)
#         self.l.addWidget(self.dc,2,2)
#         self.navi_toolbar = NavigationToolbar(self.dc,self.main_widget)
#         self.l.addWidget(self.navi_toolbar,3,2)
#
#     def fileQuit(self):
#         self.close()
#
#     def closeEvent(self, ce):
#         self.fileQuit()
#
#     def update_statusBar(self,event):
#         if not event.inaxes:
#             return
#         x,y = self.dc.get_xy(event)
#         self.statusBar().showMessage("x = %.2f, y = %.2f"%(x,y), 0)
#
#     def about(self):
#         QtWidgets.QMessageBox.about(self, "About",
#                                     """SpectraWiz Spectrometer code by : Jeremy Porquez""")
#
# class SpectrometerConnection(object):
#     def __init__(self,url="127.0.0.1",port=2500,server=None):
#         if server is not None :
#             self.server = server
#         self.url = url
#         self.port = port
#         self.setupServer()
#
#     def setupServer(self):
#         self.address = (self.url,self.port)
#
#
#     def scan(self,*args,**kwargs):
#         self.server.send(["scan",args,kwargs])
#
#     def plot(self,*args,**kwargs):
#         self.server.send(["plot",args,kwargs])
#
#     def save(self,*args,**kwargs):
#         self.server.send(["save",args,kwargs])



if __name__ == '__main__':
    import sys
    import ctypes
    myappid = u'microscoperspectrometer'  # arbitrary string
    if os.name == "nt" :
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    # qApp = QtWidgets.QApplication(sys.argv)
    # aw = Spectrometer_App2()
    # aw.setWindowTitle("%s" % "Spectrometer App")
    # aw.show()
    # sys.exit(qApp.exec_())

    qApp = QtWidgets.QApplication(sys.argv)
    app = Spectrometer()
    # mw.setWindowTitle("%s" % "Spectrometer App")
    sys.exit(qApp.exec_())




