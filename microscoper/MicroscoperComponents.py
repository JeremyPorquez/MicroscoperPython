import time
import os
import configparser
from threading import Thread
from Devices.AnalogDigitalOut import AnalogDigital_output_MCC, Digital_output, Analog_output
from Devices.AnalogIn import AnalogInput
from MNetwork.Connections import ClientObject
import ctypes

import numpy as np

def getNumberOfChannels(channel='Dev1/ai0:2'):
    if 'ai' in channel : chType = 'ai'
    else : chType = 'ao'
    try :
        upper = int(channel[channel.find(":") + 1:])
        lower = int(channel[channel.find(chType)+2:channel.find(":")])
        number_of_channels = upper - lower + 1
    except :
        number_of_channels = 1
    return number_of_channels

class NetworkDevice(object):
    def __init__(self, parent = None, deviceName = "thorlabsdds220", parentName = "microscoper",
                 varName="networkDevice", verbose=False):
        """
        Creates a networked device.
        :param deviceName: Should be the same as deviceName in the server.ini file.
        :param parentName: Should be the same as the deviceName in the server.ini file.
        :param varName: Should be the same as the variable declared in the parent python file.
        """

        self.parent = parent
        if not hasattr(self.parent,"connection"):
            raise Exception('parent must have connection attribute of class ClientObject')
        self.deviceName = deviceName
        self.parentName = parentName
        self.varName = varName
        self.verbose = verbose

    def sendCommand(self,command="moveAbs(25,1)"):
        '''A command template'''
        self.parent.connection.sendConnectionMessage(f"{self.deviceName}.{command}")


    def sendQuery(self,query="currentPosition",targetVar="delayStagePosition"):
        '''A query template'''
        self.parent.connection.askForResponse(receiver=self.deviceName,
                                              sender=self.parentName,
                                              question=f"{query}",
                                              target=f"{self.varName}.{targetVar}",
                                              wait=True,
                                              verbose=self.verbose
                                              )

        ## if varName is device, this returns self.parent.device.delayStagePosition
        return getattr(eval("self.parent.{}".format(self.varName)), targetVar)

    def getPos(self):
        return self.sendQuery()

    def move(self,absPosition = None, moveVel = None):
        self.sendCommand("moveAbs({},{})".format(absPosition,moveVel))

    def moveToStartPosition(self):
        self.sendCommand("moveToStartPosition()")

    def initScan(self, arg="continuous"):
        self.sendCommand(f"initScan(\"{arg}\")")

    def startScan(self):
        self.sendCommand("startScan()")

    def status(self):
        """ Returns True if the stage is not moving else False
        """
        return not self.sendQuery("isMoving","isMoving")

    def stop(self):
        self.sendCommand("stop()")


