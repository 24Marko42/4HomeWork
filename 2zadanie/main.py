import sys
import os
import sqlite3
from datetime import datetime
from PyQt5 import uic
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableWidgetItem, QMessageBox,QDialog, QFormLayout, QLineEdit, QSpinBox, QPushButton, QVBoxLayout, QComboBox)
from PyQt5.QtCore import Qt


class FilmDialog(QDialog):
    def __init__(self, parent=None, film_data=None):
        super().__init__(parent)
        self.setWindowTitle("Фильм")
        self.resize(300, 250)

        # Поля формы
        self.title_edit = QLineEdit()
        self.year_spin = QSpinBox()
        self.year_spin.setRange(1890, datetime.now().year)
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 1000)
        self.genre_combo = QComboBox() 

        # Загружаем жанры из БД
        self.load_genres()

        # Заполняем данные, если редакт
        if film_data:
            self.title_edit.setText(film_data.get("title", ""))
            self.year_spin.setValue(film_data.get("year", 2000))
            self.duration_spin.setValue(film_data.get("duration", 90))
            genre_id = film_data.get("genre", 1)
            # Жанр по ID
            for i in range(self.genre_combo.count()):
                if int(self.genre_combo.itemData(i)) == genre_id:
                    self.genre_combo.setCurrentIndex(i)
                    break

        layout = QFormLayout()
        layout.addRow("Название:", self.title_edit)
        layout.addRow("Год:", self.year_spin)
        layout.addRow("Длительность (мин):", self.duration_spin)
        layout.addRow("Жанр:", self.genre_combo)  

        btn_ok = QPushButton("OK")
        btn_cancel = QPushButton("Отмена")
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)

        btn_layout = QVBoxLayout()
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)
        layout.addRow(btn_layout)

        self.setLayout(layout)

    def load_genres(self):
        """Загружает список жанров из БД и заполняет combo box"""
        try:
            conn = sqlite3.connect("films_db.sqlite")
            cursor = conn.cursor()
            cursor.execute("SELECT id, title FROM genres ORDER BY title")
            genres = cursor.fetchall()
            conn.close()

            self.genre_combo.clear()
            for genre_id, genre_title in genres:
                self.genre_combo.addItem(genre_title, genre_id)  

        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить жанры:\n{e}")
            # Добавим хотя бы дефолтные
            self.genre_combo.addItems(["драма", "фантастика", "комедия"])

    def get_data(self):
        """Возвращает данные фильма, включая ID жанра"""
        return {
            "title": self.title_edit.text().strip(),
            "year": self.year_spin.value(),
            "duration": self.duration_spin.value(),
            "genre": int(self.genre_combo.currentData())  
        }

    def validate(self):
        if not self.title_edit.text().strip():
            QMessageBox.warning(self, "Ошибка", "Название не может быть пустым.")
            return False
        return True


