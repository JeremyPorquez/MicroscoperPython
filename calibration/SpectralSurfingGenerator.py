## Updates:
## October 17 2017 added right click to add data points

from PyQt5 import QtWidgets, QtCore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5 import NavigationToolbar2QT as NavigationToolbar
from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from Gui.SSCalibExtract import Ui_SSCalibExtract
import pandas as pd
import numpy as np
import sys, os

def getMaxValues(data,label=['wavelength','theta','value']):

    maxpositions = data.idxmax(axis=1)
    maxvalues = data.max(axis=1)

    maxpositions = np.array(maxpositions)
    maxvalues = np.array(maxvalues)

    df = pd.DataFrame()
    df[label[0]] = data.index
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
        if (event.key() == QtCore.Qt.Key_Delete) or (event.key() == 16777248):
            self.signal.delete.emit()
        if (event.key() == QtCore.Qt.Key_Return) or (event.key() == QtCore.Qt.Key_Enter):
            self.signal.enter.emit()
        super().keyPressEvent(event)


class MplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

    def __init__(self, parent=None, parentApp=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        fig.subplots_adjust(left=0.15, bottom=0.15, right=0.95, top=0.95, wspace=0, hspace=0)
        self.axes = fig.add_subplot(111)
        self.compute_initial_figure()
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)
        self.parentApp = parentApp
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
                # print(self.x,self.y,self.index)
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

                except:
                    pass

            elif event.button == 3: ## add data point
                theta = event.ydata
                wavenumber = event.xdata
                pumpwavelength = self.parentApp.ui.pumpWavelengthSpinBoxWidget.value()
                pumpwavenumber = 1.e7/pumpwavelength
                stokeswn = pumpwavenumber-wavenumber
                wavelength = 1.e7/stokeswn
                self.indicatorPlot.set_data([[event.xdata],[event.ydata]])
                self.parentApp.maxValues = self.parentApp.maxValues.append(
                    pd.DataFrame([[wavelength, theta, 1, wavenumber]],
                                 columns=['wavelength', 'theta', 'value', 'wavenumber']))
                self.clearIndicatorPlot()
                self.parentApp.plotScatter()
                # self.maxValues['wavenumber'].values, self.maxValues['theta'].values

        # self.mpl_connect('pick_event', onpick1)
        focused_widget = QtWidgets.QApplication.focusWidget()
        if focused_widget is not None:
            focused_widget.clearFocus()
        self.mpl_connect('button_press_event',buttonPress)


## add 45 deg at linear fit towards max freq

