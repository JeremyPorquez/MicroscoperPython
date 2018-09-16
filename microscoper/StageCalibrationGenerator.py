from PyQt5 import QtWidgets, QtCore, QtGui
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationToolbar
from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from Gui.StageCalibration import Ui_StageCalibration
import pandas as pd
import numpy as np
import sys, os
import time
from threading import Thread

def getMaxValues(data,label=['theta','wavelength','value']):

    maxpositions = data.idxmax(axis=0)
    maxvalues = data.max(axis=0)

    maxpositions = np.array(maxpositions)
    maxvalues = np.array(maxvalues)

    df = pd.DataFrame()
    df[label[0]] = data.columns
    df[label[1]] = maxpositions
    df[label[2]] = maxvalues

    return df

def dropNan(data):
    data_copy = data.copy()
    data_copy.index = pd.to_numeric(data_copy.index,errors='coerce')
    data_copy.columns = pd.to_numeric(data_copy.columns,errors='coerce')
    data_copy = data_copy[~np.isnan(data_copy.index)]
    data_copy = data_copy.transpose()
    data_copy = data_copy[~np.isnan(data_copy.index)]
    data_copy = data_copy.transpose()
    return data_copy

class CustomMainWindow(QtWidgets.QMainWindow):
    class Signal(QtCore.QObject):
        delete = QtCore.pyqtSignal()
        enter = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
        self.signal = self.Signal()

    def keyPressEvent(self, event):
        print(event.key())
        if (event.key() == QtCore.Qt.Key_Delete) or (event.key() == 16777248):
            self.signal.delete.emit()
        if event.key() == QtCore.Qt.Key_Enter or event.key() == QtCore.Qt.Key_Return:
            self.signal.enter.emit()

        super().keyPressEvent(event)



class MplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        fig.subplots_adjust(left=0.15, bottom=0.15, right=0.95, top=0.95, wspace=0, hspace=0)
        self.axes = fig.add_subplot(111)
        self.compute_initial_figure()
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self,
                                   QtWidgets.QSizePolicy.Expanding,
                                   QtWidgets.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)
        self.setupMousePressEvent()
        self.index = None
        self.x = None
        self.y = None

    def compute_initial_figure(self):
        self.plot = self.axes.plot([], '.', color='yellow', lw=3,picker=5)[0]
        self.indicatorPlot = self.axes.plot([], 'o', color='yellow', lw=5,picker=0)[0]
        self.fitPlot = self.axes.plot([],color='red',alpha=0.3,lw=2)[0]

    def clearIndicatorPlot(self):
        self.indicatorPlot.set_data([],[])

    def setupMousePressEvent(self):
        def onpick1(event):
            if isinstance(event.artist, Line2D):
                thisline = event.artist
                xdata = thisline.get_xdata()
                ydata = thisline.get_ydata()
                ind = event.ind
                self.x = np.take(xdata, ind)[0]
                self.y = np.take(ydata, ind)[0]
                self.index = abs(ydata - self.y).argmin()
                self.indicatorPlot.set_data([self.x,self.y])
                print(self.x,self.y,self.index)
                self.draw()

        def buttonPress(event):
            if event.button == 1: ## select data
                try :
                    xdata,ydata = self.plot.get_data()
                    xRange = self.axes.get_xlim()[1] - self.axes.get_xlim()[0]
                    yRange = self.axes.get_ylim()[1] - self.axes.get_ylim()[0]
                    xDiff = (xdata - event.xdata)/xRange
                    yDiff = (ydata - event.ydata)/yRange
                    clickDistance = xDiff**2 + yDiff**2
                    self.index = clickDistance.argmin()
                    # print(self.index,xdata[self.index],ydata[self.index])
                    self.indicatorPlot.set_data([xdata[self.index], ydata[self.index]])
                    self.draw()

                    focused_widget = QtWidgets.QApplication.focusWidget()
                    focused_widget.clearFocus()


                except:
                    pass
            # xdata,ydata = self.plot.get_data()
            # xRange = self.axes.get_xlim()[1] - self.axes.get_xlim()[0]
            # yRange = self.axes.get_ylim()[1] - self.axes.get_ylim()[0]
            # xDiff = (xdata - event.xdata)/xRange
            # yDiff = (ydata - event.ydata)/yRange
            # clickDistance = xDiff**2 + yDiff**2
            # if clickDistance.size > 0:
            #     self.index = clickDistance.argmin()
            #     print(self.index,xdata[self.index],ydata[self.index])
            #     self.indicatorPlot.set_data([xdata[self.index], ydata[self.index]])
            #     self.draw()
        # self.mpl_connect('pick_event', onpick1)

        self.mpl_connect('button_press_event',buttonPress)


