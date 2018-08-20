## Updates
## October 18, 2017 : serverlet restart function now restarts main server through os.system function v2
## October 17, 2017 : serverlet restart function now restarts main server through os.system function

import socket

from Network.Connections import clientObject
from multiprocessing.connection import Listener
from Gui.Server_gui import Ui_ServerGui
from PyQt5 import QtWidgets, QtGui
from threading import Thread
import configparser
import os
import queue
import time
import sys


class AuthKey(object):
    key = os.urandom(32)
    key = b"mICROSC0PER"

authKey = AuthKey()

class emptyObject(object):
    def __init__(self):
        pass

    def start(self):
        pass

class Server(clientObject):
    def __init__(self,address,name,parent,verbose=True):
        self.connection = clientObject(parent=self)
        self.address = address
        self.name = name
        self.parent = parent
        self.verbose = verbose
        self.autoconnect = False
        self.serverConnection = None

        self.commandQueue = queue.Queue()
        self.startListener()
        self.executerThread = Thread(target=self.executer)
        self.executerThread.daemon = True
        self.executerThread.start()



    def startListener(self):
        self.listener = Listener(self.address, authkey=authKey.key)
        self.isConnected = True
        self.listenThread = Thread(target=self.listen)
        self.listenThread.daemon = True
        self.listenThread.start()

    def listen(self):
        try :
            self.serverConnection = self.listener.accept()
            print("%s connected"%self.name)
            while self.isConnected:
                try:

                    # receive command from connection
                    self.command = self.serverConnection.recv()
                    print(self.command)

                    # disseminate to other servers
                    receiver = self.getReceiver(self.command)
                    command = self.getCommand(self.command)
                    for server in self.parent.servers:
                        # if the receiver is self then queue the command for execution
                        if self.name == receiver:
                            self.commandQueue.put_nowait(self.command)
                            if self.verbose:
                                print("Queueing command message, %s, to %s"%(self.command,receiver))
                            break
                        # if the server's name is that of the receiver, send the command to that server
                        if server.name == receiver :
                            server.serverConnection.send("self%s"%command)
                            if self.verbose:
                                print("Transmitting message, %s, to %s"%(self.command,receiver))
                except ConnectionResetError:
                    if self.autoconnect:
                        reconnectStatus = "Trying to reconnect."
                        self.restart()
                    else:
                        reconnectStatus = ""
                    self.isConnected = False
                    print('Connection with %s has been lost. %s' % (self.name,reconnectStatus))
                except AttributeError as e:
                    print(e)
        except ConnectionAbortedError:
            print('Connection with %s aborted.'%self.name)
        except OSError:
            #[WinError 10038] An operation was attempted on something that is not a socket')
            #Socket closed even before connecting
            pass
        time.sleep(0.1)


    def restart(self):
        self.close()

        for server in self.parent.servers:
            if server.name == "server":
                parentcwd = self.parent.cwd
                server.serverConnection.send("self.xit()")
                os.system('"' + os.path.join(parentcwd, "Server.bat") + '"')

        # try :
        #     self.serverConnection.close()
        # except Exception as e:
        #     print(e)
        # self.listener.close()
        # self.startListener()


    def getReceiver(self,message):
        receiver = message[:message.find(".")]
        return receiver

    def getCommand(self,message):
        command = message[message.find("."):]
        return command

    def executer(self):
        while self.isConnected:
            if not self.commandQueue.empty():
                rawCommand = self.commandQueue.get_nowait()
                print(rawCommand)
                receiver = rawCommand[:rawCommand.find(".")]
                command = rawCommand[rawCommand.find("."):]
                commandPassed = False
                # Filter commands such that it is directed to this serverlet
                if receiver.lower() == self.name.lower():
                    try :
                        self.serverConnection.send("%s%s"%("self",command))
                        commandPassed = True
                    except ConnectionError:
                        print('Connection error with %s'%(self.name))
                if commandPassed: print("Command passed")
            time.sleep(0.1)

    def close(self):
        print("Connection %s closed."%self.name)
        self.isConnected = False

        # self.listener.close()
        # self.listener._listener._socket.close()
        # self.listener._listener._socket.shutdown(socket.SHUT_RDWR)
        # self.listener.shutdown()

    def stop(self):
        self.close()




