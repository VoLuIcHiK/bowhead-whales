from os.path import isfile

from PyQt5.QtWidgets import QMainWindow, QWidget

from qtpure.buttonController import uploadController, uploadControllerSecond
from qtpure.modal_drop import Ui_Form


def dragEnterEvent(event):
    try:
        mime = event.mimeData()
        if len(mime.urls()) > 1:
            return
        else:
            if isfile(mime.urls()[0].toLocalFile()):
                return
            event.acceptProposedAction()
    except:
        return


def dropEventWrapper(main_window, last_window, new_window, new_window_ui):
    def dropEvent(event):
        last_window.setupUi(main_window)

        file_name = event.mimeData().urls()[0].toLocalFile()
        upload = uploadControllerSecond(new_window, new_window_ui)
        main_window.setHidden(True)
        upload(file_name)

    return dropEvent


def dragMoveEventWrapper(main_window: QMainWindow):
    def dragMoveEvent(evt):
        n = QWidget()
        n_x = Ui_Form()
        n_x.setupUi(n)
        main_window.setCentralWidget(n)
        evt.accept()

    return dragMoveEvent


def dragLeaveEventWrapper(main_window: QMainWindow, last_window):
    def dragLeaveEvent(evt):
        last_window.setupUi(main_window)
        evt.accept()

    return dragLeaveEvent