class MicroscopeDetector(object):
    def __init__(self, widgets=None, model="3101"):
        ''' widget = array of PyQT widgets
            define slider widgets first before preset widgets'''
        self.PMT = AnalogDigital_output_MCC(boardNumber=0,model=model,name="PMT")
        self.TPEF = 0
        self.SHG = 1
        self.CARS = 2
        self.Tr = 3

        # Define actions array
        self.setPMTsInitActions = []
        self.setPMTsSliderActions = []
        self.setPMTsZeroActions = []
        self.setPMTsPresetActions = []

        # Define widgets array
        self.labelWidgets = []
        self.sliderWidgets = []

        if widgets is not None: self.__setWidgets(widgets)

        self.setPMTsZero()

    def test(self):
        self.PMT.set_voltage(1,self.TPEF)
        self.PMT.set_voltage(1, self.SHG)
        self.PMT.set_voltage(1.0, self.CARS)

    def setPMTs(self):
        for action in self.setPMTsInitActions:
            action()
        print('Setting PMTs to voltage.')
        self.statusWidget.setText('PMT Status : On')

    def setPMTsZero(self):
        for action in self.setPMTsZeroActions:
            action(slider=False)
            # exec(action)
        self.statusWidget.setText('PMT Status : Off')

    def stop(self):
        self.PMT.set_voltage(0,self.TPEF)
        self.PMT.set_voltage(0, self.SHG)
        self.PMT.set_voltage(0, self.CARS)
        self.PMT.set_voltage(0, self.Tr)

    def __defValuePresetFunction(self,n,widget):
        value = widget.text()
        # value = eval("self.PresetWidget%s.text()" % n)
        if 'zero' in value.lower(): value = 0
        value = int(value)
        def valuePresetFunction(execute=True,slider=True):
            if slider:
                try : self.sliderWidgets[n].setValue(value)
                except : print('No slider widget defined. Define slider widget first if available.')
                try : self.labelWidgets[n].setText("%i"%(value))
                except : print('No text indicator widget defined. Define text widget first if available.')
            voltage = value/1000.
            if execute :
                self.PMT.set_voltage(voltage, int(n))
        return valuePresetFunction

    def __defSetPMTFunction(self,n,widget):
        def setPMTFunction(execute=False):
            value = widget.value()
            voltage = value/1000.
            self.labelWidgets[n].setText('%i'%(value))
            if execute :
                self.PMT.set_voltage(voltage, n)
        return setPMTFunction

    def __defInitPMTFunction(self,n,widget):
        def initPMTFunction(execute=True):
            value = widget.value()
            voltage = value/1000.
            if execute :
                self.PMT.set_voltage(voltage, n)
        return initPMTFunction


    def __hasNumbers(self,inputString):
        return any(char.isdigit() for char in inputString)

    def __getNumber(self,inputString):
        for char in inputString:
            if char.isdigit():
                return int(char)

    def __setWidgets(self,widgets):
        for widget in widgets:
            widgetName = widget.objectName().lower()
            if 'slider' in widgetName :
                if self.__hasNumbers(widgetName) :
                    n = self.__getNumber(widgetName)
                    self.sliderWidgets.append(widget)
                    self.setPMTsSliderActions.append(self.__defSetPMTFunction(n,widget))
                    self.setPMTsInitActions.append(self.__defInitPMTFunction(n,widget))
            if 'label' in widgetName :
                if self.__hasNumbers(widgetName) :
                    n = self.__getNumber(widgetName)
                    self.labelWidgets.append(widget)
            if 'zero' in widgetName :
                if self.__hasNumbers(widgetName) :
                    n = self.__getNumber(widgetName)
                    self.setPMTsZeroActions.append(self.__defValuePresetFunction(n,widget))
            if 'preset' in widgetName:
                if self.__hasNumbers(widgetName):
                    n = self.__getNumber(widgetName)
                    self.setPMTsPresetActions.append(self.__defValuePresetFunction(n,widget))
            if 'status' in widgetName:
                    self.statusWidget = widget
            print('%s Stage widget connected.'%widget.objectName())

class MicroscopeShutter(object):
    def __makeFunctionChangeName(self,widget):
        originalText = widget.text()
        def newFunction(value=True):
            if value == True :
                widget.setText(originalText + ' is open')
            else :
                widget.setText(originalText + ' closed')
        return newFunction

    def __setWidgets(self,widgets):
        for widget in widgets:
            widgetName = widget.objectName().lower()
            if 'pump' in widgetName :
                self.pumpChangeText = self.__makeFunctionChangeName(widget)
                if self.Pump_shutter.get_digital_in() == 0:
                    widget.setText(widget.text() + ' is open')
                    self.pump = True
                else :
                    widget.setText(widget.text() + ' closed')
                    self.pump = False
            if 'stokes' in widgetName :
                # widget.setText(widget.text() + ' closed')
                # self.stokes = False
                self.stokesChangeText = self.__makeFunctionChangeName(widget)
                if self.Stokes_shutter.get_digital_in() == 0:
                    widget.setText(widget.text() + ' is open')
                    self.stokes = True
                else :
                    widget.setText(widget.text() + ' closed')
                    self.stokes = False

    def __init__(self,widgets=None):
        self.Stokes_shutter = AnalogDigital_output_MCC(model="3101",name='Stokes shutter')
        self.Pump_shutter = AnalogDigital_output_MCC(model="3101",name='Pump shutter')
        self.Microscope_shutter = Digital_output("Dev1/port0/line7")
        self.Microscope_shutter_close()
        self.Pump_shutter_close()
        self.Stokes_shutter_close()

        if widgets is not None :
            self.__setWidgets(widgets)


    def Pump_shutter_close(self):
        print('Pump shutter close')
        self.Pump_shutter.set_digital_out(value=1,port=1)

    def Pump_shutter_open(self):
        print('Pump shutter open')
        self.Pump_shutter.set_digital_out(value=0,port=1)

    def Stokes_shutter_close(self):
        print('Stokes shutter close')
        self.Stokes_shutter.set_digital_out(1,port=2)

    def Stokes_shutter_open(self):
        print('Stokes shutter open')
        self.Stokes_shutter.set_digital_out(0,port=2)

    def Microscope_shutter_close(self):
        self.Microscope_shutter.write(np.array([255],dtype=np.uint8))
        # self.Microscope_shutter.close()

    def Microscope_shutter_open(self):
        self.Microscope_shutter.write(np.array([0],dtype=np.uint8))
        # self.Microscope_shutter.close()

    def Set_PumpShutter(self):
        self.pump = not self.pump
        if self.pump :
            self.Pump_shutter_open()
        else :
            self.Pump_shutter_close()
        try :
            self.pumpChangeText(self.pump)
        except :
            pass


    def Set_StokesShutter(self):
        self.stokes = not self.stokes
        if self.stokes :
            self.Stokes_shutter_open()
        else :
            self.Stokes_shutter_close()
        try :
            self.stokesChangeText(self.stokes)
        except :
            pass


