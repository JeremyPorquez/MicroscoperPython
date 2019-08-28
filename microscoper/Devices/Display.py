import numpy as np
import pyqtgraph as pg
from pyqtgraph.widgets import RawImageWidget
from PyQt5 import QtWidgets, QtCore, QtGui
from threading import Thread
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import time


pg.setConfigOptions(imageAxisOrder='row-major')


class imageWidget(RawImageWidget.RawImageWidget, QtWidgets.QWidget):
    ''' Image container. Basically a wrapper for RawImageWidget with a modified mousePressEvent.
    '''
    class Signal(QtCore.QObject):

        mousePressSignal = QtCore.pyqtSignal()

    def __init__(self):
        RawImageWidget.RawImageWidget.__init__(self,scaled=True)
        QtWidgets.QWidget.__init__(self)


        self.clickPosition = None
        self.signal = self.Signal()

    def display(self,image,levels):
        # self.setImage(image)
        self.setImage(image,levels=levels)

    def mousePressEvent(self,event):
        self.clickPosition = event.pos().x(),event.pos().y()
        self.clickPositionRatio = self.clickPosition[0]/self.frameSize().width(), self.clickPosition[1]/self.frameSize().height()
        self.signal.mousePressSignal.emit()

class image(QtWidgets.QLabel):
    ''' Image container. Basically a wrapper for QtWidgets.QLabel with a modified mousePressEvent.
    '''
    class Signal(QtCore.QObject):

        mousePressSignal = QtCore.pyqtSignal()

    def __init__(self,imageData,imgFormat):
        super().__init__()
        self.clickPosition = None
        self.imageData = imageData
        self.w = self.imageData.shape[1]
        self.h = self.imageData.shape[0]
        self.imgFormat = imgFormat
        # image = QtGui.QImage(self.imageData, self.w, self.h, self.imgFormat)
        # pixmap = QtGui.QPixmap.fromImage(image)
        # self.setPixmap(pixmap.scaled(self.w,self.h,QtCore.Qt.KeepAspectRatio))
        self.clickPosition = None
        self.signal = self.Signal()

    def display(self,image,levels):
        try :
            image,alpha = pg.makeARGB(image,levels=levels)
            image = QtGui.QImage(image, image.shape[1], image.shape[0], self.imgFormat)
            pixmap = QtGui.QPixmap.fromImage(image)
            self.setPixmap(pixmap.scaled(self.w, self.h, QtCore.Qt.KeepAspectRatio))
        # self.setPixmap(QtGui.QPixmap.fromImage(image))
        except :
            pass

    def mousePressEvent(self, QMouseEvent):
        self.clickPosition = QMouseEvent.pos().x(),QMouseEvent.pos().y()
        self.signal.mousePressSignal.emit()
#        return self.clickPosition

class imageItem(pg.ImageItem):
    def __init__(self):
        super().__init__()
        self.clickPosition = None

    def mouseClickEvent(self,event):
        self.clickPosition = event.pos().x(), event.pos().y()
        print(self.clickPosition) ## todo: replace with sprite at click position
        return self.clickPosition

class MplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        # super().__init__()
        # Figure().__init__(figsize=(width,height), dpi=dpi)

        self.figure = Figure(figsize=(width, height), dpi=dpi)
        # self.axes = fig.add_subplot(111)
        self.compute_initial_figure()
        FigureCanvas.__init__(self, self.figure)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def compute_initial_figure(self):
        pass


