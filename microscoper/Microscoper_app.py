import os, sys
import time
from threading import Thread
import numpy as np
import pandas as pd
from PyQt5 import QtWidgets, QtGui, QtCore
from pathlib import Path

from Devices.TTL_delay_stage import TTL_Delay_Stage
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
    scan_thread_interrupt: bool = False
    _scan_thread: Thread

    def stage_to_wavenumber(self):
        try:
            wavenumber = float(self.ui.WavenumberText.text()[:-5])
        except:
            wavenumber = 0
        return wavenumber

    def display_calibration(self):
        self.is_displaying_calibration = False

        def calculate():
            while True:
                try:
                    self.calibration_file = self.ui.calibrationFilenameText.text()
                    calibrationFile = open(self.calibration_file, "r")
                    self.stageCalibrationFormulaString = calibrationFile.read()
                    self.is_displaying_calibration = True
                    while self.is_displaying_calibration:
                        pos = self.devices["delaystage"].getPos()
                        if not type(self.devices["delaystage"].delayStagePosition) == type("a"):
                            pos = str(pos)
                        wavenumber = eval(
                            self.stageCalibrationFormulaString.replace("x", pos))
                        self.ui.WavenumberText.setText('%i cm-1' % wavenumber)
                        time.sleep(0.01)
                except:
                    self.ui.WavenumberText.setText("Invalid calibration file.")
                    self.is_displaying_calibration = False
                    time.sleep(0.5)
                    # self.displayCalibration() ## try reconnecting

        self.calc_thread = Thread(target=calculate)
        self.calc_thread.daemon = True
        self.calc_thread.start()

        # except:
        #     self.displayingCalibration = False
        #     # self.ui.WavenumberText.setText("Invalid calibration file.")
        #     # self.displayingCalibration = False

    def get_calibration_file(self):
        self.calibration_file = QtWidgets.QFileDialog.getOpenFileName()[0]
        self.ui.calibrationFilenameText.setText(self.calibration_file)
        self.display_calibration()

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

    cwd = Path().absolute()

    def __init__(self, app=None, name="microscoper"):

        self.__checkExists()
        self.load_config()

        self.connection = ClientObject(parent=self, verbose=self.verbose)
        self.setupUi()
        self.setup_devices()

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
                                                    input_channels=self.settings["input channels"],
                                                    polarity_widgets=self.pmtPolarityWidgets)

        self.connection.autoConnect(self.settings["connection port"])
        self.init_stage()

    def setupScanList(self):
        scanFilePath = Path(self.cwd, "Microscoper_app_scanList.csv")
        self.scanList = pd.read_csv(scanFilePath)
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
        self.signal.scanStopAcquire.connect(self.acquire_stop)
        self.connection.connectionSignal.connectionLost.connect(self.acquire_stop)

    def setup_devices(self):
        self.pmtWidgets = [self.ui.PMTSlider0, self.ui.PMTLabel0, self.ui.PMTZero0, self.ui.PMTPreset0,
                           self.ui.PMTSlider1, self.ui.PMTLabel1, self.ui.PMTZero1, self.ui.PMTPreset1,
                           self.ui.PMTSlider2, self.ui.PMTLabel2, self.ui.PMTZero2, self.ui.PMTPreset2,
                           self.ui.PMTSlider3, self.ui.PMTLabel3, self.ui.PMTZero3, self.ui.PMTPreset3,
                           self.ui.PMTStatusText]

        self.pmtPolarityWidgets = [self.ui.pmtInvert1, self.ui.pmtInvert2, self.ui.pmtInvert3, self.ui.pmtInvert4]
        self.detectors = MicroscoperComponents.MicroscopeDetector(widgets=self.pmtWidgets,
                                                                  model="1208")  # Setup components
        if bool(int(self.settings["shutters enabled"])):
            self.shutterWidgets = [self.ui.pumpShutterButton, self.ui.stokesShutterButton]
            self.shutter = MicroscoperComponents.Shutters(widgets=self.shutterWidgets)

    def setup_delay_stage(self):
        self.delay_stage = TTL_Delay_Stage()

    def init_stage(self):
        self.devices = {}
        for key, value in self.deviceList.items():
            self.devices[str(key)] = MicroscoperComponents.NetworkDevice(parent=self, deviceName=value,
                                                                         parentName="microscoper",
                                                                         varName="devices['%s']" % key,
                                                                         timeout=1,
                                                                         verbose=False)
        self.setup_delay_stage()
        self.init_calibration()

    def init_calibration(self):
        if "delaystage" in self.devices:
            self.devices["delaystage"].getPos()
            self.display_calibration()

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
        self.settings["delay_stage_steps"] = str(self.ui.doubleSpinBoxSteps.value())

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
        self.ui.browseButton.clicked.connect(
            lambda: self.ui.directoryText.setText(QtWidgets.QFileDialog.getExistingDirectory()))

        self.ui.browseCalibrationButton.clicked.connect(self.get_calibration_file)

        self.ui.upButton.clicked.connect(lambda: self.changeRasterOffset("Up", self.ui.galvoOffsetRadio.isChecked()))
        self.ui.upButton.clicked.connect(self.acquire_soft_restart)
        self.ui.downButton.clicked.connect(
            lambda: self.changeRasterOffset("Down", self.ui.galvoOffsetRadio.isChecked()))
        self.ui.downButton.clicked.connect(self.acquire_soft_restart)
        self.ui.leftButton.clicked.connect(
            lambda: self.changeRasterOffset("Left", self.ui.galvoOffsetRadio.isChecked()))
        self.ui.leftButton.clicked.connect(self.acquire_soft_restart)
        self.ui.rightButton.clicked.connect(
            lambda: self.changeRasterOffset("Right", self.ui.galvoOffsetRadio.isChecked()))
        self.ui.rightButton.clicked.connect(self.acquire_soft_restart)
        self.ui.zeroOffsetButton.clicked.connect(
            lambda: self.changeRasterOffset("zero", self.ui.galvoOffsetRadio.isChecked()))
        self.ui.zeroOffsetButton.clicked.connect(self.acquire_soft_restart)

        self.ui.zoomWidget.valueChanged.connect(self.acquire_soft_restart)
        self.ui.dwellTime.valueChanged.connect(self.acquire_soft_restart)
        self.ui.resolutionWidget.valueChanged.connect(self.acquire_soft_restart)

        self.ui.fillFractionWidget.valueChanged.connect(self.acquire_soft_restart)
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
        self.ui.doubleSpinBoxSteps.valueChanged.connect(self.save_config)

    def initGetScanAttributes(self):
        index = self.ui.scanTypeWidget.currentIndex()
        self.scan_name = self.ui.scanTypeWidget.currentText()
        self.scan_stage = self.scanList.loc[index]['Stage']
        self.scan_move_type = self.scanList.loc[index]['Move Type']
        self.scan_frames = self.scanList.loc[index]['Frames']
        self.scan_detector = self.scanList.loc[index]['Detector Type']
        self.scan_units = self.scanList.loc[index]['Move Units']

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

    def acquire_init_stage(self):
        """Home the stage."""
        if ("linearstage" in self.scan_stage.lower()):

            if "continuous" in self.scan_move_type.lower():

                self.devices["delaystage"].initScan("continuous")

                # wait while stage is moving
                while not self.devices["delaystage"].status():
                    time.sleep(0.1)

            elif "discrete" in self.scan_move_type.lower():

                pass

                # self.devices["delaystage"].initScan("discrete")
                #
                # # wait while stage is moving
                # while not self.devices["delaystage"].status():
                #     time.sleep(0.1)

    def acquire_init_spectrometer(self):
        if self.scan_detector == "Spectrometer":
            self.devices["spectrometer"].spectrometerInit()

    def init_analog_output(self):
        device = self.settings["input channels"][:4]
        self.ao = MicroscoperComponents.Analog_output(channels=self.settings["output channels"],
                                                      resolution=int(self.settings["resolution"]),
                                                      line_dwell_time=int(self.settings["dwell time"]),
                                                      fill_fraction=float(self.settings["fill fraction"]),
                                                      hwbuffer=int(self.settings["device buffer"]),
                                                      verbose=self.verbose,
                                                      trigger=f"/{device}/ai/StartTrigger")
        self.generateAOScanPattern()

    def init_analog_input(self, image_maxima=None, image_minima=None):
        wait_for_last_frame = False
        single_frame_scan = False
        if self.scan_detector == "PMT":
            if self.scan_move_type == 'Continuous':
                # somehow grab discrete does not need to wait for the last frame
                wait_for_last_frame = True
            if self.scan_frames == "Discrete":
                single_frame_scan = True
            if image_maxima is None:
                image_maxima = [float(self.settings["image maximums %i" % i]) for i in
                                range(0, MicroscoperComponents.getNumberOfChannels(self.settings["input channels"]))]
            if image_minima is None:
                image_minima = [float(self.settings["image minimums %i" % i]) for i in
                                range(0, MicroscoperComponents.getNumberOfChannels(self.settings["input channels"]))]
            self.ai.init(channel=self.settings["input channels"],
                         resolution=int(self.settings["resolution"]),
                         line_dwell_time=float(self.settings["dwell time"]),
                         fill_fraction=float(self.settings["fill fraction"]),
                         hwbuffer=int(self.settings["device buffer"]),
                         verbose=self.verbose,
                         save=self.ui.saveCheckBox.isChecked(),
                         saveFilename=self.saveFilename,
                         saveFileIndex=self.saveFileIndex,
                         xAxis=self.x_axis,
                         metadata=self.metadata,
                         waitForLastFrame=wait_for_last_frame,
                         singleFrameScan=single_frame_scan,
                         framesToAverage=int(self.settings["frames to average"]),
                         dataMaximums=image_maxima,
                         dataMinimums=image_minima,
                         )

    def init_display(self):
        if self.scan_detector == "PMT":
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
            self.display.signal.close.connect(self.acquire_stop)
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
        if self.scan_move_type == 'Continuous':
            self.x_axis = [self.devices["delaystage"].getPos]
            if self.is_displaying_calibration:
                self.x_axis.append(self.stage_to_wavenumber)
        elif self.scan_move_type in ["Discrete", "Grab"]:
            if self.scan_stage == "LinearStage":
                self.x_axis = [self.devices["delaystage"].getPos]
                if self.is_displaying_calibration:
                    self.x_axis.append(self.stage_to_wavenumber)
        else:
            self.x_axis = 'Default'

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
        if 'point' in self.scan_name.lower():
            data_x = np.tile(float(self.settings["scan x offset"]), self.ao.x_pixels_total * self.ao.y_pixels)
            data_y = np.tile(float(self.settings["scan y offset"]), self.ao.x_pixels_total * self.ao.y_pixels)
            data = np.array([data_x, data_y])
            self.ao.set_data(data)
        else:
            self.ao.set_data(
                MMath.generateRasterScan(float(self.settings["max scan amplitude"]) / int(self.settings["zoom"]),
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
                self.settings["scan y offset"] = str(
                    float(self.settings["scan y offset"]) + self.ui.deltaOffset.value())
            if ('right' in direction):
                self.settings["scan x offset"] = str(
                    float(self.settings["scan x offset"]) + self.ui.deltaOffset.value())
            if ('down' in direction):
                self.settings["scan y offset"] = str(
                    float(self.settings["scan y offset"]) - self.ui.deltaOffset.value())
            if ('left' in direction):
                self.settings["scan x offset"] = str(
                    float(self.settings["scan x offset"]) - self.ui.deltaOffset.value())
            elif ("zero" in direction):
                self.settings["scan x offset"] = "0"
                self.settings["scan y offset"] = "0"
            print((float(self.settings["scan x offset"]), float(self.settings["scan y offset"])))

    def displayCreateImageLevelsWindow(self):
        def createWindow():
            numberOfImages = MicroscoperComponents.getNumberOfChannels(self.settings["input channels"])
            imageMaximums = [float(self.settings["image maximums %i" % i]) for i in
                             range(0, MicroscoperComponents.getNumberOfChannels(self.settings["input channels"]))]
            imageMinimums = [float(self.settings["image minimums %i" % i]) for i in
                             range(0, MicroscoperComponents.getNumberOfChannels(self.settings["input channels"]))]

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
            self.acquire_stop()

    def acquire(self):
        # self.devices["spectrometer"].spectrometerSendQuery()
        # self.connection.askForResponse(receiver="spectrometer", sender="microscoper", timeout=15)
        # print(self.connection.connectionIsWaitingForResponse)
        # self.connection.askForResponse(receiver="thorlabsdds220", sender="microscoper", timeout=15)
        # print(self.connection.connectionIsWaitingForResponse)
        # self.devices["spectrometer"].spectrometerScan()
        # self.devices["delaystage"].status()
        self.initialize_acquire_settings()
        self.start_acquire()

    def initialize_acquire_settings(self):

        self.signal.scanInitSignal.emit()
        self.acquiring = True
        self.ui.acquireButton.setText("Stop Acquire")

        ## Initialize defaults --------------------------------------
        self.update_ui_variables()
        self.initGetXYScanPosition()
        self.initGetScanAttributes()

        self.acquire_init_stage()
        self.acquire_init_spectrometer()
        self.initMetadata()
        self.initSavefile()

        self.detectors.setPMTs()

        # wait for PMTs to stabilize
        time.sleep(1)

        # self.shutter.microscope_shutter_open()

        ## Determine x axis display plot  -------------------------------------
        self.initSetupHorizontalAxis()
        #############################################################

        ## Create analog channels -----------------------------
        self.init_analog_output()
        self.init_analog_input()

        ## Initialize display ----------------------------------
        self.init_display()
        #############################################################

    def start_acquire(self):
        # emit scan start signal
        self.signal.scanStartSignal.emit()

        # start the galvos
        self.ao.start()

        # start PMT acquisition
        # if the detector is PMT
        if self.scan_detector == "PMT":

            self.ai.start()
            self.display.start()

        # acquire spectrum
        # if the detector is the spectrometer
        elif self.scan_detector == "Spectrometer":

            self.devices["spectrometer"].spectrometerScan()

            if self.ui.saveCheckBox.isChecked():

                if self.settings["directory"] != '':
                    fileName = os.path.join(self.settings["directory"], self.settings["filename"])
                    xAxis = self.x_axis

                self.devices["spectrometer"].spectrometerSave(fileName, xAxis)

        # run the scan thread
        self._scan_thread = Thread(target=self.scan_thread)

        self._scan_thread.start()

    def acquire_soft_start(self):
        self.signal.scanStartSignal.emit()
        self.update_ui_variables()
        time.sleep(0.1)
        self.init_analog_output()

        if self.scan_detector == "PMT":
            self.init_analog_input(image_maxima=self.ai.dataMaximums,
                                   image_minima=self.ai.dataMinimums)
            self.display.set(imageInput=self.ai.imageData,
                             intensityPlot=self.ai.intensities,
                             intensityIndex=self.ai.intensitiesIndex,
                             imageMaximums=self.ai.dataMaximums,
                             imageMinimums=self.ai.dataMinimums,
                             app=self.app,
                             )
        self.ao.start()

        if self.scan_detector == "Spectrometer":
            self.devices["spectrometer"].spectrometerScan()
            if self.ui.saveCheckBox.isChecked():
                if self.settings["directory"] != '':
                    fileName = os.path.join(self.settings["directory"], self.settings["filename"])
                    xAxis = self.x_axis
                self.devices["spectrometer"].spectrometerSave(fileName, xAxis)
        else:  # PMT
            self.ai.start()

    def acquire_soft_stop(self):
        """
        Stops the galvos, clears analog input memory after screen grab,
         and emit scan done signal.
         """
        self.ao.clear()
        while self.ai.reading:
            time.sleep(0.1)
        if self.scan_detector == "PMT":
            self.ai.clear()
        # self.shutter.Microscope_shutter_close()
        self.signal.scanSoftDoneSignal.emit()

    def acquire_soft_restart(self):
        if self.acquiring:
            if self.scan_detector == "PMT":
                self.ao.clear()
                self.ai.clear()
            self.acquire_soft_start()

    def acquire_stop(self):
        try:
            self.devices["delaystage"].stop()
            self.ai.clear()
            if self.display is not None: self.display.stop()
            while self.ai.reading: time.sleep(0.1)
            if self.ao is not None:
                if self.ao.running: self.ao.clear()
            # self.getxyScanPosition()
            self.scan_thread_interrupt = True
            # self.shutter.Microscope_shutter_close()
            self.detectors.setPMTsZero()
            self.ui.acquireButton.setText("Acquire")
            self.acquiring = False
        except Exception as e:
            print(e)
        self.signal.scanDoneSignal.emit()

    def set_connection_not_busy(self):
        self.connection.connectionIsBusy = False

    def set_connection_is_busy(self):
        self.connection.connectionIsBusy = True

    def scan_thread(self):
        """ Controls the scan thread."""

        # set scan flag to false
        self.scan_thread_interrupt = False

        def move_stage_continuously_until_scan_ends():
            if self.scan_stage == "LinearStage":
                self.devices["delaystage"].startScan()
                while not self.devices["delaystage"].status():
                    time.sleep(0.1)
            elif self.scan_stage == "zStage":
                self.devices["focusController"].startScan()
                while not self.devices["focusController"].status():
                    time.sleep(0.1)
            self.acquire_stop()
            self.acquire_init_stage()

        def wait_until_not_reading():
            while True:
                time.sleep(0.1)
                if not self.ai.reading:
                    self.acquire_soft_stop()
                    break

        def wait_for_first_frame_to_finish():
            wait_until_not_reading()
            self.acquire_stop()
            self.set_connection_not_busy()

        def grab_one_frame():
            self.acquire_soft_start()
            wait_until_not_reading()

        # todo test scan_and_move_stage_in_discrete_steps
        def scan_and_move_stage_in_discrete_steps(number_of_steps=200):

            # grab first frame
            wait_until_not_reading()

            # grab subsequent frames
            for i in range(number_of_steps):
                # initiate move
                self.delay_stage.toggle_move()

                # waif for stage to stabilize
                time.sleep(1)

                grab_one_frame()

                if self.scan_thread_interrupt:
                    break

            self.acquire_stop()
            self.acquire_init_stage()
            self.set_connection_not_busy()

        def zDiscreteUntilEnds():
            while (self.zStage.currentPosition < self.zStage.endScanPosition) and (not self.scan_thread_interrupt):
                if not self.ai.reading:
                    self.acquire_soft_stop()
                    targetPosition = self.ui.ZStageStart.value() + self.stageMoveIndex * self.zStage.MoveDef.value()
                    self.stageMoveIndex += 1
                    self.zStage.MoveAbs(targetPosition)
                    while self.zStage.moving:
                        time.sleep(0.1)
                    time.sleep(1)
                    self.acquire_soft_start()
                time.sleep(0.1)
            else:
                self.acquire_stop()
                self.set_connection_not_busy()

        def stageDefault():
            self.connection.connectionIsBusy = False

        if self.scan_move_type == "None":
            if self.scan_frames == "Discrete":
                wait_for_first_frame_to_finish()
            else:
                stageDefault()
        if self.scan_move_type == "Continuous":
            move_stage_continuously_until_scan_ends()
        if self.scan_move_type == "Discrete":
            # self.stageStartPosition = self.ui.LStageStart.value()
            # self.stageMoveIndex = 1
            if self.scan_stage == "LinearStage":
                try:
                    scan_and_move_stage_in_discrete_steps(int(float(self.settings["delay_stage_steps"])))
                except Exception as e:
                    print(e)
            if self.scan_stage == "zStage":
                zDiscreteUntilEnds()

    def close(self, event):
        if self.mainWindow.isEnabled():
            self.listening = False
            if self.acquiring:
                self.acquire_stop()
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
