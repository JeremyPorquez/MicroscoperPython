from zaber.serial import BinarySerial, BinaryDevice
from Gui.ZaberStage_gui import Ui_Zaber
from PyQt5 import QtWidgets, QtGui
from threading import Thread
import time
import configparser
import os
import sys
from Network.Connections import ClientObject

def degToMicrosteps(deg,microstepSize=0.0009375):
    microSteps = int(deg / microstepSize)
    # print(microstepsToDeg(microSteps),microstepsToDeg(microSteps+1))
    # print(deg - microstepsToDeg(microSteps), deg - microstepsToDeg(microSteps + 1))
    # if abs(microstepsToDeg(microSteps)-deg) < abs(microstepsToDeg(microSteps+2)-deg):
    #     return int(microSteps)
    # else :
    #     return int(microSteps+1)
    return int(microSteps)

def microstepsToDeg(microsteps,microstepSize=0.0009375):
    deg = microsteps*microstepSize
    return deg

class CustomMainWindow(QtWidgets.QMainWindow):
    def __init__(self,parent=None):
        super().__init__()
        self.parent = parent

    def closeEvent(self, event):
        self.parent.quit()
        event.accept()

class Zaber():
    ini_file = os.path.dirname(os.path.realpath(__file__)) + '/Zaber.ini'
    settings = None

    def __checkExists(self):
        if os.name == "nt":
            handle = ctypes.windll.user32.FindWindowW(None, "Zaber 2017")
            if handle != 0:
                ctypes.windll.user32.ShowWindow(handle, 10)
                exit(0)

    def __init__(self,port = "COM4"):
        self.__checkExists()
        self.name = port
        self.loadDevice(port)
        self.defineDefaultSettings()

        self.connection = ClientObject(parent=self)
        self.setupUi()
        self.connectUI()

        self.loadConfig()
        self.updateUi()
        self.currentPosition = 0

        self.running = True

        self.positionThread = Thread(target=self.getPositionThread)
        self.positionThread.start()

        self.establishConnection()

    def loadDevice(self,port):
        try :
            binaryPort = BinarySerial(port)
            # self.port = AsciiSerial(port)
            self.address = 1
            # AsciiDevice.__init__(self,self.port,1)
            self.device = BinaryDevice(binaryPort,self.address)
            self.deviceLoaded = True
        except :
            print(f'Device not found in {port}, simulating device.')
            self.deviceLoaded = False

    def establishConnection(self):
        self.connection.autoConnect(connectionPort = int(self.settings["connection port"]))
        self.connection.connectionIsBusy = False

    def setupUi(self):
        self.ui = Ui_Zaber()
        self.mainWindow = CustomMainWindow(parent=self)
        self.mainWindow.setWindowIcon((QtGui.QIcon('Gui/zaber.ico')))
        self.ui.setupUi(self.mainWindow)
        self.mainWindow.setWindowTitle("Zaber Controller v.2019.2.24")
        self.mainWindow.show()
        screen = QtWidgets.QDesktopWidget().screenGeometry()
        size = self.mainWindow.geometry()
        self.mainWindow.move(1232, screen.height() - size.height() - 100)
        self.mainWindow.activateWindow()

    def connectUI(self):
        self.ui.buttonSetPorts.clicked.connect(self.setPorts)
        self.ui.homeButton.clicked.connect(self.home)
        self.ui.setHomeOffsetButton.clicked.connect(self.setHomeOffset)
        self.ui.moveButton1.clicked.connect(self.move1)
        self.ui.moveButton2.clicked.connect(self.move2)
        self.ui.moveButton3.clicked.connect(self.move3)
        self.ui.upButton.clicked.connect(self.moveUp)
        self.ui.downButton.clicked.connect(self.moveDown)
        self.ui.action_Connect.triggered.connect(self.connection.startClientConnection)
        self.ui.action_Disconnect.triggered.connect(self.connection.stopClientConnection)
        self.ui.action_Quit.triggered.connect(self.quit)

    def updateUi(self):
        self.ui.moveSpinbox1.setValue(float(self.settings["move preset1"]))
        self.ui.moveSpinbox2.setValue(float(self.settings["move preset2"]))
        self.ui.moveSpinbox3.setValue(float(self.settings["move preset3"]))
        self.ui.incSpinbox.setValue(float(self.settings["move increments"]))
        self.ui.homeOffsetSpinbox.setValue(float(self.settings["offset"]))

    def updateUiVariables(self):
        self.settings['connection port'] = self.ui.lineEditConnport.text()
        self.settings['move preset1'] = str(self.ui.moveSpinbox1.value())
        self.settings['move preset2'] = str(self.ui.moveSpinbox2.value())
        self.settings['move preset3'] = str(self.ui.moveSpinbox3.value())
        self.settings['move increments'] = str(self.ui.incSpinbox.value())
        self.settings["offset"] = str(self.ui.homeOffsetSpinbox.value())

    def defineDefaultSettings(self):
        self.settings = {
            "connection port" : "10122",
            "move preset1" : "0",
            "move preset2" : "15",
            "move preset3" : "30",
            "move increments" : "0.5",
            "move offset" : "0",
        }


    def loadConfig(self):
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
        self.device.home()
        # self.send("home")

    def setHomeOffset(self):
        homeOffset = degToMicrosteps(self.ui.homeOffsetSpinbox.value())
        data = self.device.send(47,homeOffset).data

    def setPorts(self):
        self.updateUiVariables()
        self.saveConfig()
        self.name = self.ui.lineEditComport.text()
        self.loadDevice(self.name)
        self.connection.stopClientConnection()
        self.establishConnection()

    def move_abs(self,position):
        if self.deviceLoaded:
            microsteps = degToMicrosteps(position)
            def move():
                self.connection.connectionIsBusy = True
                self.device.move_abs(microsteps)
                self.connection.connectionIsBusy = False
            while True:
                try :
                    move()
                    break
                except Exception as e:
                    print(e)
                    continue
        else:
            self.currentPosition = position

    def move_rel(self,position,wait=False):
        blocking = not wait
        if self.deviceLoaded:
            microsteps = degToMicrosteps(position)
            def move():
                self.connection.connectionIsBusy = True
                try:
                    self.device.move_rel(microsteps)
                except Exception as e:
                    print(e)
                self.connection.connectionIsBusy = False
            moveThread = Thread(target=move)
            moveThread.daemon = True
            moveThread.start()
        else:
            self.currentPosition += position

    def move1(self,wait=False):
        blocking = not wait
        self.move_abs(self.ui.moveSpinbox1.value())
            # self.move_abs(degToMicrosteps(self.moveSpinbox1.value()))
            # self.move_abs(degToMicrosteps(self.moveSpinbox1.value()),blocking=blocking)
            # print('moved')
        # self.getPosition()

    def move2(self,wait=False):
        blocking = not wait
        self.move_abs(self.ui.moveSpinbox2.value())

    def move3(self,wait=False):
        blocking = not wait
        self.move_abs((self.ui.moveSpinbox3.value()))

    def moveUp(self,wait=True):
        blocking = not wait
        targetPosition = self.currentPosition + self.ui.incSpinbox.value()
        self.move_abs(targetPosition)

    def moveDown(self,wait=True):
        blocking = not wait
        targetPosition = self.currentPosition - self.ui.incSpinbox.value()
        self.move_abs(targetPosition)

    def getPosition(self):
        if self.deviceLoaded :
            data = self.device.send(60,0).data
            position = int(data)
            position = microstepsToDeg(position)
            self.currentPosition = position
        self.ui.lcdNumber.display('%.3f' % self.currentPosition)
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

class ZaberExtension:
    '''Contains message protocols that connect to the Zaber class and its subclasses'''
    def __init__(self, parent=None):
        self.parent = parent
        self.waitingForResponse = False
        pass

    def move_abs(self,position,wait=False):
        self.parent.send("zaber.move(%.5f,%s)"%(position,wait))

    def move_rel(self,position,wait=False):
        self.parent.send("zaber.move_rel(%.5f,%s)" % (position, wait))

# port = AsciiSerial("COM4")
# device = AsciiDevice(port,1)

if __name__ == "__main__":
    import ctypes
    myappid = u'microscoperzaber'  # arbitrary string
    if os.name == "nt":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    if len(sys.argv) > 1:
        port = sys.argv[1]
        assert isinstance(port,str)
        port = port.capitalize()
        if 'COM' not in com:
            port = 'COM4'
    else:
        port = 'COM4'
    qapp = QtWidgets.QApplication([])
    app = Zaber(port=port)
    qapp.exec()

# command = AsciiCommand("home")
# device.write(command)

