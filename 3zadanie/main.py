# drawing_app.py
import sys
import random
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from PyQt5.QtGui import QPainter, QBrush, QColor, QPolygon
from PyQt5.QtCore import Qt, QPoint
from PyQt5 import uic

class DrawingWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.shapes = []

    def mousePressEvent(self, event):
        x, y = event.x(), event.y()
        if event.button() == Qt.LeftButton:
            self.add_shape('circle', x, y)
        elif event.button() == Qt.RightButton:
            self.add_shape('square', x, y)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Space:
            pos = self.mapFromGlobal(self.cursor().pos())
            self.add_shape('triangle', pos.x(), pos.y())

    def add_shape(self, shape_type, x, y):
        color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        size = random.randint(10, 50)
        self.shapes.append((shape_type, x, y, size, color))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        for shape_type, x, y, size, (r, g, b) in self.shapes:
            painter.setBrush(QBrush(QColor(r, g, b)))
            painter.setPen(Qt.NoPen)

            if shape_type == 'circle':
                painter.drawEllipse(x - size, y - size, size * 2, size * 2)
            elif shape_type == 'square':
                painter.drawRect(x - size, y - size, size * 2, size * 2)
            elif shape_type == 'triangle':
                points = [
                    QPoint(x, y - size),
                    QPoint(x - size, y + size),
                    QPoint(x + size, y + size)
                ]
                painter.drawPolygon(QPolygon(points))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('main.ui', self)  

        self.drawing_area = DrawingWidget()
        self.drawing_area.setFocusPolicy(Qt.StrongFocus)  

        layout = QVBoxLayout()
        layout.addWidget(self.drawing_area)
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.setWindowTitle("Рисовалка")
        self.resize(800, 600)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())