import os, sys
import time
from threading import Thread
import numpy as np
import pandas as pd
from PyQt5 import QtWidgets, QtGui, QtCore
from ui.microscoper import Ui_Microscoper
from Devices import Display
from MNetwork.Connections import ClientObject
import MicroscoperComponents
import MMath
import csv

if sys.maxsize > 2 ** 32:
    sixfourbit = True
else :
    sixfourbit = False

class Microscope(MicroscoperComponents.Microscope):

    def toWavenumber(self):
        try : wavenumber = eval(
            self.stageCalibrationFormulaString.replace("x", self.ui.currentLStagePositionText.text()))
        except :
            wavenumber = 0
        return wavenumber

    def displayWavenumber(self):
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

    def getSaveFile(self):
        self.ui.directoryText.setText(QtWidgets.QFileDialog.getExistingDirectory())

    # def __getCalibrationFile(self):
    #     self.calibrationFile = QtWidgets.QFileDialog.getOpenFileName()[0]
    #     self.ui.CalibrationFilenameText.setText(self.calibrationFile)
    #     self.__displayCalibration()

    class Signal(QtCore.QObject):
        scanInitSignal = QtCore.pyqtSignal()
        scanStartSignal = QtCore.pyqtSignal()
        scanStartAcquire = QtCore.pyqtSignal()
        scanDoneSignal = QtCore.pyqtSignal()
        scanSoftDoneSignal = QtCore.pyqtSignal()
        scanStopAcquire = QtCore.pyqtSignal()
        imageAcquireStartSignal = QtCore.pyqtSignal()
        imageAcquireFinishedSignal = QtCore.pyqtSignal()

    cwd = os.path.dirname(os.path.realpath(__file__))

    def __init__(self, app = None, name = "microscoper"):

        self.__checkExists()
        self.loadConfig()

        self.connection = ClientObject(parent=self)
        self.setupUi()
        self.setupDevices()
        self.setupStage()

        self.updateUi()
        self.connectUi()
        self.connectSignals()

        # #Initiates inheritance

        self.verbose = True

        self.mainWindow.setEnabled(False)


        self.mainWindow.setEnabled(True)

        self.imageLevels = None
        self.display = None
        self.ao = None
        self.saveFilename = ""
        self.app = app

        # # Preloads analog input multiprocessing
        self.ai = MicroscoperComponents.AnalogInput(parent=self,
                                                    inputChannels=self.settings["input channels"],
                                                    polarityWidgets=self.pmtPolarityWidgets)

        self.connection.autoConnect(self.settings["connection port"])

    def setupScanList(self):
        scanFilePath = os.path.join(self.cwd,"Microscoper_app_scanList.csv")
        self.scanList = pd.read_csv(scanFilePath, delimiter='\t')
        scanList = self.scanList['Scan Name'].values
        self.ui.scanTypeWidget.clear()
        self.ui.scanTypeWidget.addItems(scanList)

    def setupUi(self):
        self.ui = Ui_Microscoper()
        self.mainWindow = QtWidgets.QMainWindow()
        self.ui.setupUi(self.mainWindow)
        self.setupScanList()
        self.mainWindow.setWindowIcon((QtGui.QIcon('ui/plopperPig.ico')))
        self.mainWindow.setWindowTitle("Microscoper 2019")

        screen = QtGui.QDesktopWidget().screenGeometry()
        size = self.mainWindow.geometry()
        self.mainWindow.move(0, screen.height() - size.height() - 100)
        self.mainWindow.activateWindow()
        self.mainWindow.show()

        # override defaults
        self.mainWindow.closeEvent = self.close

    def connectUi(self):
        self.setupButtonActions()
        self.setupMenuActions()

    def connectSignals(self):
        self.signal = self.Signal()
        self.signal.scanStartAcquire.connect(self.acquire)
        self.signal.scanStopAcquire.connect(self.acquireStop)
        self.connection.connectionSignal.connectionLost.connect(self.acquireStop)

    def setupDevices(self):
        self.pmtWidgets = [self.ui.PMTSlider0, self.ui.PMTLabel0, self.ui.PMTZero0, self.ui.PMTPreset0,
                           self.ui.PMTSlider1, self.ui.PMTLabel1, self.ui.PMTZero1, self.ui.PMTPreset1,
                           self.ui.PMTSlider2, self.ui.PMTLabel2, self.ui.PMTZero2, self.ui.PMTPreset2,
                           self.ui.PMTSlider3, self.ui.PMTLabel3, self.ui.PMTZero3, self.ui.PMTPreset3,
                           self.ui.PMTStatusText]

        self.pmtPolarityWidgets = [self.ui.pmtInvert1, self.ui.pmtInvert2, self.ui.pmtInvert3, self.ui.pmtInvert4]
        self.shutterWidgets = [self.ui.pumpShutterButton, self.ui.stokesShutterButton]
        self.detectors = MicroscoperComponents.MicroscopeDetector(widgets=self.pmtWidgets,model="3101")       # Setup components
        self.shutter = MicroscoperComponents.MicroscopeShutter(widgets=self.shutterWidgets)

    def setupStage(self):
        self.devices = {}
        for key, value in self.deviceList.items():
            self.devices[str(key)] = MicroscoperComponents.NetworkDevice(parent=self, deviceName=value, parentName = "microscoper", varName = "devices['%s']"%key)
        # self.linearStage = MicroscoperComponents.NetworkDevice(parent=self, deviceName="odl220", parentName = "microscoper", varName = "linearStage")
        # self.LinearStage = MicroscoperComponents.LStage(serialNumber=94839332, widgets=self.linearStageWidgets,name='linear stage')
        # self.xStage = MicroscoperComponents.LStage(serialNumber=94839334, widgets=self.xStageWidgets,name='x stage')
        # self.yStage = MicroscoperComponents.LStage(serialNumber=94839333, widgets=self.yStageWidgets,name='y stage')
        # if sixfourbit: self.zStage = MicroscoperComponents.ZStage(widgets=self.zStageWidgets)
        # try:
        #     if sixfourbit : self.zStage = MicroscoperComponents.ZStage(widgets=self.zStageWidgets)
        # except:
        #     self.zStage = None
        #     print('Failed to initialize focus controller.')

        # if self.ui.CalibrationFilenameText.text() is not '':            # show calibration text
        #     try : self.__displayCalibration()
        #     except : pass

    def updateUi(self):
        self.ui.zoomWidget.setValue(int(self.settings["zoom"]))
        self.ui.resolutionWidget.setValue(int(self.settings["resolution"]))
        self.ui.dwellTime.setValue(int(self.settings["dwell time"]))
        self.ui.fillFractionWidget.setValue(float(self.settings["fill fraction"]))
        self.ui.filenameText.setText(self.settings["filename"])
        self.ui.directoryText.setText(self.settings["directory"])
        self.ui.scansToAverage.setValue(int(self.settings["frames to average"]))
        # self.ui.LStageStart.setValue(float(self.settings["delay start position"]))
        # self.ui.LStageEnd.setValue(float(self.settings["delay end position"]))
        # self.ui.LStageMove.setValue(float(self.settings["delay increments"]))
        # self.ui.ZStageStart.setValue(float(self.settings["focus start position"]))
        # self.ui.ZStageEnd.setValue(float(self.settings["focus end position"]))
        # self.ui.ZStageMove.setValue(float(self.settings["focus increments"]))
        # self.ui.LstagePresetWidget1.setValue(float(self.settings["delay preset1"]))
        # self.ui.LstagePresetWidget2.setValue(float(self.settings["delay preset2"]))
        # self.ui.LstagePresetWidget3.setValue(float(self.settings["delay preset3"]))
        # self.ui.xStagePresetWidget1.setValue(float(self.settings["stage x target"]))
        # self.ui.yStagePresetWidget1.setValue(float(self.settings["stage y target"]))
        # self.ui.zStagePresetWidget1.setValue(float(self.settings["stage z target"]))


    def updateUiVariables(self):
        self.settings["zoom"] = str(int(self.ui.zoomWidget.value()))
        self.settings["resolution"] = str(int(self.ui.resolutionWidget.value()))
        self.settings["dwell time"] = str(int(self.ui.dwellTime.value()))
        self.settings["fill fraction"] = str(self.ui.fillFractionWidget.value())
        self.settings["filename"] = self.ui.filenameText.text()
        self.settings["directory"] = self.ui.directoryText.text()


        # self.settings["delay start position"] = str(self.ui.LStageStart.value())
        # self.settings["delay end position"] = str(self.ui.LStageEnd.value())
        # self.settings["delay increments"] = str(self.ui.LStageMove.value())
        # self.settings["focus start position"] = str(self.ui.ZStageStart.value())
        # self.settings["focus end position"] = str(self.ui.ZStageEnd.value())
        # self.settings["focus increments"] = str(self.ui.ZStageMove.value())
        # self.settings["delay preset1"] = str(self.ui.LstagePresetWidget1.value())
        # self.settings["delay preset2"] = str(self.ui.LstagePresetWidget2.value())
        # self.settings["delay preset3"] = str(self.ui.LstagePresetWidget3.value())
        # self.settings["stage x target"] = str(self.ui.xStagePresetWidget1.value())
        # self.settings["stage y target"] = str(self.ui.yStagePresetWidget1.value())
        # self.settings["stage z target"] = str(self.ui.zStagePresetWidget1.value())
        self.settings["frames to average"] = str(int(self.ui.scansToAverage.value()))

    def saveConfig(self):
        self.updateUiVariables()
        super().saveConfig()

    def setupMenuActions(self):
        self.ui.action_setImageLevels.triggered.connect(self.displayCreateImageLevelsWindow)
        self.ui.actionBring_all_to_front.triggered.connect(self.maximizeWindows)

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

        self.ui.pumpShutterButton.clicked.connect(self.shutter.Set_PumpShutter) # from class Shutters
        self.ui.stokesShutterButton.clicked.connect(self.shutter.Set_StokesShutter)
        self.ui.acquireButton.clicked.connect(self.acquireSet)
        self.ui.browseButton.clicked.connect(lambda : self.ui.directoryText.setText(QtWidgets.QFileDialog.getExistingDirectory())
)

        # self.ui.browseCalibrationButton.clicked.connect(self.__getCalibrationFile)

        # self.ui.LstagePresetButton1.clicked.connect(self.LinearStage.movePresetFunction[1]) #from class LSTAGE
        # self.ui.LstagePresetButton2.clicked.connect(self.LinearStage.movePresetFunction[2])
        # self.ui.LstagePresetButton3.clicked.connect(self.LinearStage.movePresetFunction[3])
        # self.ui.upButton.clicked.connect(lambda: self.yStage.MoveDir("Up", self.ui.microcopeOffsetRadio.isChecked()))
        self.ui.upButton.clicked.connect(lambda: self.changeRasterOffset("Up",self.ui.galvoOffsetRadio.isChecked()))
        self.ui.upButton.clicked.connect(self.acquireSoftRestart)
        # self.ui.downButton.clicked.connect(lambda: self.yStage.MoveDir("Down",self.ui.microcopeOffsetRadio.isChecked()))
        self.ui.downButton.clicked.connect(lambda: self.changeRasterOffset("Down", self.ui.galvoOffsetRadio.isChecked()))
        self.ui.downButton.clicked.connect(self.acquireSoftRestart)
        # self.ui.leftButton.clicked.connect(lambda: self.xStage.MoveDir("Left",self.ui.microcopeOffsetRadio.isChecked()))
        self.ui.leftButton.clicked.connect(lambda: self.changeRasterOffset("Left", self.ui.galvoOffsetRadio.isChecked()))
        self.ui.leftButton.clicked.connect(self.acquireSoftRestart)
        # self.ui.rightButton.clicked.connect(lambda: self.xStage.MoveDir("Right",self.ui.microcopeOffsetRadio.isChecked()))
        self.ui.rightButton.clicked.connect(lambda: self.changeRasterOffset("Right",self.ui.galvoOffsetRadio.isChecked()))
        self.ui.rightButton.clicked.connect(self.acquireSoftRestart)
        self.ui.zeroOffsetButton.clicked.connect(lambda: self.changeRasterOffset("zero",self.ui.galvoOffsetRadio.isChecked()))
        self.ui.zeroOffsetButton.clicked.connect(self.acquireSoftRestart)

        self.ui.zoomWidget.valueChanged.connect(self.acquireSoftRestart)
        self.ui.dwellTime.valueChanged.connect(self.acquireSoftRestart)
        self.ui.resolutionWidget.valueChanged.connect(self.acquireSoftRestart)
        # self.ui.resolutionWidget.valueChanged.connect(changeResolutionSteps)

        self.ui.fillFractionWidget.valueChanged.connect(self.acquireSoftRestart)
        self.ui.microcopeOffsetRadio.clicked.connect(self.changeDOffsetLabel)
        self.ui.galvoOffsetRadio.clicked.connect(self.changeDOffsetLabel)
        # self.ui.stageReadRadioNormal.clicked.connect(self.changeStageRead)
        # self.ui.stageReadRadioCalibrated.clicked.connect(self.changeStageRead)
        # self.ui.xPresetButton1.clicked.connect(self.xStage.movePresetFunction[1])
        # self.ui.yPresetButton1.clicked.connect(self.yStage.movePresetFunction[1])
        # if self.zStage is not None:
        #     self.ui.zPresetButton1.clicked.connect(self.zStage.movePresetFunction[1])
        self.ui.scanTypeWidget.currentIndexChanged.connect(self.changeScanTypeWidget)
        self.ui.filenameText.textChanged.connect(self.saveConfig)
        self.ui.directoryText.textChanged.connect(self.saveConfig)
        self.ui.resolutionWidget.valueChanged.connect(self.saveConfig)
        self.ui.zoomWidget.valueChanged.connect(self.saveConfig)
        self.ui.fillFractionWidget.valueChanged.connect(self.saveConfig)
        self.ui.dwellTime.valueChanged.connect(self.saveConfig)

    def initGetScanAttributes(self):
        index = self.ui.scanTypeWidget.currentIndex()
        self.scanName = self.ui.scanTypeWidget.currentText()
        self.scanStage = self.scanList.loc[index]['Stage']
        self.scanMove = self.scanList.loc[index]['Move Type']
        self.scanDetector = self.scanList.loc[index]['Detector Type']
        self.scanFrames = self.scanList.loc[index]['Frames']
        self.scanUnits = self.scanList.loc[index]['Move Units']

    def initGetXYScanPosition(self):
        if (self.display is not None) & (hasattr(self.display,"clickPositionRatio")):
            x = float(self.settings["scan x offset"]) + (
                        int(self.settings["max scan amplitude"]) / int(self.settings["zoom"])) * (
                            self.display.clickPositionRatio[0] - 0.5)
            y = float(self.settings["scan y offset"]) + (
                        int(self.settings["max scan amplitude"]) / int(self.settings["zoom"])) * (
                            self.display.clickPositionRatio[1] - 0.5)
        else:
            x = float(self.settings["scan x offset"])
            y = float(self.settings["scan y offset"])
        self.xyPointScanPosition = x, y
        return x, y

    def initStage(self):
        if ("linearstage" in self.scanStage.lower()) & ("continuous" in self.scanMove.lower()):
            self.devices["delaystage"].initScan("continuous")
            while not self.devices["delaystage"].status():
                time.sleep(0.1)


    def initAnalogOutput(self):
        device = self.settings["input channels"][:4]
        self.ao = MicroscoperComponents.Analog_output(channels=self.settings["output channels"],
                                                      resolution=int(self.settings["resolution"]),
                                                      line_dwell_time=int(self.settings["dwell time"]),
                                                      fill_fraction=float(self.settings["fill fraction"]),
                                                      hwbuffer=int(self.settings["device buffer"]),
                                                      verbose=self.verbose,
                                                      trigger=f"/{device}/ai/StartTrigger")
        self.generateAOScanPattern()

    def initAnalogInput(self, imageMaximums = None, imageMinimums = None):
        waitForLastFrame = False
        singleFrameScan = False
        if self.scanDetector == "PMT":
            if self.scanMove in ['Continuous', 'Discrete']: waitForLastFrame = True
            if self.scanFrames in ['Discrete', 'Grab']: singleFrameScan = True
            if imageMaximums is None:
                imageMaximums = [float(self.settings["image maximums %i" %i]) for i in range(0, MicroscoperComponents.getNumberOfChannels(self.settings["input channels"]))]
            if imageMinimums is None:
                imageMinimums = [float(self.settings["image minimums %i" %i]) for i in range(0, MicroscoperComponents.getNumberOfChannels(self.settings["input channels"]))]
            self.ai.init(channel=self.settings["input channels"],
                         resolution=int(self.settings["resolution"]),
                         line_dwell_time=float(self.settings["dwell time"]),
                         fill_fraction=float(self.settings["fill fraction"]),
                         hwbuffer=int(self.settings["device buffer"]),
                         verbose=self.verbose,
                         save=self.ui.saveCheckBox.isChecked(),
                         saveFilename=self.saveFilename,
                         saveFileIndex=self.saveFileIndex,
                         xAxis=self.xAxis,
                         metadata=self.metadata,
                         waitForLastFrame=waitForLastFrame,
                         singleFrameScan=singleFrameScan,
                         framesToAverage=int(self.settings["frames to average"]),
                         dataMaximums=imageMaximums,
                         dataMinimums=imageMinimums,
                         )

    def initDisplay(self):
        if self.scanDetector == "PMT":
            if self.display is not None:
                try:
                    self.display.signal.close.disconnect()
                except:
                    pass
                self.display.close()
                self.display = Display.Display2D(imageInput=self.ai.imageData,
                                                 intensityPlot=self.ai.intensities,
                                                 intensityIndex=self.ai.intensitiesIndex,
                                                 imageMaximums=self.ai.dataMaximums,
                                                 imageMinimums=self.ai.dataMinimums,
                                                 app=self.app,
                                                 )
            else:
                self.display = Display.Display2D(imageInput=self.ai.imageData,
                                                 intensityPlot=self.ai.intensities,
                                                 intensityIndex=self.ai.intensitiesIndex,
                                                 imageMaximums=self.ai.dataMaximums,
                                                 imageMinimums=self.ai.dataMinimums,
                                                 app=self.app,
                                                 )
            self.display.fps = 15
            self.display.signal.close.connect(self.acquireStop)
            self.display.signal.close.connect(self.displayClose)

    def initMetadata(self):
        metadata = {'Zoom' : self.settings["zoom"],
                         'Line dwell time' : self.settings["dwell time"],
                         'Pixel dwell time': (1000 * int(self.settings["dwell time"])) / (
                                     int(self.settings["resolution"]) * (1 + float(self.settings["fill fraction"]))),
                         'Fill fraction' : self.settings["fill fraction"],
                         'Resolution' : self.settings["resolution"],
                         'Linear Scan speed' : self.settings["delay increments"],
                         'Z-steps' : self.settings["focus increments"],
                         'xposition' : self.settings["stage x current"],
                         'yposition' : self.settings["stage y current"],
                         'zposition' : self.settings["stage z current"],
                         }
        for i in range(0,MicroscoperComponents.getNumberOfChannels(self.settings["input channels"])):
            PMTSettings = {f"pmt {i}" : self.settings[f"pmt {i}"],
                           f"image maximums {i}" : self.settings[f"image maximums {i}"],
                           f"image minimums {i}" : self.settings[f"image minimums {i}"],
                           }

        self.metadata = {**metadata, **PMTSettings}

    def initSavefile(self):
        self.saveFileIndex = time.strftime("%Y_%m_%d_%H%M%S", time.gmtime())

        if self.ui.saveCheckBox.isChecked():
            if self.settings["directory"] == "":
                self.saveFilename = ''
            else :
                if not os.path.exists(self.settings["directory"]):
                    os.mkdir(self.settings["directory"])

                self.saveFilename = os.path.join(self.settings["directory"], self.settings["filename"])
                self.saveFilename += "_{}".format(self.saveFileIndex)
                if not os.path.exists(self.saveFilename):
                    os.mkdir(self.saveFilename)

                infoFilePath = "{}/info.csv".format(self.saveFilename)

                try :
                    with open(infoFilePath,'w',newline='') as infoFile:
                        csvFile = csv.writer(infoFile)
                        for key, val in self.metadata.items():
                            csvFile.writerow([key, val])

                    print("Saving to %s"%self.saveFilename)
                except :
                    print('Cannot save to %s'%self.saveFilename)
                    self.saveFilename = ""
        else:
            self.saveFilename = ""

    def initSetupHorizontalAxis(self):
        if self.scanMove == "None": self.xAxis = 'Default'
        elif self.scanMove == 'Continuous':
            self.xAxis = self.devices["linearstage"].getPos# , self.toWavenumber
        elif self.scanMove in ["Discrete", "Grab"]:
            if self.scanStage == "LinearStage" : self.xAxis = self.devices["linearstage"].getPos, self.toWavenumber()
        else : self.xAxis = 'Default'

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

    def displayCreate(self):
        self.display = Display.Display2D(imageInput=self.ai.imageData)
        self.display.fps = 15

    def displayClose(self):
        if self.display is not None:
            if hasattr(self.display,"close"):
                self.display.close()
                self.display = None
        # if self.imageLevels is not None:
        #     if hasattr(self.imageLevels,"close"):
        #         self.imageLevels.close()
        #         self.imageLevels = None

    def generateAOScanPattern(self):
        if 'point' in self.scanName.lower() :
            data_x = np.tile(float(self.settings["scan x offset"]),self.ao.x_pixels_total*self.ao.y_pixels)
            data_y = np.tile(float(self.settings["scan y offset"]),self.ao.x_pixels_total*self.ao.y_pixels)
            data = np.array([data_x,data_y])
            self.ao.set_data(data)
        else:
            self.ao.set_data(MMath.generateRasterScan(float(self.settings["max scan amplitude"]) / int(self.settings["zoom"]),
                                                      self.ao.x_pixels,
                                                      self.ao.y_pixels,
                                                      self.ao.x_pixels_flyback,
                                                      (float(self.settings["scan x offset"]),
                                                       float(self.settings["scan y offset"]))
                                                      ))

    def changeRasterOffset(self,direction='Up',execute=False):
        direction = direction.lower()
        if execute:
            if ('up' in direction):
                self.settings["scan y offset"] = str(float(self.settings["scan y offset"]) + self.ui.deltaOffset.value())
            if ('right' in direction):
                self.settings["scan x offset"] = str(float(self.settings["scan x offset"]) + self.ui.deltaOffset.value())
            if ('down' in direction):
                self.settings["scan y offset"] = str(float(self.settings["scan y offset"]) - self.ui.deltaOffset.value())
            if ('left' in direction):
                self.settings["scan x offset"] = str(float(self.settings["scan x offset"]) - self.ui.deltaOffset.value())
            elif ("zero" in direction):
                self.settings["scan x offset"] = "0"
                self.settings["scan y offset"] = "0"
            print((float(self.settings["scan x offset"]),float(self.settings["scan y offset"])))

    def displayCreateImageLevelsWindow(self):
        def createWindow():
            numberOfImages = MicroscoperComponents.getNumberOfChannels(self.settings["input channels"])
            imageMaximums = [float(self.settings["image maximums %i" %i]) for i in range(0, MicroscoperComponents.getNumberOfChannels(self.settings["input channels"]))]
            imageMinimums = [float(self.settings["image minimums %i" %i]) for i in range(0, MicroscoperComponents.getNumberOfChannels(self.settings["input channels"]))]

            self.imageLevels = Display.ImageLevelsWidget(parent=self,
                                      numberOfImages=numberOfImages,
                                      arrayValuesMax=imageMaximums,
                                      arrayValuesMin=imageMinimums,
                                      images=self.ai.imageData)

            def passDisplayLevels():
                # pass to settings
                for i in range(0, len(self.ai.dataMaximums)):
                    self.settings["image maximums %i" % i] = str(self.imageLevels.arrayValuesMax[i])
                    self.settings["image minimums %i" % i] = str(self.imageLevels.arrayValuesMin[i])
                # pass to analog input
                self.ai.dataMaximums = self.imageLevels.arrayValuesMax
                self.ai.dataMinimums = self.imageLevels.arrayValuesMin
                # pass to display
                if hasattr(self.display,"imageMaximums"):
                    self.display.imageMaximums = self.imageLevels.arrayValuesMax
                    self.display.imageMinimums = self.imageLevels.arrayValuesMin

            self.imageLevels.signal.update.connect(passDisplayLevels)

        if hasattr(self,"imageLevels"):
            if hasattr(self.imageLevels, "close"):
                self.imageLevels.close()
        # if hasattr(self.ai,"dataMaximums"):
        createWindow()
        if hasattr(self.imageLevels, "signal"):
            self.imageLevels.signal.close.connect(self.displayImageLevelsWindowClosed)



    def displayImageLevelsWindowClosed(self):
        self.imageLevels = None

    def acquireSet(self):
        self.saveConfig()
        if not self.acquiring :
            self.acquire()
        else :
            self.acquireStop()

    def acquire(self):
        self.acquireInit()
        self.acquireStart()

    def acquireInit(self):

        self.signal.scanInitSignal.emit()
        self.acquiring = True
        self.ui.acquireButton.setText("Stop Acquire")

        ## Initialize defaults --------------------------------------
        self.updateUiVariables()
        self.initGetXYScanPosition()
        self.initGetScanAttributes()


        self.initStage()
        self.initMetadata()
        self.initSavefile()

        self.detectors.setPMTs()
        time.sleep(1)
        self.shutter.Microscope_shutter_open()

        ## Determine x axis display plot  -------------------------------------
        self.initSetupHorizontalAxis()
        #############################################################

        ## Create analog channels -----------------------------
        self.initAnalogOutput()
        self.initAnalogInput()

        ## Initialize display ----------------------------------
        self.initDisplay()
        #############################################################


    def acquireStart(self):
        self.signal.scanStartSignal.emit()
        self.ao.start()
        if self.scanDetector == "PMT":
            self.ai.start()
            self.display.start()
        self.detectScanStatusThread = Thread(target=self.detectScanStatus)
        self.detectScanStatusThread.start()

    def acquireSoftStart(self):
        self.signal.scanStartSignal.emit()
        self.updateUiVariables()
        time.sleep(0.1)
        self.initAnalogOutput()

        if self.scanDetector == "PMT":
            self.initAnalogInput(imageMaximums=self.ai.dataMaximums,
                                 imageMinimums=self.ai.dataMinimums)
            self.display.set(imageInput=self.ai.imageData,
                             intensityPlot=self.ai.intensities,
                             intensityIndex=self.ai.intensitiesIndex,
                             imageMaximums=self.ai.dataMaximums,
                             imageMinimums=self.ai.dataMinimums,
                             app=self.app,
                             )
        self.ao.start()

        if self.scanDetector == "PMT":
            self.ai.start()


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
            self.devices["delaystage"].stop()
            self.ai.clear()
            if self.display is not None: self.display.stop()
            while self.ai.reading: time.sleep(0.1)
            if self.ao is not None :
                if self.ao.running : self.ao.clear()
            # self.getxyScanPosition()
            self.scanStatusThreadInterrupt = True
            # self.shutter.Microscope_shutter_close()
            self.detectors.setPMTsZero()
            self.ui.acquireButton.setText("Acquire")
            self.acquiring = False
        except Exception as e:
            print(e)
        self.signal.scanDoneSignal.emit()

    def setConnectionNotBusy(self):
        self.connection.connectionIsBusy = False

    def setConnectionIsBusy(self):
        self.connection.connectionIsBusy = True

    def detectScanStatus(self):
        self.scanStatusThreadInterrupt = False

        def stageContinuousUntilEnds():
            if self.scanStage == "LinearStage":
                self.devices["delaystage"].startScan()
                while not self.devices["delaystage"].status():
                    time.sleep(0.1)
            elif self.scanStage == "zStage":
                self.devices["focusController"].startScan()
                while not self.devices["focusController"].status():
                    time.sleep(0.1)
            self.acquireStop()
            self.initStage()

        def stageDiscreteUntilEnds(): ## todo: fix discreteUntilEnds
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
            self.initStage()
            self.setConnectionNotBusy()

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
                self.setConnectionNotBusy()

        def grab():
            while True:
                time.sleep(0.1)
                if not self.ai.reading:
                    self.acquireStop()
                    self.setConnectionNotBusy()
                    break

        def stageDefault():
            self.connection.connectionIsBusy = False

        if self.scanMove == "None": stageDefault()
        if self.scanMove == "Continuous": stageContinuousUntilEnds()
        if self.scanMove == "Discrete":
            self.stageStartPosition = self.ui.LStageStart.value()
            self.stageMoveIndex = 1
            if self.scanStage == "LinearStage": stageDiscreteUntilEnds()
            if self.scanStage == "zStage": zDiscreteUntilEnds()
        if self.scanMove == "Grab":
            grab()


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

    def close(self, event):
        if self.mainWindow.isEnabled():
            self.listening = False
            if self.acquiring:
                self.acquireStop()
            if self.display is not None:
                self.display.close()
            if self.imageLevels is not None:
                self.imageLevels.close()
            # self.linearStage.stageUpdate = False
            # self.xStage.stageUpdate = False
            # self.yStage.stageUpdate = False
            # self.LinearStage.Clear()
            # self.xStage.Clear()
            # self.yStage.Clear()
            # if sixfourbit : self.zStage.Clear()
            # self.ai.terminate()
            self.saveConfig()
            self.connection.stopClientConnection()
            # self.mainWindow.close()
        if self.mainWindow.isEnabled():
            event.accept()
        else : event.ignore()
        # self.defaultCloseEvent(event)

if __name__ == "__main__":
    import ctypes
    myappid = u'microscoper'  # arbitrary string
    if os.name == "nt":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    qapp = QtWidgets.QApplication([])
    app = Microscope(app=qapp)
    qapp.exec()