import os
import configparser
from mcculw import ul
from mcculw.enums import ULRange, DigitalPortType
from Devices.AnalogDigitalOut import Digital_output
import ctypes
from Devices.AnalogIn import AnalogInput
from Devices.AnalogDigitalOut import Analog_output

import numpy as np
import math


def getNumberOfChannels(channel='Dev1/ai0:2'):
    if 'ai' in channel:
        chType = 'ai'
    else:
        chType = 'ao'
    try:
        upper = int(channel[channel.find(":") + 1:])
        lower = int(channel[channel.find(chType) + 2:channel.find(":")])
        number_of_channels = upper - lower + 1
    except:
        number_of_channels = 1
    return number_of_channels


class NetworkDevice(object):
    def __init__(self, parent=None, deviceName="thorlabsdds220", parentName="microscoper",
                 varName="networkDevice", verbose=False, timeout=15):
        """
        Creates a networked device.
        :param deviceName: Should be the same as deviceName in the server.ini file.
        :param parentName: Should be the same as the deviceName in the server.ini file.
        :param varName: Should be the same as the variable declared in the parent python file.
        """

        self.parent = parent
        if not hasattr(self.parent, "connection"):
            raise Exception('parent must have connection attribute of class ClientObject')
        self.deviceName = deviceName
        self.parentName = parentName
        self.varName = varName
        self.verbose = verbose
        self.timeout = timeout

    def sendCommand(self, command="moveAbs(25,1)"):
        '''A command template'''
        self.parent.connection.sendConnectionMessage(f"{self.deviceName}.{command}")

    def sendQuery(self, query="currentPosition", targetVar="delayStagePosition"):
        '''A query template'''
        localObject = eval("self.parent.{}".format(self.varName))
        if not hasattr(localObject, targetVar):
            setattr(localObject, targetVar, None)

        response = self.parent.connection.askForResponse(receiver=self.deviceName,
                                                         sender=self.parentName,
                                                         question="{}".format(query),
                                                         target="{}.{}".format(self.varName, targetVar),
                                                         wait=True,
                                                         verbose=self.verbose,
                                                         timeout=self.timeout,
                                                         )
        if response is 1:  ## has timedout
            return None
        else:

            ## if varName is device, this returns self.parent.device.delayStagePosition
            ## return getattr(eval("self.parent.{}".format(self.varName)), targetVar)
            return getattr(localObject, targetVar)

    def getPos(self):
        return self.sendQuery()

    def move(self, absPosition=None, moveVel=None):
        self.sendCommand("moveAbs({},{})".format(absPosition, moveVel))

    def moveToStartPosition(self):
        self.sendCommand("moveToStartPosition()")

    def initScan(self, arg="continuous"):
        self.sendCommand(f"initScan(\"{arg}\")")

    def startScan(self):
        self.sendCommand("startScan()")

    def status(self):
        """ Returns True if the stage is not moving else False
        """
        return not self.sendQuery("isMoving", "isMoving")

    def stop(self):
        self.sendCommand("stop()")

    def spectrometerInit(self):
        self.sendCommand('stopContinuousScan()')

    def spectrometerSendQuery(self):
        self.parent.connection.askForResponse(receiver="spectrometer", sender="microscoper")

    def spectrometerScan(self):
        time.sleep(1)
        self.sendCommand("spectrometer.scan(background_subtract=False)")
        self.sendCommand("spectrometer.plot()")
        time.sleep(0.5)
        self.spectrometerSendQuery()

    def spectrometerSave(self, fileName=None, xAxis=None):
        if xAxis is None:
            xAxis = lambda: None
        xAxis = xAxis[0]
        if fileName is not '':
            self.sendCommand("save(filename=r'%s',label='%.3f',append=True)"
                             % (fileName, xAxis()))
        time.sleep(0.1)
        self.spectrometerSendQuery()

    def spectrometerEndScan(self):
        if self.parent is not None:
            if self.parent.scanDetector == "Spectrometer":
                self.parent.connection.sendConnectionMessage('spectrometer.fileLoaded = False')
        else:
            raise ValueError('self.parent must be set')


