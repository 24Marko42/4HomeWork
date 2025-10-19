# results_table.py
import sys
import csv
import re
from PyQt5 import QtWidgets, QtCore, QtGui

CSV_ENCODING = "utf-8"  # если будет ошибка — попробуйте 'cp1251'

class Participant:
    def __init__(self, place, name, login, score):
        self.place = place
        self.name = name
        self.login = login
        try:
            self.score = int(score)
        except:
            # попадаются строки с пустым Score
            self.score = 0
        # парсим школу и класс из логина
        m = re.search(r'sh-[^-\s]+-(\d+)-(\d+)-', self.login)
        if m:
            self.school = m.group(1)
            self.cls = m.group(2)
        else:
            self.school = ''
            self.cls = ''

def load_csv(path):
    participants = []
    with open(path, newline='', encoding=CSV_ENCODING) as f:
        rdr = csv.reader(f)
        for row in rdr:
            if not row: continue
            # формат: place,user_name,login,"1(...)","2(...)","3(...)","4(...)",Score
            # возьмём place,row[1],row[2],row[-1]
            place = row[0]
            name = row[1].strip()
            login = row[2].strip()
            score = row[-1].strip() if len(row) >= 4 else "0"
            participants.append(Participant(place, name, login, score))
    return participants

class ResultsWindow(QtWidgets.QWidget):
    def __init__(self, csv_path):
        super().__init__()
        self.setWindowTitle("Результаты олимпиады")
        self.resize(800, 600)
        layout = QtWidgets.QVBoxLayout(self)

        hl = QtWidgets.QHBoxLayout()
        self.cbSchool = QtWidgets.QComboBox(); self.cbSchool.addItem("Все школы")
        self.cbClass = QtWidgets.QComboBox(); self.cbClass.addItem("Все классы")
        self.btnReset = QtWidgets.QPushButton("Сброс")
        hl.addWidget(QtWidgets.QLabel("Школа:")); hl.addWidget(self.cbSchool)
        hl.addWidget(QtWidgets.QLabel("Класс:")); hl.addWidget(self.cbClass)
        hl.addWidget(self.btnReset)
        layout.addLayout(hl)

        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Логин", "ФИО", "Score"])
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        layout.addWidget(self.table)

        self.participants = load_csv(csv_path)
        self.fill_filters()
        self.cbSchool.currentIndexChanged.connect(self.apply_filters)
        self.cbClass.currentIndexChanged.connect(self.apply_filters)
        self.btnReset.clicked.connect(self.reset_filters)

        self.apply_filters()

    def fill_filters(self):
        schools = sorted({p.school for p in self.participants if p.school})
        classes = sorted({p.cls for p in self.participants if p.cls})
        for s in schools:
            self.cbSchool.addItem(s)
        for c in classes:
            self.cbClass.addItem(c)

    def reset_filters(self):
        self.cbSchool.setCurrentIndex(0)
        self.cbClass.setCurrentIndex(0)
        self.apply_filters()

    def apply_filters(self):
        sel_school = self.cbSchool.currentText()
        sel_class = self.cbClass.currentText()
        def visible(p):
            if sel_school != "Все школы" and p.school != sel_school:
                return False
            if sel_class != "Все классы" and p.cls != sel_class:
                return False
            return True

        filtered = [p for p in self.participants if visible(p)]
        # сортируем по убыванию score для отображения
        filtered.sort(key=lambda x: (-x.score, x.name))

        # определяем топ-3 уникальных значений score
        unique_scores = sorted({p.score for p in filtered}, reverse=True)
        top_scores = unique_scores[:3]  # может быть менее 3
        # цвета: первое место — золотой, второе — серебро, третье — бронза
        color_map = {
            top_scores[0]: QtGui.QColor(255, 223, 0) if len(top_scores) > 0 else None,
        }
        if len(top_scores) > 1:
            color_map[top_scores[1]] = QtGui.QColor(192, 192, 192)
        if len(top_scores) > 2:
            color_map[top_scores[2]] = QtGui.QColor(205, 127, 50)

        self.table.setRowCount(len(filtered))
        for r, p in enumerate(filtered):
            self.table.setItem(r, 0, QtWidgets.QTableWidgetItem(p.login))
            self.table.setItem(r, 1, QtWidgets.QTableWidgetItem(p.name))
            self.table.setItem(r, 2, QtWidgets.QTableWidgetItem(str(p.score)))
            # подсветка строки если в top 3
            if p.score in color_map:
                color = color_map[p.score]
                for c in range(3):
                    item = self.table.item(r, c)
                    if item:
                        item.setBackground(color)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    # укажите путь к скачанному CSV файлу
    path = "results.csv"
    w = ResultsWindow(path)
    w.show()
    sys.exit(app.exec_())
