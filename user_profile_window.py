from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QTableWidget, QTableWidgetItem,
    QComboBox, QLineEdit, QMessageBox, QHeaderView
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QFont, QColor
import styles
from database import Database


class BounceButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(200)
        self.anim.setEasingCurve(QEasingCurve.OutBounce)
        self.block = False

    def enterEvent(self, event):
        if not self.block:
            self.block = True
            self.animate_bounce()
            QTimer.singleShot(300, self.unblock)
        super().enterEvent(event)

    def unblock(self):
        self.block = False

    def animate_bounce(self):
        rect = self.geometry()
        self.anim.setStartValue(rect)
        self.anim.setKeyValueAt(0.5, rect.adjusted(-5, -5, 5, 5))
        self.anim.setEndValue(rect)
        self.anim.start()


class UserProfileWindow(QMainWindow):
    def __init__(self, db, user):
        super().__init__()
        self.db = db
        self.user = user
        self.setWindowTitle(f"ReactionRPS - {user['username']}")
        self.setGeometry(100, 100, 900, 600)
        self.setStyleSheet(f"background-color: {styles.COLORS['bg_white']};")

        self.init_ui()
        self.load_sessions()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        # Главный layout
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)

        # Шапка профиля
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 15px;
                border: 2px solid """ + styles.COLORS['accent_yellow'] + """;
            }
        """)
        header_frame.setFixedHeight(80)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 10, 20, 10)

        # Никнейм
        username_label = QLabel(self.user['username'])
        username_label.setFont(QFont("Segoe UI", 24, QFont.Bold))
        username_label.setStyleSheet(f"color: {styles.COLORS['text_dark']};")
        header_layout.addWidget(username_label)

        header_layout.addStretch()

        # Кнопка назад
        self.back_btn = BounceButton("← НАЗАД")
        self.back_btn.setFixedSize(100, 40)
        self.back_btn.setStyleSheet(styles.BUTTON_STYLE)
        self.back_btn.clicked.connect(self.go_back)
        header_layout.addWidget(self.back_btn)

        main_layout.addWidget(header_frame)

        # Карточка с информацией
        info_card = QFrame()
        info_card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 15px;
                border: 2px solid """ + styles.COLORS['accent_yellow'] + """;
            }
        """)
        info_layout = QVBoxLayout(info_card)
        info_layout.setContentsMargins(30, 25, 30, 25)
        info_layout.setSpacing(20)

        # Заголовок раздела
        section_title = QLabel("👤 О себе")
        section_title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        section_title.setStyleSheet(f"color: {styles.COLORS['text_dark']};")
        info_layout.addWidget(section_title)

        # Возраст
        age_layout = QHBoxLayout()
        age_layout.setSpacing(15)

        age_label = QLabel("Возраст:")
        age_label.setFont(QFont("Segoe UI", 12))
        age_label.setFixedWidth(80)
        age_label.setStyleSheet(f"color: {styles.COLORS['text_dark']};")
        age_layout.addWidget(age_label)

        self.age_input = QLineEdit()
        self.age_input.setFont(QFont("Segoe UI", 12))
        self.age_input.setPlaceholderText("Не указан")
        self.age_input.setMaxLength(3)
        if self.user['age']:
            self.age_input.setText(str(self.user['age']))
        self.age_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 2px solid """ + styles.COLORS['accent_yellow'] + """;
                border-radius: 8px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 2px solid """ + styles.COLORS['accent_orange'] + """;
            }
        """)
        age_layout.addWidget(self.age_input)
        age_layout.addStretch()

        info_layout.addLayout(age_layout)

        # Пол
        gender_layout = QHBoxLayout()
        gender_layout.setSpacing(15)

        gender_label = QLabel("Пол:")
        gender_label.setFont(QFont("Segoe UI", 12))
        gender_label.setFixedWidth(80)
        gender_label.setStyleSheet(f"color: {styles.COLORS['text_dark']};")
        gender_layout.addWidget(gender_label)

        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["Не указан", "Мужчина", "Женщина"])
        if self.user['gender'] == "Мужской" or self.user['gender'] == "Мужчина":
            self.gender_combo.setCurrentIndex(1)
        elif self.user['gender'] == "Женский" or self.user['gender'] == "Женщина":
            self.gender_combo.setCurrentIndex(2)
        self.gender_combo.setFont(QFont("Segoe UI", 12))
        self.gender_combo.setFixedWidth(150)
        self.gender_combo.setStyleSheet("""
            QComboBox {
                padding: 8px 12px;
                border: 2px solid """ + styles.COLORS['accent_yellow'] + """;
                border-radius: 8px;
                background-color: white;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid """ + styles.COLORS['accent_yellow'] + """;
                border-top: 5px solid transparent;
                border-bottom: 5px solid transparent;
            }
            QComboBox:hover {
                border: 2px solid """ + styles.COLORS['accent_orange'] + """;
            }
        """)
        gender_layout.addWidget(self.gender_combo)
        gender_layout.addStretch()

        info_layout.addLayout(gender_layout)

        # Кнопка сохранения
        save_btn_layout = QHBoxLayout()
        save_btn_layout.addStretch()

        self.save_btn = BounceButton("💾 СОХРАНИТЬ")
        self.save_btn.setFixedSize(150, 45)
        self.save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {styles.COLORS['accent_green']};
                color: white;
                border: none;
                border-radius: 10px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #05b586;
            }}
        """)
        self.save_btn.clicked.connect(self.save_profile)
        save_btn_layout.addWidget(self.save_btn)

        info_layout.addLayout(save_btn_layout)

        main_layout.addWidget(info_card)

        # Карточка с историей тренировок
        history_card = QFrame()
        history_card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 15px;
                border: 2px solid """ + styles.COLORS['accent_yellow'] + """;
            }
        """)
        history_layout = QVBoxLayout(history_card)
        history_layout.setContentsMargins(20, 20, 20, 20)
        history_layout.setSpacing(15)

        # Заголовок раздела
        history_title = QLabel("📊 История тренировок")
        history_title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        history_title.setStyleSheet(f"color: {styles.COLORS['text_dark']};")
        history_layout.addWidget(history_title)

        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Дата", "Среднее (мс)", "Лучшее (мс)", "Вариативность", "Точность", "Ошибки"
        ])

        # Настройка таблицы
        self.table.setShowGrid(True)
        self.table.setGridStyle(Qt.SolidLine)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid """ + styles.COLORS['accent_yellow'] + """;
                border-radius: 8px;
                background-color: white;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid """ + styles.COLORS['accent_yellow'] + """;
            }
            QTableWidget::item:selected {
                background-color: """ + styles.COLORS['accent_yellow'] + """;
                color: """ + styles.COLORS['text_dark'] + """;
            }
            QHeaderView::section {
                background-color: """ + styles.COLORS['accent_yellow'] + """;
                color: """ + styles.COLORS['text_dark'] + """;
                padding: 8px;
                border: none;
                font-weight: bold;
                font-size: 12px;
            }
            QTableWidget::item:alternate {
                background-color: """ + styles.COLORS['bg_soft'] + """;
            }
        """)

        # Растягиваем колонки
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setStretchLastSection(True)

        history_layout.addWidget(self.table)
        main_layout.addWidget(history_card)

    def save_profile(self):
        # Проверка возраста
        age_text = self.age_input.text().strip()
        age = None
        if age_text:
            try:
                age = int(age_text)
                if age < 0 or age > 120:
                    QMessageBox.warning(self, "Ошибка", "Введите корректный возраст (0-120)")
                    return
            except ValueError:
                QMessageBox.warning(self, "Ошибка", "Введите число")
                return

        # Пол
        gender = self.gender_combo.currentText()
        if gender == "Не указан":
            gender = None

        self.db.update_user_profile(self.user['id'], age, gender)
        self.user['age'] = age
        self.user['gender'] = gender

        QMessageBox.information(self, "Успех", "Профиль обновлен")

    def load_sessions(self):
        sessions = self.db.get_user_sessions(self.user['id'])

        self.table.setRowCount(len(sessions))

        for row, session in enumerate(sessions):
            # Дата
            date_str = session['date'][:16].replace('T', ' ')
            date_item = QTableWidgetItem(date_str)
            date_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, date_item)

            # Среднее время
            avg_item = QTableWidgetItem(f"{session['avg_reaction']:.0f}")
            avg_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 1, avg_item)

            # Лучшее время
            min_item = QTableWidgetItem(f"{session['min_reaction']:.0f}")
            min_item.setTextAlignment(Qt.AlignCenter)
            if session['min_reaction'] < 300:
                min_item.setForeground(QColor(styles.COLORS['accent_green']))
            elif session['min_reaction'] < 500:
                min_item.setForeground(QColor(styles.COLORS['accent_yellow']))
            else:
                min_item.setForeground(QColor(styles.COLORS['accent_red']))
            self.table.setItem(row, 2, min_item)

            # Вариативность
            std_item = QTableWidgetItem(f"{session['std_deviation']:.1f}")
            std_item.setTextAlignment(Qt.AlignCenter)
            if session['std_deviation'] < 50:
                std_item.setForeground(QColor(styles.COLORS['accent_green']))
            elif session['std_deviation'] < 100:
                std_item.setForeground(QColor(styles.COLORS['accent_yellow']))
            else:
                std_item.setForeground(QColor(styles.COLORS['accent_red']))
            self.table.setItem(row, 3, std_item)

            # Точность
            acc_item = QTableWidgetItem(f"{session['accuracy']:.1f}%")
            acc_item.setTextAlignment(Qt.AlignCenter)
            if session['accuracy'] >= 90:
                acc_item.setForeground(QColor(styles.COLORS['accent_green']))
            elif session['accuracy'] >= 70:
                acc_item.setForeground(QColor(styles.COLORS['accent_yellow']))
            else:
                acc_item.setForeground(QColor(styles.COLORS['accent_red']))
            self.table.setItem(row, 4, acc_item)

            # Ошибки
            wrong_item = QTableWidgetItem(str(session['total_wrong']))
            wrong_item.setTextAlignment(Qt.AlignCenter)
            if session['total_wrong'] == 0:
                wrong_item.setForeground(QColor(styles.COLORS['accent_green']))
            elif session['total_wrong'] < 5:
                wrong_item.setForeground(QColor(styles.COLORS['accent_yellow']))
            else:
                wrong_item.setForeground(QColor(styles.COLORS['accent_red']))
            self.table.setItem(row, 5, wrong_item)

        # Если нет тренировок
        if len(sessions) == 0:
            self.table.setRowCount(1)
            empty_item = QTableWidgetItem("Пока нет тренировок. Начните первую!")
            empty_item.setTextAlignment(Qt.AlignCenter)
            empty_item.setForeground(QColor(styles.COLORS['text_soft']))
            self.table.setSpan(0, 0, 1, 6)
            self.table.setItem(0, 0, empty_item)

    def go_back(self):
        from main_window import MainWindow
        self.main_window = MainWindow(self.db)
        self.main_window.show()
        self.close()