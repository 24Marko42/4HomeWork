# main.py
import sys
import os
import sqlite3
import hashlib
import secrets
import binascii
import shutil
import uuid
from pathlib import Path

from PyQt5 import uic
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTableWidgetItem, QMessageBox, QPushButton,
    QDialog, QFileDialog, QWidget, QHBoxLayout
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PIL import Image, ImageDraw, ImageFont

# Config 
DB_FILE = "library.db"
IMAGES_DIR = "images"
PLACEHOLDER = "placeholder.png"

def resource_path(rel):
    """Support PyInstaller _MEIPASS and normal mode."""
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.abspath('.')
    return os.path.join(base, rel)

def get_conn():
    return sqlite3.connect(resource_path(DB_FILE))

def hash_password(password, salt_hex=None, iterations=100_000):
    if salt_hex is None:
        salt = secrets.token_bytes(16)
    else:
        salt = binascii.unhexlify(salt_hex)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
    return binascii.hexlify(dk).decode('ascii'), binascii.hexlify(salt).decode('ascii')

def ensure_storage():
    Path(resource_path(IMAGES_DIR)).mkdir(parents=True, exist_ok=True)
    ph = resource_path(os.path.join(IMAGES_DIR, PLACEHOLDER))
    if not os.path.exists(ph):
        try:
            img = Image.new('RGBA', (200, 280), (230, 230, 230, 255))
            d = ImageDraw.Draw(img)
            txt = "No Image"
            try:
                f = ImageFont.load_default()
            except:
                f = None
            try:
                bbox = d.textbbox((0, 0), txt, font=f)
                w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
            except AttributeError:
                try:
                    w, h = d.textsize(txt, font=f)
                except Exception:
                    w, h = 100, 20
            d.text(((200 - w) / 2, (280 - h) / 2), txt, fill=(100, 100, 100), font=f)
            img.save(ph)
        except Exception as e:
            print("Placeholder create error:", e)

