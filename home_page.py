from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import styles


class HomePage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(52, 44, 52, 44)
        layout.setSpacing(0)

        self.greeting = QLabel("Привет! Готов тренироваться?")
        self.greeting.setFont(QFont("Segoe UI", 26, QFont.Bold))
        self.greeting.setStyleSheet(f"color: {styles.COLORS['text_dark']};")
        layout.addWidget(self.greeting)

        layout.addSpacing(28)

        rules_title = QLabel("Как играть")
        rules_title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        rules_title.setStyleSheet(f"color: {styles.COLORS['text_dark']};")
        layout.addWidget(rules_title)

        layout.addSpacing(14)

        rules_text = (
            "Приложение измеряет скорость твоей реакции с помощью камеры — "
            "ты отвечаешь жестами руки, а не кнопками.\n\n"
            "🪨 ✂️ 🧻  Используются три жеста: камень, ножницы, бумага.\n\n"
            "🟢  Зелёный фон — покажи жест, который ПОБЕЖДАЕТ изображённый.\n"
            "🔴  Красный фон — покажи жест, который ПРОИГРЫВАЕТ изображённому.\n\n"
            "Перед каждым ответом верни руку в нейтральное положение ☝️ (один палец вверх). "
            "Если ошибся — просто смени жест, возвращаться в нейтраль не нужно.\n\n"
            "⚡  Реагируй как можно быстрее. Результаты сохраняются в Профиле."
        )

        rules_label = QLabel(rules_text)
        rules_label.setFont(QFont("Segoe UI", 13))
        rules_label.setStyleSheet(f"color: {styles.COLORS['text_mid']};")
        rules_label.setWordWrap(True)
        rules_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        layout.addWidget(rules_label)

        layout.addStretch()

        self._auth_hint = QLabel("")
        self._auth_hint.setFont(QFont("Segoe UI", 11))
        self._auth_hint.setStyleSheet(f"color: {styles.COLORS['text_soft']};")
        layout.addWidget(self._auth_hint)

        self.refresh()

    def refresh(self):
        user = self.main_window.current_user
        if user:
            self.greeting.setText(f"Привет, {user['username']}! 👋")
            self._auth_hint.setText("")
        else:
            self.greeting.setText("Привет! Готов тренироваться?")
            self._auth_hint.setText("💡 Войди в профиль, чтобы сохранять результаты тренировок.")
