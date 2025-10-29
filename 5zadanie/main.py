# main.py
import sys
import os
from PyQt5 import QtCore, QtGui, QtWidgets, uic

def resource_path(relative_path):
    """ Получить абсолютный путь к ресурсу, работает и в .exe, и в режиме разработки """
    try:
        # PyInstaller создаёт временную папку _MEIPASS и кладёт туда файлы
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class UFOControl(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        ui_file = resource_path("main2.ui")
        uic.loadUi(ui_file, self)

        img_file = resource_path("UFO.png")
        self.ufo_pixmap = QtGui.QPixmap(img_file)
        if self.ufo_pixmap.isNull():
            raise FileNotFoundError(f"Не удалось загрузить изображение: {img_file}")

        self.ufo_x = self.width() // 2
        self.ufo_y = self.height() // 2
        self.step = 20
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.drawPixmap(self.ufo_x, self.ufo_y, self.ufo_pixmap)

    def keyPressEvent(self, event):
        key = event.key()
        if key == QtCore.Qt.Key_Left:
            self.ufo_x -= self.step
        elif key == QtCore.Qt.Key_Right:
            self.ufo_x += self.step
        elif key == QtCore.Qt.Key_Up:
            self.ufo_y -= self.step
        elif key == QtCore.Qt.Key_Down:
            self.ufo_y += self.step
        else:
            super().keyPressEvent(event)
            return

        w, h = self.width(), self.height()
        uw, uh = self.ufo_pixmap.width(), self.ufo_pixmap.height()

        if self.ufo_x < -uw:
            self.ufo_x = w
        elif self.ufo_x > w:
            self.ufo_x = -uw

        if self.ufo_y < -uh:
            self.ufo_y = h
        elif self.ufo_y > h:
            self.ufo_y = -uh

        self.repaint()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.repaint()

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = UFOControl()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()