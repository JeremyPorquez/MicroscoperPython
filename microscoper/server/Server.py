## Updates
## February 19, 2019 : Fixed server reconnection
## October 18, 2017 : serverlet restart function now restarts main server through os.system function v2
## October 17, 2017 : serverlet restart function now restarts main server through os.system function
try:
    from microscoper.MNetwork.Connections import ClientObject
except ImportError:
    from MNetwork.Connections import ClientObject
from multiprocessing.connection import Listener
from ui.server import Ui_ServerUi
from PyQt5 import QtWidgets, QtGui
from threading import Thread
import configparser
import os
import queue
import time


class AuthKey(object):
    key = os.urandom(32)
    key = b"mICROSC0PER"


authKey = AuthKey()


class Server(ClientObject):
    errorPrinted = False

    def __init__(self, address, port, name, parent, verbose=False):
        self.connection = ClientObject(parent=self)
        self.address = address
        self.port = port
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
        self.listener = Listener((self.address, int(self.port)), authkey=authKey.key)
        self.isConnected = True
        self.listenThread = Thread(target=self.listen)
        self.listenThread.daemon = True
        self.listenThread.start()

    def listen(self):
        while True:
            try:
                self.serverConnection = self.listener.accept()  # accept one connection
                print("%s connected" % self.name)
                self.errorPrinted = False
                while self.isConnected:
                    self.command = self.serverConnection.recv()  # Wait to receive something
                    if not self.command:  # Receive nothing? client closed connection,
                        self.serverConnection.close()  # Close the connection and exit loop
                        break
                    if self.verbose: print("from %s : %s" % (self.name, self.command))
                    receiver = self.getReceiver(self.command)
                    command = self.getCommand(self.command)
                    for server in self.parent.servers:  # disseminate command to other apps
                        if self.name == receiver:  # checks whether if self is the appropriate receiver
                            self.commandQueue.put_nowait(self.command)
                            if self.verbose:
                                print("Queueing command message, %s, to %s" % (self.command, receiver))
                            # return 0
                        if server.name == receiver:  # checks whether the other app is the appropriate receiver
                            server.serverConnection.send("self%s" % command)
                            if self.verbose:
                                print("Transmitting message, %s, to %s" % (self.command, receiver))
                            # return 1
            except ConnectionResetError:
                # self.serverConnection.close()
                self.listener.close()
                print(self.name, 'connection lost. Reconnecting..')
                self.startListener()
            except AttributeError as e:
                print("Error in Server.listen(): %s%s : %s" % (receiver, command, e))

            time.sleep(0.1)

    def getReceiver(self, message):
        receiver = message[:message.find(".")]
        return receiver

    def getCommand(self, message):
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
                    try:
                        self.serverConnection.send("%s%s" % ("self", command))
                        commandPassed = True
                    except ConnectionError:
                        print('Connection error with %s' % (self.name))
                if commandPassed: print("Command passed")
            time.sleep(0.1)

    def close(self):
        print("Connection %s closed." % self.name)
        self.isConnected = False

    def stop(self):
        self.close()


