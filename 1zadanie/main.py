import os
import sys
import re
import csv
from PyQt5 import QtWidgets, uic
from PyQt5.QtGui import QColor

class OlympiadViewer(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        # путь до файлов
        script_dir = os.path.dirname(os.path.abspath(__file__))
        ui_path = os.path.join(script_dir, "table.ui")
        csv_path = os.path.join(script_dir, "rez.csv")

        uic.loadUi(ui_path, self)

        self.data = []
        self.schools = set()
        self.classes = set()
        
        self.load_data(csv_path)

        self.schoolComboBox.addItem("Все")
        self.classComboBox.addItem("Все")

        # Сортировка
        sorted_schools = sorted(self.schools, key=int)
        sorted_classes = sorted(self.classes, key=int)

        self.schoolComboBox.addItems(sorted_schools)
        self.classComboBox.addItems(sorted_classes)

        self.schoolComboBox.currentTextChanged.connect(self.apply_filters)
        self.classComboBox.currentTextChanged.connect(self.apply_filters)

        self.apply_filters()

    def load_data(self, filename):
        try:
            with open(filename, newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                headers = next(reader) 
                try:
                    score_index = headers.index("Score")
                except ValueError:
                    print("Ошибка: колонка 'Score' не найдена в CSV.")
                    return

                for row in reader:
                    if len(row) < 5:
                        continue
                    name = row[1]
                    login = row[2]
                    score_str = row[score_index].strip()

                    # Парсинг логина sh-kaluga16-09-11-1
                    match = re.match(r"sh-kaluga16-(\d{2})-(\d{2})-\d+", login)
                    if not match:
                        continue

                    school_str, class_str = match.groups() 
                    try:
                        score = int(score_str) if score_str.isdigit() else 0
                    except:
                        score = 0

                    self.data.append({
                        "login": login,
                        "name": name,
                        "school": school_str,
                        "class": class_str,
                        "score": score
                    })
                    self.schools.add(school_str)
                    self.classes.add(class_str)

        except FileNotFoundError:
            print(f"Файл не найден: {filename}")
        except Exception as e:
            print(f"Ошибка при загрузке данных: {e}")

    def apply_filters(self):
        selected_school = self.schoolComboBox.currentText()
        selected_class = self.classComboBox.currentText()

        filtered = []
        for entry in self.data:
            school_ok = (selected_school == "Все") or (entry["school"] == selected_school)
            class_ok = (selected_class == "Все") or (entry["class"] == selected_class)
            if school_ok and class_ok:
                filtered.append(entry)

        # Сортировка по убыванию баллов
        filtered.sort(key=lambda x: -x["score"])

        # Определение призёров
        if not filtered:
            self.update_table([])
            return

        unique_scores = sorted(set(e["score"] for e in filtered), reverse=True)
        top3_scores = unique_scores[:3]

        display_data = []
        for entry in filtered:
            if entry["score"] in top3_scores:
                rank = top3_scores.index(entry["score"]) + 1
            else:
                rank = None
            display_data.append((entry["login"], entry["name"], entry["score"], rank))

        self.update_table(display_data)

    def update_table(self, display_data):
        table = self.resultTable
        table.clearContents()
        table.setRowCount(len(display_data))
        table.setColumnCount(3)

        for i, (login, name, score, rank) in enumerate(display_data):
            table.setItem(i, 0, QtWidgets.QTableWidgetItem(login))
            table.setItem(i, 1, QtWidgets.QTableWidgetItem(name))
            table.setItem(i, 2, QtWidgets.QTableWidgetItem(str(score)))

            # Цвета за места
            if rank == 1:
                color = QColor(255, 215, 0)      # золото
            elif rank == 2:
                color = QColor(192, 192, 192)    # серебро
            elif rank == 3:
                color = QColor(205, 127, 50)     # бронза
            else:
                color = None

            if color:
                for col in range(3):
                    table.item(i, col).setBackground(color)

        table.resizeColumnsToContents()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = OlympiadViewer()
    window.show()
    sys.exit(app.exec_())