from . import Script
import time
from scipy.interpolate import interp1d
import pandas as pd
from threading import Thread
import os
import configparser

class script(Script.Script):
    def __init__(self,parent):
        # self is Script.Script
        # parent is Server class
        self.parent = parent

        self.cwd = os.path.dirname(os.path.realpath(__file__))
        self.iniFile = os.path.join(self.cwd,"ZaberStageSync.ini")

        self.verbose = False
        self.stageCalibrationFormulaString = None
        self.spectralSurfingCalibration = None

        # self.loadDefaults()

        surfingCalibrationFilename = "calibrationSurfing.csv"
        stageCalibrationFilename = "calibrationStage.txt"

        self.surfingCalibrationFilePath = os.path.join(self.parent.cwd,'Calibrations',surfingCalibrationFilename)
        self.stageCalibrationFilePath = os.path.join(self.parent.cwd,'Calibrations',stageCalibrationFilename)


        # self.surfingCalibrationFilePath = os.path.join(self.cwd,surfingCalibrationFilename)
        # self.stageCalibrationFilePath = os.path.join(self.cwd,stageCalibrationFilename)


    def start(self):
        self.parent.scriptStagePosition = None
        self.loadStageCalibrationFile()
        self.loadSurfingCalibrationFile()
        self.startSyncThread()
        # self.startZaberSync()

    def startSyncThread(self):
        self.running = True
        self.syncThread = Thread(target = self.sync)
        self.syncThread.daemon = True
        self.syncThread.start()

    def getStagePosition(self):
        self.parent.connection.askForResponse(receiver="main", sender="server", question="self.parent.LinearStage.currentPosition",
                                   target='self.scriptStagePosition', wait=True, verbose=self.verbose)
        return self.parent.scriptStagePosition


    def sync(self):
        while self.running :
            self.getStagePosition()
            # self.extractRamanFrequency()
            if self.parent.scriptStagePosition is not None:
                self.calculateRotation()
                self.moveZaberStage(self.calculateRotation())
                if self.verbose: print(self.extractRamanFrequency(),self.calculateRotation())
            time.sleep(0.1)

    def loadStageCalibrationFile(self):
        calibrationFile = open(self.stageCalibrationFilePath,"r")
        self.stageCalibrationFormulaString = calibrationFile.read()

    def loadSurfingCalibrationFile(self):
        self.spectralSurfingCalibration = pd.read_csv(self.surfingCalibrationFilePath)

    def extractRamanFrequency(self):
        wavenumber = eval(self.stageCalibrationFormulaString.replace("x", str(self.parent.scriptStagePosition)))
        self.parent.statusLabel.setText('%.2f cm-1'%wavenumber)
        return wavenumber

    def calculateRotation(self):
        frequency = self.extractRamanFrequency()
        x,y = self.spectralSurfingCalibration['wavenumber'],self.spectralSurfingCalibration['theta']
        f = interp1d(x,y,kind='cubic',fill_value='extrapolate')
        angle = f(frequency)
        if angle > 45: angle = 45
        if angle < 0: angle = 0
        return angle


    def oldcalculateRotation(self):
        frequency = self.extractRamanFrequency()
        index = abs(self.spectralSurfingCalibration[
                        self.spectralSurfingCalibration.columns[0]] - frequency).argmin()
        if (index > self.spectralSurfingCalibration.index.min()) & (index < self.spectralSurfingCalibration.index.max()):
            prev = abs(
                self.spectralSurfingCalibration[self.spectralSurfingCalibration.columns[0]][index - 1] - frequency)
        else:
            prev = abs(
                self.spectralSurfingCalibration[self.spectralSurfingCalibration.columns[0]][index] - frequency)

        if (index > self.spectralSurfingCalibration.index.min()) & (index < self.spectralSurfingCalibration.index.max()):
            next = abs(
                self.spectralSurfingCalibration[self.spectralSurfingCalibration.columns[0]][index + 1] - frequency)
        else:
            next = abs(
                self.spectralSurfingCalibration[self.spectralSurfingCalibration.columns[0]][index] - frequency)

        if prev < next:
            y2 = self.spectralSurfingCalibration[self.spectralSurfingCalibration.columns[1]][index]
            y1 = self.spectralSurfingCalibration[self.spectralSurfingCalibration.columns[1]][index - 1]
            x2 = self.spectralSurfingCalibration[self.spectralSurfingCalibration.columns[0]][index]
            x1 = self.spectralSurfingCalibration[self.spectralSurfingCalibration.columns[0]][index - 1]
            angle = y1 + (y2 - y1) * (frequency - x1) / (x2 - x1)
        elif prev > next :
            y2 = self.spectralSurfingCalibration[self.spectralSurfingCalibration.columns[1]][index + 1]
            y1 = self.spectralSurfingCalibration[self.spectralSurfingCalibration.columns[1]][index]
            x2 = self.spectralSurfingCalibration[self.spectralSurfingCalibration.columns[0]][index + 1]
            x1 = self.spectralSurfingCalibration[self.spectralSurfingCalibration.columns[0]][index]
            angle = y1 + (y2 - y1) * (frequency - x1) / (x2 - x1)
        else :
            angle = self.spectralSurfingCalibration[self.spectralSurfingCalibration.columns[1]][index]
        if angle > 45: angle = 45
        if angle < 0: angle = 0
        return angle

    def moveZaberStage(self,position):
        self.scriptSend('zaber.move_abs(%.2f)' % position)

    def stop(self):
        self.running = False

    def loadDefaults(self):

        config = configparser.ConfigParser()

        def make_default_ini():
            config['Files'] = {}
            config['Files']['Surfing file'] = ''
            config['Files']['Calibration file'] = ''

            with open(self.ini_file, 'w') as configfile:
                config.write(configfile)

        def read_ini():
            self.surfingCalibrationFilePath = config['Files']['Surfing file']
            self.stageCalibrationFilePath = config['Files']['Calibration file']

        try:
            read_ini()
        except:
            make_default_ini()
            read_ini()

    def saveDefaults(self):

        config = configparser.ConfigParser()

        config['Files'] = {}
        config['Files']['Surfing file'] = self.surfingCalibrationFilePath
        config['Files']['Calibration file'] = self.stageCalibrationFilePath