class SSCalibExtract(object):

    def __init__(self):
        self.cwd = os.path.dirname(os.path.realpath(__file__))
        self.plots = []
        self.setupUi()
        self.rawdata = None


    def setupUi(self):
        self.mainWindow = CustomMainWindow()
        self.ui = Ui_SSCalibExtract()
        self.ui.setupUi(self.mainWindow)
        self.setupCanvas()
        self.setupButtons()
        self.mainWindow.setWindowTitle("Spectral surfing calibration generator")
        self.mainWindow.show()

    def setupCanvas(self):
        self.canvas = MplCanvas(parentApp=self)
        self.ui.guiCanvas.addWidget(self.canvas)
        self.navi_toolbar = NavigationToolbar(self.canvas, self.mainWindow)
        self.ui.guiCanvas.addWidget(self.navi_toolbar)
        # self.canvasPlot = self.canvas.plot
        self.canvas.compute_initial_figure()
        self.setupCanvasKeyPressEvent()

    def setupCanvasKeyPressEvent(self):
        self.mainWindow.signal.delete.connect(self.deleteDataPoint)
        self.mainWindow.signal.enter.connect(self.evaluatePlot)

    def setupButtons(self):
        self.ui.loadFileButtonWidget.clicked.connect(self.loadFile)
        self.ui.saveFileButtonWidget.clicked.connect(lambda: self.saveFile())
        self.ui.saveFileDefaultButtonWidget.clicked.connect(lambda: self.saveFile(type="default"))
        self.ui.executePushButtonWidget.clicked.connect(self.executeText)
        # self.ui.upperFrequencyCutOffSpinBoxWidget.valueChanged.connect(self.evaluatePlot)

    def loadFile(self):
        absolutePath = QtWidgets.QFileDialog.getOpenFileName(directory=self.cwd)[0]
        if absolutePath != '':
            self.rawdata = pd.read_csv(absolutePath, index_col=0)
            # data = dropNan(data)
            try:
                self.evaluatePlot()
            except:
                print('Not a valid hyperspectral file')

    def saveFile(self,type="absPath"):
        if type == "absPath":
            absolutePath = QtWidgets.QFileDialog.getSaveFileName(directory=self.cwd)[0]
        else:
            absolutePath = os.path.join(self.cwd, 'Calibrations/calibrationSurfing.csv')
        if absolutePath != '':
            saveDf = pd.DataFrame(self.maxValues['theta'].values,index=self.maxValues['wavenumber'],columns=['theta'])
            saveDf.index.name = 'wavenumber'

            try :
                saveDf.to_csv(absolutePath)
                self.ui.statusbar.showMessage('%s saved' % absolutePath)
            except Exception as e:
                print(e)
                self.ui.statusbar.showMessage('%s' % e)


    def executeText(self):
        try:
            exec(self.ui.executeText.text())
        except Exception as e:
            print("Error occured executing text : {0}".format(e))

    def evaluatePlot(self):
        if self.rawdata is not None:
            data = self.rawdata
            lowFrequencyCutOff = self.ui.lowerFrequencyCutOffSpinBoxWidget.value()
            highFrequencyCutOff = self.ui.upperFrequencyCutOffSpinBoxWidget.value()
            data.columns = pd.to_numeric(data.columns)
            data.index = np.round(data.index, 2)
            self.data = data

            pump = self.ui.pumpWavelengthSpinBoxWidget.value()
            lowWavelengthCutOff = 1./(1./pump - lowFrequencyCutOff/1.e7)
            highWavelengthCutOff = 1./(1./pump - highFrequencyCutOff/1.e7)
            croppedData = self.data.loc[lowWavelengthCutOff:highWavelengthCutOff,:]
            self.getMaxValuesOfData(croppedData)
            self.maxValues = self.filterRepeatData(self.maxValues)
            self.maxValues['wavenumber'] = 1.e7 / pump - 1.e7 / self.maxValues['wavelength'] ## add a column wavenumber to maxvalues dataframe
            self.appendMinValuesFiller()
            self.appendMaxValuesFiller()

            self.plotContour()
            self.plotScatter()
            self.setPlotLimits()
        else:
            print('Load data.')

    def getMaxValuesOfData(self,data):
        self.maxValues = getMaxValues(data)
        return self.maxValues

    def filterRepeatData(self,data,column_name='theta'):
        value = data[column_name][0]
        for i in range(1,len(data[column_name])):
            if data[column_name][i] == value:
                data = data.drop([i])
            else:
                value = data[column_name][i]
        return data

    def appendMaxValuesFiller(self,limitWavenumber=5000,increment=100):
        maxWavenumber = self.maxValues.wavenumber.max()
        if maxWavenumber < limitWavenumber:
            pump = self.ui.pumpWavelengthSpinBoxWidget.value()
            pumpfreq = 1.e7/pump
            lastTheta = self.maxValues.theta.max()
            wavenumber = np.arange(maxWavenumber+increment,limitWavenumber,increment)
            wavenumber = pd.DataFrame(wavenumber,columns=['wavenumber'])
            wavelength = 1.e7/(pumpfreq-wavenumber.values)
            wavelength = pd.DataFrame(wavelength,columns=['wavelength'])
            theta = [lastTheta for i in range(len(wavenumber))]
            theta = pd.DataFrame(theta,columns=['theta'])
            value = [0 for i in range(len(wavenumber))]
            value = pd.DataFrame(value,columns=['value'])
            filler = pd.concat([wavelength,theta,value,wavenumber],axis=1)
            self.maxValues = self.maxValues.append(filler,ignore_index=True)

    def appendMinValuesFiller(self):
        pump = self.ui.pumpWavelengthSpinBoxWidget.value()
        pumpfreq = 1.e7 / pump
        firstTheta = self.maxValues.theta[0]
        wavenumber = np.linspace(0,self.ui.lowerFrequencyCutOffSpinBoxWidget.value(),5)
        wavenumber = pd.DataFrame(wavenumber,columns=['wavenumber'])
        wavelength = 1.e7/(pumpfreq-wavenumber.values)
        wavelength = pd.DataFrame(wavelength,columns=['wavelength'])
        theta = [firstTheta for i in range(len(wavenumber))]
        theta = pd.DataFrame(theta,columns=['theta'])
        value = [0 for i in range(len(wavenumber))]
        value = pd.DataFrame(value,columns=['value'])
        filler = pd.concat([wavelength,theta,value,wavenumber],axis=1)
        self.maxValues = self.maxValues.append(filler,ignore_index=True)

    def deleteDataPoint(self):
        if self.canvas.index is not None:
            self.maxValues = self.maxValues[self.maxValues.index != self.canvas.index]
            self.maxValues.reset_index(drop=True, inplace=True)
            #need to reindex dataframe
            self.canvas.clearIndicatorPlot()
            self.plotScatter()

    def plotContour(self):
        # xValues = self.data[self.data.columns[0]].values
        # yValues = self.data[self.data.columns[1]].values
        pump = self.ui.pumpWavelengthSpinBoxWidget.value()
        x, y, z = (1./pump - 1./self.data.index)*1e7, self.data.columns, self.data.transpose().values
        self.x, self.y, self.z = x, y, z

        self.canvasContour = self.canvas.axes.contourf(x,y,z,levels=np.linspace(z.min(),z.max(),100),cmap=plt.cm.jet)
        self.canvas.draw()

    def plotScatter(self):
        self.canvas.plot.set_data(self.maxValues['wavenumber'].values, self.maxValues['theta'].values)
        self.canvas.draw()


    def setPlotLimits(self):
        self.canvas.axes.set_xlim(-100,4000)
        self.canvas.axes.set_ylim(self.y.min(),self.y.max())
        self.canvas.draw()
        pass
        # set_extent([left,right,top,bottom])
        # xValues = self.data[self.data.columns[0]].values
        # yValues = self.data[self.data.columns[1]].values
        # xRange = xValues.max() - xValues.min()
        # yRange = yValues.max() - yValues.min()
        # self.canvasPlot.axes.set_xlabel(r"Wavenumber $cm^{-1}$")
        # self.canvasPlot.axes.set_ylabel(r'Angle $\theta$')
        # self.canvasPlot.axes.set_xlim([xValues.min()-xRange*0.05,xValues.max()+xRange*0.05])
        # self.canvasPlot.axes.set_ylim([yValues.min()-yRange*0.05,yValues.max()+yRange*0.05])

if __name__ == "__main__":
    qApp = QtWidgets.QApplication([])
    app = SSCalibExtract()
    sys.exit(qApp.exec_())