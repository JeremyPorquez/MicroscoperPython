if __name__ == "__main__":
    import ctypes
    from PyQt5 import QtWidgets
    import os
    from Server import MainServer

    myappid = u'microscoperserver'  # arbitrary string
    if os.name == "nt":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    qapp = QtWidgets.QApplication([])
    server = MainServer()
    qapp.exec_()