class Microscope(object):
    mainPath = os.path.dirname(os.path.realpath(__file__))
    ini_file = mainPath + '/Microscoper_app.ini'
    acquiring = False
    settings = None
    extensionApps = None
    devices = None

    def __init__(self):
        self.defineDefaultSettings()

    def __checkExists(self):
        if os.name == "nt":
            handle = ctypes.windll.user32.FindWindowW(None, "Microscoper 2017")     # Checks if the app is already running
            if handle != 0:
                ctypes.windll.user32.ShowWindow(handle, 10)                         # If the app exists, move window to top
                exit(0)                                                             # Close the python program

    def maximizeWindows(self):
        handles = []
        if os.name == "nt":
            for appWindowName in self.extensionApps:
                handle = ctypes.windll.user32.FindWindowW(None, appWindowName)
                ctypes.windll.user32.ShowWindow(handle, 10)

    def defineDefaultSettings(self):
        self.settings = {
            "filename": "Microscoper",
            "directory": "C:/Users/Jeremy/Desktop/Microscoper",
            "device buffer": "8192",
            "max scan amplitude": "16",
            "input channels": "Dev1/ai0:3",
            "output channels": "Dev1/ao0:1",
            "resolution": "32",
            "zoom": "1",
            "dwell time": "1",
            "fill fraction": "1",
            "delay start position": "0",
            "delay end position": "10",
            "delay increments": "0.050",
            "focus start position": "0",
            "focus end position": "20",
            "focus increments": "0.48",
            "delay preset1": "0",
            "delay preset2": "80",
            "delay preset3": "150",
            "stage x target": "0",
            "stage y target": "0",
            "stage z target": "0",
            "stage x current": "0",
            "stage y current": "0",
            "stage z current": "0",
            "frames to average": "1",
            "connection port": "10230",
            "scan x offset": "0",
            "scan y offset": "0",
        }

        for i in range(0, getNumberOfChannels(self.settings["input channels"])):
            self.settings["PMT %i" % i] = "0"
            self.settings["Image Maximums %i" % i] = "1000"
            self.settings["Image Minimums %i" % i] = "0"

        self.deviceList = {
            "linearstage" : "odl220",
        }

    def loadConfig(self):

        config = configparser.ConfigParser()

        def make_default_ini():
            self.defineDefaultSettings()
            config["Settings"] = {}
            for key, value in self.settings.items():
                config['Settings'][str(key)] = str(value)
            config["Devices"] = {}
            for key, value in self.deviceList.items():
                config["Devices"][str(key)] = str(value)

            with open(self.ini_file, 'w') as configfile:
                config.write(configfile)

        def read_ini():
            self.defineDefaultSettings()
            config.read(self.ini_file)
            configSettings = list(config.items("Settings"))

            for key, value in configSettings:
                self.settings[key] = value

            self.imageMaximums = []
            self.imageMinimums = []
            for i in range(0,getNumberOfChannels(self.settings["input channels"])):
                max = float(config['Settings']['Image Maximums %i' % i])
                min = float(config['Settings']['Image Minimums %i' % i])
                if max == min:
                    max += 1
                self.imageMaximums.append(max)
                self.imageMinimums.append(min)

            devices = list(config.items("Devices"))

            for key, value in devices:
                self.deviceList[key] = value

        try:
            read_ini()
        except:
            make_default_ini()
            read_ini()


    def saveConfig(self):
        config = configparser.ConfigParser()
        config["Settings"] = {}
        config["Extension apps"] = {}
        config["Devices"] = {}
        for key, value in self.settings.items():
            config['Settings'][str(key)] = str(value)
        for key, value in self.deviceList.items():
            config['Devices'][str(key)] = str(value)
        with open(self.ini_file, 'w') as configfile:
            config.write(configfile)


if __name__ == "__main__":
    import time
    s = MicroscopeShutter()
    # s.Pump_shutter_open()
    s.Stokes_shutter_open()
    time.sleep(1)
    # s.Pump_shutter_close()
    s.Stokes_shutter_close()
    # s.Microscope_shutter_close()
  # s.Stokes_shutter_open()