import ctypes
import os
import sys
from PyQt5 import QtGui,QtWidgets, QtCore
if __package__ : from .zstepper_ui import Ui_zstepper
else : from zstepper_ui import Ui_zstepper
from threading import Thread
import time


class zstepper(object):
    cwd = os.path.dirname(os.path.realpath(__file__))
    micronsToZ = -0.025/100.
    zToMicrons = 100./-0.025

    def __init__(self):

        if sys.maxsize > 2 ** 32:
            dllname = os.path.join(self.cwd,'ThorZStepper.dll')
            self.dll = ctypes.WinDLL(dllname)
            self.deviceCountC = ctypes.pointer(ctypes.c_long())
            self.dll.FindDevices(self.deviceCountC)
            self.deviceCount = self.deviceCountC.contents.value
            if self.deviceCount < 1:
                print('No devices found. Simulating stage.')
                self.deviceLoaded = False
            else:
                self.dll.SelectDevice(0)
                self.deviceLoaded = True
        else :
            dllname = os.path.join(self.cwd,'ThorZStepper32.dll')
            self.dll = ctypes.CDLL(dllname)
            self.deviceCountC = ctypes.pointer(ctypes.c_long())
            self.dll.FindDevices(self.deviceCountC)
            self.deviceCount = self.deviceCountC.contents.value
            if self.deviceCount < 1:
                print('No devices found. Simulating stage.')
                self.deviceLoaded = False
            else:
                self.dll.SelectDevice(0)
                self.deviceLoaded = True


        # except:
        #     print('No devices found. Simulating stage.')
        #     self.position = 0
        #     self.deviceLoaded = False
        #     self.deviceCount = 0

        # self.getParamInfo()
        # self.getPosition()



    def getParamInfo(self,paramID = 400):
        if self.deviceLoaded:
            paramID = ctypes.c_long(paramID)
            self.minimum = ctypes.pointer(ctypes.c_double())
            self.maximum = ctypes.pointer(ctypes.c_double())
            self.paramType = ctypes.pointer(ctypes.c_double())
            self.paramAvailable = ctypes.pointer(ctypes.c_double())
            self.paramReadOnly = ctypes.pointer(ctypes.c_double())
            self.paramDefault = ctypes.pointer(ctypes.c_double())
            self.dll.GetParamInfo(paramID,
                                  self.paramType,
                                  self.paramAvailable,
                                  self.paramReadOnly,
                                  self.minimum,
                                  self.maximum,
                                  self.paramDefault
                                  )
        # print(self.minimum.contents.value,self.maximum.contents.value,self.paramDefault.contents.value)

    def getPosition(self):
        paramID = 407
        if self.deviceLoaded:
            paramID = ctypes.c_long(paramID)
            param = ctypes.pointer(ctypes.c_double())
            if sys.maxsize > 2**32 : self.dll.GetParam(paramID, param)
            else : self.dll.GetParam()
            self.position = param.contents.value*self.zToMicrons
            return self.position

    def statusPosition(self):
        status = ctypes.pointer(ctypes.c_int32())
        self.dll.StatusPosition(status)
        status = status.contents.value
        return status

    def move(self,position,tolerance=0.05,maxIterations=20):
        if self.deviceLoaded:
            position *= self.micronsToZ
            position = ctypes.c_double(position)
            self.dll.SetParam(ctypes.c_long(400),position)
            self.dll.PreflightPosition()
            self.dll.SetupPosition()
            self.dll.StartPosition()
            self.dll.PostflightPosition()
            while(self.statusPosition() == 0):
                time.sleep(0.05)
        else:
            self.position = position

class CustomMainWindow(QtWidgets.QMainWindow):
    class Signal(QtCore.QObject):
        closeEventSignal = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.signal = self.Signal()

    def closeEvent(self, event):
        self.signal.closeEventSignal.emit()
        super().closeEvent(event)


class zstepper_app(zstepper):
    def __init__(self, show=True):
        self.ui = Ui_zstepper()
        self.mainWindow = CustomMainWindow()
        zstepper.__init__(self)
        self.setupUi()
        self.zTolerance = 0.05 #overwritten by microscoper_app
        self.maxIterations = 20
        self.numberOfIterations = 0
        self.moving = False
        self.running = True
        if show:
            self.mainWindow.show()
            self.startPositionThread()

    def setupUi(self):
        self.ui.setupUi(self.mainWindow)
        self.ui.zSlider.setValue(int(self.getPosition()))
        self.ui.zPositionSpinBoxWidget.setValue(self.getPosition())
        self.ui.zSlider.valueChanged.connect(lambda : self.moveZ(self.ui.zSlider.value()))
        self.ui.zSlider.valueChanged.connect(lambda : self.ui.zPositionSpinBoxWidget.setValue(self.ui.zSlider.value()))
        self.ui.zPositionSpinBoxWidget.valueChanged.connect(lambda : self.moveZ(self.ui.zPositionSpinBoxWidget.value()))
        self.ui.zPositionSpinBoxWidget.valueChanged.\
            connect(lambda : self.ui.zSlider.setValue(self.ui.zPositionSpinBoxWidget.value()))

        self.mainWindow.signal.closeEventSignal.connect(self.stop)

    def moveZ(self,position):
        if not self.moving:
            self.moveZThread = Thread(target=self.moveZUntilPosition, args=(position,))
            self.moveZThread.start()

    def moveZUntilPosition(self,position):
        self.moving = True
        while abs(self.position - position) > self.zTolerance:
            oldPosition = self.position
            self.move(position)

            if self.position == oldPosition:
                self.move(position)
                self.numberOfIterations += 1
                print(oldPosition, self.position, self.numberOfIterations)
            else :
                self.numberOfIterations = 0
            if self.numberOfIterations > self.maxIterations : break
            time.sleep(0.2)
            self.getPosition()


        self.numberOfIterations = 0
        self.moving = False
        # self.zPositionSpinBoxWidget.setValue(self.getPosition())
        # self.zSlider.setValue(self.getPosition())

    def startPositionThread(self):
        self.positionThread = Thread(target = self.getPositionThread)
        self.positionThread.start()

    def getPositionThread(self):
        while self.running:
            position = self.getPosition()
            print(position)
            self.ui.positionLabelWidget.setText("%.3f"%position)
            time.sleep(0.1)

    def stop(self):
        self.running = False


if __name__ == "__main__":
    qapp = QtWidgets.QApplication([])
    stage = zstepper_app()
    qapp.exec_()
    # stage = zstepper()