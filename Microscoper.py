import time
import os
import configparser
from threading import Thread
from Devices.AnalogDigitalOut import AnalogDigital_output_MCC, Digital_output, Analog_output
from Devices.AnalogIn import Analog_input

import numpy as np
from Devices.Stage.PyAPT import APTMotor
from Devices.Stage import zstepper

def get_number_of_channels(channel='Dev1/ai0:2'):
    if 'ai' in channel : chType = 'ai'
    else : chType = 'ao'
    try :
        upper = int(channel[channel.find(":") + 1:])
        lower = int(channel[channel.find(chType)+2:channel.find(":")])
        number_of_channels = upper - lower + 1
    except :
        number_of_channels = 1
    return number_of_channels

class baseDevice(object):
    def __init__(self):
        self.motorLoaded = False
        self.stageUpdate = False
        self.presetWidgets = [None for i in range(999)]
        self.movePresetFunction = [None for i in range(999)]
        self.currentPosition = None
        self.simulating = False


    def baseDeviceHasNumbers(self,inputString):
        return any(char.isdigit() for char in inputString)

    def baseDeviceGetNumber(self,inputString):
        for char in inputString:
            if char.isdigit():
                return int(char)

    def baseDeviceDefMovePresetFunction(self,n):
        def MoveFunction():
            pos = self.presetWidgets[n].value()
            # pos = self.presetWidgets[n].value()
            # pos = eval("self.presetWidget%s.value()"%n)
            if self.motorLoaded:
                # self.threadThis(self.verifyMoveStatus(self.MoveAbs(pos)))
                self.MoveAbs(pos)
            else:
                self.currentPosition = pos
        # exec("self.MovePreset%s = MoveFunction"%n)
        exec("self.movePresetFunction[%i] = MoveFunction"%n)
        return MoveFunction

    def setWidgets(self,widgets):
        for widget in widgets:
            widgetName = widget.objectName().lower()
            if 'start' in widgetName :  self.StartPos = widget
            if 'end' in widgetName : self.EndPos = widget
            if ('move' in widgetName) or ('offset' in widgetName) : self.MoveDef = widget
            if 'current' and 'position' in widgetName : self.currentStagePositionText = widget
            if 'preset' in widgetName :
                if self.baseDeviceHasNumbers(widgetName) :
                    n = self.baseDeviceGetNumber(widgetName)
                    self.presetWidgets[n] = widget
                    # exec("self.presetWidget%s = widget"%n)
                    self.baseDeviceDefMovePresetFunction(n)
                    # self.movePresetFunction[n] = self.baseDeviceDefMovePresetFunction(n)
                    ## exec("self.MovePreset%s = self.__defMovePresetFunction(n)"%n)
            print('%s Stage widget connected.'%widget.objectName())

    def verifyMoveStatus(self,function,*args):
        def changeBool(*args):
            self.positionStageOK = False
            try : function(*args)
            except : function
            self.positionStageOK = True
        return changeBool

    def threadThis(self,function,*args):
        Thread(target=function,args=args).start()

    def getPositionThread(self):
        while self.stageUpdate:
            time.sleep(0.05)
            self.currentPosition = self.GetPos()
            self.currentStagePositionText.setText("%.3f" % self.currentPosition)

    def simulateStageMotion(self):
        dt = 0.1
        if self.moveType == 'Continuous':
            while (self.currentPosition < self.EndPos.value()) & (self.simulating):
                time.sleep(dt)
                self.currentPosition += (self.MoveDef.value())*dt

    def GetPos(self):
        pass

    def MoveAbs(self,pos=None):
        pass

    def MoveRel(self,pos=None):
        pass

