from PyQt5 import QtWidgets, QtGui, QtCore
from ui.ThorlabsStage import Ui_Thorlabs
import time
import configparser
import os
from MNetwork.Connections import ClientObject
from Dependencies.PyAPT import APTMotor
from Dependencies.Device import BaseDevice

class CustomMainWindow(QtWidgets.QMainWindow):
    def __init__(self,parent=None):
        super().__init__()
        self.parent = parent

    def closeEvent(self, event):
        self.parent.quit()
        event.accept()

class ThorlabsStage(BaseDevice):
    settings = None
    motorLoaded = False
    ini_file = os.path.dirname(os.path.realpath(__file__)) + '/ThorlabsStage.ini'

    def __checkExists(self):
        if os.name == "nt":
            handle = ctypes.windll.user32.FindWindowW(None, "ThorlabsStage BBD Series")
            if handle != 0:
                ctypes.windll.user32.ShowWindow(handle, 10)
                exit(0)

    class Signal(QtCore.QObject):
        startScan = QtCore.pyqtSignal()

        def disconnectAll(self):
            try :
                self.startScan.disconnect()
            except :
                pass

        def connect(self, signal, function):
            assert isinstance(signal, QtCore.pyqtBoundSignal)
            try:
                signal.disconnect()
            except:
                pass
            signal.connect(function)

    def __init__(self,verbose=False,visible=True):
        BaseDevice.__init__(self)
        self.loadConfig()

        self.loadDevice(verbose=verbose)

        self.connection = ClientObject(parent=self)
        self.setupUi(visible)
        self.connectUi()
        self.updateUi()
        self.connectSignals()

        self.threadThis(self.getPositionThread, (0.01))
        self.establishConnection()

        self.isMoving = False
        self.moveThread = None

    def defineDefaultSettings(self):
        self.settings = {
            "connection port" : "10124",
            "serial number" : "94876470",
            "hwtype" : "31",
            "move preset1" : "0",
            "move preset2" : "50",
            "move preset3" : "100",
            "move increments" : "0.1",
            "scan speed" : "0.01",
            "scan start position" : "50",
            "scan end position" : "55",
            "max velocity" : "10",
        }

    def updateUi(self):
        self.ui.lineEditConnport.setText(self.settings["connection port"])
        self.ui.lineEditSerialNumber.setText(self.settings["serial number"])
        self.ui.moveSpinbox1.setValue(float(self.settings["move preset1"]))
        self.ui.moveSpinbox2.setValue(float(self.settings["move preset2"]))
        self.ui.moveSpinbox3.setValue(float(self.settings["move preset3"]))
        self.ui.incSpinbox.setValue(float(self.settings["move increments"]))
        self.ui.moveSpeedSpinbox.setValue(float(self.settings["scan speed"]))
        self.ui.startPositionSpinbox.setValue(float(self.settings["scan start position"]))
        self.ui.endPositionSpinbox.setValue(float(self.settings["scan end position"]))

    def updateUiVariables(self):
        self.settings["connection port"] = self.ui.lineEditConnport.text()
        self.settings["serial number"] = self.ui.lineEditSerialNumber.text()
        self.settings["move preset1"] = self.ui.moveSpinbox1.value()
        self.settings["move preset2"] = self.ui.moveSpinbox2.value()
        self.settings["move preset3"] = self.ui.moveSpinbox3.value()
        self.settings["move increments"] = self.ui.incSpinbox.value()
        self.settings["scan speed"] = self.ui.moveSpeedSpinbox.value()
        self.settings["scan start position"] = self.ui.startPositionSpinbox.value()
        self.settings["scan end position"] = self.ui.endPositionSpinbox.value()

    def loadConfig(self):

        config = configparser.ConfigParser()

        def make_default_ini():
            self.defineDefaultSettings()
            for key, value in self.settings.items():
                config['Settings'][str(key)] = str(value)

        def read_ini():
            config.read(self.ini_file)
            configSettings = list(config.items("Settings"))

            for key, value in configSettings:
                self.settings[key] = value

        try:
            read_ini()
        except:
            make_default_ini()
            read_ini()

        self.serial = int(self.settings["serial number"])
        self.hwtype = int(self.settings["hwtype"])

    def saveConfig(self):
        self.updateUiVariables()
        config = configparser.ConfigParser()

        config["Settings"] = {}
        for key, value in self.settings.items():
            config['Settings'][str(key)] = str(value)

        with open(self.ini_file, 'w') as configfile:
            config.write(configfile)

    def loadDevice(self,verbose=False):
        try :
            self.motor = APTMotor(int(self.settings["serial number"]),
                                  HWTYPE=int(self.settings["hwtype"]),
                                  verbose=verbose)
            self.motorLoaded = True
            self.motor.aptdll.EnableEventDlg(False) ## Added 2017-10-03 : Prevents appearing of APT event dialog which causes 64 bit systems to crash
            # self.currentPosition = self.getPos()
            print("Stage %s loaded."%(self.settings["serial number"]))
        except :
            self.motorLoaded = False
            self.currentPosition = 100
            print("Stage not loaded, simulating stage at position %.4f"%(self.currentPosition))

    def setupUi(self, visible=True):
        self.ui = Ui_Thorlabs()
        self.mainWindow = CustomMainWindow(parent=self)
        self.mainWindow.setWindowIcon(QtGui.QIcon("ui/ThorlabsStage.png"))
        self.ui.setupUi(self.mainWindow)
        if visible:
            self.mainWindow.setWindowTitle("Thorlabs Stage Controller v.2019.2.24")
            self.mainWindow.show()
            self.mainWindow.activateWindow()

    def connectUi(self):
        self.ui.buttonSetPorts.clicked.connect(self.setPorts)
        self.ui.homeButton.clicked.connect(self.moveHome)
        self.ui.moveButton1.clicked.connect(lambda: self.moveAbs(self.ui.moveSpinbox1.value()))
        self.ui.moveButton2.clicked.connect(lambda: self.moveAbs(self.ui.moveSpinbox2.value()))
        self.ui.moveButton3.clicked.connect(lambda: self.moveAbs(self.ui.moveSpinbox3.value()))
        self.ui.upButton.clicked.connect(lambda: self.moveRel(self.ui.incSpinbox.value()))
        self.ui.downButton.clicked.connect(lambda: self.moveRel(-self.ui.incSpinbox.value()))
        self.ui.action_Quit.triggered.connect(self.quit)
        self.ui.moveSpeedSpinbox.valueChanged.connect(lambda: self.setSpeed(self.ui.moveSpeedSpinbox.value()))
        self.ui.scanButton.clicked.connect(lambda: self.initScan())
        self.ui.stopButton.clicked.connect(self.stop)

    def connectSignals(self):
        self.signal = self.Signal()

    def setPorts(self):
        self.updateUiVariables()
        self.connection.stopClientConnection()
        self.connection.autoConnect(connectionPort = int(self.settings["connection port"]))
        self.connection.connectionIsBusy = False

        self.clear()
        self.loadDevice()
        self.threadThis(self.getPositionThread)

    def establishConnection(self):
        self.updateUiVariables()
        self.connection.autoConnect(connectionPort = int(self.settings["connection port"]))
        self.connection.connectionIsBusy = False

    def moveHome(self):
        """
        Moves the stage to home position.
        """
        if self.motorLoaded:
            def move():
                self.motor.go_home()
            self.threadThis(move)
        else:
            self.currentPosition = 110

    def getPos(self):
        """
        Returns the stage position and updates the ui display.
        """
        if self.motorLoaded :
            currentPosition = self.motor.getPos()
        else:
            currentPosition = self.currentPosition
        self.ui.lcdNumber.display("%.3f" % currentPosition)
        return currentPosition

    def moveAbs(self,absPosition = None, moveVel = None):
        """
        Moves stage to absolute position. When moveVel is not defined, moveVel is set to 10
        """
        if absPosition is None:
            absPosition = 0
        if moveVel is None:
            moveVel = 10

        def move():
            if self.isMoving:
                self.softStop()
            self.isMoving = True
            self.threadThis(lambda: self.motor.mcAbs(absPosition, moveVel))
            while (abs(self.currentPosition - absPosition) > 1e-5) & (self.isMoving):
                time.sleep(0.001)
            self.isMoving = False

        if self.motorLoaded :
            self.threadThis(move)
        else :
            self.currentPosition = absPosition

    def moveRel(self, relativeDistance = None, moveVel = None):
        if relativeDistance is None:
            relativeDistance = 0
        if moveVel is None:
            moveVel = 10
        def move():
            if self.isMoving:
                self.softStop()
            self.isMoving = True
            self.threadThis(lambda: self.motor.mcRel(relativeDistance, moveVel=moveVel))
            while (abs(self.currentPosition - float(self.ui.startPositionSpinbox.value())) > 1e-5) & (self.isMoving):
                time.sleep(0.001)
            self.isMoving = False

        if self.motorLoaded :
            self.threadThis(move)
        else :
            self.currentPosition += relativeDistance

    def moveToStartPosition(self):
        self.stop()
        time.sleep(0.1)
        if self.motorLoaded:
            self.threadThis(self.moveAbs(float(self.ui.startPositionSpinbox.value()),float(self.settings["max velocity"])))
        else :
            self.moveAbs(float(self.ui.startPositionSpinbox.value()),float(self.settings["max velocity"]))


    def moveToEndPosition(self):
        self.Stop()
        time.sleep(0.1)
        if self.motorLoaded:
            self.threadThis(self.moveAbs(float(self.ui.endPositionSpinbox.value()),float(self.settings["max velocity"])))
        else :
            self.moveAbs(float(self.ui.endPositionSpinbox.value()),float(self.settings["max velocity"]))

    def initScan(self, moveType="continuous", stepSize=0.1):
        """
        Initiates the stage for scanning by moving it to the start position.
        Stage movement can start through by calling
            "signal.startScan.emit()"
        """
        self.moveToStartPosition()

        if self.motorLoaded:
            if 'continuous' in moveType.lower():
                self.signal.connect(self.signal.startScan, lambda: self.moveAbs(self.ui.endPositionSpinbox.value(), self.ui.moveSpeedSpinbox.value()))
            if 'discrete' in moveType.lower():
                self.signal.connect(self.signal.startScan, lambda: self.moveRel(relativeDistance=stepSize))
        else :
            self.simulating = True
            self.threadThis(self.simulateStageMotion)

    def startScan(self):
        self.signal.startScan.emit()

    def setSpeed(self,maxVel=10,minVel=0,acc=10):
        if self.motorLoaded :
            self.motor.setVelocityParameters(minVel, acc, maxVel)

    def status(self):
        return not self.isMoving

    def stop(self):
        if self.motorLoaded:
            try : self.motor.aptdll.MOT_StopImmediate(self.motor.SerialNum)
            except : self.motor.aptdll.MOT_StopProfiled(self.motor.SerialNum)
        else :
            self.simulating = False
        time.sleep(0.5)
        self.isMoving = False

    def softStop(self):
        if self.motorLoaded:
            try : self.motor.aptdll.MOT_StopImmediate(self.motor.SerialNum)
            except : self.motor.aptdll.MOT_StopProfiled(self.motor.SerialNum)
        else :
            self.simulating = False
        time.sleep(0.5)

    def clear(self):
        self.stop()
        self.signal.disconnectAll()
        super().clear()
        if self.motorLoaded:
            self.motor.cleanUpAPT()
            self.motorLoaded = False

    def quit(self):
        self.stop()
        self.connection.stopClientConnection()
        self.clear()
        self.saveConfig()
        self.mainWindow.close()

if __name__ == "__main__":
    import ctypes
    qapp = QtWidgets.QApplication([])
    app = ThorlabsStage(visible=True)
    myappid = u"ThorlabsStage BBD Series"  # arbitrary string
    if os.name == "nt":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    qapp.exec()