## todo : create new 2D display showing intensity number and more basic qt label based on autoalign
class Display2D(pg.GraphicsWindow):
    '''pg.GraphicsWindow is also a QtWidgets.Widget class
    Display2D class is a window that displays microscope images
    INPUT :
    image_input = 3D array having type [channel,y,x]
    imageMaximums = 1D array containing maximum image intensities to be displayed for image levelling
    imageMinimums = 1D array containing minimum image intensities to be displayed for image levelling

    attributes
    fps : integer - number of frames displayed per second
    simulate : Boolean - to simulate microscope data as noise
    '''

    # ﻿app.processEvents()

    reading = False
    fps = 30.
    simulate = False
    __title = "Microscoper Display 2017"

    class Signal(QtCore.QObject):
        close = QtCore.pyqtSignal()
        update = QtCore.pyqtSignal()

    def __displayThread(self):
        while self.displaying:
            if self.simulate:
                self.simulate_image()
                self.image.setImage(self.imageData*1.5)
            else:
                self.signal.update.emit()
            time.sleep(1. / self.fps)


    ## create additional panel for spectrometer data receiving data at some socket then plot
    def __init__(self, imageInput, intensityPlot=None,
                 intensityIndex=None, imageMaximums=None, imageMinimums=None,
                 app=None, parent=None):
        super().__init__()
        self.setWindowTitle(self.__title)
        self.signal = self.Signal()

        ## CREATE READ AND DISPLAY THREAD
        self.imageData = imageInput
        self.intensities = intensityPlot
        self.intensitiesIndex = intensityIndex

        if imageMaximums is None:
            self.imageMaximums = [1] * len(self.imageData)
        else:
            self.imageMaximums = imageMaximums

        if imageMinimums is None:
            self.imageMinimums = [0] * len(self.imageData)
        else:
            self.imageMinimums = imageMinimums

        self.clickPosition = None
        self.app = app

        self.displaying = False
        self.shown = False
        self.initUI()
        self.setupSignals()

    def set(self, imageInput, intensityPlot=None,
                 intensityIndex=None, imageMaximums=None, imageMinimums=None,
                 app=None, parent=None):

        self.imageData = imageInput
        self.intensities = intensityPlot
        self.intensitiesIndex = intensityIndex
        if imageMaximums is None:
            self.imageMaximums = [1] * len(self.imageData)
        else:
            self.imageMaximums = imageMaximums
        if imageMinimums is None:
            self.imageMinimums = [0] * len(self.imageData)
        else:
            self.imageMinimums = imageMinimums
        self.clickPosition = None
        self.app = app
        # self.signal = self.Signal()
        self.show()
        # self.activateWindow() ## commented out because sometimes crashes


    def start(self):

        self.initUI()
        self.displayThread = Thread(target=self.__displayThread)
        self.displayThread.daemon = False
        self.displaying = True
        self.displayThread.start()

    def initUI(self):

        # self.mainWindow = QtWidgets.QWidget() self.imageData.__len__() * 200
        self.setGeometry(50, 50, self.imageData.__len__() * 300, 400)
        self.scaleWidth = 1
        self.scaleHeight = 1

        self.layout = QtWidgets.QGridLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)

        self.setLayout(self.layout)
        self.imgFormat = QtGui.QImage.Format_ARGB32

        self.w = self.imageData[0].shape[1]
        self.h = self.imageData[0].shape[0]

        screen = QtWidgets.QDesktopWidget()
        if not self.shown:
        # Creates container / widget for images
            self.img_handle = []

            for i in range(0, self.imageData.__len__()):
                img = imageWidget()
                img.signal.mousePressSignal.connect(self.getClickPosition)
                self.img_handle.append(img)
                self.layout.addWidget(img, 0, i, 2, 1)

            # Add intensity plots layout
            self.plots = []
            self.plotWidgets = []
            for i in range(0, self.imageData.__len__()):
                plotWidget = pg.PlotWidget()
                plot = plotWidget.plot()
                self.plotWidgets.append(plotWidget)
                self.plots.append(plot)
                self.layout.addWidget(plotWidget, 2, i, 1, 1)

            # todo : Add intensity values
            self.intensityWidgets = []
            for i in range(0, self.imageData.__len__()):
                intensityLabel = QtWidgets.QLabel()
                intensityLabel.setStyleSheet('color: yellow')
                intensityLabel.setText(f"ASD{i}")
                sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
                sizePolicy.setHorizontalStretch(0)
                sizePolicy.setVerticalStretch(0)
                sizePolicy.setHeightForWidth(intensityLabel.sizePolicy().horizontalStretch())
                intensityLabel.setSizePolicy(sizePolicy)
                self.intensityWidgets.append(intensityLabel)
                self.layout.addWidget(intensityLabel, 1, i, 1, 1)

            self.layout.setRowMinimumHeight(0, 400)
            self.layout.setRowMinimumHeight(1, 0)
            self.layout.setRowMinimumHeight(2, 1)


            self.show()
            self.shown = True

    def setupSignals(self):
        self.signal.update.connect(self.display)

    def display(self):
        for i in range(0, self.imageData.__len__()):
            # Update display
            self.img_handle[i].display(self.imageData[i].T, levels=[self.imageMinimums[i],self.imageMaximums[i]])
            # self.img_handle[i].setImage(self.imageData[i], autoLevels=False)
            if self.intensities is not None:
                try:
                    self.plots[i].setData(y=self.intensities[i], x=self.intensitiesIndex[i])
                except:
                    pass

    def simulate_image(self):
        self.simulate = True
        self.imageData = np.random.rand(200 * 200)
        self.imageData = self.imageData.reshape((200, 200))

    def getClickPosition(self):
        for image in self.img_handle:
            try:
                if image.clickPosition is not None:
                    self.clickPosition = image.clickPosition
                    image.clickPosition = None
                    print(self.clickPosition)
            except:
                pass

    # def resizeEvent(self, QResizeEvent):
    #     for i in range(0, self.imageData.__len__()):
    #         self.img_handle[i].scaleDisplay()

    def setImage(self, image_input):
        self.imageData = image_input


    def setIntensity(self, intensities=None, intensitiesIndex=None):
        self.intensities = intensities
        self.intensitiesIndex = intensitiesIndex

    def stop(self):
        if self.displaying:
            print("Display stopped.")
            self.displaying = False
            # self.displayThread.join()

    def closeEvent(self, event):
        self.stop()
        self.signal.close.emit()
        event.accept()