class LStage(baseDevice):

    def __init__(self,serialNumber=94839332,hwtype=31,verbose=False,widgets=None,name=''):
        baseDevice.__init__(self)
        self.serial = serialNumber
        self.motorLoaded = False
        self.name = name
        try :
            self.motor = APTMotor(serialNumber,HWTYPE=hwtype,verbose=verbose)
            self.motorLoaded = True
            self.motor.aptdll.EnableEventDlg(False) ## Added 2017-10-03 : Prevents appearing of APT event dialog which causes 64 bit systems to crash
            self.currentPosition = self.GetPos()
            print("Stage %s loaded currently at %.4f."%(serialNumber,self.currentPosition))
        except :
            self.motorLoaded = False
            self.currentPosition = 100
            print("Stage not loaded, simulating stage at position %.4f"%(self.currentPosition))

        self.SetMoveType()
        if widgets is not None :
            self.setWidgets(widgets)
        self.stageUpdate = True
        self.threadThis(self.getPositionThread)
        self.positionStageOK = True
        self.targetPosition = self.currentPosition
        self.endScanPosition = None


    def GetPos(self):
        if self.motorLoaded :
            return self.motor.getPos()
        else :
            return self.currentPosition

    def MoveAbs(self,absPosition=110, moveVel=10):
        def Move():
            self.motor.mcAbs(absPosition, moveVel)
        if self.motorLoaded :
            self.threadThis(Move)
        else :
            self.currentPosition = absPosition

    def MoveRel(self,relative_distance,velocity=10):
        def Move():
            self.motor.mcRel(relative_distance, moveVel=velocity)
        if self.motorLoaded :
            self.threadThis(Move)
        else :
            self.currentPosition += relative_distance

    def MoveDir(self,direction='Up',execute=False,velocity=10):
        direction = direction.lower()
        def moveUp():
            self.motor.mcAbs(self.currentPosition + self.MoveDef.value(), moveVel=velocity)
        def moveDown():
            self.motor.mcAbs(self.currentPosition - self.MoveDef.value(), moveVel=velocity)

        if execute:
            if self.motorLoaded :
                if ('up' in direction) or ('right' in direction):
                    self.threadThis(moveUp)
                if ('down' in direction) or ('left' in direction):
                    self.threadThis(moveDown)
            else :
                if ('up' in direction) or ('right' in direction):
                    self.currentPosition = self.currentPosition + self.MoveDef.value()
                if ('down' in direction) or ('left' in direction):
                    self.currentPosition = self.currentPosition - self.MoveDef.value()

    def SetMoveType(self,moveType='None'):
        self.moveType = moveType

    def SetStartPosition(self):
        self.Stop()
        time.sleep(0.1)
        if self.motorLoaded:
            if ('none' not in self.moveType.lower()):
                self.threadThis(self.MoveAbs(float(self.StartPos.value())))
                while abs(self.currentPosition - float(self.StartPos.value())) > 1e-5 :
                    time.sleep(0.1)
        else :
            if ('none' not in self.moveType.lower()):
                self.currentPosition = float(self.StartPos.value())
                self.positionStageOK = True

        self.endScanPosition = self.EndPos.value()

        # self.signal.setStartPositionDone.emit()

    def SetStartScan(self):
        if self.motorLoaded:
            if 'continuous' in self.moveType.lower():
                self.threadThis(self.MoveAbs(self.EndPos.value(),self.MoveDef.value()))
            if 'discrete' in self.moveType.lower():
                self.threadThis(self.MoveAbs(self.currentPosition + self.MoveDef.value()))
        else :
            self.simulating = True
            self.threadThis(self.simulateStageMotion)
        while not self.positionStageOK :
            time.sleep(0.1)

    def SetSpeed(self,maxVel=10,minVel=0,acc=10):
        if self.motorLoaded :
            self.motor.setVelocityParameters(minVel, acc, maxVel)

    def Stop(self):
        if self.motorLoaded :
            try : self.motor.aptdll.MOT_StopImmediate(self.motor.SerialNum)
            except : self.motor.aptdll.MOT_StopProfiled(self.motor.SerialNum)
        else :
            # print("Stopping stage %s"%(self.name))
            self.simulating = False

    def Clear(self):
        try : self.motor.aptdll.cleanUpAPT()
        except : pass

class ZStage(baseDevice,zstepper.zstepper_app):


    def __init__(self, widgets=None):
        baseDevice.__init__(self)
        zstepper.zstepper_app.__init__(self,show=False)
        if widgets is not None:
            self.setWidgets(widgets)
        if self.deviceCount > 0:
            self.deviceLoaded = True
            self.motorLoaded = True
        else :
            self.deviceLoaded = False
            self.motorLoaded = True

        self.stageUpdate = True
        self.endScanPosition = None
        self.targetPosition = self.getPosition()
        self.threadThis(self.getPositionThread)
        self.positionStageOK = True


    def MoveAbs(self,position=None):
        ## for compatibility
        if position is not None :
            self.threadThis(self.moveZ(position))

    def GetPos(self):
        if not self.moving:
            self.getPosition()
        return self.position

    def SetMoveType(self,moveType='None'):
        self.moveType = moveType

    def SetStartPosition(self):
        if self.deviceLoaded:
            self.threadThis(self.moveZ(float(self.StartPos.value())))
            # self.MoveAbs(float(self.StartPos.value()))
            while self.moving:
                time.sleep(0.1)
        self.endScanPosition = self.EndPos.value()

    def SetStartScan(self):
        if self.deviceLoaded:
            self.MoveAbs(self.currentPosition + self.MoveDef.value())
        else :
            self.simulating = True
            self.threadThis(self.__simulateStageMotion)
        while self.moving :
            time.sleep(0.1)

    def Stop(self):
        pass

    def Clear(self):
        self.stageUpdate = False
        self.running = False
        self.stop()


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
            # exec(action)
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
    def __init__(self):
        pass

class MicroscopeSettings(object):
    imageMaximums = []
    imageMinimums = []
    numberOfInputChannels = 0
    outputChannels = 0
    rasterOffset = 0, 0
    #todo : fill up this and use this to simplify microscoper_app code

    def get_settings(self, **kwargs):
        for key, value in kwargs:
            if (hasattr(self,key)):
                setattr(self,key,value)


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