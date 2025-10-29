import sys
import random
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton

class EscapingButtonWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Убегающая кнопка")
        self.resize(600, 400)

        self.button = QPushButton("Поймай меня!", self)
        self.button.resize(100, 40)
        self.button.move(250, 180)

        self.setMouseTracking(True)

    def mouseMoveEvent(self, event):
        cursor = event.pos()
        btn = self.button.geometry()
        center = btn.center()
        dist = ((cursor.x() - center.x())**2 + (cursor.y() - center.y())**2) ** 0.5

        if dist < 100:
            w, h = self.width(), self.height()
            bw, bh = self.button.width(), self.button.height()
            x = random.randint(0, w - bw)
            y = random.randint(0, h - bh)
            self.button.move(x, y)

        super().mouseMoveEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EscapingButtonWidget()
    window.show()
    sys.exit(app.exec_())