class SSCalibExtract(object):

    def __init__(self):
        self.cwd = os.path.dirname(os.path.realpath(__file__))
        self.data = None
        self.maxValues = None
        self.plots = []
        self.setupUi()

    def setupUi(self):
        self.mainWindow = CustomMainWindow()
        self.ui = Ui_StageCalibration()
        self.ui.setupUi(self.mainWindow)
        self.setupCanvas()
        self.setupButtons()
        self.mainWindow.setWindowTitle("Stage calibration generator")
        self.mainWindow.show()
        self.mainWindow.activateWindow()

    def setupCanvas(self):
        self.canvas = MplCanvas()
        self.ui.guiCanvas.addWidget(self.canvas)
        self.navi_toolbar = NavigationToolbar(self.canvas, self.mainWindow)
        self.ui.guiCanvas.addWidget(self.navi_toolbar)
        # self.canvasPlot = self.canvas.plot
        self.canvas.compute_initial_figure()
        self.setupCanvasKeyPressEvent()

    def setupCanvasKeyPressEvent(self):
        self.mainWindow.signal.delete.connect(self.deleteDataPoint)
        self.mainWindow.signal.enter.connect(self.replot)

    def setupButtons(self):
        self.ui.loadFileButtonWidget.clicked.connect(self.loadFile)
        self.ui.saveFileButtonWidget.clicked.connect(lambda: self.saveFile())
        self.ui.saveFileDefaultButtonWidget.clicked.connect(lambda: self.saveFile(type="default"))
        self.ui.executePushButtonWidget.clicked.connect(self.executeText)

        # self.ui.lowerStageSpinBoxWidget.valueChanged.connect(self.replot)
        # self.ui.higherStageSpinBoxWidget.valueChanged.connect(self.replot)
        # self.ui.lowWavelengthSpinBoxWidget.valueChanged.connect(self.replot)
        # self.ui.highWavelengthSpinBoxWidget.valueChanged.connect(self.replot)

    def loadFile(self):
        absolutePath = QtWidgets.QFileDialog.getOpenFileName(directory=self.cwd)[0]
        if absolutePath != '':
            data = pd.read_csv(absolutePath, index_col=0)
            # data = dropNan(data)
            data.columns = pd.to_numeric(data.columns)
            data.index = np.round(data.index, 2)
            self.data = data
            self.getMaxValuesOfData()
            self.plotContour(self.data)
            self.plotScatter()
            self.fitPlot()
            self.plotFitLine()
            self.setPlotLimits()

    def saveFile(self,type="absPath"):
        if type == "absPath":
            absolutePath = QtWidgets.QFileDialog.getSaveFileName(directory=self.cwd)[0]
        else:
            absolutePath = os.path.join(self.cwd,'Calibrations/calibrationStage.txt')
        if (self.maxValues is not None) & (absolutePath != ''):
            dirname = os.path.dirname(absolutePath)
            basename = os.path.basename(absolutePath)
            if ".txt" not in absolutePath[absolutePath.find("."):]:
                absolutePath = os.path.join(dirname, basename + ".txt")
            file = open(absolutePath,"w")
            file.write(self.ui.formulaWidget.text())
            file.close()
            self.ui.statusbar.showMessage('%s saved'%absolutePath)


    def executeText(self):
        try:
            exec(self.ui.executeText.text())
        except Exception as e:
            print("Error occured executing text : {0}".format(e))

    def getMaxValuesOfData(self):
        pump = self.ui.pumpWavelengthSpinBoxWidget.value()
        lowWavelengthCutOff = self.ui.lowWavelengthSpinBoxWidget.value()
        highWavelengthCutOff = self.ui.highWavelengthSpinBoxWidget.value()
        lowStageCutOff = self.ui.lowerStageSpinBoxWidget.value()
        highStageCutOff = self.ui.higherStageSpinBoxWidget.value()
        if lowStageCutOff > self.data.columns.max():
            lowStageCutOff = self.data.columns.min()
            self.ui.lowerStageSpinBoxWidget.setValue(lowStageCutOff)
        if highStageCutOff < self.data.columns.min():
            highStageCutOff = self.data.columns.max()
            self.ui.higherStageSpinBoxWidget.setValue(highStageCutOff)
        self.croppedData = self.data.loc[lowWavelengthCutOff:highWavelengthCutOff,lowStageCutOff:highStageCutOff]

        self.maxValues = getMaxValues(self.croppedData,label = ['stage position','wavelength','value'])
        self.maxValues['wavenumber'] = 1.e7/self.maxValues['wavelength'] - 1.e7/pump

    def fitPlot(self):
        try :
            fit_calibration = np.polyfit(self.maxValues['stage position'],self.maxValues['wavenumber'], 2)
            self.fitx = np.linspace(self.data.columns.min(),self.data.columns.max())
            self.fity = np.poly1d(fit_calibration)(self.fitx)
            formulaArray = ['+(%.20f)' % i + '*x' * (2 - idx) for idx, i in enumerate(fit_calibration)]
            formulaString = ''
            for formulaTerm in formulaArray:
                formulaString += formulaTerm
            self.ui.formulaWidget.setText(formulaString)
        except Exception as e:
            print(e)

    def deleteDataPoint(self):
        if self.canvas.index is not None:
            self.maxValues = self.maxValues[self.maxValues.index != self.canvas.index]
            self.maxValues.reset_index(drop=True, inplace=True)
            #need to reindex dataframe
            self.canvas.clearIndicatorPlot()

            # replots scatter and fit
            self.plotScatter()
            self.fitPlot()
            self.plotFitLine()


    def plotContour(self,data):
        # xValues = self.data[self.data.columns[0]].values
        # yValues = self.data[self.data.columns[1]].values
        pump = self.ui.pumpWavelengthSpinBoxWidget.value()

        # if data == None:
        # x, y, z = self.data.columns, (1./self.data.index - 1./pump)*1e7, self.data.values
        # else :
        x, y, z = data.columns, (1./data.index - 1./pump)*1e7, data.values
        self.canvasContour = self.canvas.axes.contourf(x,y,z,levels=np.linspace(z.min(),z.max(),100),cmap=plt.cm.jet)
        self.canvas.draw()

    def plotScatter(self):
        self.canvas.plot.set_data(self.maxValues['stage position'].values, self.maxValues['wavenumber'].values)
        # self.axestwin = self.canvas.axes.twinx()
        # self.axestwin.set_ylim(self.axestwin.get_ylim())
        self.canvas.draw()

        ## todo : add secondary y axis : twinx() to show wavelength? or show in status bar

    def plotFitLine(self):
        self.canvas.fitPlot.set_data(self.fitx,self.fity)
        self.canvas.draw()

    def setPlotLimits(self):
        self.canvas.axes.set_xlim(self.data.columns.min(),self.data.columns.max())
        self.canvas.axes.set_ylim(-100, 4000)
        self.canvas.draw()
        # set_extent([left,right,top,bottom])
        # xValues = self.data[self.data.columns[0]].values
        # yValues = self.data[self.data.columns[1]].values
        # xRange = xValues.max() - xValues.min()
        # yRange = yValues.max() - yValues.min()
        # self.canvasPlot.axes.set_xlabel(r"Wavenumber $cm^{-1}$")
        # self.canvasPlot.axes.set_ylabel(r'Angle $\theta$')
        # self.canvasPlot.axes.set_xlim([xValues.min()-xRange*0.05,xValues.max()+xRange*0.05])
        # self.canvasPlot.axes.set_ylim([yValues.min()-yRange*0.05,yValues.max()+yRange*0.05])

    def replot(self):
        try :
            self.getMaxValuesOfData()
            self.fitPlot()
            self.plotScatter()
            self.plotFitLine()
            # self.plotContour(self.croppedData)
            try:
                Thread(target=self.plotContour,args=(self.croppedData,)).start()
            except:
                pass
        except Exception as e:
            print(e)
        # self.setPlotLimits()

if __name__ == "__main__":
    qApp = QtWidgets.QApplication([])
    app = SSCalibExtract()
    sys.exit(qApp.exec_())