class ImageLevelsWidget(QtWidgets.QWidget):

    class Signal(QtCore.QObject):
        close = QtCore.pyqtSignal()
        update = QtCore.pyqtSignal()

    class SpinBox(QtWidgets.QSpinBox):
        def __init__(self, parent=None):
            QtWidgets.QSpinBox.__init__(self,parent)

        def updateArrayFunction(self):
            ## Weak ref?
            pass

        def keyPressEvent(self, event):
            super().keyPressEvent(event)
            if event.key() == QtCore.Qt.Key_Return:
                self.updateArrayFunction()
            else :
                pass

    def __init__(self,parent=None,numberOfImages=0,arrayValuesMax=None,arrayValuesMin=None,images=None):
        super().__init__()
        self.parent = parent
        self.exists = True
        self.numberOfSliders = int(numberOfImages)
        self.arrayValuesMax = arrayValuesMax
        self.arrayValuesMin = arrayValuesMin
        if images is not None :self.images = images

        self.setObjectName("DisplayLevels")
        width = 20+60*self.numberOfSliders
        height = 135
        self.resize(width, height)
        self.createLayout()

        self.verticalSlidersMin = []
        self.verticalSlidersMax = []
        self.spinBoxesMin = []
        self.spinBoxesMax = []

        self.createAutoButton()
        for i in range(0,self.numberOfSliders):
            # self.createVerticalSlider(i)
            self.createSpinbox(i)
        self.createActionUpdates()
        self.show()
        self.running = True

        self.signal = self.Signal()
        # passTimeThread = Thread(target=self.passTime)
        # passTimeThread.start()

    def reloadImages(self):
        if self.parent is not None:
            self.setImage(self.parent.ai.imageData)

    def autoLevel(self):
        try :
            self.reloadImages()
            for i,image in enumerate(self.images):
                maximum = image.max()
                minimum = image.min()
                self.arrayValuesMax[i] = maximum
                self.arrayValuesMin[i] = minimum
                # self.verticalSlidersMax[i].setValue(maximum)
                self.spinBoxesMax[i].setValue(maximum)
                self.spinBoxesMin[i].setValue(minimum)
            self.signal.update.emit()
        except :
            print('No images loaded.')

    def createAutoButton(self):
        self.autoButton = QtWidgets.QPushButton('Auto Level',self)
        self.autoButton.resize(100,30)
        self.autoButton.move(10,10)
        self.autoButton.clicked.connect(self.autoLevel)

    def createActionUpdates(self):
        self.updateSpinboxFunctions = []
        self.updateSliderFunctions = []

        for i in range(0,len(self.spinBoxesMax)):
            def arrayValueFunction(i):
                def updateArrayValue():
                    self.arrayValuesMax[i] = self.spinBoxesMax[i].value()
                    self.arrayValuesMin[i] = self.spinBoxesMin[i].value()
                    self.signal.update.emit()
                return updateArrayValue


            updateArrayValueNewFunction = arrayValueFunction(i)

            self.spinBoxesMax[i].updateArrayFunction = updateArrayValueNewFunction
            self.spinBoxesMin[i].updateArrayFunction = updateArrayValueNewFunction
            self.spinBoxesMax[i].valueChanged.connect(lambda: self.signal.update.emit())
            self.spinBoxesMin[i].valueChanged.connect(lambda: self.signal.update.emit())
            #self.spinBoxesMax[i].valueChanged.connect(updateArrayMaxValueNewFunction)
            #self.spinBoxesMin[i].valueChanged.connect(updateArrayMinValueNewFunction)

            # def updateSpinboxFunction(i):
            #     def updateSpinbox():
            #         self.spinBoxesMax[i].setValue(self.verticalSlidersMax[i].value())
            #         self.arrayValues[i] = self.verticalSlidersMax[i].value()
            #     return updateSpinbox
            # updateSpinboxNewFunction = updateSpinboxFunction(i)
            # self.spinBoxesMax[i].valueChanged.connect(updateSliderNewFunction)
            # self.verticalSlidersMax[i].valueChanged.connect(updateSpinboxNewFunction)

            # def updateSliderFunction(i):
            #     def updateSlider():
            #         self.verticalSlidersMax[i].setValue(self.spinBoxesMax[i].value())
            #         self.arrayValues[i] = self.spinBoxesMax[i].value()
            #     return updateSlider

            # updateSliderNewFunction = updateSliderFunction(i)


    def createLayout(self):
        self.verticalLayoutWidget = QtWidgets.QWidget(self)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(10, 50, 60*self.numberOfSliders, 80))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.gridLayout = QtWidgets.QGridLayout(self.verticalLayoutWidget)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")

    def createSpinbox(self,n):
        self.spinBoxesMax.append(self.SpinBox(self.verticalLayoutWidget))#QtWidgets.QSpinBox(self.verticalLayoutWidget))
        self.spinBoxesMax[-1].setMinimumSize(QtCore.QSize(55, 0))
        self.spinBoxesMax[-1].setMinimum(-999999)
        self.spinBoxesMax[-1].setMaximum(999999)
        self.spinBoxesMax[-1].setValue(self.arrayValuesMax[n])
        self.spinBoxesMax[-1].setObjectName("spinBoxMax")
        self.gridLayout.addWidget(self.spinBoxesMax[-1], 0, n, 1, 1)

        self.spinBoxesMin.append(self.SpinBox(self.verticalLayoutWidget))
        self.spinBoxesMin[-1].setMinimumSize(QtCore.QSize(55, 0))
        self.spinBoxesMin[-1].setMinimum(-999999)
        self.spinBoxesMin[-1].setMaximum(999999)
        self.spinBoxesMin[-1].setValue(self.arrayValuesMin[n])
        self.spinBoxesMin[-1].setObjectName("spinBoxMin")
        self.gridLayout.addWidget(self.spinBoxesMin[-1], 1, n, 1, 1)

    def createVerticalSlider(self,n):
        self.verticalSlidersMax.append(QtWidgets.QSlider(self.verticalLayoutWidget))
        self.verticalSlidersMax[-1].setMinimum(1)
        self.verticalSlidersMax[-1].setMaximum(65535)
        self.verticalSlidersMax[-1].setValue(self.arrayValues[n])
        self.verticalSlidersMax[-1].setOrientation(QtCore.Qt.Vertical)
        self.verticalSlidersMax[-1].setObjectName("verticalSlider")
        self.gridLayout.addWidget(self.verticalSlidersMax[-1], 0, n, 1, 1, QtCore.Qt.AlignHCenter)
        # self.verticalSlidersMin.append(QtWidgets.QSlider(self.verticalLayoutWidget))
        # self.verticalSlidersMin[-1].setMaximum(65535)
        # self.verticalSlidersMin[-1].setOrientation(QtCore.Qt.Vertical)
        # self.verticalSlidersMin[-1].setObjectName("verticalSlider")
        # self.gridLayout.addWidget(self.verticalSlidersMin[-1], 0, n, 1, 1, QtCore.Qt.AlignHCenter)

        # self.histoWidget = pg.HistogramLUTWidget(self.verticalLayoutWidget)
        # self.histoWidget.setBackground(None)
        # self.histoWidget.setHistogramRange(0,65535)
        # self.gridLayout.addWidget(self.histoWidget,0,2,1,1,QtCore.Qt.AlignHCenter)

    def closeEvent(self, event):
        self.exists = False
        self.running = False
        self.signal.close.emit()
        event.accept()

    def setImage(self,image):
        self.images = image

