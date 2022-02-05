if __name__ == "__main__":
    import ctypes
    from PyQt5 import QtWidgets
    import os
    from StellarN import Spectrometer

    myappid = u'focusController'
    if os.name == "nt":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    qapp = QtWidgets.QApplication([])
    app = Spectrometer()
    qapp.exec()