class MainServer(object):
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
    ini_file = os.path.join(cwd, 'Server.ini')
    serverScriptsPath = os.path.join(cwd, 'ServerScripts')

    def __checkExists(self):
        if os.name == "nt":
            handle = ctypes.windll.user32.FindWindowW(None, "Microscoper Server 2019")
            if handle != 0:
                ctypes.windll.user32.ShowWindow(handle, 10)
                exit(0)

    def __init__(self):
        self.__checkExists()

        self.loadConfig()
        self.connection = ClientObject(parent=self)
        self.scriptObject = None
        self.executerThread = None
        self.commandQueue = queue.Queue()

        self.mainWindow = QtWidgets.QMainWindow()
        self.ui = Ui_ServerUi()

        self.mainWindow.setWindowIcon((QtGui.QIcon('Gui/server.ico')))
        self.setupUi()
        self.servers = []
        self.startServerConnection()
        self.connection.autoConnect(self.serverPort)

    def setupUi(self):
        self.ui.setupUi(self.mainWindow)
        self.ui.sendButtonWidget.clicked.connect(lambda: self.sendServerMessage(port=int(self.ui.portNumber.toPlainText()),
                                                                                message=self.ui.textWidgetSend.toPlainText(),
                                                                                verbose=False)
                                                 )
        self.ui.portComboBox.currentIndexChanged.connect(self.updateUi)
        self.ui.portNumber.setPlainText(self.configPorts[0][1])
        self.ui.textWidgetSend.setPlainText(self.configMessages[0][1])
        self.ui.portComboBox.addItems([self.configPorts[i][0] for i in range(0, len(self.configPorts))])
        self.ui.action_Quit.triggered.connect(self.quit)
        self.loadScriptButtonWidgets = []
        self.loadScriptButtonWidgets.append(self.ui.loadScriptButtonWidget1)
        self.loadScriptButtonWidgets.append(self.ui.loadScriptButtonWidget2)
        self.loadScriptButtonWidgets.append(self.ui.loadScriptButtonWidget3)
        self.runScriptButtonWidgets = []
        self.runScriptButtonWidgets.append(self.ui.runScriptButtonWidget1)
        self.runScriptButtonWidgets.append(self.ui.runScriptButtonWidget2)
        self.runScriptButtonWidgets.append(self.ui.runScriptButtonWidget3)
        self.loadScriptButtonWidgets[0].clicked.connect(lambda: self.loadScript(index=0))
        self.loadScriptButtonWidgets[1].clicked.connect(lambda: self.loadScript(index=1))
        self.loadScriptButtonWidgets[2].clicked.connect(lambda: self.loadScript(index=2))
        self.runScriptButtonWidgets[0].clicked.connect(lambda: self.runScript(index=0))
        self.runScriptButtonWidgets[1].clicked.connect(lambda: self.runScript(index=1))
        self.runScriptButtonWidgets[2].clicked.connect(lambda: self.runScript(index=2))

        for index, value in enumerate(self.configScripts):
            if value is '':
                value = 'Load script'
            else:
                value = os.path.basename(value)
            self.loadScriptButtonWidgets[index].setText(value)

        self.scriptRunning = [False for i in range(0, 3)]
        self.mainWindow.setWindowTitle("Microscoper Server 2019")
        screen = QtWidgets.QDesktopWidget().screenGeometry()
        widgetSize = QtWidgets.QDesktopWidget().screenGeometry(-1)
        size = self.mainWindow.geometry()

        self.mainWindow.closeEvent = self.closeEvent

        self.mainWindow.move(screen.width() - size.width(), screen.height() - size.height() - 100)
        self.mainWindow.activateWindow()
        self.mainWindow.show()

    def loadScript(self, index=None):
        if index is not None:
            if not os.path.exists(self.serverScriptsPath):
                os.mkdir(self.serverScriptsPath)
            filePath = QtWidgets.QFileDialog.getOpenFileName(self.mainWindow,
                                                             caption="Open Server script",
                                                             directory=os.path.join(self.cwd, 'ServerScripts'),
                                                             filter="*.py")[0]
            fileName = os.path.basename(filePath)
            self.configScripts[index] = filePath
            if fileName is '':  fileName = 'Load Script'
            self.loadScriptButtonWidgets[index].setText(fileName)

    def runScript(self, index=None):
        scriptName = os.path.basename(self.configScripts[str(index)])
        scriptName = scriptName[:scriptName.find('.py')]
        if not self.scriptRunning[index]:
            if scriptName != '':
                package = "ServerScripts"
                imported = getattr(__import__(package, fromlist=[scriptName]), scriptName)
                self.scriptObject = imported.script(parent=self)
                scriptThread = Thread(target=self.scriptObject.start)
                scriptThread.daemon = True
                scriptThread.start()
                self.runScriptButtonWidgets[index].setText('End script')
                self.currentlyRunningScriptIndex = index
        else:
            if self.scriptObject is not None:
                self.scriptObject.stop()
                del self.scriptObject
                self.scriptObject = None
                self.runScriptButtonWidgets[index].setText('Run script')
        self.scriptRunning[index] = not self.scriptRunning[index]

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

        self.servers = []
        ## self.connections is an array contains (port number, server type) of type tuple.

        self.serverAddresses = []
        for name, address in self.configAddresses:
            self.serverAddresses.append((name, address))

        self.serverConnections = []
        for name, port in self.configPorts:
            self.serverConnections.append((name, port))
            if name.lower() == "server":
                self.serverPort = port

        if serverType is None:
            for index, ((name, address), (name2, port)) in enumerate(zip(sorted(self.serverAddresses), sorted(self.serverConnections))):
                if name == name2:
                    self.startServer(address=address, port=int(port), serverType=name)
        else:
            for index, ((name, address), (name2, port)) in enumerate(zip(sorted(self.serverAddresses), sorted(self.serverConnections))):
                # for name, port in self.serverConnections : # loop through to get port number
                if name == name2:
                    if serverType.lower() == name.lower():
                        self.startServer(address=address, port=int(port), serverType=name)

    def startServer(self, address="127.0.0.1", port=None, serverType=None):
        ## Start Listeners
        server = Server(address, port, name=serverType, parent=self, verbose=self.verbose)
        server.autoconnect = True
        self.servers.append(server)

    def getReceiver(self, message):
        receiver = message[:message.find(".")]
        return receiver

    def getCommand(self, message):
        index = message.find("self.")
        if index == -1:
            command = message
        else:
            command = message[index:]
        return command

    def sendServerMessage(self, name=None, port=None, message=None, verbose=True):
        if (name is not None) & (port is None):
            for server in self.servers:
                if name == server.name:
                    port = server.port
        if (message is not None) & (port is not None):
            for server in self.servers:
                if server.port == port:
                    if server.listener.last_accepted is not None:
                        if "self." not in message:
                            command = self.getCommand(message)
                            msg = "self.%s" % command
                            server.serverConnection.send(msg)
                        else:
                            server.serverConnection.send(message)
                        if verbose:
                            print("%s sent as %s" % (message, message))
                    else:
                        print("Port %s not connected" % port)


        else:
            print('Function sendServerMessage(widget) must have argument widget.')

    def stopServerConnection(self):
        for server in self.servers:
            server.close()
        self.ui.startButtonWidget.setEnabled(True)
        self.ui.stopButtonWidget.setEnabled(False)

    def terminateConnections(self):
        for server in self.servers:
            server.close()

    # def xit(self):
    #     self.close()

    def quit(self):
        self.connection.stopClientConnection()
        self.running = False
        self.saveConfig()
        self.mainWindow.close()

    def closeEvent(self, event):
        self.saveConfig()
        self.terminateConnections()

    def defineDefaultSettings(self):
        self.configAddresses = {
            "Server": "127.0.0.1",
            "Microscoper": "127.0.0.1",
            "Spectrometer": " 127.0.0.1",
            "Rotation Stage": "127.0.0.1",
            "Thorlabsdds220": "127.0.0.1",
            "focusController": "127.0.0.1",
            "stagex": "127.0.0.1",
            "stagey": "127.0.0.1",
        }
        self.configPorts = {
            "Server": "10119",
            "Microscoper": "10120",
            "Spectrometer": " 10121",
            "Rotation Stage": "10122",
            "Thorlabsdds220": "10123",
            "focusController": "10124",
            "stagex": "10126",
            "stagey": "10127",
        }
        self.configMessages = {
            "Microscoper": "none",
            "Spectrometer": " none",
            "Rotation Stage": "none",
            "Thorlabsdds220": "none",
            "focusController": "none",
        }
        self.configScripts = [
        ]

    def loadConfig(self):
        config = configparser.ConfigParser()

        def make_default_ini():
            self.defineDefaultSettings()
            config["Addresses"] = {}
            config["Ports"] = {}
            config["Messages"] = {}
            config["Scripts"] = {}
            config["Settings"] = {}
            for key, value in self.configAddresses.items():
                config["Addresses"][str(key)] = str(value)
            for key, value in self.configPorts.items():
                config["Ports"][str(key)] = str(value)
            for key, value in self.configMessages.items():
                config["Messages"][str(key)] = str(value)
            for key, value in self.configSettings.items():
                config["Settings"][str(key)] = str(value)
            with open(self.ini_file, 'w') as configfile:
                config.write(configfile)

        def read_ini():
            self.defineDefaultSettings()
            config.read(self.ini_file)
            self.configAddresses = list(config.items("Addresses"))
            self.configSettings = list(config.items("Settings"))
            self.configPorts = list(config.items("Ports"))
            self.configMessages = list(config.items("Messages"))
            self.configScripts = [list(config.items("Scripts"))[i][1] for i in range(0, len(config.items("Scripts")))]
            self.verbose = bool(int(config["Settings"]["verbose"]))

        try:
            read_ini()
        except:
            make_default_ini()
            read_ini()

    def saveConfig(self):
        self.updateUiVariables()
        config = configparser.ConfigParser()
        config['Addresses'] = {}
        config['Ports'] = {}
        config['Messages'] = {}
        config['Scripts'] = {}
        config['Settings'] = {}
        for key, value in self.configAddresses:
            config['Addresses'][str(key)] = str(value)
        for key, value in self.configPorts:
            config['Ports'][str(key)] = str(value)
        for key, value in self.configMessages:
            config["Messages"][str(key)] = str(value)
        for index, value in enumerate(self.configScripts):
            config["Scripts"][str(index)] = str(value)
        for index, value in self.configSettings:
            config["Settings"][str(index)] = str(value)
        with open(self.ini_file, 'w') as configfile:
            config.write(configfile)

    def updateUi(self):
        index = self.ui.portComboBox.currentIndex()
        self.ui.portNumber.setPlainText(self.configPorts[index][1])
        self.ui.textWidgetSend.setPlainText(self.configMessages[index][1])

    def updateUiVariables(self):
        index = self.ui.portComboBox.currentIndex()
        self.configPorts[index] = self.ui.portComboBox.itemText(index), self.ui.portNumber.toPlainText()
        self.configMessages[index] = self.ui.portComboBox.itemText(index), self.ui.textWidgetSend.toPlainText()

    def loadFilename(self):
        self.filename, self.saveextension = QtWidgets.QFileDialog.getSaveFileName(options=QtWidgets.QFileDialog.DontConfirmOverwrite)


if __name__ == "__main__":
    import ctypes

    myappid = u'microscoperserver'  # arbitrary string
    if os.name == "nt":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    qapp = QtWidgets.QApplication([])
    server = MainServer()
    qapp.exec_()