class testCanvas(pg.GraphicsWindow):
    def __init__(self):

        super().__init__()
        self.resize(300,600)
        self.move(300,300)
        self.initUI()

        # self.canvas1.figure.add_subplot(111)
        # self.canvas4.figure.add_subplot(121)
        # self.canvas4.figure.add_subplot(122)
        self.show()

    def initUI(self):

        self.layout = QtWidgets.QGridLayout()
        self.layout.setSpacing(10)
        self.plot1 = self.addPlot()
        self.plot1.plot(np.random.random(300))
        # self.plot = pg.PlotWidget(parent=self)
        # pg.plot(np.random.random(300))
        # self.canvas1 = MplCanvas(self)
        # self.canvas2 = MplCanvas(self)
        # self.canvas3 = MplCanvas(self)
        # self.canvas4 = MplCanvas(self)
        # self.layout.addWidget(self.canvas1,0,0,1,1)
        # self.layout.addWidget(self.canvas2,0,1,1,1)
        # self.layout.addWidget(self.canvas3,1,0,1,1)
        # self.layout.addWidget(self.canvas4,2,0,1,2)
        self.setLayout(self.layout)
        self.activateWindow()


if __name__ == '__main__' :
    app = QtWidgets.QApplication([])
    canvas = testCanvas()
    app.exec_()
