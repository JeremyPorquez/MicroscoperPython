import serial
from ui.focusController import Ui_focusController
from PyQt5 import QtWidgets, QtGui
from threading import Thread
import time
import configparser
import os
try:
    from microscoper.MNetwork.Connections import ClientObject
except ImportError:
    from MNetwork.Connections import ClientObject

def readDevice(device, wait=0.3):
    assert isinstance(device, serial.Serial)
    time.sleep(wait)
    bytesInPort = device.inWaiting()
    return device.read(bytesInPort)

def focusToMicroscopePosition(pos):
    calibration = 0.1
    return pos*calibration

def microscopeToFocusPosition(pos):
    calibration = 10.
    return int(pos*calibration)

class CustomMainWindow(QtWidgets.QMainWindow):
    def __init__(self,parent=None):
        super().__init__()
        self.parent = parent

    def closeEvent(self, event):
        self.parent.quit()
        event.accept()

class FocusController():
    ini_file = os.path.dirname(os.path.realpath(__file__)) + '/prior.ini'
    settings = None

    def __checkExists(self):
        if os.name == "nt":
            handle = ctypes.windll.user32.FindWindowW(None, "Prior Z Stage 2019")
            if handle != 0:
                ctypes.windll.user32.ShowWindow(handle, 10)
                exit(0)

    def __init__(self):
        self.__checkExists()
        self.loadConfig()
        self.loadDevice(self.settings["com port"])

        self.connection = ClientObject(parent=self)
        self.setupUi()
        self.connectUI()


        self.updateUi()
        self.currentPosition = 0

        self.running = True

        self.positionThread = Thread(target=self.getPositionThread)
        self.positionThread.start()

        self.establishConnection()

    def loadDevice(self,port):
        try :
            self.device = serial.Serial(port, timeout=1)
            self.device.baudrate = 9600
            self.device.write(b"DATE\r")
            time.sleep(0.2)
            bytesInPort = self.device.inWaiting()
            dataOut = self.device.read(bytesInPort)
            if b"Prior Scientific Instruments ES10ZE" in dataOut:
                self.deviceLoaded = True
                print("Sueccessfully connected device.")
            else:
                self.deviceLoaded = False
        except :
            print(f'Device not found in {port}, simulating device.')
            self.deviceLoaded = False

    def disconnectDevice(self):
        self.device.close()

    def establishConnection(self):
        self.connection.autoConnect(connectionPort = int(self.settings["connection port"]))
        self.connection.connectionIsBusy = False

    def setupUi(self):
        self.ui = Ui_focusController()
        self.mainWindow = CustomMainWindow(parent=self)
        self.mainWindow.setWindowIcon((QtGui.QIcon('Gui/focusController.png')))
        self.ui.setupUi(self.mainWindow)
        self.mainWindow.setWindowTitle("Focus Controller v.2019.5.3")
        self.ui.moveSpinbox1.setMinimum(float(self.settings["lower limit"]))
        self.ui.moveSpinbox2.setMinimum(float(self.settings["lower limit"]))
        self.ui.moveSpinbox3.setMinimum(float(self.settings["lower limit"]))
        self.ui.moveSpinbox1.setMaximum(float(self.settings["upper limit"]))
        self.ui.moveSpinbox2.setMaximum(float(self.settings["upper limit"]))
        self.ui.moveSpinbox3.setMaximum(float(self.settings["upper limit"]))
        self.mainWindow.show()
        screen = QtWidgets.QDesktopWidget().screenGeometry()
        size = self.mainWindow.geometry()
        self.mainWindow.move(1232, screen.height() - size.height() - 100)
        self.mainWindow.activateWindow()

    def connectUI(self):
        self.ui.buttonSetPorts.clicked.connect(self.setPorts)
        self.ui.homeButton.clicked.connect(self.home)
        self.ui.zeroButton.clicked.connect(self.zero)
        self.ui.moveButton1.clicked.connect(self.move1)
        self.ui.moveButton2.clicked.connect(self.move2)
        self.ui.moveButton3.clicked.connect(self.move3)
        self.ui.upButton.clicked.connect(self.moveUp)
        self.ui.downButton.clicked.connect(self.moveDown)
        self.ui.action_Quit.triggered.connect(self.quit)

    def updateUi(self):
        self.ui.lineEditComport.setText(self.settings["com port"])
        self.ui.lineEditConnport.setText(self.settings["connection port"])
        self.ui.moveSpinbox1.setValue(float(self.settings["move preset1"]))
        self.ui.moveSpinbox2.setValue(float(self.settings["move preset2"]))
        self.ui.moveSpinbox3.setValue(float(self.settings["move preset3"]))
        self.ui.incSpinbox.setValue(float(self.settings["move increments"]))

    def updateUiVariables(self):
        self.settings["com port"] = self.ui.lineEditComport.text()
        self.settings['connection port'] = self.ui.lineEditConnport.text()
        self.settings['move preset1'] = str(self.ui.moveSpinbox1.value())
        self.settings['move preset2'] = str(self.ui.moveSpinbox2.value())
        self.settings['move preset3'] = str(self.ui.moveSpinbox3.value())
        self.settings['move increments'] = str(self.ui.incSpinbox.value())

    def defineDefaultSettings(self):
        self.settings = {
            "com port" : "com3",
            "connection port" : "10124",
            "move preset1" : "0",
            "move preset2" : "1000",
            "move preset3" : "4800",
            "move increments" : "5",
            "upper limit" : "10000",
            "lower limit" : "0",
        }

    def loadConfig(self):
        self.defineDefaultSettings()
        config = configparser.ConfigParser()

        def make_default_ini():
            self.defineDefaultSettings()
            config["Settings"] = {}
            for key, value in self.settings.items():
                config["Settings"][str(key)] = str(value)

        def read_ini():
            config.read(self.ini_file)
            configSettings = list(config.items("Settings"))
            for key, value in configSettings:
                self.settings[key] = value

        try :
            read_ini()
        except :
            make_default_ini()
            read_ini()

    def saveConfig(self):
        self.updateUiVariables()
        config = configparser.ConfigParser()

        config["Settings"] = {}
        for key, value in self.settings.items():
            config['Settings'][str(key)] = str(value)

        with open(self.ini_file, 'w') as configfile:
            config.write(configfile)

    def home(self):
        if self.deviceLoaded:
            def home(self):
                try:
                    self.connection.connectionIsBusy = True
                    self.device.write(b"M\r")
                    readDevice(self.device)
                    while self.currentPosition != 0:
                        self.connection.connectionIsBusy = True
                    self.connection.connectionIsBusy = False
                except Exception as e:
                    print(e)

            moveThread = Thread(target=home, args=(self,))
            moveThread.daemon = True
            moveThread.start()

        else:
            self.currentPosition = 0


    def zero(self):
        self.device.write(b"Z\r")
        readDevice(self.device)


    def setPorts(self):
        self.updateUiVariables()
        self.saveConfig()
        try :
            self.disconnectDevice()
            print("Successfully disconnected device.")
        except :
            pass
        self.loadDevice(self.settings["com port"])
        self.connection.stopClientConnection()
        self.establishConnection()

    def moveAbs(self,pos):
        if self.deviceLoaded:

            def move(self,pos):
                try:
                    self.connection.connectionIsBusy = True
                    self.device.write(b"I\r")   # interrupt device movement
                    focusPosition = microscopeToFocusPosition(pos) #convert position
                    moveCommand = "V,{}\r".format(focusPosition)
                    self.device.write(str.encode(moveCommand))
                    readDevice(self.device)
                    while self.currentPosition != pos:
                        self.connection.connectionIsBusy = True
                    self.connection.connectionIsBusy = False
                except Exception as e:
                    print(e)

            moveThread = Thread(target=move, args=(self, pos))
            moveThread.daemon = True
            moveThread.start()

        else:
            self.currentPosition = pos

    def moveRel(self,inc):
        scanOk = False

        if (inc > 0) & (self.currentPosition + inc < float(self.settings["upper limit"])):
            scanOk = True
        if (inc < 0) & (self.currentPosition + inc > float(self.settings["lower limit"])):
            scanOk = True

        if not scanOk:
            if inc > 0:
                self.moveAbs(float(self.settings["upper limit"]))
            if inc < 0:
                self.moveAbs(float(self.settings["lower limit"]))

        if scanOk:
            if self.deviceLoaded:
                def move(self,inc):
                    try:
                        self.connection.connectionIsBusy = True
                        self.device.write(b"I\r")  # interrupt device movement
                        inc = microscopeToFocusPosition(inc)
                        currentPosition = self.currentPosition
                        moveCommand = "U,{}\r".format(inc)
                        self.device.write(str.encode(moveCommand))
                        readDevice(self.device)
                        while self.currentPosition != currentPosition + inc:
                            self.connection.connectionIsBusy = True
                        self.connection.connectionIsBusy = False
                    except Exception as e:
                        print(e)

                moveThread = Thread(target=move,args=(self,inc))
                moveThread.daemon = True
                moveThread.start()
            else:
                self.currentPosition += inc

    def move1(self):
        self.moveAbs(self.ui.moveSpinbox1.value())

    def move2(self):
        self.moveAbs(self.ui.moveSpinbox2.value())

    def move3(self):
        self.moveAbs((self.ui.moveSpinbox3.value()))

    def moveUp(self):
        self.moveRel(self.ui.incSpinbox.value())

    def moveDown(self):
        self.moveRel(-self.ui.incSpinbox.value())

    def getPosition(self):
        if self.deviceLoaded :
            self.device.write(b"PZ\r")
            positionData = int(readDevice(self.device,0.1))
            position = focusToMicroscopePosition(positionData)
            self.currentPosition = position
        self.ui.lcdNumber.display('%.2f' % self.currentPosition)
        return(self.currentPosition)

    def getPositionThread(self):
        while self.running:
            try :
                self.getPosition()
            except :
                pass
            time.sleep(0.1)

    def quit(self):
        self.connection.stopClientConnection()
        self.running = False
        self.saveConfig()
        self.mainWindow.close()

if __name__ == "__main__":
    import ctypes
    myappid = u'focusController'
    if os.name == "nt":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    qapp = QtWidgets.QApplication([])
    app = FocusController()
    qapp.exec()

