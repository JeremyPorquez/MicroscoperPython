import os, sys
import time
from threading import Thread
import configparser
import numpy as np
import pandas as pd
from PyQt5 import QtWidgets, QtGui, QtCore
import Microscoper
from Microscoper import get_number_of_channels
from Gui.Microscoper_gui import Ui_Microscoper2017
from Devices import Display
from Network.Connections import clientObject
import Math
from StellarN import SpectrometerExtension
import csv

## todo : to implement memcached instead of my own custom server

if sys.maxsize > 2 ** 32:
    sixfourbit = True
else :
    sixfourbit = False

class Microscope(Microscoper.Microscope):
    connectionPort = None
    inputChannels = None
    rasterOffset = [0,0]


    class Signal(QtCore.QObject):
        scanDoneSignal = QtCore.pyqtSignal()
        scanSoftDoneSignal = QtCore.pyqtSignal()
        scanStartSignal = QtCore.pyqtSignal()
        imageAcquireStartSignal = QtCore.pyqtSignal()
        imageAcquireFinishedSignal = QtCore.pyqtSignal()

    def __checkExists(self):
        handle = ctypes.windll.user32.FindWindowW(None, "Microscoper 2017")
        if handle != 0:
            ctypes.windll.user32.ShowWindow(handle, 10)
            exit(0)

    def __init__(self, app = None):
        self.__checkExists()
        self.signal = self.Signal()

        #Initiates inheritance
        self.mainWindow = QtWidgets.QMainWindow()
        self.ui = Ui_Microscoper2017()

        Microscoper.Microscope.__init__(self)
        self.connection = clientObject(parent=self)
        self.cwd = os.path.dirname(os.path.realpath(__file__))
        self.verbose = True

        # Setup UI
        self.setupUi()

        #Load ini file
        self.loadDefaults()

        self.mainWindow.setEnabled(False)

        self.detectors = Microscoper.MicroscopeDetector(widgets=self.pmtWidgets,model="3101")
        self.shutter = Microscoper.MicroscopeShutter(widgets=self.shutterWidgets)

        self.setupStage()

        self.mainWindow.setEnabled(True)
        self.setupScanList()

        self.imageLevels = None
        self.display = None
        self.ao = None
        self.app = app
        self.numberOfInputChannels = Microscoper.get_number_of_channels(self.inputChannels)
        self.xyPointScanPosition = self.rasterOffset[0], self.rasterOffset[1]

        # Preloads analog input multiprocessing
        self.ai = Microscoper.Analog_input(parent=self,
                                           inputChannels = self.inputChannels,
                                           polarityWidgets = self.pmtPolarityWidgets)
        self.createDisplay()
        self.spectrometer = SpectrometerExtension(self)

        self.connection.autoConnect(self.connectionPort)
        self.connection.connectionSignal.connectionLost.connect(self.acquireStop)

    def setupScanList(self):
        scanFilePath = os.path.join(self.cwd,"Microscoper_app_scanList.csv")
        self.scanList = pd.read_csv(scanFilePath)
        scanList = self.scanList['Scan Name'].values
        self.ui.scanTypeWidget.clear()
        self.ui.scanTypeWidget.addItems(scanList)

    def setupUi(self):
        self.ui.setupUi(self.mainWindow)
        self.setupWidgets()
        self.setupMenuActions()
        self.mainWindow.setWindowIcon((QtGui.QIcon('Gui/plopperPig.ico')))
        self.mainWindow.setWindowTitle("Microscoper 2018")
        self.mainWindow.show()
        screen = QtGui.QDesktopWidget().screenGeometry()
        size = self.mainWindow.geometry()
        self.mainWindow.move(0, screen.height() - size.height() - 100)
        self.mainWindow.activateWindow()

    def setupStage(self):
        self.LinearStage = Microscoper.LStage(serialNumber=94839332, widgets=self.linearStageWidgets,name='linear stage')
        self.xStage = Microscoper.LStage(serialNumber=94839334, widgets=self.xStageWidgets,name='x stage')
        self.yStage = Microscoper.LStage(serialNumber=94839333, widgets=self.yStageWidgets,name='y stage')
        if sixfourbit : self.zStage = Microscoper.ZStage(widgets=self.zStageWidgets)

        if self.ui.CalibrationFilenameText.text() is not '':
            try : self.__displayCalibration()
            except : pass

        self.updateUi()

    def updateUi(self):
        self.setupButtonActions()
        self.ui.FilenameText.setText(self.saveFilename)
        self.ui.DirectoryText.setText(self.saveDirectory)

    def setupWidgets(self):
        self.pmtWidgets = [self.ui.PMTSlider0, self.ui.PMTLabel0, self.ui.PMTZero0, self.ui.PMTPreset0,
                      self.ui.PMTSlider1, self.ui.PMTLabel1, self.ui.PMTZero1, self.ui.PMTPreset1,
                      self.ui.PMTSlider2, self.ui.PMTLabel2, self.ui.PMTZero2, self.ui.PMTPreset2,
                      self.ui.PMTSlider3, self.ui.PMTLabel3, self.ui.PMTZero3, self.ui.PMTPreset3,
                      self.ui.PMTStatusText]

        self.pmtPolarityWidgets = [self.ui.pmtInvert1, self.ui.pmtInvert2, self.ui.pmtInvert3, self.ui.pmtInvert4]
        self.shutterWidgets = [self.ui.PumpShutterButton, self.ui.StokesShutterButton]
        self.linearStageWidgets = [self.ui.LstagePresetWidget1, self.ui.LstagePresetWidget2, self.ui.LstagePresetWidget3,
                                   self.ui.LStageStart,self.ui.LStageEnd,self.ui.LStageMove,self.ui.currentLStagePositionText]
        self.xStageWidgets = [self.ui.xStagePresetWidget1, self.ui.currentXStagePositionText, self.ui.deltaOffset]
        self.yStageWidgets = [self.ui.yStagePresetWidget1, self.ui.currentYStagePositionText, self.ui.deltaOffset]
        self.zStageWidgets = [self.ui.ZStageStart, self.ui.ZStageEnd, self.ui.ZStageMove, self.ui.zStagePresetWidget1, self.ui.currentZStagePositionText]

    def setupMenuActions(self):
        self.ui.action_Quit.triggered.connect(self.fileQuit)
        self.ui.action_setImageLevels.triggered.connect(self.setImageLevels)
        # self.action_Spectrometer.triggered.connect(self.openSpectrometer)
        self.ui.action_Connect.triggered.connect(self.connection.startClientConnection)
        # self.action_Rotation_Stage.triggered.connect(self.openRotationStage)
        self.ui.actionBring_all_to_front.triggered.connect(self.__maximizeWindows)

    def setupButtonActions(self):
        self.ui.PMTPreset0.clicked.connect(lambda: self.detectors.setPMTsPresetActions[0](self.acquiring))
        self.ui.PMTPreset1.clicked.connect(lambda: self.detectors.setPMTsPresetActions[1](self.acquiring))
        self.ui.PMTPreset2.clicked.connect(lambda: self.detectors.setPMTsPresetActions[2](self.acquiring))
        self.ui.PMTPreset3.clicked.connect(lambda: self.detectors.setPMTsPresetActions[3](self.acquiring))

        self.ui.PMTZero0.clicked.connect(lambda : self.detectors.setPMTsZeroActions[0](self.acquiring))
        self.ui.PMTZero1.clicked.connect(lambda: self.detectors.setPMTsZeroActions[1](self.acquiring))
        self.ui.PMTZero2.clicked.connect(lambda: self.detectors.setPMTsZeroActions[2](self.acquiring))
        self.ui.PMTZero3.clicked.connect(lambda: self.detectors.setPMTsZeroActions[3](self.acquiring))

        self.ui.PMTSlider0.valueChanged.connect(lambda : self.detectors.setPMTsSliderActions[0](self.acquiring))
        self.ui.PMTSlider1.valueChanged.connect(lambda : self.detectors.setPMTsSliderActions[1](self.acquiring))
        self.ui.PMTSlider2.valueChanged.connect(lambda : self.detectors.setPMTsSliderActions[2](self.acquiring))
        self.ui.PMTSlider3.valueChanged.connect(lambda: self.detectors.setPMTsSliderActions[3](self.acquiring))

        self.ui.PumpShutterButton.clicked.connect(self.shutter.Set_PumpShutter) # from class Shutters
        self.ui.StokesShutterButton.clicked.connect(self.shutter.Set_StokesShutter)
        self.ui.AcquireButton.clicked.connect(self.acquireSet)
        self.ui.browseButton.clicked.connect(self.__getSaveFile)
        self.ui.browseCalibrationButton.clicked.connect(self.__getCalibrationFile)
        self.ui.DirectoryText.textChanged.connect(self.saveDefaults)
        self.ui.LstagePresetButton1.clicked.connect(self.LinearStage.movePresetFunction[1]) #from class LSTAGE
        self.ui.LstagePresetButton2.clicked.connect(self.LinearStage.movePresetFunction[2])
        self.ui.LstagePresetButton3.clicked.connect(self.LinearStage.movePresetFunction[3])
        self.ui.upButton.clicked.connect(lambda: self.yStage.MoveDir("Up", self.ui.microcopeOffsetRadio.isChecked()))
        self.ui.upButton.clicked.connect(lambda: self.changeRasterOffset("Up",self.ui.galvoOffsetRadio.isChecked()))
        self.ui.upButton.clicked.connect(self.acquireSoftRestart)
        self.ui.downButton.clicked.connect(lambda: self.yStage.MoveDir("Down",self.ui.microcopeOffsetRadio.isChecked()))
        self.ui.downButton.clicked.connect(lambda: self.changeRasterOffset("Down", self.ui.galvoOffsetRadio.isChecked()))
        self.ui.downButton.clicked.connect(self.acquireSoftRestart)
        self.ui.leftButton.clicked.connect(lambda: self.xStage.MoveDir("Left",self.ui.microcopeOffsetRadio.isChecked()))
        self.ui.leftButton.clicked.connect(lambda: self.changeRasterOffset("Left", self.ui.galvoOffsetRadio.isChecked()))
        self.ui.leftButton.clicked.connect(self.acquireSoftRestart)
        self.ui.rightButton.clicked.connect(lambda: self.xStage.MoveDir("Right",self.ui.microcopeOffsetRadio.isChecked()))
        self.ui.rightButton.clicked.connect(lambda: self.changeRasterOffset("Right",self.ui.galvoOffsetRadio.isChecked()))
        self.ui.rightButton.clicked.connect(self.acquireSoftRestart)
        self.ui.zoomWidget.valueChanged.connect(self.acquireSoftRestart)
        self.ui.zoomWidget.valueChanged.connect(self.saveDefaults)
        self.ui.dwellTime.valueChanged.connect(self.acquireSoftRestart)
        self.ui.dwellTime.valueChanged.connect(self.saveDefaults)
        self.ui.resolutionWidget.valueChanged.connect(self.acquireSoftRestart)
        self.ui.resolutionWidget.valueChanged.connect(self.saveDefaults)
        self.ui.fillFractionWidget.valueChanged.connect(self.acquireSoftRestart)
        self.ui.fillFractionWidget.valueChanged.connect(self.saveDefaults)
        self.ui.microcopeOffsetRadio.clicked.connect(self.changeDOffsetLabel)
        self.ui.galvoOffsetRadio.clicked.connect(self.changeDOffsetLabel)
        self.ui.stageReadRadioNormal.clicked.connect(self.changeStageRead)
        self.ui.stageReadRadioCalibrated.clicked.connect(self.changeStageRead)
        self.ui.xPresetButton1.clicked.connect(self.xStage.movePresetFunction[1])
        self.ui.yPresetButton1.clicked.connect(self.yStage.movePresetFunction[1])
        if sixfourbit : self.ui.zPresetButton1.clicked.connect(self.zStage.movePresetFunction[1])
        self.ui.scanTypeWidget.currentIndexChanged.connect(self.changeScanTypeWidget)

    def getScanAttributes(self):
        index = self.ui.scanTypeWidget.currentIndex()
        self.scanName = self.ui.scanTypeWidget.currentText()
        self.scanStage = self.scanList.loc[index]['Stage']
        self.scanMove = self.scanList.loc[index]['Move Type']
        self.scanDetector = self.scanList.loc[index]['Detector Type']
        self.scanFrames = self.scanList.loc[index]['Frames']
        self.scanUnits = self.scanList.loc[index]['Move Units']

    def changeDOffsetLabel(self):
        if self.ui.microcopeOffsetRadio.isChecked() : self.ui.deltaOffsetLabel.setText("dOffset (mm)")
        else : self.ui.deltaOffsetLabel.setText("dOffset(V)")

    def changeStageRead(self):
        pass
        # if self.stageReadRadioNormal.isChecked(): showNormal


    def changeScanTypeWidget(self):
        index = self.ui.scanTypeWidget.currentIndex()
        incrementString = self.scanList.loc[index]['Move Units']
        try :
            self.ui.LStageMoveLabel.setText(incrementString)
            # self.LStageMoveLabel.setText(text[self.scanTypeWidget.currentText()])
        except :
            pass
            # self.LStageMoveLabel.setText('Speed (mm/s)')

    def createDisplay(self):
        self.display = Display.Display2D(image_input=self.ai.imageData)
        self.display.fps = 15

    def closeDisplay(self):
        try : self.display.close()
        except : pass
        self.display = None

    def generateScan(self):
        if 'point' in self.scanName.lower() :
            if self.xyPointScanPosition is not None :
                data_x = np.tile(self.xyPointScanPosition[0],self.ao.x_pixels_total*self.ao.y_pixels)
                data_y = np.tile(self.xyPointScanPosition[1],self.ao.x_pixels_total*self.ao.y_pixels)
                data = np.array([data_x,data_y])
                self.ao.set_data(data)
            else :
                print('No xy point scan position provided, defaulting to center point')
                self.ao.set_data(Math.generateRasterScan(0,
                                                         self.ao.x_pixels,
                                                         self.ao.y_pixels,
                                                         self.ao.x_pixels_flyback,
                                                         self.rasterOffset))
        else :
            self.ao.set_data(Math.generateRasterScan(self.maxScanAmplitude / self.zoom,
                                                     self.ao.x_pixels,
                                                     self.ao.y_pixels,
                                                     self.ao.x_pixels_flyback,
                                                     self.rasterOffset))

    def changeRasterOffset(self,direction='Up',execute=False):
        direction = direction.lower()
        if execute:
            if ('up' in direction):
                self.rasterOffset[1] += self.ui.deltaOffset.value()
            if ('right' in direction):
                self.rasterOffset[0] += self.ui.deltaOffset.value()
            if ('down' in direction):
                self.rasterOffset[1] -= self.ui.deltaOffset.value()
            if ('left' in direction):
                self.rasterOffset[0] -= self.ui.deltaOffset.value()
            print(self.rasterOffset)

    def setImageLevels(self):
        def createWindow():
            try :
                self.imageLevels = \
                Display.ImageLevelsWidget(parent=self,
                                          numberOfImages=self.numberOfInputChannels,
                                          arrayValuesMax=self.imageMaximums,
                                          arrayValuesMin=self.imageMinimums,
                                          images=self.ai.imageData)
                self.imageLevels.signal.update.connect(self.display.update)
            except : self.imageLevels = \
                Display.ImageLevelsWidget(parent=self,
                                          numberOfImages=self.numberOfInputChannels,
                                          arrayValuesMax=self.imageMaximums,
                                          arrayValuesMin=self.imageMinimums,
                                          )
        try :
            self.imageLevels.close()
            createWindow()
        except :
            createWindow()

        self.imageLevels.signal.close.connect(self.setImageLevelsClosed)

    def setImageLevelsClosed(self):
        self.imageLevels = None

    def setStage(self):
        if self.scanStage == "LinearStage":
            self.LinearStage.SetStartPosition()
        elif self.scanStage == "zStage":
            self.zStage.SetStartPosition()

    def acquireSet(self):
        self.saveDefaults()
        self.acquiring = not self.acquiring
        if self.acquiring :
            self.acquire()
        else :
            self.acquireStop()

    def acquire(self):
        self.ui.AcquireButton.setText("Stop Acquire")
        self.acquireInit()
        self.acquireStart()

    def acquireInit(self):

        ## Initialize defaults --------------------------------------
        self.zoom = int(self.ui.zoomWidget.value())
        self.getxyScanPosition()
        self.resolution = (int(self.ui.resolutionWidget.value()), int(self.ui.resolutionWidget.value()))
        self.msline = self.ui.dwellTime.value()
        self.__calculate_fillFraction()
        self.getScanAttributes()
        if self.scanStage == "LinearStage":
            self.LinearStage.SetMoveType(self.scanMove)
        elif self.scanStage == "zStage":
            self.zStage.SetMoveType(self.scanMove)
            self.zStage.zTolerance = self.ui.ZStageMove.value()/10
        #############################################################

        ## Initiatelize spectrometer --------------------------------
        self.initSpectrometer()
        #############################################################

        ## Set the stage position -----------------------------------
        self.setStage()

        ## Create analog output channel -----------------------------
        self.ao = Microscoper.Analog_output(channels=self.outputChannels,
                                            resolution=self.resolution,
                                            line_dwell_time=self.msline,
                                            fill_fraction=self.ff,
                                            hwbuffer=self.device_buffer,
                                            verbose=self.verbose,
                                            trigger="/Dev1/ai/StartTrigger")
        self.generateScan()
        #############################################################


        ## Generate save files --------------------------------------
        self.metadata = {'Zoom' : self.ui.zoomWidget.value(),
                         'Line dwell time' : self.msline,
                         'Pixel dwell time' : (1000*self.msline)/(self.resolution[0]*(1+self.ff)),
                         'Fill fraction' : self.ff,
                         'Resolution' : self.resolution,
                         'Linear Scan speed' : self.ui.LStageMove.value(),
                         'Z-steps' : self.zStage.MoveDef.value(),
                         'PMT0' : self.ui.PMTSlider0.value(),
                         'PMT1' : self.ui.PMTSlider1.value(),
                         'PMT2' : self.ui.PMTSlider2.value(),
                         'ImageLevelsMin' : self.imageMinimums,
                         'ImageLevelsMax' : self.imageMaximums,
                         'xposition' : self.ui.currentXStagePositionText.text(),
                         'yposition' : self.ui.currentYStagePositionText.text(),
                         'zposition' : self.ui.currentZStagePositionText.text(),
                         }

        self.saveFileIndex = time.strftime("%Y_%m_%d_%H%M%S", time.gmtime())

        if self.ui.saveCheckBox.isChecked():
            if self.ui.DirectoryText.text() == '':
                self.saveFilename = ''
            else :
                if not os.path.exists(self.ui.DirectoryText.text()):
                    os.mkdir(self.ui.DirectoryText.text())

                self.saveFilename = os.path.join(self.ui.DirectoryText.text(), self.ui.FilenameText.text())
                self.saveFilename += "_{}".format(self.saveFileIndex)
                if not os.path.exists(self.saveFilename):
                    os.mkdir(self.saveFilename)

                infoFilePath = "{}/info.csv".format(self.saveFilename)

                try :
                    with open(infoFilePath,'w',newline='') as infoFile:
                        csvFile = csv.writer(infoFile)
                        for key, val in self.metadata.items():
                            csvFile.writerow([key, val])
                    # self.saveFilename += ' %ix %ims ff%.1f %.3fmmps x%.3fy%.3f' % (self.zoom, self.msline, self.ff, self.LStageMove.value(), float(self.currentXStagePositionText.text()),float(self.currentYStagePositionText.text()))

                    print("Saving to %s"%self.saveFilename)
                except :
                    print('Cannot save to %s'%self.saveFilename)
                    self.saveFilename = ''

        #############################################################

        self.detectors.setPMTs()
        print('Warming up PMTs')
        time.sleep(1)
        self.shutter.Microscope_shutter_open()

        ## Determine x axis display plot  -------------------------------------
        if self.scanMove == "None": self.xAxis = 'Default'
        elif self.scanMove == 'Continuous':
            self.xAxis = self.LinearStage.GetPos, self.__returnCalibration
        elif self.scanMove == "Discrete":
            if self.scanStage == "zStage": self.xAxis = self.zStage.GetPos
            elif self.scanStage == "LinearStage" : self.xAxis = self.LinearStage.GetPos, self.__returnCalibration
        else : self.xAxis = 'Default'
        #############################################################

        ## Create analog input channels -----------------------------
        if self.scanDetector == "PMT":
            singleFrameScan = False
            waitForLastFrame = False
            if self.scanMove in ['Continuous','Discrete']: waitForLastFrame = True
            if self.scanFrames == 'Discrete': singleFrameScan = True
            self.ai.init(channel=self.inputChannels,
                         resolution=self.resolution,
                         line_dwell_time=self.msline,
                         fill_fraction=self.ff,
                         hwbuffer=self.device_buffer,
                         verbose=self.verbose,
                         save=self.ui.saveCheckBox.isChecked(),
                         saveFilename=self.saveFilename,
                         saveFileIndex=self.saveFileIndex,
                         xAxis=self.xAxis,
                         metadata=self.metadata,
                         waitForLastFrame=waitForLastFrame,
                         singleFrameScan=singleFrameScan,
                         framesToAverage=self.ui.scansToAverage.value(),
                         dataMaximums=self.imageMaximums,
                         dataMinimums=self.imageMinimums,
                         )

        ## Initialize Spectrometer ----------------------------------
        if self.scanDetector == "PMT":
            if self.display is not None :
                try : self.display.signal.close.disconnect()
                except : pass
                self.display.close()
                self.display = Display.Display2D(image_input=self.ai.imageData,
                                                 intensity_plot=self.ai.intensities,
                                                 intensity_index=self.ai.intensitiesIndex,
                                                 imageMaximums=self.imageMaximums,
                                                 imageMinimums=self.imageMinimums,
                                                 app = self.app,
                                                 )
            else :
                self.display = Display.Display2D(image_input=self.ai.imageData,
                                                 intensity_plot=self.ai.intensities,
                                                 intensity_index=self.ai.intensitiesIndex,
                                                 imageMaximums=self.imageMaximums,
                                                 imageMinimums=self.imageMinimums,
                                                 app = self.app,
                                                 )
            self.display.fps = 15
            self.display.signal.close.connect(self.acquireStop)
            self.display.signal.close.connect(self.closeDisplay)
        #############################################################

        ## Set display levels ---------------------------------------
        if self.imageLevels is not None:
            self.imageLevels.setImage(self.ai.imageData)
            self.imageLevels.signal.update.connect(self.display.update)
        #############################################################

    def acquireStart(self):
        self.signal.scanStartSignal.emit()
        self.ao.start()
        if self.scanDetector == "PMT":
            self.ai.start()
            self.display.start()
        if self.scanDetector == "Spectrometer":
            self.spectrometerScan()
        self.detectScanStatusThread = Thread(target=self.detectScanStatus)
        self.detectScanStatusThread.start()

    def acquireSoftStart(self):
        self.signal.scanStartSignal.emit()
        self.zoom = int(self.ui.zoomWidget.value())
        self.resolution = (int(self.ui.resolutionWidget.value()), int(self.ui.resolutionWidget.value()))
        self.msline = self.ui.dwellTime.value()
        self.__calculate_fillFraction()
        # self.shutter.Microscope_shutter_open()
        time.sleep(0.1)
        self.ao = Microscoper.Analog_output(channels=self.outputChannels,
                                            resolution=self.resolution,
                                            line_dwell_time=self.msline,
                                            fill_fraction=self.ff,
                                            hwbuffer=self.device_buffer,
                                            verbose=self.verbose)
        self.generateScan()

        if self.scanDetector == "PMT":
            singleFrameScan = False
            waitForLastFrame = False
            if self.scanMove in ['Continuous', 'Discrete']: waitForLastFrame = True
            if self.scanMove in ['Grab', 'Discrete']: singleFrameScan = True
            self.ai.init(channel=self.inputChannels,
                         resolution=self.resolution,
                         line_dwell_time=self.msline,
                         fill_fraction=self.ff,
                         hwbuffer=self.device_buffer,
                         verbose=self.verbose,
                         save=self.ui.saveCheckBox.isChecked(),
                         saveFilename=self.saveFilename,
                         saveFileIndex=self.saveFileIndex,
                         xAxis=self.xAxis,
                         metadata=self.metadata,
                         waitForLastFrame=waitForLastFrame,
                         singleFrameScan=singleFrameScan,
                         framesToAverage=self.ui.scansToAverage.value(),
                         dataMaximums=self.imageMaximums,
                         dataMinimums=self.imageMinimums,
                         )

            # self.display.setImage(self.ai.imageData)
            self.display.set(image_input=self.ai.imageData,
                             intensity_plot=self.ai.intensities,
                             intensity_index=self.ai.intensitiesIndex,
                             imageMaximums=self.imageMaximums,
                             imageMinimums=self.imageMinimums,
                             app=self.app,
                             )

        self.ao.start()

        if self.scanDetector == "PMT":
            self.ai.start()
        if self.scanDetector == "Spectrometer":
            self.spectrometerScan()


    def acquireSoftStop(self):
        self.ao.clear()
        while self.ai.reading :
            time.sleep(0.1)
        if self.scanDetector == "PMT":
            self.ai.clear()
        # self.shutter.Microscope_shutter_close()
        self.signal.scanSoftDoneSignal.emit()

    def acquireSoftRestart(self):
        if self.acquiring:
            if self.scanDetector == "PMT":
                self.ao.clear()
                self.ai.clear()
            self.acquireSoftStart()

    def acquireStop(self):
        try :
            self.spectrometer.endScan()
            self.LinearStage.Stop()
            self.xStage.Stop()
            self.yStage.Stop()
            if sixfourbit : self.zStage.Stop()
            if self.ai.reading : self.ai.clear()
            if self.display is not None: self.display.stop()
            while self.ai.reading: time.sleep(0.1)
            if self.ao is not None :
                if self.ao.running : self.ao.clear()
            self.getxyScanPosition()
            self.scanStatusThreadInterrupt = True
            self.shutter.Microscope_shutter_close()
            self.detectors.setPMTsZero()
            self.ui.AcquireButton.setText("Acquire")
            self.acquiring = False
        except Exception as e:
            print(e)
        self.signal.scanDoneSignal.emit()

    def detectScanStatus(self):
        self.scanStatusThreadInterrupt = False
        def stageContinuousUntilEnds():
            if self.scanStage == "LinearStage":
                self.LinearStage.SetStartScan()
            elif self.scanStage == "zStage":
                self.zStage.SetStartScan()
            while (abs(self.LinearStage.currentPosition - self.LinearStage.endScanPosition) > 1e-4) and (not self.scanStatusThreadInterrupt):
                time.sleep(0.1)
            else :
                self.acquireStop()
                self.setStage()
        def stageDiscreteUntilEnds():
            while (self.LinearStage.currentPosition < self.LinearStage.endScanPosition) and (not self.scanStatusThreadInterrupt):
                if not self.ai.reading:
                    self.acquireSoftStop()
                    self.LinearStage.MoveAbs(self.LinearStage.currentPosition+self.LinearStage.MoveDef.value())
                    while not self.LinearStage.positionStageOK:
                        time.sleep(0.1)
                    time.sleep(1)
                    self.acquireSoftStart()
                time.sleep(0.1)
            self.acquireStop()
            self.setStage()
        def zDiscreteUntilEnds():
            while (self.zStage.currentPosition < self.zStage.endScanPosition) and (not self.scanStatusThreadInterrupt):
                if not self.ai.reading:
                    self.acquireSoftStop()
                    targetPosition = self.ui.ZStageStart.value() + self.stageMoveIndex*self.zStage.MoveDef.value()
                    self.stageMoveIndex += 1
                    self.zStage.MoveAbs(targetPosition)
                    while self.zStage.moving:
                        time.sleep(0.1)
                    time.sleep(1)
                    self.acquireSoftStart()
                time.sleep(0.1)
            else :
                self.acquireStop()
        def stageDefault():
            return None

        if self.scanMove == "None": stageDefault()
        if self.scanMove == "Continuous": stageContinuousUntilEnds()
        if self.scanMove == "Discrete":
            self.stageStartPosition = self.ui.LStageStart.value()
            self.stageMoveIndex = 1
            if self.scanStage == "LinearStage": stageDiscreteUntilEnds()
            if self.scanStage == "zStage": zDiscreteUntilEnds()

    def initSpectrometer(self):
        if self.scanDetector == "Spectrometer":
            if self.spectrometer is None :
                self.openSpectrometer()
            self.connection.sendConnectionMessage('spectrometer.stopContinuousScan()')

    def spectrometerScan(self):
        self.spectrometer.scan()
        if self.ui.saveCheckBox.isChecked():
            if self.saveDirectory is not '':
                fileName = os.path.join(self.ui.DirectoryText.text(), self.saveFilename)
                xAxis = self.xAxis
                self.spectrometer.save(fileName=fileName, xAxis=xAxis)
        self.connection.askForResponse(receiver="spectrometer",sender="main",timeout=5)

    def closeEvent(self, event):
        self.fileQuit()
        if self.mainWindow.isEnabled():
            event.accept()
        else : event.ignore()

    def fileQuit(self):
       if self.mainWindow.isEnabled():
           print('Quit pressed')
           self.listening = False
           if self.acquiring:
               self.acquireStop()
           if self.display is not None:
               self.display.close()
           if self.imageLevels is not None:
               self.imageLevels.close()
           self.LinearStage.stageUpdate = False
           self.xStage.stageUpdate = False
           self.yStage.stageUpdate = False
           self.LinearStage.Clear()
           self.xStage.Clear()
           self.yStage.Clear()
           if sixfourbit : self.zStage.Clear()
           self.ai.terminate()
           self.saveDefaults()
           self.connection.stopClientConnection()
           self.mainWindow.close()

    def loadDefaults(self):

        config = configparser.ConfigParser()

        def make_default_ini():
            config['Files'] = {}
            config['Files']['Default filename'] = 'Microscoper'
            config['Files']['Default directory'] = 'C:/Users/Jeremy/Desktop/Microscoper'
            config['Settings'] = {}
            config['Settings']['Device buffer'] = '8192'
            config['Settings']['Maximum scan amplitude'] = '16'
            config['Settings']['Input channels'] = 'Dev1/ai0:3'
            config['Settings']['Output channels'] = 'Dev1/ao0:1'
            config['Settings']['Detector max'] = '1000'
            config['Settings']['Detector min'] = '0'
            config['Settings']['Resolution'] = '32'
            config['Settings']['Zoom'] = '1'
            config['Settings']['Dwell time'] = '1'
            config['Settings']['Fill fraction'] = '1'
            config['Stage'] = {}
            config['Stage']["Start position"] = "0"
            config['Stage']['End position'] = "10"
            config['Stage']['Increments'] = "0.050"
            config['Stage']["Z Start position"] = "0"
            config['Stage']['Z End position'] = "20"
            config['Stage']['Z Increments'] = "0.48"
            config['Stage']['x preset'] = '0'
            config['Stage']['y preset'] = '0'
            config['Stage']['z preset'] = '0'
            config['Stage']['l preset1'] = '0'
            config['Stage']['l preset2'] = '80'
            config['Stage']['l preset3'] = '150'
            config['Scan'] = {}
            config['Scan']['Frames to average'] = '1'
            for i in range(0,get_number_of_channels(config['Settings']['Input channels'])):
                config['Scan']['Image Maximums %i' % i] = '1000'
                config['Scan']['Image Minimums %i' % i] = '0'
            config['Scan']['X Offset'] = '0'
            config['Scan']['Y Offset'] = '0'
            config['Connection'] = {}
            config['Connection']['Port'] = '10120'
            config['Paths'] = {}
            config['Paths']['Python 32bit'] = 'C:/Python36-32'

            with open(self.ini_file, 'w') as configfile:
                config.write(configfile)

        def read_ini():
            config.read(self.ini_file)
            self.saveFilename = config['Files']['Default filename']
            self.saveDirectory = config['Files']['Default directory']
            self.device_buffer = int(config['Settings']['Device buffer'])
            self.maxScanAmplitude = float(config['Settings']['Maximum scan amplitude'])
            self.inputChannels = config['Settings']['Input channels']
            self.outputChannels = config['Settings']['Output channels']
            self.detectorMax = int(config['Settings']['Detector max'])
            self.detectorMin = int(config['Settings']['Detector min'])
            self.ui.resolutionWidget.setValue(int(config['Settings']['Resolution']))
            self.ui.zoomWidget.setValue(int(config['Settings']['Zoom']))
            self.ui.dwellTime.setValue(float(config['Settings']['Dwell time']))
            self.ui.fillFractionWidget.setValue(float(config['Settings']['Fill fraction']))
            self.ui.LStageStart.setValue(float(config['Stage']["Start position"]))
            self.ui.LStageEnd.setValue(float(config['Stage']['End position']))
            self.ui.LStageMove.setValue(float(config['Stage']['Increments']))
            self.ui.ZStageStart.setValue(float(config['Stage']["Z Start position"]))
            self.ui.ZStageEnd.setValue(float(config['Stage']['Z End position']))
            self.ui.ZStageMove.setValue(float(config['Stage']['Z Increments']))
            self.ui.LstagePresetWidget1.setValue(float(config['Stage']['l preset1']))
            self.ui.LstagePresetWidget2.setValue(float(config['Stage']['l preset2']))
            self.ui.LstagePresetWidget3.setValue(float(config['Stage']['l preset3']))
            self.ui.xStagePresetWidget1.setValue(float(config['Stage']['x preset']))
            self.ui.yStagePresetWidget1.setValue(float(config['Stage']['y preset']))
            self.ui.zStagePresetWidget1.setValue(float(config['Stage']['z preset']))
            self.ui.CalibrationFilenameText.setText(config['Calibration']['Calibration File'])
            self.ui.scansToAverage.setValue(int(config['Scan']['Frames to average']))
            self.imageMaximums = []
            self.imageMinimums = []
            for i in range(0,Microscoper.get_number_of_channels(self.inputChannels)):
                max = float(config['Scan']['Image Maximums %i' % i])
                min = float(config['Scan']['Image Minimums %i' % i])
                if max == min:
                    max += 1
                self.imageMaximums.append(max)
                self.imageMinimums.append(min)
            self.rasterOffset = [0,0]
            self.rasterOffset[0] = float(config['Scan']['X Offset'])
            self.rasterOffset[1] = float(config['Scan']['Y Offset'])
            self.connectionPort = int(config['Connection']['Port'])
            self.python32path = config['Paths']['Python 32bit']
        # try:
        read_ini()
        # except:
        #     make_default_ini()
        #     read_ini()


    def saveDefaults(self):
        config = configparser.ConfigParser()

        config['Files'] = {}
        config['Files']['Default filename'] = self.ui.FilenameText.text()
        config['Files']['Default directory'] = self.ui.DirectoryText.text()
        config['Settings'] = {}
        config['Settings']['Device buffer'] = str(self.device_buffer)
        config['Settings']['Maximum scan amplitude'] = str(self.maxScanAmplitude)
        config['Settings']['Input channels'] = self.inputChannels
        config['Settings']['Output channels'] = self.outputChannels
        config['Settings']['Detector max'] = str(self.detectorMax)
        config['Settings']['Detector min'] = str(self.detectorMin)
        config['Settings']['Resolution'] = str(int(self.ui.resolutionWidget.value()))
        config['Settings']['Zoom'] = str(int(self.ui.zoomWidget.value()))
        config['Settings']['Dwell time'] = str(self.ui.dwellTime.value())
        config['Settings']['Fill fraction'] = str(self.ui.fillFractionWidget.value())
        config['Stage'] = {}
        config['Stage']["Start position"] = str(self.ui.LStageStart.value())
        config['Stage']['End position'] = str(self.ui.LStageEnd.value())
        config['Stage']['Increments'] = str(self.ui.LStageMove.value())
        config['Stage']["Z Start position"] = str(self.ui.ZStageStart.value())
        config['Stage']['Z End position'] = str(self.ui.ZStageEnd.value())
        config['Stage']['Z Increments'] = str(self.ui.ZStageMove.value())
        config['Stage']['l preset1'] = str(self.ui.LstagePresetWidget1.value())
        config['Stage']['l preset2'] = str(self.ui.LstagePresetWidget2.value())
        config['Stage']['l preset3'] = str(self.ui.LstagePresetWidget3.value())
        config['Stage']['x preset'] = str(self.ui.xStagePresetWidget1.value())
        config['Stage']['y preset'] = str(self.ui.yStagePresetWidget1.value())
        config['Stage']['z preset'] = str(self.ui.zStagePresetWidget1.value())
        config['Calibration'] = {}
        config['Calibration']['Calibration File'] = self.ui.CalibrationFilenameText.text()
        config['Scan'] = {}
        config['Scan']['Frames to average'] = str(int(self.ui.scansToAverage.value()))
        for i in range(0, Microscoper.get_number_of_channels(self.inputChannels)):
            config['Scan']['Image Maximums %i' % i] = str(self.imageMaximums[i])
            config['Scan']['Image Minimums %i' % i] = str(self.imageMinimums[i])
        config['Scan']['X Offset'] = str(self.rasterOffset[0])
        config['Scan']['Y Offset'] = str(self.rasterOffset[1])
        config['Connection'] = {}
        config['Connection']['Port'] = str(self.connectionPort)
        config['Paths'] = {}
        config['Paths']['Python 32bit'] = self.python32path

        with open(self.ini_file, 'w') as configfile:
            config.write(configfile)

    def __calculate_fillFraction(self):
        self.ff = self.ui.fillFractionWidget.value()
        # if self.zoomWidget.value() < 4:
        #     self.ff = 1
        # else :
        #     self.ff = 0.5
        if self.verbose : print('Fill fraction set to %.2f'%self.ff)

    def __getSaveFile(self):
        self.saveDirectory = QtWidgets.QFileDialog.getExistingDirectory()
        self.ui.DirectoryText.setText(self.saveDirectory)

    def __getCalibrationFile(self):
        self.calibrationFile = QtWidgets.QFileDialog.getOpenFileName()[0]
        self.ui.CalibrationFilenameText.setText(self.calibrationFile)
        self.__displayCalibration()

    def __displayCalibration(self):
        self.displayingCalibration = False
        self.calibrationFile = self.ui.CalibrationFilenameText.text()
        try:
            calibrationFile = open(self.calibrationFile, "r")
            self.stageCalibrationFormulaString = calibrationFile.read()

            def calculate():
                while self.displayingCalibration:
                    wavenumber = eval(
                        self.stageCalibrationFormulaString.replace("x", self.ui.currentLStagePositionText.text()))
                    self.ui.WavenumberText.setText('%i cm-1' % wavenumber)
                    time.sleep(0.1)

            self.displayingCalibration = True
            calcThread = Thread(target=calculate)
            calcThread.daemon = True
            calcThread.start()

        except:
            pass

    def __returnCalibration(self):
        wavenumber = eval(
            self.stageCalibrationFormulaString.replace("x", self.ui.currentLStagePositionText.text()))
        return wavenumber

    def __maximizeWindows(self):
        handles = []
        handles.append(ctypes.windll.user32.FindWindowW(None, "Microscoper 2018"))
        handles.append(ctypes.windll.user32.FindWindowW(None, "Microscoper Display 2017"))
        handles.append(ctypes.windll.user32.FindWindowW(None, "Microscoper Server 2017"))
        handles.append(ctypes.windll.user32.FindWindowW(None, "Zaber 2017"))
        handles.append(ctypes.windll.user32.FindWindowW(None, "Spectrometer 2017"))
        for handle in handles:
            ctypes.windll.user32.ShowWindow(handle, 10)

    def getxyScanPosition(self):
        try :
            x = self.rasterOffset[0] + (self.maxScanAmplitude/self.zoom)*(self.display.clickPositionRatio[0]-0.5)
            y = self.rasterOffset[1] + (self.maxScanAmplitude/self.zoom)*(self.display.clickPositionRatio[1]-0.5)
            self.xyPointScanPosition = x,y
        except :
            x = self.rasterOffset[0]
            y = self.rasterOffset[1]
            self.xyPointScanPosition = x,y
        return x,y

if __name__ == "__main__":
    import sys
    import ctypes
    myappid = u'microscoper'  # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    qAppx = QtWidgets.QApplication(sys.argv)
    app = Microscope(app=qAppx)
    sys.exit(qAppx.exec_())
    ## todo : grab does not work properly