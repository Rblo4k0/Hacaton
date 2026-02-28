from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame, QMessageBox
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QFont
import styles
from trainer_window import TrainerWindow
from profile_window import ProfileWindow
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


class MainWindow(QMainWindow):
    def __init__(self, db=None):
        super().__init__()
        self.db = db if db else Database()
        self.current_user = self.db.get_active_user()
        self.setWindowTitle("ReactionRPS")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet(f"background-color: {styles.COLORS['bg_white']};")

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

        title = QLabel("🧠 ReactionRPS")
        title.setFont(styles.get_font_large(48))
        title.setAlignment(Qt.AlignCenter)
        content_layout.addWidget(title)

        subtitle = QLabel("тренажер скорости реакции")
        subtitle.setFont(styles.get_font_regular(16))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(f"color: {styles.COLORS['text_soft']};")
        content_layout.addWidget(subtitle)

        card = QFrame()
        card.setStyleSheet(styles.CARD_STYLE)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(15)

        # Кнопка начать тренировку
        self.start_btn = BounceButton("🚀 НАЧАТЬ ТРЕНИРОВКУ")
        self.start_btn.setStyleSheet(styles.BUTTON_STYLE)
        self.start_btn.clicked.connect(self.open_trainer)
        card_layout.addWidget(self.start_btn)

        # Кнопка профиля
        self.profile_btn = BounceButton("👁️ ПРОФИЛЬ")
        self.profile_btn.setStyleSheet(styles.BUTTON_STYLE)
        self.profile_btn.clicked.connect(self.open_profile)
        card_layout.addWidget(self.profile_btn)

        # Кнопка лидеров
        self.leaders_btn = BounceButton("🏆 ЛИДЕРЫ")
        self.leaders_btn.setStyleSheet(styles.BUTTON_STYLE)
        self.leaders_btn.clicked.connect(self.open_leaders)
        card_layout.addWidget(self.leaders_btn)

        content_layout.addWidget(card)
        main_layout.addWidget(content_widget)

    def open_trainer(self):
        if not self.current_user:
            reply = QMessageBox.question(
                self,
                "Вход не выполнен",
                "Для сохранения результатов необходимо войти в профиль.\n\nХотите войти сейчас?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.open_profile()
                return

        self.trainer = TrainerWindow(self.db, self.current_user)
        self.trainer.show()
        self.hide()

    def open_profile(self):
        self.profile_window = ProfileWindow(self.db)
        self.profile_window.show()
        self.hide()

    def open_leaders(self):
        QMessageBox.information(self, "ReactionRPS", "Таблица лидеров будет доступна в следующем обновлении")