class Spectrometer(NetworkDevice):
    def __init__(self, parent=None, deviceName="spectrometer", parentName="microscoper",
                 varName="networkDevice", verbose=False):
        super().__init__(parent=parent, deviceName=deviceName, parentName=parentName, varName=varName, verbose=verbose)

    def scan(self):
        time.sleep(1)
        self.sendCommand("spectrometer.scan(background_subtract=False")
        self.sendCommand("spectrometer.plot()")
        time.sleep(0.5)

    def save(self, fileName=None, xAxis=None):
        if xAxis is None:
            xAxis = lambda: None
        xAxis = xAxis[0]
        if fileName is not '':
            self.sendCommand("save(filename=r'%s',label='%.3f',append=True)"
                             % (fileName, xAxis()))
        time.sleep(0.1)

    def endScan(self):
        if self.parent is not None:
            if self.parent.scanDetector == "Spectrometer":
                self.parent.connection.sendConnectionMessage('spectrometer.fileLoaded = False')
        else:
            raise ValueError('self.parent must be set')

    def sendQuery(self, query="scanning", targetVar="scanning"):
        return super().sendQuery(query, targetVar)


class MCCDev:
    def __init__(self, number_of_channels=2):
        self.board_num = 0
        self.number_of_channels = number_of_channels

    def set_voltage(self, voltage=0, channel=0):
        bits = 4095
        if channel < self.number_of_channels:
            bit_voltage = math.floor(voltage * bits)
            bit_voltage = bit_voltage if bit_voltage < bits else bits if bit_voltage > 0 else 0
            ul.a_out(self.board_num, channel, ULRange.BIP1VOLTS, bit_voltage)

    def set_digital_out(self, value, port):
        ul.d_bit_out(self.board_num, port_type=DigitalPortType.FIRSTPORTA, bit_num=port, bit_value=value)


class MicroscopeDetector(object):
    ao_range = ULRange.BIP1VOLTS

    def __init__(self, widgets=None, model="1208"):
        ''' widget = array of PyQT widgets
            define slider widgets first before preset widgets'''
        self.PMT = MCCDev()
        self.TPEF = 0
        self.SHG = 1
        # self.CARS = 2
        # self.Tr = 3

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
        self.PMT.set_voltage(1, self.TPEF)
        self.PMT.set_voltage(1, self.SHG)
        # self.PMT.set_voltage(1.0, self.CARS)

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
        self.PMT.set_voltage(0, self.TPEF)
        self.PMT.set_voltage(0, self.SHG)
        # self.PMT.set_voltage(0, self.CARS)
        # self.PMT.set_voltage(0, self.Tr)

    def __defValuePresetFunction(self, n, widget):
        value = widget.text()
        # value = eval("self.PresetWidget%s.text()" % n)
        if 'zero' in value.lower(): value = 0
        value = int(value)

        def valuePresetFunction(execute=True, slider=True):
            if slider:
                try:
                    self.sliderWidgets[n].setValue(value)
                except:
                    print('No slider widget defined. Define slider widget first if available.')
                try:
                    self.labelWidgets[n].setText("%i" % (value))
                except:
                    print('No text indicator widget defined. Define text widget first if available.')
            voltage = value / 1000.
            if execute:
                self.PMT.set_voltage(voltage, int(n))

        return valuePresetFunction

    def __defSetPMTFunction(self, n, widget):
        def setPMTFunction(execute=False):
            value = widget.value()
            voltage = value / 1000.
            self.labelWidgets[n].setText('%i' % (value))
            if execute:
                self.PMT.set_voltage(voltage, n)

        return setPMTFunction

    def __defInitPMTFunction(self, n, widget):
        def initPMTFunction(execute=True):
            value = widget.value()
            voltage = value / 1000.
            if execute:
                self.PMT.set_voltage(voltage, n)

        return initPMTFunction

    def __hasNumbers(self, inputString):
        return any(char.isdigit() for char in inputString)

    def __getNumber(self, inputString):
        for char in inputString:
            if char.isdigit():
                return int(char)

    def __setWidgets(self, widgets):
        for widget in widgets:
            widgetName = widget.objectName().lower()
            if 'slider' in widgetName:
                if self.__hasNumbers(widgetName):
                    n = self.__getNumber(widgetName)
                    self.sliderWidgets.append(widget)
                    self.setPMTsSliderActions.append(self.__defSetPMTFunction(n, widget))
                    self.setPMTsInitActions.append(self.__defInitPMTFunction(n, widget))
            if 'label' in widgetName:
                if self.__hasNumbers(widgetName):
                    n = self.__getNumber(widgetName)
                    self.labelWidgets.append(widget)
            if 'zero' in widgetName:
                if self.__hasNumbers(widgetName):
                    n = self.__getNumber(widgetName)
                    self.setPMTsZeroActions.append(self.__defValuePresetFunction(n, widget))
            if 'preset' in widgetName:
                if self.__hasNumbers(widgetName):
                    n = self.__getNumber(widgetName)
                    self.setPMTsPresetActions.append(self.__defValuePresetFunction(n, widget))
            if 'status' in widgetName:
                self.statusWidget = widget
            print('%s Stage widget connected.' % widget.objectName())