def init_db():
    conn = get_conn(); cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        pwd_hash TEXT NOT NULL,
        salt TEXT NOT NULL
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS genres (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL UNIQUE
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        year INTEGER,
        genre INTEGER,
        image_path TEXT,
        FOREIGN KEY(genre) REFERENCES genres(id)
    )""")
    cur.execute("SELECT COUNT(*) FROM genres"); if_none = cur.fetchone()[0]
    if if_none == 0:
        cur.executemany("INSERT INTO genres (title) VALUES (?)", [("драма",), ("фантастика",), ("комедия",)])
    cur.execute("SELECT COUNT(*) FROM books"); bcnt = cur.fetchone()[0]
    if bcnt == 0:
        cur.execute("INSERT INTO books (title, author, year, genre, image_path) VALUES (?, ?, ?, ?, ?)",
                    ("Пример книги", "Автор Примеров", 2020, 1, None))
    conn.commit(); conn.close()

# ---------- Auth Dialog ----------
class AuthDialog(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi(resource_path("auth.ui"), self)
        self.login_btn.clicked.connect(self.try_login)
        self.register_btn.clicked.connect(self.try_register)
        self.user_id = None

    def try_login(self):
        username = self.login_edit.text().strip()
        password = self.pwd_edit.text()
        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Введите логин и пароль")
            return
        conn = get_conn(); cur = conn.cursor()
        cur.execute("SELECT id, pwd_hash, salt FROM users WHERE username = ?", (username,))
        row = cur.fetchone(); conn.close()
        if not row:
            QMessageBox.warning(self, "Ошибка", "Пользователь не найден")
            return
        uid, db_hash, db_salt = row
        calc, _ = hash_password(password, db_salt)
        if calc == db_hash:
            self.user_id = uid
            self.accept()
        else:
            QMessageBox.warning(self, "Ошибка", "Неверный пароль")

    def try_register(self):
        username = self.login_edit.text().strip()
        password = self.pwd_edit.text()
        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Введите логин и пароль")
            return
        conn = get_conn(); cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cur.fetchone():
            QMessageBox.warning(self, "Ошибка", "Логин уже занят")
            conn.close(); return
        pwd_hash, salt = hash_password(password)
        cur.execute("INSERT INTO users (username, pwd_hash, salt) VALUES (?, ?, ?)", (username, pwd_hash, salt))
        conn.commit(); conn.close()
        QMessageBox.information(self, "OK", "Пользователь создан. Войдите.")

# как FilmDialog 
class BookDialog(QDialog):
    def __init__(self, parent=None, book_data=None):
        super().__init__(parent)
        uic.loadUi(resource_path("book.ui"), self)
        self.book = book_data
        self.selected_file = None
        self.choose_btn.clicked.connect(self.choose_image)
        self.ok_btn.clicked.connect(self.on_ok)
        self.cancel_btn.clicked.connect(self.reject)
        self.load_genres()
        if book_data:
            if isinstance(book_data, dict):
                self.title_edit.setText(book_data.get("title",""))
                self.author_edit.setText(book_data.get("author",""))
                self.year_spin.setValue(book_data.get("year", 2000))
                gid = book_data.get("genre")
            else:
                self.title_edit.setText(book_data[1])
                self.author_edit.setText(book_data[2])
                self.year_spin.setValue(book_data[3] or 2000)
                gid = book_data[4]
                if book_data[5]:
                    self.image_name_label.setText(str(book_data[5]))
                else:
                    self.image_name_label.setText("(не выбрано)")
            if gid:
                for i in range(self.genre_combo.count()):
                    if int(self.genre_combo.itemData(i)) == int(gid):
                        self.genre_combo.setCurrentIndex(i)
                        break

    def load_genres(self):
        try:
            conn = get_conn(); cur = conn.cursor()
            cur.execute("SELECT id, title FROM genres ORDER BY title")
            rows = cur.fetchall(); conn.close()
            self.genre_combo.clear()
            for rid, title in rows:
                self.genre_combo.addItem(title, rid)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить жанры:\n{e}")
            self.genre_combo.addItems(["драма","фантастика","комедия"])

    def choose_image(self):
        f, _ = QFileDialog.getOpenFileName(self, "Выберите изображение", os.path.abspath("."), "Images (*.png *.jpg *.jpeg *.bmp)")
        if f:
            self.selected_file = f
            self.image_name_label.setText(os.path.basename(f))

    def on_ok(self):
        title = self.title_edit.text().strip()
        author = self.author_edit.text().strip()
        year = self.year_spin.value()
        gid = self.genre_combo.currentData()
        if not title or not author:
            QMessageBox.warning(self, "Ошибка", "Название и автор обязательны")
            return
        image_rel = None
        if self.selected_file:
            ext = os.path.splitext(self.selected_file)[1]
            newname = f"{uuid.uuid4().hex}{ext}"
            dst = resource_path(os.path.join(IMAGES_DIR, newname))
            try:
                shutil.copy2(self.selected_file, dst)
                image_rel = os.path.join(IMAGES_DIR, newname)
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить изображение: {e}")
                return
        else:
            if self.book and isinstance(self.book, tuple):
                image_rel = self.book[5]
        self.result = {"title": title, "author": author, "year": year, "genre": gid, "image_path": image_rel}
        self.accept()

class Catalog(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(resource_path("main2.ui"), self)
        ensure_storage()
        init_db()

        self.conn = get_conn()

        self.btnAdd = QPushButton("Добавить")
        self.btnEdit = QPushButton("Изменить")
        self.btnDelete = QPushButton("Удалить")
        self.btnAdd.clicked.connect(self.add_book)
        self.btnEdit.clicked.connect(self.edit_book)
        self.btnDelete.clicked.connect(self.delete_book)

        bl = QHBoxLayout()
        bl.addWidget(self.btnAdd)
        bl.addWidget(self.btnEdit)
        bl.addWidget(self.btnDelete)
        container = QWidget()
        container.setLayout(bl)
        main_layout = self.centralWidget().layout()
        main_layout.insertWidget(0, container)

        self.tableWidget.setSelectionBehavior(self.tableWidget.SelectRows)
        self.tableWidget.setEditTriggers(self.tableWidget.NoEditTriggers)

        self.load_books()

        self.tableWidget.cellDoubleClicked.connect(self.show_details)

    def load_books(self):
        try:
            cur = self.conn.cursor()
            query = """
                SELECT b.id, b.title, b.author, b.year, g.title as genre, b.image_path
                FROM books b
                LEFT JOIN genres g ON b.genre = g.id
                ORDER BY b.id
            """
            cur.execute(query)
            rows = cur.fetchall()
            headers = ["id", "Название", "Автор", "Год", "Жанр"]
            self.tableWidget.setColumnCount(len(headers))
            self.tableWidget.setHorizontalHeaderLabels(headers)
            self.tableWidget.setRowCount(len(rows))
            for i, r in enumerate(rows):
                for j, val in enumerate(r[:5]):
                    item = QTableWidgetItem(str(val) if val is not None else "")
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self.tableWidget.setItem(i, j, item)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить книги:\n{e}")

    def get_selected_book_id(self):
        sel = self.tableWidget.selectedItems()
        if not sel:
            return None
        row = sel[0].row()
        item = self.tableWidget.item(row, 0)
        return int(item.text()) if item else None

    def add_book(self):
        dlg = BookDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.result
            try:
                cur = self.conn.cursor()
                cur.execute("INSERT INTO books (title, author, year, genre, image_path) VALUES (?, ?, ?, ?, ?)",
                            (data["title"], data["author"], data["year"], data["genre"], data["image_path"]))
                self.conn.commit()
                self.load_books()
                QMessageBox.information(self, "Успех", "Книга добавлена.")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось добавить:\n{e}")

    def edit_book(self):
        bid = self.get_selected_book_id()
        if bid is None:
            QMessageBox.warning(self, "Ошибка", "Выберите книгу для редактирования.")
            return
        cur = self.conn.cursor()
        cur.execute("SELECT id, title, author, year, genre, image_path FROM books WHERE id = ?", (bid,))
        row = cur.fetchone()
        if not row:
            QMessageBox.warning(self, "Ошибка", "Книга не найдена.")
            return
        dlg = BookDialog(self, book_data=row)
        if dlg.exec_() == QDialog.Accepted:
            data = dlg.result
            try:
                cur.execute("UPDATE books SET title=?, author=?, year=?, genre=?, image_path=? WHERE id=?",
                            (data["title"], data["author"], data["year"], data["genre"], data["image_path"], bid))
                self.conn.commit()
                self.load_books()
                QMessageBox.information(self, "Успех", "Книга обновлена.")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось обновить:\n{e}")

    def delete_book(self):
        bid = self.get_selected_book_id()
        if bid is None:
            QMessageBox.warning(self, "Ошибка", "Выберите книгу для удаления.")
            return
        reply = QMessageBox.question(self, "Подтвердите", "Удалить книгу?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.No:
            return
        try:
            cur = self.conn.cursor()
            cur.execute("DELETE FROM books WHERE id = ?", (bid,))
            self.conn.commit()
            self.load_books()
            QMessageBox.information(self, "Успех", "Книга удалена.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось удалить:\n{e}")

    def show_details(self, row, col):
        id_item = self.tableWidget.item(row, 0)
        if not id_item:
            return
        bid = int(id_item.text())
        cur = self.conn.cursor()
        cur.execute("SELECT title, author, year, genre, image_path FROM books WHERE id = ?", (bid,))
        book = cur.fetchone()
        if not book:
            return
        title, author, year, genre_name, image_rel = book[0], book[1], book[2], book[3], book[4]
        txt = f"Название: {title}\nАвтор: {author}\nГод: {year}\nЖанр: {genre_name}"
        img_path = resource_path(os.path.join(IMAGES_DIR, PLACEHOLDER))
        if image_rel:
            cand = resource_path(image_rel)
            if os.path.exists(cand):
                img_path = cand
        pix = QPixmap(img_path).scaled(240, 320, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        msg = QMessageBox(self)
        msg.setWindowTitle("Информация о книге")
        msg.setText(txt)
        msg.setIconPixmap(pix)
        msg.exec_()

    def closeEvent(self, ev):
        try:
            self.conn.close()
        finally:
            ev.accept()

def main():
    app = QApplication(sys.argv)
    ensure_storage()
    init_db()
    auth = AuthDialog()
    if auth.exec_() != QDialog.Accepted:
        sys.exit(0)
    w = Catalog()
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
