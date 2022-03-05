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
else:
    sixfourbit = False


class Microscope(MicroscoperComponents.Microscope):
    shutterWidgets: list
    pmtWidgets: list
    pmtPolarityWidgets: list
    shutter: MicroscoperComponents.Shutters

    def toWavenumber(self):
        try:
            wavenumber = float(self.ui.WavenumberText.text()[:-5])
        except:
            wavenumber = 0
        return wavenumber

    def displayCalibration(self):
        self.displayingCalibration = False

        def calculate():
            while True:
                try:
                    self.calibrationFile = self.ui.calibrationFilenameText.text()
                    calibrationFile = open(self.calibrationFile, "r")
                    self.stageCalibrationFormulaString = calibrationFile.read()
                    self.displayingCalibration = True
                    while self.displayingCalibration:
                        pos = self.devices["delaystage"].getPos()
                        if not type(self.devices["delaystage"].delayStagePosition) == type("a"):
                            pos = str(pos)
                        wavenumber = eval(
                            self.stageCalibrationFormulaString.replace("x", pos))
                        self.ui.WavenumberText.setText('%i cm-1' % wavenumber)
                        time.sleep(0.01)
                except:
                    self.ui.WavenumberText.setText("Invalid calibration file.")
                    self.displayingCalibration = False
                    time.sleep(0.5)
                    # self.displayCalibration() ## try reconnecting

        self.calcThread = Thread(target=calculate)
        self.calcThread.daemon = True
        self.calcThread.start()

        # except:
        #     self.displayingCalibration = False
        #     # self.ui.WavenumberText.setText("Invalid calibration file.")
        #     # self.displayingCalibration = False

    def getCalibrationFile(self):
        self.calibrationFile = QtWidgets.QFileDialog.getOpenFileName()[0]
        self.ui.calibrationFilenameText.setText(self.calibrationFile)
        self.displayCalibration()

    def getSaveFile(self):
        self.ui.directoryText.setText(QtWidgets.QFileDialog.getExistingDirectory())

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

    def __init__(self, app=None, name="microscoper"):

        self.__checkExists()
        self.load_config()

        self.connection = ClientObject(parent=self, verbose=self.verbose)
        self.setupUi()
        self.setupDevices()

        self.update_ui()
        self.connectUi()
        self.connectSignals()

        # #Initiates inheritance
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
        self.init_stage()

    def setupScanList(self):
        scanFilePath = os.path.join(self.cwd, "Microscoper_app_scanList.csv")
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

        # screen = QtGui.QDesktopWidget().screenGeometry()
        screen = QtGui.QGuiApplication.primaryScreen().geometry()
        size = self.mainWindow.geometry()
        self.mainWindow.move(0, screen.height() - size.height() - 100)
        self.mainWindow.activateWindow()
        self.mainWindow.show()

        # override defaults
        self.mainWindow.closeEvent = self.close

    def connectUi(self):
        self.init_ui_buttons()
        self.init_ui_menus()

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
        self.detectors = MicroscoperComponents.MicroscopeDetector(widgets=self.pmtWidgets, model="1208")  # Setup components
        if bool(int(self.settings["shutters enabled"])):
            self.shutterWidgets = [self.ui.pumpShutterButton, self.ui.stokesShutterButton]
            self.shutter = MicroscoperComponents.Shutters(widgets=self.shutterWidgets)

    def init_stage(self):
        self.devices = {}
        for key, value in self.deviceList.items():
            self.devices[str(key)] = MicroscoperComponents.NetworkDevice(parent=self, deviceName=value,
                                                                         parentName="microscoper",
                                                                         varName="devices['%s']" % key,
                                                                         timeout=1,
                                                                         verbose=False)
        self.init_calibration()

    def init_calibration(self):
        if "delaystage" in self.devices:
            self.devices["delaystage"].getPos()
            self.displayCalibration()

    def update_ui(self):
        self.ui.zoomWidget.setValue(int(self.settings["zoom"]))
        self.ui.resolutionWidget.setValue(int(self.settings["resolution"]))
        self.ui.dwellTime.setValue(int(self.settings["dwell time"]))
        self.ui.fillFractionWidget.setValue(float(self.settings["fill fraction"]))
        self.ui.filenameText.setText(self.settings["filename"])
        self.ui.directoryText.setText(self.settings["directory"])
        self.ui.scansToAverage.setValue(int(self.settings["frames to average"]))
        self.ui.calibrationFilenameText.setText(self.settings["calibration file"])

    def update_ui_variables(self):
        self.settings["zoom"] = str(int(self.ui.zoomWidget.value()))
        self.settings["resolution"] = str(int(self.ui.resolutionWidget.value()))
        self.settings["dwell time"] = str(int(self.ui.dwellTime.value()))
        self.settings["fill fraction"] = str(self.ui.fillFractionWidget.value())
        self.settings["filename"] = self.ui.filenameText.text()
        self.settings["directory"] = self.ui.directoryText.text()
        self.settings["frames to average"] = str(int(self.ui.scansToAverage.value()))
        self.settings["calibration file"] = self.ui.calibrationFilenameText.text()

    def save_config(self):
        self.update_ui_variables()
        super().save_config()

    def init_ui_menus(self):
        self.ui.action_setImageLevels.triggered.connect(self.displayCreateImageLevelsWindow)
        self.ui.actionBring_all_to_front.triggered.connect(self.maximizeWindows)
        self.ui.action_Quit.triggered.connect(self.mainWindow.close)

    def init_ui_buttons(self):
        self.ui.PMTPreset0.clicked.connect(lambda: self.detectors.setPMTsPresetActions[0](self.acquiring))
        self.ui.PMTPreset1.clicked.connect(lambda: self.detectors.setPMTsPresetActions[1](self.acquiring))
        self.ui.PMTPreset2.clicked.connect(lambda: self.detectors.setPMTsPresetActions[2](self.acquiring))
        self.ui.PMTPreset3.clicked.connect(lambda: self.detectors.setPMTsPresetActions[3](self.acquiring))

        self.ui.PMTZero0.clicked.connect(lambda: self.detectors.setPMTsZeroActions[0](self.acquiring))
        self.ui.PMTZero1.clicked.connect(lambda: self.detectors.setPMTsZeroActions[1](self.acquiring))
        self.ui.PMTZero2.clicked.connect(lambda: self.detectors.setPMTsZeroActions[2](self.acquiring))
        self.ui.PMTZero3.clicked.connect(lambda: self.detectors.setPMTsZeroActions[3](self.acquiring))

        self.ui.PMTSlider0.valueChanged.connect(lambda: self.detectors.setPMTsSliderActions[0](self.acquiring))
        self.ui.PMTSlider1.valueChanged.connect(lambda: self.detectors.setPMTsSliderActions[1](self.acquiring))
        self.ui.PMTSlider2.valueChanged.connect(lambda: self.detectors.setPMTsSliderActions[2](self.acquiring))
        self.ui.PMTSlider3.valueChanged.connect(lambda: self.detectors.setPMTsSliderActions[3](self.acquiring))

        # self.ui.pumpShutterButton.clicked.connect(self.shutter.flip_pump_shutter) # from class Shutters
        # self.ui.stokesShutterButton.clicked.connect(self.shutter.flip_stokes_shutter)
        self.ui.acquireButton.clicked.connect(self.acquireSet)
        self.ui.browseButton.clicked.connect(lambda: self.ui.directoryText.setText(QtWidgets.QFileDialog.getExistingDirectory()))

        self.ui.browseCalibrationButton.clicked.connect(self.getCalibrationFile)

        self.ui.upButton.clicked.connect(lambda: self.changeRasterOffset("Up", self.ui.galvoOffsetRadio.isChecked()))
        self.ui.upButton.clicked.connect(self.acquireSoftRestart)
        self.ui.downButton.clicked.connect(lambda: self.changeRasterOffset("Down", self.ui.galvoOffsetRadio.isChecked()))
        self.ui.downButton.clicked.connect(self.acquireSoftRestart)
        self.ui.leftButton.clicked.connect(lambda: self.changeRasterOffset("Left", self.ui.galvoOffsetRadio.isChecked()))
        self.ui.leftButton.clicked.connect(self.acquireSoftRestart)
        self.ui.rightButton.clicked.connect(lambda: self.changeRasterOffset("Right", self.ui.galvoOffsetRadio.isChecked()))
        self.ui.rightButton.clicked.connect(self.acquireSoftRestart)
        self.ui.zeroOffsetButton.clicked.connect(lambda: self.changeRasterOffset("zero", self.ui.galvoOffsetRadio.isChecked()))
        self.ui.zeroOffsetButton.clicked.connect(self.acquireSoftRestart)

        self.ui.zoomWidget.valueChanged.connect(self.acquireSoftRestart)
        self.ui.dwellTime.valueChanged.connect(self.acquireSoftRestart)
        self.ui.resolutionWidget.valueChanged.connect(self.acquireSoftRestart)

        self.ui.fillFractionWidget.valueChanged.connect(self.acquireSoftRestart)
        self.ui.microcopeOffsetRadio.clicked.connect(self.changeDOffsetLabel)
        self.ui.galvoOffsetRadio.clicked.connect(self.changeDOffsetLabel)

        self.ui.scanTypeWidget.currentIndexChanged.connect(self.changeScanTypeWidget)
        self.ui.calibrationFilenameText.textChanged.connect(self.save_config)
        self.ui.filenameText.textChanged.connect(self.save_config)
        self.ui.directoryText.textChanged.connect(self.save_config)
        self.ui.resolutionWidget.valueChanged.connect(self.save_config)
        self.ui.zoomWidget.valueChanged.connect(self.save_config)
        self.ui.fillFractionWidget.valueChanged.connect(self.save_config)
        self.ui.dwellTime.valueChanged.connect(self.save_config)

    def initGetScanAttributes(self):
        index = self.ui.scanTypeWidget.currentIndex()
        self.scanName = self.ui.scanTypeWidget.currentText()
        self.scanStage = self.scanList.loc[index]['Stage']
        self.scanMove = self.scanList.loc[index]['Move Type']
        self.scanDetector = self.scanList.loc[index]['Detector Type']
        self.scanFrames = self.scanList.loc[index]['Frames']
        self.scanUnits = self.scanList.loc[index]['Move Units']

    def initGetXYScanPosition(self):
        if (self.display is not None) & (hasattr(self.display, "clickPositionRatio")):
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
        if ("linearstage" in self.scanStage.lower()):
            if ("continuous" in self.scanMove.lower()):
                self.devices["delaystage"].initScan("continuous")
                while not self.devices["delaystage"].status():
                    time.sleep(0.1)
            elif ("discrete" in self.scanMove.lower()):
                self.devices["delaystage"].initScan("discrete")
                while not self.devices["delaystage"].status():
                    time.sleep(0.1)

    def initSpectrometer(self):
        if self.scanDetector == "Spectrometer":
            self.devices["spectrometer"].spectrometerInit()

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

    def initAnalogInput(self, imageMaximums=None, imageMinimums=None):
        waitForLastFrame = False
        singleFrameScan = False
        if self.scanDetector == "PMT":
            if self.scanMove in ['Continuous', 'Discrete']: waitForLastFrame = True
            if self.scanFrames in ['Discrete', 'Grab']: singleFrameScan = True
            if imageMaximums is None:
                imageMaximums = [float(self.settings["image maximums %i" % i]) for i in range(0, MicroscoperComponents.getNumberOfChannels(self.settings["input channels"]))]
            if imageMinimums is None:
                imageMinimums = [float(self.settings["image minimums %i" % i]) for i in range(0, MicroscoperComponents.getNumberOfChannels(self.settings["input channels"]))]
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
        metadata = {'Zoom': self.settings["zoom"],
                    'Line dwell time': self.settings["dwell time"],
                    'Pixel dwell time': (1000 * int(self.settings["dwell time"])) / (
                            int(self.settings["resolution"]) * (1 + float(self.settings["fill fraction"]))),
                    'Fill fraction': self.settings["fill fraction"],
                    'Resolution': self.settings["resolution"],
                    'Linear Scan speed': self.settings["delay increments"],
                    'Z-steps': self.settings["focus increments"],
                    'xposition': self.settings["stage x current"],
                    'yposition': self.settings["stage y current"],
                    'zposition': self.settings["stage z current"],
                    }
        for i in range(0, MicroscoperComponents.getNumberOfChannels(self.settings["input channels"])):
            PMTSettings = {f"pmt {i}": self.settings[f"pmt {i}"],
                           f"image maximums {i}": self.settings[f"image maximums {i}"],
                           f"image minimums {i}": self.settings[f"image minimums {i}"],
                           }

        self.metadata = {**metadata, **PMTSettings}

    def initSavefile(self):
        self.saveFileIndex = time.strftime("%Y_%m_%d_%H%M%S", time.gmtime())

        if self.ui.saveCheckBox.isChecked():
            if self.settings["directory"] == "":
                self.saveFilename = ''
            else:
                if not os.path.exists(self.settings["directory"]):
                    os.mkdir(self.settings["directory"])

                self.saveFilename = os.path.join(self.settings["directory"], self.settings["filename"])
                self.saveFilename += "_{}".format(self.saveFileIndex)
                if not os.path.exists(self.saveFilename):
                    os.mkdir(self.saveFilename)

                infoFilePath = "{}/info.csv".format(self.saveFilename)

                try:
                    with open(infoFilePath, 'w', newline='') as infoFile:
                        csvFile = csv.writer(infoFile)
                        for key, val in self.metadata.items():
                            csvFile.writerow([key, val])

                    print("Saving to %s" % self.saveFilename)
                except:
                    print('Cannot save to %s' % self.saveFilename)
                    self.saveFilename = ""
        else:
            self.saveFilename = ""

    def initSetupHorizontalAxis(self):
        if self.scanMove == 'Continuous':
            self.xAxis = [self.devices["delaystage"].getPos]
            if self.displayingCalibration:
                self.xAxis.append(self.toWavenumber)
        elif self.scanMove in ["Discrete", "Grab"]:
            if self.scanStage == "LinearStage":
                self.xAxis = [self.devices["delaystage"].getPos]
                if self.displayingCalibration:
                    self.xAxis.append(self.toWavenumber)
        else:
            self.xAxis = 'Default'

    def changeDOffsetLabel(self):
        if self.ui.microcopeOffsetRadio.isChecked():
            self.ui.deltaOffsetLabel.setText("dOffset (mm)")
        else:
            self.ui.deltaOffsetLabel.setText("dOffset(V)")

    def changeStageRead(self):
        pass
        # if self.stageReadRadioNormal.isChecked(): showNormal

    def changeScanTypeWidget(self):
        index = self.ui.scanTypeWidget.currentIndex()
        incrementString = self.scanList.loc[index]['Move Units']
        try:
            self.ui.LStageMoveLabel.setText(incrementString)
            # self.LStageMoveLabel.setText(text[self.scanTypeWidget.currentText()])
        except:
            pass
            # self.LStageMoveLabel.setText('Speed (mm/s)')

    def displayCreate(self):
        self.display = Display.Display2D(imageInput=self.ai.imageData)
        self.display.fps = 15

    def displayClose(self):
        if self.display is not None:
            if hasattr(self.display, "close"):
                self.display.close()
                self.display = None
        # if self.imageLevels is not None:
        #     if hasattr(self.imageLevels,"close"):
        #         self.imageLevels.close()
        #         self.imageLevels = None

    def generateAOScanPattern(self):
        if 'point' in self.scanName.lower():
            data_x = np.tile(float(self.settings["scan x offset"]), self.ao.x_pixels_total * self.ao.y_pixels)
            data_y = np.tile(float(self.settings["scan y offset"]), self.ao.x_pixels_total * self.ao.y_pixels)
            data = np.array([data_x, data_y])
            self.ao.set_data(data)
        else:
            self.ao.set_data(MMath.generateRasterScan(float(self.settings["max scan amplitude"]) / int(self.settings["zoom"]),
                                                      self.ao.x_pixels,
                                                      self.ao.y_pixels,
                                                      self.ao.x_pixels_flyback,
                                                      (float(self.settings["scan x offset"]),
                                                       float(self.settings["scan y offset"]))
                                                      ))

    def changeRasterOffset(self, direction='Up', execute=False):
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
            print((float(self.settings["scan x offset"]), float(self.settings["scan y offset"])))

    def displayCreateImageLevelsWindow(self):
        def createWindow():
            numberOfImages = MicroscoperComponents.getNumberOfChannels(self.settings["input channels"])
            imageMaximums = [float(self.settings["image maximums %i" % i]) for i in range(0, MicroscoperComponents.getNumberOfChannels(self.settings["input channels"]))]
            imageMinimums = [float(self.settings["image minimums %i" % i]) for i in range(0, MicroscoperComponents.getNumberOfChannels(self.settings["input channels"]))]

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
                if hasattr(self.display, "imageMaximums"):
                    self.display.imageMaximums = self.imageLevels.arrayValuesMax
                    self.display.imageMinimums = self.imageLevels.arrayValuesMin

            self.imageLevels.signal.update.connect(passDisplayLevels)

        if hasattr(self, "imageLevels"):
            if hasattr(self.imageLevels, "close"):
                self.imageLevels.close()
        # if hasattr(self.ai,"dataMaximums"):
        createWindow()
        if hasattr(self.imageLevels, "signal"):
            self.imageLevels.signal.close.connect(self.displayImageLevelsWindowClosed)

    def displayImageLevelsWindowClosed(self):
        self.imageLevels = None

    def acquireSet(self):
        self.save_config()
        if not self.acquiring:
            self.acquire()
        else:
            self.acquireStop()

    def acquire(self):
        # self.devices["spectrometer"].spectrometerSendQuery()
        # self.connection.askForResponse(receiver="spectrometer", sender="microscoper", timeout=15)
        # print(self.connection.connectionIsWaitingForResponse)
        # self.connection.askForResponse(receiver="thorlabsdds220", sender="microscoper", timeout=15)
        # print(self.connection.connectionIsWaitingForResponse)
        # self.devices["spectrometer"].spectrometerScan()
        # self.devices["delaystage"].status()
        self.acquireInit()
        self.acquireStart()

    def acquireInit(self):

        self.signal.scanInitSignal.emit()
        self.acquiring = True
        self.ui.acquireButton.setText("Stop Acquire")

        ## Initialize defaults --------------------------------------
        self.update_ui_variables()
        self.initGetXYScanPosition()
        self.initGetScanAttributes()

        self.initStage()
        self.initSpectrometer()
        self.initMetadata()
        self.initSavefile()

        self.detectors.setPMTs()
        time.sleep(1)
        # self.shutter.microscope_shutter_open()

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
        elif self.scanDetector == "Spectrometer":
            self.devices["spectrometer"].spectrometerScan()
            if self.ui.saveCheckBox.isChecked():
                if self.settings["directory"] is not '':
                    fileName = os.path.join(self.settings["directory"], self.settings["filename"])
                    xAxis = self.xAxis
                self.devices["spectrometer"].spectrometerSave(fileName, xAxis)
        self.detectScanStatusThread = Thread(target=self.detectScanStatus)
        self.detectScanStatusThread.start()

    def acquireSoftStart(self):
        self.signal.scanStartSignal.emit()
        self.update_ui_variables()
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
        elif self.scanDetector == "Spectrometer":
            self.devices["spectrometer"].spectrometerScan()
            if self.ui.saveCheckBox.isChecked():
                if self.settings["directory"] is not '':
                    fileName = os.path.join(self.settings["directory"], self.settings["filename"])
                    xAxis = self.xAxis
                self.devices["spectrometer"].spectrometerSave(fileName, xAxis)

    def acquireSoftStop(self):
        self.ao.clear()
        while self.ai.reading:
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
        try:
            self.devices["delaystage"].stop()
            self.ai.clear()
            if self.display is not None: self.display.stop()
            while self.ai.reading: time.sleep(0.1)
            if self.ao is not None:
                if self.ao.running: self.ao.clear()
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

        def stageDiscreteUntilEnds():
            self.devices["delaystage"].sendQuery("ui.endPositionSpinbox.value()", "endPos")
            while (self.devices["delaystage"].getPos() < self.devices["delaystage"].endPos) and (not self.scanStatusThreadInterrupt):
                if not self.ai.reading:
                    self.acquireSoftStop()
                    self.devices["delaystage"].sendCommand("moveRel()")
                    while not self.devices["delaystage"].status():
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
                    targetPosition = self.ui.ZStageStart.value() + self.stageMoveIndex * self.zStage.MoveDef.value()
                    self.stageMoveIndex += 1
                    self.zStage.MoveAbs(targetPosition)
                    while self.zStage.moving:
                        time.sleep(0.1)
                    time.sleep(1)
                    self.acquireSoftStart()
                time.sleep(0.1)
            else:
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
            # self.stageStartPosition = self.ui.LStageStart.value()
            # self.stageMoveIndex = 1
            if self.scanStage == "LinearStage": stageDiscreteUntilEnds()
            if self.scanStage == "zStage": zDiscreteUntilEnds()
        if self.scanMove == "Grab":
            grab()

    def close(self, event):
        if self.mainWindow.isEnabled():
            self.listening = False
            if self.acquiring:
                self.acquireStop()
            if self.display is not None:
                self.display.close()
            if self.imageLevels is not None:
                self.imageLevels.close()
            self.save_config()
            self.connection.stopClientConnection()
        if self.mainWindow.isEnabled():
            event.accept()
        else:
            event.ignore()


if __name__ == "__main__":
    import ctypes

    myappid = u'microscoper'  # arbitrary string
    if os.name == "nt":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    qapp = QtWidgets.QApplication([])
    app = Microscope(app=qapp)
    qapp.exec()