class MainServer(QtWidgets.QMainWindow,Ui_ServerGui):
    '''
    Starts server which sends and listens to data at certain ports.
    Automatically connects to local address at 127.0.0.1

    The server also creates a client for itself.

    The main function is
        startServerConnection
            Creates listeners at various ports.
            Also starts the secondary main function --> startExecuter
            startServerConnection creates
            Server.serverConnections : tuple of (port, serverType)
                serverType is a string to assist in server identification for filtering and sending commands

        startExecuter
            Filters and executes received data from servers
    '''
    n = 1
    cwd = os.path.dirname(os.path.realpath(__file__))
    ini_file = os.path.join(cwd,'Server.ini')
    serverScriptsPath = os.path.join(cwd, 'ServerScripts')

    def __checkExists(self):
        handle = ctypes.windll.user32.FindWindowW(None, "Microscoper Server 2017")
        if handle != 0:
            ctypes.windll.user32.ShowWindow(handle, 10)
            exit(0)

    def __init__(self, address = "127.0.0.1", connectionPort = 10125):
        # self.listener = None
        self.__checkExists()

        self.connection = clientObject(parent=self)
        self.scriptsPaths = []
        self.scriptObject = None
        self.executerThread = None
        self.commandQueue = queue.Queue()

        QtWidgets.QMainWindow.__init__(self)
        Ui_ServerGui.__init__(self)
        self.setWindowIcon((QtGui.QIcon('Gui/server.ico')))
        # self.connection = clientObject(parent=self)
        self.setupUi()
        self.loadDefaults()
        self.servers = []
        self.startServerConnection()
        self.connection.autoConnect(connectionPort)
        # self.autoConnect(connectionPort)




    def setupUi(self):
        super().setupUi(self)
        self.startButtonWidget.clicked.connect(lambda: self.startServerConnection())
        self.actionStart.triggered.connect(self.startServerConnection)
        self.stopButtonWidget.clicked.connect(self.stopServerConnection)
        self.actionStop.triggered.connect(self.stopServerConnection)
        self.stopButtonWidget.setEnabled(False)
        self.mainSendButtonWidget.clicked.connect(lambda: self.sendServerMessage(self.mainPortTextWidgetSend))
        self.spectrometerSendButtonWidget.clicked.connect(lambda: self.sendServerMessage(self.spectrometerPortTextWidgetSend))
        self.rotationStageSendButtonWidget.clicked.connect(lambda: self.sendServerMessage(self.rotationStageTextWidgetSend))
        self.extraPortSendButtonWidget.clicked.connect((lambda: self.sendServerMessage(self.extraPortTextWidgetSend)))
        self.loadScriptButtonWidgets = []
        self.loadScriptButtonWidgets.append(self.loadScriptButtonWidget1)
        self.loadScriptButtonWidgets.append(self.loadScriptButtonWidget2)
        self.loadScriptButtonWidgets.append(self.loadScriptButtonWidget3)
        self.runScriptButtonWidgets = []
        self.runScriptButtonWidgets.append(self.runScriptButtonWidget1)
        self.runScriptButtonWidgets.append(self.runScriptButtonWidget2)
        self.runScriptButtonWidgets.append(self.runScriptButtonWidget3)
        # for i in range(0,len(self.loadScriptButtonWidgets)):
        #     self.loadScriptButtonWidgets[i].clicked.connect(lambda: self.loadScript(index=i))
        # for i in range(0,len(self.runScriptButtonWidgets)):
        #     self.runScriptButtonWidgets[i].clicked.connect(lambda: self.runScript(index = i))
        self.loadScriptButtonWidgets[0].clicked.connect(lambda: self.loadScript(index=0))
        self.loadScriptButtonWidgets[1].clicked.connect(lambda: self.loadScript(index=1))
        self.loadScriptButtonWidgets[2].clicked.connect(lambda: self.loadScript(index=2))
        self.runScriptButtonWidgets[0].clicked.connect(lambda: self.runScript(index=0))
        self.runScriptButtonWidgets[1].clicked.connect(lambda: self.runScript(index=1))
        self.runScriptButtonWidgets[2].clicked.connect(lambda: self.runScript(index=2))
        self.scriptRunning = [False for i in range(0,3)]
        self.setWindowTitle("Microscoper Server 2017")
        self.show()
        screen = QtWidgets.QDesktopWidget().screenGeometry()
        widgetSize = QtWidgets.QDesktopWidget().screenGeometry(-1)
        size = self.geometry()

        self.move(screen.width()-self.size().width(), screen.height() - size.height() - 100)
        self.activateWindow()


    def loadScript(self, index = None):
        if index is not None:
            if not os.path.exists(self.serverScriptsPath):
                os.mkdir(self.serverScriptsPath)
            filePath = QtWidgets.QFileDialog.getOpenFileName(self,
                                                             caption = "Open Server script",
                                                             directory = os.path.join(self.cwd,'ServerScripts'),
                                                             filter = '*.py')[0]
            fileName = os.path.basename(filePath)
            self.scriptsPaths[index] = filePath
            if fileName is '':  fileName = 'Load Script'
            self.loadScriptButtonWidgets[index].setText(fileName)

    def runScript(self, index = None):
        scriptName = os.path.basename(self.scriptsPaths[index])
        scriptName = scriptName[:scriptName.find('.py')]
        if not self.scriptRunning[index] :
            if scriptName != '' :
                # scriptObject = emptyObject()
                # from ServerScripts import script
                package = "ServerScripts"
                imported = getattr(__import__(package, fromlist=[scriptName]), scriptName)
                self.scriptObject = imported.script(parent=self)
                scriptThread = Thread(target=self.scriptObject.start)
                scriptThread.daemon = True
                scriptThread.start()
                self.runScriptButtonWidgets[index].setText('End script')
                self.currentlyRunningScriptIndex = index
        else :
            if self.scriptObject is not None:
                self.scriptObject.stop()
                del self.scriptObject
                self.scriptObject = None
                self.runScriptButtonWidgets[index].setText('Run script')
        self.scriptRunning[index] = not self.scriptRunning[index]


        # exec('from ServerScripts import %s' % script)
        # exec('scriptObject = %s.script(self)' % script)
        # exec('scriptObject.start()')
        # exec('script.start()')

    def endScript(self):
        index = self.currentlyRunningScriptIndex
        if self.scriptObject is not None:
            self.scriptObject.stop()
            del self.scriptObject
            self.scriptObject = None
            self.runScriptButtonWidgets[index].setText('Run script')
        self.scriptRunning[index] = False


    def startServerConnection(self, serverType=None):
        '''
        Initiates startServer function which creates the different listeners at the different ports which are :
            1. mainPort
            2. spectrometerPort
            3. rotationPort
        if serverType == None :
            The function starts the server connection at all ports, else only starts at the serverType.
        '''
        localAddress = self.localAddressTextWidget.toPlainText()
        self.mainPort = int(self.mainPortTextWidget.toPlainText())
        self.spectrometerPort = int(self.spectrometerPortTextWidget.toPlainText())
        self.rotationPort = int(self.rotationStageTextWidget.toPlainText())
        self.extraPort = int(self.extraPortTextWidget.toPlainText())
        self.serverPort = 10125

        self.servers = []
        ## self.connections is an array contains (port number, server type) of type tuple.

        self.serverConnections = [(self.mainPort, "main"),
                            (self.spectrometerPort, "spectrometer"),
                            (self.rotationPort, "zaber"),
                            (self.serverPort, "server"),
                            (self.extraPort, "extra")]

        if serverType is None :
            for port, serverType_ in self.serverConnections :
                self.startServer(address=localAddress, connectionPort=port, serverType=serverType_)
        else :
            for port, serverType_ in self.serverConnections : # loop through to get port number
                if serverType.lower() == serverType_.lower():
                    self.startServer(address=localAddress, connectionPort=port, serverType=serverType_)

        ## disable start button
        self.startButtonWidget.setEnabled(False)
        self.stopButtonWidget.setEnabled(False)
        # self.stopButtonWidget.setEnabled(True) #while not fixed, disable this


    def startServer(self, address="127.0.0.1", connectionPort=None, serverType=None):
        address = (address,int(connectionPort))
        ## Start Listeners
        server = Server(address,name=serverType,parent=self,verbose=False)
        server.autoconnect = True
        self.servers.append(server)
        # listener = Listener(address, authkey=b"mICROSC0PER")

        # serverConnection = None
        # self.listeners.append([listener,serverConnection,serverType])

        # print('%s waiting for connection at %s'%(serverType,address))
        # self.isConnected = True
        ## A listener has a self identifier which is the server type
        # listenThread = Thread(target=self.listen, args=(serverType,))
        # listenThread.daemon = True
        # listenThread.start()

    def getReceiver(self,message):
        receiver = message[:message.find(".")]
        return receiver

    def getCommand(self,message):
        command = message[message.find("."):]
        return command

    def sendServerMessage(self,widget=None,verbose=True):
        if widget is not None:
            raw_message = widget.toPlainText()
            receiver = self.getReceiver(raw_message)
            command = self.getCommand(raw_message)
            for server in self.servers:
                if server.name == receiver:
                    if "self" not in raw_message[:4]:
                        msg = "self%s"%command
                        server.serverConnection.send(msg)
                    else:
                        server.serverConnection.send(raw_message)
                    if verbose:
                        print("%s sent as %s"%(raw_message,msg))
        else:
            print('Function sendServerMessage(widget) must have argument widget.')

    def stopServerConnection(self):
        for server in self.servers:
            server.close()
        self.startButtonWidget.setEnabled(True)
        self.stopButtonWidget.setEnabled(False)

    def terminateConnections(self):
        for server in self.servers:
            server.close()

    def xit(self):
        self.close()

    def closeEvent(self, event):
        self.saveDefaults()
        super().closeEvent(event)
        self.terminateConnections()

    def loadDefaults(self):

        config = configparser.ConfigParser()

        def make_default_ini():
            config['Address'] = {}
            config['Address']['Local'] = '127.0.0.1'
            config['Ports'] = {}
            config['Ports']['Main'] = '10120'
            config['Ports']['Spectrometer'] = '10121'
            config['Ports']['Rotation Stage'] = '10122'
            config['Ports']['Extra Port'] = '10123'
            config['Message'] = {}
            config['Message']['Main'] = ''
            config['Message']['Spectrometer'] = ''
            config['Message']['Rotation Stage'] = ''
            config['Scripts'] = {}
            config['Scripts']['1'] = ''
            config['Scripts']['2'] = ''

            with open(self.ini_file, 'w') as configfile:
                config.write(configfile)

        def read_ini():
            config.read(self.ini_file)
            self.localAddressTextWidget.setPlainText(config['Address']['Local'])
            self.mainPortTextWidget.setPlainText(config['Ports']['Main'])
            self.spectrometerPortTextWidget.setPlainText(config['Ports']['Spectrometer'])
            self.rotationStageTextWidget.setPlainText(config['Ports']['Rotation Stage'])
            self.extraPortTextWidget.setPlainText(config['Ports']['Extra Port'])
            self.mainPortTextWidgetSend.setPlainText(config['Message']['Main'])
            self.spectrometerPortTextWidgetSend.setPlainText(config['Message']['Spectrometer'])
            self.rotationStageTextWidgetSend.setPlainText(config['Message']['Rotation Stage'])
            self.extraPortTextWidgetSend.setPlainText(config['Message']['Extra Port'])
            self.scriptsPaths = []
            self.scriptsPaths.append(config['Scripts']['1'])
            self.scriptsPaths.append(config['Scripts']['2'])
            self.scriptsPaths.append(config['Scripts']['3'])
            for index, sectionItem in enumerate(config.items('Scripts')):
                option, value = sectionItem
                try :
                    if value is '': value = 'Load script'
                    else : value = os.path.basename(value)
                    self.loadScriptButtonWidgets[index].setText(value)
                except :
                    print('Load script button widget %i does not exist'%index)

        try:
            read_ini()
        except:
            make_default_ini()
            read_ini()




    def saveDefaults(self):
        config = configparser.ConfigParser()

        config['Address'] = {}
        config['Address']['Local'] = self.localAddressTextWidget.toPlainText()
        config['Ports'] = {}
        config['Ports']['Main'] = self.mainPortTextWidget.toPlainText()
        config['Ports']['Spectrometer'] = self.spectrometerPortTextWidget.toPlainText()
        config['Ports']['Rotation Stage'] = self.rotationStageTextWidget.toPlainText()
        config['Ports']['Extra Port'] = self.extraPortTextWidget.toPlainText()
        config['Message'] = {}
        config['Message']['Main'] = self.mainPortTextWidgetSend.toPlainText()
        config['Message']['Spectrometer'] = self.spectrometerPortTextWidgetSend.toPlainText()
        config['Message']['Rotation Stage'] = self.rotationStageTextWidgetSend.toPlainText()
        config['Message']['Extra Port'] = self.extraPortTextWidgetSend.toPlainText()
        config['Scripts'] = {}
        config['Scripts']['1'] = self.scriptsPaths[0]
        config['Scripts']['2'] = self.scriptsPaths[1]
        config['Scripts']['3'] = self.scriptsPaths[2]

        with open(self.ini_file, 'w') as configfile:
            config.write(configfile)

    def loadFilename(self):
        self.filename, self.saveextension = QtWidgets.QFileDialog.getSaveFileName(options=QtWidgets.QFileDialog.DontConfirmOverwrite)


if __name__ == "__main__":
    import ctypes
    myappid = u'microscoperserver'  # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    qapp = QtWidgets.QApplication([])
    server = MainServer()
    qapp.exec_()