class DBSample(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('main.ui', self)

        # БД
        db_path = "films_db.sqlite"
        if not os.path.exists(db_path):
            self.create_test_db(db_path)
        self.connection = sqlite3.connect(db_path)

        # Добавим кнопки программно
        from PyQt5.QtWidgets import QHBoxLayout, QWidget
        button_layout = QHBoxLayout()

        self.btnAdd = QPushButton("Добавить")
        self.btnEdit = QPushButton("Изменить")
        self.btnDelete = QPushButton("Удалить")

        self.btnAdd.clicked.connect(self.add_film)
        self.btnEdit.clicked.connect(self.edit_film)
        self.btnDelete.clicked.connect(self.delete_film)

        button_layout.addWidget(self.btnAdd)
        button_layout.addWidget(self.btnEdit)
        button_layout.addWidget(self.btnDelete)

        # Кнопки над таблицей
        main_layout = self.centralWidget().layout()
        if main_layout is None:
            widget = QWidget()
            main_layout = QVBoxLayout(widget)
            self.setCentralWidget(widget)
        main_layout.insertLayout(0, button_layout)

        self.load_films()

    def create_test_db(self, path):
        con = sqlite3.connect(path)
        cur = con.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS genres (
            id INTEGER PRIMARY KEY, title TEXT NOT NULL)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS films (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            year INTEGER NOT NULL,
            duration INTEGER NOT NULL,
            genre INTEGER NOT NULL,
            FOREIGN KEY(genre) REFERENCES genres(id))""")
        cur.executemany("INSERT INTO genres VALUES (?, ?)", [(1, "драма"), (2, "фантастика"), (3, "комедия")])
        cur.executemany("INSERT INTO films VALUES (?, ?, ?, ?, ?)",
                        [(1, "Интерстеллар", 2014, 169, 2),
                         (2, "Побег из Шоушенка", 1994, 142, 1)])
        con.commit()
        con.close()

    def load_films(self):
        try:
            cursor = self.connection.cursor()
            # JOIN для получения названия жанра
            query = """
                SELECT films.id, films.title, films.year, films.duration, genres.title AS genre
                FROM films
                JOIN genres ON films.genre = genres.id
                ORDER BY films.id
            """
            cursor.execute(query)
            rows = cursor.fetchall()

            headers = [desc[0] for desc in cursor.description]
            self.tableWidget.setColumnCount(len(headers))
            self.tableWidget.setHorizontalHeaderLabels(headers)
            self.tableWidget.setRowCount(len(rows))

            for i, row in enumerate(rows):
                for j, val in enumerate(row):
                    item = QTableWidgetItem(str(val))
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self.tableWidget.setItem(i, j, item)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Загрузка не удалась:\n{e}")

    def get_selected_film_id(self):
        selected = self.tableWidget.selectedItems()
        if not selected:
            return None
        row = selected[0].row()
        id_item = self.tableWidget.item(row, 0)
        return int(id_item.text()) if id_item else None

    def add_film(self):
        dialog = FilmDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            if not dialog.validate():
                return
            data = dialog.get_data()
            try:
                cur = self.connection.cursor()
                cur.execute(
                    "INSERT INTO films (title, year, duration, genre) VALUES (?, ?, ?, ?)",
                    (data["title"], data["year"], data["duration"], data["genre"])
                )
                self.connection.commit()
                self.load_films()
                QMessageBox.information(self, "Успех", "Фильм добавлен.")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось добавить:\n{e}")

    def edit_film(self):
        film_id = self.get_selected_film_id()
        if film_id is None:
            QMessageBox.warning(self, "Ошибка", "Выберите фильм для редактирования.")
            return

        try:
            cur = self.connection.cursor()
            cur.execute("SELECT title, year, duration, genre FROM films WHERE id = ?", (film_id,))
            row = cur.fetchone()
            if not row:
                raise Exception("Фильм не найден")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить фильм:\n{e}")
            return

        film_data = {"title": row[0], "year": row[1], "duration": row[2], "genre": row[3]}
        dialog = FilmDialog(self, film_data=film_data)
        if dialog.exec_() == QDialog.Accepted:
            if not dialog.validate():
                return
            data = dialog.get_data()
            try:
                cur.execute(
                    "UPDATE films SET title = ?, year = ?, duration = ?, genre = ? WHERE id = ?",
                    (data["title"], data["year"], data["duration"], data["genre"], film_id)
                )
                self.connection.commit()
                self.load_films()
                QMessageBox.information(self, "Успех", "Фильм обновлён.")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось обновить:\n{e}")

    def delete_film(self):
        film_id = self.get_selected_film_id()
        if film_id is None:
            QMessageBox.warning(self, "Ошибка", "Выберите фильм для удаления.")
            return

        reply = QMessageBox.question(
            self, "Подтверждение",
            "Удалить выбранный фильм?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.No:
            return

        try:
            cur = self.connection.cursor()
            cur.execute("DELETE FROM films WHERE id = ?", (film_id,))
            self.connection.commit()
            self.load_films()
            QMessageBox.information(self, "Успех", "Фильм удалён.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось удалить:\n{e}")

    def closeEvent(self, event):
        self.connection.close()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = DBSample()
    ex.show()
    sys.exit(app.exec_())