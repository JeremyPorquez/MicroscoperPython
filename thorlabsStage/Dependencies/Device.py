# version 2019.2.24
import time
from threading import Thread

class BaseDevice(object):
    def __init__(self):
        self.motorLoaded = False
        self.running = False
        self.presetWidgets = [None for i in range(999)]
        self.movePresetFunction = [None for i in range(999)]
        self.currentPosition = None
        self.simulating = False
        self.startPosition = None
        self.endPosition = None
        self.moveIncrements = None

    def baseDeviceHasNumbers(self,inputString):
        return any(char.isdigit() for char in inputString)

    def baseDeviceGetNumber(self,inputString):
        for char in inputString:
            if char.isdigit():
                return int(char)

    def baseDeviceDefMovePresetFunction(self,n):
        def MoveFunction():
            pos = self.presetWidgets[n].value()
            if self.motorLoaded:
                self.moveAbs(pos)
            else:
                self.currentPosition = pos
        exec("self.movePresetFunction[%i] = MoveFunction"%n)
        return MoveFunction

    def verifyMoveStatus(self,function,*args):
        def changeBool(*args):
            self.positionStageOK = False
            try : function(*args)
            except : function
            self.positionStageOK = True
        return changeBool

    def threadThis(self,function,*args):
        thread = Thread(target=function,args=args)
        thread.start()
        return thread

    def getPositionThread(self, delay=0.05):
        self.running = True
        while self.running:
            time.sleep(delay)
            self.currentPosition = self.getPos()

    def simulateStageMotion(self):
        dt = 0.1
        if self.moveType == 'Continuous':
            while (self.currentPosition < self.endPosition) & (self.simulating):
                time.sleep(dt)
                self.currentPosition += (self.moveIncrements)*dt

    def getPos(self):
        pass

    def moveAbs(self,pos=None):
        pass

    def moveRel(self,pos=None):
        pass

    ## just added for compatibility

    def stop(self):
        pass

    def clear(self):
        self.running = False
        self.stop()