class Shutters(object):
    def __makeFunctionChangeName(self, widget):
        originalText = widget.text()

        def newFunction(value=True):
            if value == True:
                widget.setText(originalText + ' is open')
            else:
                widget.setText(originalText + ' closed')

        return newFunction

    def __setWidgets(self, widgets):
        for widget in widgets:
            widgetName = widget.objectName().lower()
            if 'pump' in widgetName:
                self.pumpChangeText = self.__makeFunctionChangeName(widget)
                if self.pump_shutter.get_digital_in() == 0:
                    widget.setText(widget.text() + ' is open')
                    self.pump = True
                else:
                    widget.setText(widget.text() + ' closed')
                    self.pump = False
            if 'stokes' in widgetName:
                # widget.setText(widget.text() + ' closed')
                # self.stokes = False
                self.stokesChangeText = self.__makeFunctionChangeName(widget)
                if self.stokes_shutter.get_digital_in() == 0:
                    widget.setText(widget.text() + ' is open')
                    self.stokes = True
                else:
                    widget.setText(widget.text() + ' closed')
                    self.stokes = False

    def __init__(self, widgets=None):
        self.stokes_shutter = MCCDev()
        self.pump_shutter = MCCDev()
        # self.stokes_shutter = MCCDev.Device(model="3101", name='Stokes shutter')
        # self.pump_shutter = MCCDev.Device(model="3101", name='Pump shutter')
        self.microscope_shutter = Digital_output("Dev1/port0/line7")
        self.microscope_shutter_close()
        self.pump_shutter_close()
        self.stokes_shutter_close()

        if widgets is not None:
            self.__setWidgets(widgets)

    def pump_shutter_close(self):
        print('Pump shutter close')
        self.pump_shutter.set_digital_out(value=1, port=1)

    def pump_shutter_open(self):
        print('Pump shutter open')
        self.pump_shutter.set_digital_out(value=0, port=1)

    def stokes_shutter_close(self):
        print('Stokes shutter close')
        self.stokes_shutter.set_digital_out(1, port=2)

    def stokes_shutter_open(self):
        print('Stokes shutter open')
        self.stokes_shutter.set_digital_out(0, port=2)

    def microscope_shutter_close(self):
        self.microscope_shutter.write(np.array([255], dtype=np.uint8))
        # self.microscope_shutter.close()

    def microscope_shutter_open(self):
        self.microscope_shutter.write(np.array([0], dtype=np.uint8))
        # self.microscope_shutter.close()

    def flip_pump_shutter(self):
        self.pump = not self.pump
        if self.pump:
            self.pump_shutter_open()
        else:
            self.pump_shutter_close()
        try:
            self.pumpChangeText(self.pump)
        except:
            pass

    def flip_stokes_shutter(self):
        self.stokes = not self.stokes
        if self.stokes:
            self.stokes_shutter_open()
        else:
            self.stokes_shutter_close()
        try:
            self.stokesChangeText(self.stokes)
        except:
            pass


