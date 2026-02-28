from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QLineEdit, QMessageBox
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QFont
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


class ProfileWindow(QMainWindow):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.current_user = None
        self.setWindowTitle("ReactionRPS - Профиль")
        self.setGeometry(100, 100, 500, 500)
        self.setStyleSheet(f"background-color: {styles.COLORS['bg_white']};")

        self.init_ui()
        self.check_active_user()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        # Главный layout с центрированием
        main_layout = QVBoxLayout(central)
        main_layout.setAlignment(Qt.AlignCenter)

        # Контейнер для контента с ограниченной шириной
        content_widget = QWidget()
        content_widget.setMaximumWidth(500)
        content_layout = QVBoxLayout(content_widget)
        content_layout.setAlignment(Qt.AlignCenter)
        content_layout.setSpacing(20)

        # Заголовок с эмодзи глаза
        title = QLabel("👁️ ПРОФИЛЬ")
        title.setFont(styles.get_font_large(48))
        title.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(title)

        # Карточка с формой
        self.card = QFrame()
        self.card.setStyleSheet(styles.CARD_STYLE)
        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setSpacing(15)

        # Поле ввода ника (сразу с подсказкой)
        self.username_input = QLineEdit()
        self.username_input.setFont(styles.get_font_regular(14))
        self.username_input.setMaxLength(16)
        self.username_input.setPlaceholderText("Введите юзернейм от 2 до 16 символов")
        self.username_input.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 2px solid """ + styles.COLORS['accent_yellow'] + """;
                border-radius: 10px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 2px solid """ + styles.COLORS['accent_orange'] + """;
            }
        """)
        self.card_layout.addWidget(self.username_input)

        # Контейнер для кнопок входа/выхода
        self.auth_container = QWidget()
        self.auth_layout = QHBoxLayout(self.auth_container)
        self.auth_layout.setContentsMargins(0, 0, 0, 0)
        self.auth_layout.setSpacing(10)
        self.card_layout.addWidget(self.auth_container)

        # Контейнер для дополнительных кнопок (смена ника, назад)
        self.extra_container = QWidget()
        self.extra_layout = QVBoxLayout(self.extra_container)
        self.extra_layout.setContentsMargins(0, 10, 0, 0)
        self.extra_layout.setSpacing(10)
        self.card_layout.addWidget(self.extra_container)

        content_layout.addWidget(self.card)

        # Добавляем контейнер в главный layout
        main_layout.addWidget(content_widget)

        # Показываем кнопки для входа/регистрации
        self.show_login_buttons()

    def show_login_buttons(self):
        # Очищаем контейнеры
        self.clear_layout(self.auth_layout)
        self.clear_layout(self.extra_layout)

        # Кнопка регистрации
        self.register_btn = BounceButton("ЗАРЕГИСТРИРОВАТЬСЯ")
        self.register_btn.setStyleSheet(styles.BUTTON_STYLE)
        self.register_btn.clicked.connect(self.register_user)
        self.auth_layout.addWidget(self.register_btn)

        # Кнопка входа
        self.login_btn = BounceButton("ВОЙТИ")
        self.login_btn.setStyleSheet(styles.BUTTON_STYLE)
        self.login_btn.clicked.connect(self.login_user)
        self.auth_layout.addWidget(self.login_btn)

        # Кнопка назад
        self.back_btn = BounceButton("← НАЗАД")
        self.back_btn.setStyleSheet(styles.BUTTON_STYLE)
        self.back_btn.clicked.connect(self.go_back)
        self.extra_layout.addWidget(self.back_btn)

    def show_logout_buttons(self):
        # Очищаем контейнеры
        self.clear_layout(self.auth_layout)
        self.clear_layout(self.extra_layout)

        # Кнопка выхода
        self.logout_btn = BounceButton("ВЫЙТИ")
        self.logout_btn.setStyleSheet(styles.BUTTON_STYLE)
        self.logout_btn.clicked.connect(self.logout_user)
        self.auth_layout.addWidget(self.logout_btn)

        # Кнопка смены ника
        self.change_username_btn = BounceButton("✏️ СМЕНИТЬ НИК")
        self.change_username_btn.setStyleSheet(styles.BUTTON_STYLE)
        self.change_username_btn.clicked.connect(self.show_change_username)
        self.extra_layout.addWidget(self.change_username_btn)

        # Кнопка назад
        self.back_btn = BounceButton("← НАЗАД")
        self.back_btn.setStyleSheet(styles.BUTTON_STYLE)
        self.back_btn.clicked.connect(self.go_back)
        self.extra_layout.addWidget(self.back_btn)

    def show_change_username_buttons(self):
        # Очищаем контейнеры
        self.clear_layout(self.auth_layout)
        self.clear_layout(self.extra_layout)

        # Кнопка подтверждения смены
        self.confirm_btn = BounceButton("✅ ПОДТВЕРДИТЬ")
        self.confirm_btn.setStyleSheet(styles.BUTTON_STYLE)
        self.confirm_btn.clicked.connect(self.change_username)
        self.auth_layout.addWidget(self.confirm_btn)

        # Кнопка отмены
        self.cancel_btn = BounceButton("❌ ОТМЕНА")
        self.cancel_btn.setStyleSheet(styles.BUTTON_STYLE)
        self.cancel_btn.clicked.connect(self.cancel_change_username)
        self.auth_layout.addWidget(self.cancel_btn)

        # Кнопка назад (неактивна во время смены)
        self.back_btn = BounceButton("← НАЗАД")
        self.back_btn.setStyleSheet(styles.BUTTON_STYLE)
        self.back_btn.clicked.connect(self.cancel_change_username)
        self.extra_layout.addWidget(self.back_btn)

    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def check_active_user(self):
        active_user = self.db.get_active_user()
        if active_user:
            self.current_user = active_user
            self.username_input.setText(active_user['username'])
            self.show_logout_buttons()

    def validate_username(self, username):
        if len(username) < 2:
            QMessageBox.warning(self, "Ошибка", "Юзернейм должен быть не менее 2 символов")
            return False
        if len(username) > 16:
            QMessageBox.warning(self, "Ошибка", "Юзернейм должен быть не более 16 символов")
            return False
        return True

    def register_user(self):
        username = self.username_input.text().strip()

        if not self.validate_username(username):
            return

        if self.db.username_exists(username):
            QMessageBox.warning(self, "Ошибка", "Пользователь с таким ником уже существует")
            return

        user_id = self.db.create_user(username)
        if user_id:
            self.current_user = self.db.get_user(username)
            self.show_logout_buttons()

            # Переходим в профиль пользователя
            QTimer.singleShot(500, self.go_to_user_profile)
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось создать пользователя")

    def login_user(self):
        username = self.username_input.text().strip()

        if not self.validate_username(username):
            return

        user = self.db.get_user(username)
        if user:
            self.current_user = user
            self.db.set_active_user(user['id'])
            self.show_logout_buttons()

            # Переходим в профиль пользователя
            QTimer.singleShot(500, self.go_to_user_profile)
        else:
            QMessageBox.warning(self, "Ошибка", "Пользователь не найден")

    def logout_user(self):
        self.db.clear_active_user()
        self.current_user = None
        self.username_input.clear()
        self.show_login_buttons()

    def show_change_username(self):
        self.show_change_username_buttons()
        self.username_input.setPlaceholderText("Введите новый юзернейм")

    def change_username(self):
        new_username = self.username_input.text().strip()

        if not self.validate_username(new_username):
            return

        if new_username == self.current_user['username']:
            QMessageBox.warning(self, "Ошибка", "Новый никнейм совпадает со старым")
            return

        if self.db.username_exists(new_username):
            QMessageBox.warning(self, "Ошибка", "Пользователь с таким ником уже существует")
            return

        success = self.db.update_username(self.current_user['id'], new_username)
        if success:
            self.current_user['username'] = new_username
            self.username_input.setText(new_username)
            QMessageBox.information(self, "Успех", "Никнейм успешно изменен")
            self.show_logout_buttons()
        else:
            QMessageBox.critical(self, "Ошибка", "Не удалось изменить никнейм")

    def cancel_change_username(self):
        self.username_input.setText(self.current_user['username'] if self.current_user else "")
        self.username_input.setPlaceholderText("Введите юзернейм от 2 до 16 символов")
        if self.current_user:
            self.show_logout_buttons()
        else:
            self.show_login_buttons()

    def go_to_user_profile(self):
        from user_profile_window import UserProfileWindow
        self.profile_window = UserProfileWindow(self.db, self.current_user)
        self.profile_window.show()
        self.close()

    def go_back(self):
        from main_window import MainWindow
        self.main_window = MainWindow(self.db)
        self.main_window.show()
        self.close()