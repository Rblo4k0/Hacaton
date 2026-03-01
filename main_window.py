from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QStackedWidget, QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QFont
import styles
from database import Database, OnlineDatabase


class MainWindow(QMainWindow):
    def __init__(self, db=None):
        super().__init__()
        self.db = db if db else OnlineDatabase()
        self.current_user = self.db.get_active_user()

        self.setWindowTitle("Детектор реакции 🖐️")
        self.setMinimumSize(900, 600)

        self._init_ui()
        self._update_nav_state()

        # Проверяем сервер каждые 15 секунд.
        # Если сервер появился — синхронизируем накопленные данные.
        self._server_timer = QTimer()
        self._server_timer.timeout.connect(self._periodic_server_check)
        self._server_timer.start(15_000)

    def _init_ui(self):
        root = QWidget()
        root.setStyleSheet(f"background-color: {styles.COLORS['bg_white']};")
        self.setCentralWidget(root)
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── Sidebar ──────────────────────────────────────────────
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-right: 1.5px solid {styles.COLORS['border']};
                border-radius: 0;
            }}
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(16, 28, 16, 20)
        sidebar_layout.setSpacing(6)

        logo = QLabel("🖐️ Детектор реакции")
        logo.setFont(QFont("Segoe UI", 13, QFont.Bold))
        logo.setStyleSheet(
            f"color: {styles.COLORS['text_dark']}; padding: 0 4px 16px 4px; "
            f"border-bottom: 1.5px solid {styles.COLORS['border']};"
        )
        logo.setWordWrap(True)
        sidebar_layout.addWidget(logo)
        sidebar_layout.addSpacing(8)

        self.nav_home    = self._nav_btn("🏠  Главная",    0)
        self.nav_train   = self._nav_btn("🎯  Тренировка", 1)
        self.nav_profile = self._nav_btn("👤  Профиль",    2)
        self.nav_leaders = self._nav_btn("🏆  Лидеры",     3)

        for btn in [self.nav_home, self.nav_train, self.nav_profile, self.nav_leaders]:
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        self.user_badge = QFrame()
        self.user_badge.setStyleSheet(f"""
            QFrame {{
                background-color: {styles.COLORS['bg_soft']};
                border-radius: 10px; border: none;
            }}
        """)
        badge_layout = QHBoxLayout(self.user_badge)
        badge_layout.setContentsMargins(12, 10, 12, 10)
        self.user_badge_label = QLabel("Гость")
        self.user_badge_label.setFont(QFont("Segoe UI", 11))
        self.user_badge_label.setStyleSheet(f"color: {styles.COLORS['text_mid']};")
        badge_layout.addWidget(self.user_badge_label)
        sidebar_layout.addWidget(self.user_badge)

        # Статус сервера — понятный текст для пользователя
        self._server_status = QLabel()
        self._server_status.setFont(QFont("Segoe UI", 9))
        self._server_status.setAlignment(Qt.AlignCenter)
        self._server_status.setWordWrap(True)
        self._update_server_status()
        sidebar_layout.addWidget(self._server_status)

        root_layout.addWidget(sidebar)

        # ── Stacked content ───────────────────────────────────────
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background-color: {styles.COLORS['bg_white']};")
        root_layout.addWidget(self.stack, 1)

        from home_page import HomePage
        from train_page import TrainPage
        from profile_page import ProfilePage
        from leaders_page import LeadersPage

        self.home_page    = HomePage(self)
        self.train_page   = TrainPage(self)
        self.profile_page = ProfilePage(self)
        self.leaders_page = LeadersPage(self)

        self.stack.addWidget(self.home_page)    # 0
        self.stack.addWidget(self.train_page)   # 1
        self.stack.addWidget(self.profile_page) # 2
        self.stack.addWidget(self.leaders_page) # 3

        self.nav_buttons = [self.nav_home, self.nav_train, self.nav_profile, self.nav_leaders]
        self.navigate_to(0)

    def _nav_btn(self, text, index):
        btn = QPushButton(text)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(42)
        btn.clicked.connect(lambda _, i=index: self.navigate_to(i))
        return btn

    def _animate_page(self, widget):
        """Плавный fade-in при переходе между страницами."""
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity")
        anim.setDuration(180)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start(QPropertyAnimation.DeleteWhenStopped)
        widget._page_anim = anim

    def navigate_to(self, index):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setStyleSheet(styles.NAV_BUTTON_ACTIVE if i == index else styles.NAV_BUTTON_INACTIVE)
        if index == 2:
            self.profile_page.refresh()
        if index == 3:
            self._update_server_status()
            self.leaders_page.refresh()

    # ── Периодическая проверка сервера ───────────────────────────
    def _periodic_server_check(self):
        """Каждые 15 сек проверяет сервер. Если появился — синхронизирует данные."""
        if not hasattr(self.db, '_check_server'):
            return

        was_online = object.__getattribute__(self.db, '_online')
        is_online_now = self.db._check_server()
        object.__setattr__(self.db, '_online', is_online_now)

        if is_online_now and not was_online:
            # Сервер только что появился — синхронизируем накопленные сессии
            self._sync_all_sessions_to_server()
            self._update_server_status()
            # Если открыта таблица лидеров — обновляем её
            if self.stack.currentIndex() == 3:
                self.leaders_page.refresh()
        elif not is_online_now and was_online:
            self._update_server_status()

    def _sync_all_sessions_to_server(self):
        """
        Отправляет на сервер все локальные сессии всех пользователей.
        Вызывается когда сервер становится доступен после оффлайна.
        Если сервер работает на той же машине с той же neurospint.db —
        данные уже там. Если на другой машине — отправляем копию.
        """
        try:
            local = object.__getattribute__(self.db, '_local')
            with local.get_connection() as conn:
                c = conn.cursor()
                c.execute("SELECT id, username, age, gender FROM users")
                users = c.fetchall()

            for user_id, username, age, gender in users:
                # Регистрируем пользователя на сервере (409 = уже есть, нормально)
                try:
                    self.db._post_json("/users", {
                        "username": username,
                        "age": age,
                        "gender": gender,
                    })
                except Exception:
                    pass

                sessions = local.get_user_sessions(user_id)
                for s in sessions:
                    try:
                        self.db._post_json("/sessions", {
                            "username":      username,
                            "avg_reaction":  s.get("avg_reaction", 0),
                            "min_reaction":  s.get("min_reaction", 0),
                            "max_reaction":  s.get("max_reaction", 0),
                            "std_deviation": s.get("std_deviation", 0),
                            "total_wrong":   s.get("total_wrong", 0),
                            "difficulty":    s.get("difficulty", "medium"),
                            "trials_data":   [],
                        })
                    except Exception:
                        pass
        except Exception:
            pass

    # ── Статус сервера ────────────────────────────────────────────
    def _update_server_status(self):
        if hasattr(self.db, 'is_online') and self.db.is_online:
            self._server_status.setText("🟢 Лидеры: общий\nрейтинг онлайн")
            self._server_status.setStyleSheet(
                f"color: {styles.COLORS['accent_green']}; padding: 4px 2px; font-size: 9px;"
            )
        else:
            self._server_status.setText("🔴 Лидеры: только\nлокальные данные")
            self._server_status.setStyleSheet(
                f"color: {styles.COLORS['text_soft']}; padding: 4px 2px; font-size: 9px;"
            )

    def _update_nav_state(self):
        if self.current_user:
            self.user_badge_label.setText(f"👤 {self.current_user['username']}")
            self.user_badge_label.setStyleSheet(f"color: {styles.COLORS['text_dark']}; font-weight: bold;")
        else:
            self.user_badge_label.setText("Гость")
            self.user_badge_label.setStyleSheet(f"color: {styles.COLORS['text_soft']};")

    def on_user_changed(self, user):
        self.current_user = user
        self._update_nav_state()
        if hasattr(self, 'home_page'):
            self.home_page.refresh()
        if hasattr(self, 'train_page'):
            self.train_page.update_idle_hint()