class Microscope(object):
    mainPath = os.path.dirname(os.path.realpath(__file__))
    ini_file = mainPath + '/Microscoper_app.ini'
    acquiring = False
    settings = None
    extensionApps = None
    devices = None
    verbose = True

    def __init__(self):
        self.define_default_settings()

    def __checkExists(self):
        if os.name == "nt":
            handle = ctypes.windll.user32.FindWindowW(None, "Microscoper 2017")  # Checks if the app is already running
            if handle != 0:
                ctypes.windll.user32.ShowWindow(handle, 10)  # If the app exists, move window to top
                exit(0)  # Close the python program

    def maximizeWindows(self):
        handles = []
        if os.name == "nt":
            for key, appWindowName in self.extensionApps.items():
                handle = ctypes.windll.user32.FindWindowW(None, appWindowName)
                # ctypes.windll.user32.ShowWindow(handle, 10)
                ctypes.windll.user32.SetForegroundWindow(handle)

    def define_default_settings(self):
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
            "calibration file": "",
            "verbose": "0",
            "shutters enabled": "0",
        }

        for i in range(0, getNumberOfChannels(self.settings["input channels"])):
            self.settings["PMT %i" % i] = "0"
            self.settings["Image Maximums %i" % i] = "1000"
            self.settings["Image Minimums %i" % i] = "0"

        self.deviceList = {
        }

        self.extensionApps = {
        }

    def load_config(self):

        config = configparser.ConfigParser()

        def make_default_ini():
            self.define_default_settings()
            config["Settings"] = {}
            for key, value in self.settings.items():
                config['Settings'][str(key)] = str(value)
            config["Devices"] = {}
            for key, value in self.deviceList.items():
                config["Devices"][str(key)] = str(value)

            with open(self.ini_file, 'w') as configfile:
                config.write(configfile)

        def read_ini():
            self.define_default_settings()
            config.read(self.ini_file)
            configSettings = list(config.items("Settings"))
            extensionApps = list(config.items("Extension apps"))

            for key, value in configSettings:
                self.settings[key] = value

            for key, value in extensionApps:
                self.extensionApps[key] = value

            self.imageMaximums = []
            self.imageMinimums = []
            for i in range(0, getNumberOfChannels(self.settings["input channels"])):
                max = float(config['Settings']['Image Maximums %i' % i])
                min = float(config['Settings']['Image Minimums %i' % i])
                if max == min:
                    max += 1
                self.imageMaximums.append(max)
                self.imageMinimums.append(min)

            self.verbose = bool(int(config["Settings"]["verbose"]))

            devices = list(config.items("Devices"))

            for key, value in devices:
                self.deviceList[key] = value

        try:
            read_ini()
        except:
            make_default_ini()
            read_ini()

    def save_config(self):
        config = configparser.ConfigParser()
        config["Settings"] = {}
        config["Extension apps"] = {}
        config["Devices"] = {}
        for key, value in self.settings.items():
            config['Settings'][str(key)] = str(value)
        for key, value in self.deviceList.items():
            config['Devices'][str(key)] = str(value)
        for key, value in self.extensionApps.items():
            config['Extension apps'][str(key)] = str(value)
        with open(self.ini_file, 'w') as configfile:
            config.write(configfile)