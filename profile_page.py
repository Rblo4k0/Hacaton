from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QScrollArea, QMessageBox, QStackedWidget, QSizePolicy, QFileDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
import styles


def age_label(age):
    if age is None:
        return "Возраст не указан"
    age = int(age)
    if 11 <= age % 100 <= 19:
        return f"{age} лет"
    r = age % 10
    if r == 1:   return f"{age} год"
    if r in (2, 3, 4): return f"{age} года"
    return f"{age} лет"


class ProfilePage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.db = main_window.db
        self._editing = False
        self._build()

    def _build(self):
        self._outer = QStackedWidget(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._outer)
        self._outer.addWidget(self._build_login())      # 0
        self._outer.addWidget(self._build_dashboard())  # 1

    # ─── Страница входа ───────────────────────────────────────────────
    def _build_login(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setAlignment(Qt.AlignCenter)

        container = QFrame()
        container.setFixedWidth(420)
        container.setStyleSheet(
            f"QFrame {{ background-color: white; border-radius: 20px; "
            f"border: 1.5px solid {styles.COLORS['border']}; }}"
        )
        c = QVBoxLayout(container)
        c.setContentsMargins(36, 36, 36, 36)
        c.setSpacing(16)

        title = QLabel("Добро пожаловать")
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        title.setStyleSheet(f"color: {styles.COLORS['text_dark']};")
        title.setAlignment(Qt.AlignCenter)
        c.addWidget(title)

        self._login_input = QLineEdit()
        self._login_input.setPlaceholderText("Никнейм (2–16 символов)")
        self._login_input.setMaxLength(16)
        self._login_input.setFixedHeight(48)
        self._login_input.setStyleSheet(styles.INPUT_STYLE)
        self._login_input.setFont(QFont("Segoe UI", 13))
        self._login_input.returnPressed.connect(self._login)
        c.addWidget(self._login_input)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        reg_btn = QPushButton("Зарегистрироваться")
        reg_btn.setCursor(Qt.PointingHandCursor)
        reg_btn.setFixedHeight(46)
        reg_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        reg_btn.setStyleSheet(styles.BUTTON_PRIMARY)
        reg_btn.clicked.connect(self._register)
        btn_row.addWidget(reg_btn)

        login_btn = QPushButton("Войти")
        login_btn.setCursor(Qt.PointingHandCursor)
        login_btn.setFixedHeight(46)
        login_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        login_btn.setStyleSheet(styles.BUTTON_SECONDARY)
        login_btn.clicked.connect(self._login)
        btn_row.addWidget(login_btn)

        c.addLayout(btn_row)

        self._login_error = QLabel("")
        self._login_error.setFont(QFont("Segoe UI", 11))
        self._login_error.setStyleSheet(f"color: {styles.COLORS['accent_red']};")
        self._login_error.setAlignment(Qt.AlignCenter)
        self._login_error.setWordWrap(True)
        c.addWidget(self._login_error)

        layout.addWidget(container)
        return w

    # ─── Дашборд ──────────────────────────────────────────────────────
    def _build_dashboard(self):
        w = QWidget()
        w.setStyleSheet(f"background-color: {styles.COLORS['bg_white']};")

        outer = QVBoxLayout(w)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        outer.addWidget(self._scroll)

        content = QWidget()
        content.setStyleSheet(f"background-color: {styles.COLORS['bg_white']};")
        self._dash_layout = QVBoxLayout(content)
        self._dash_layout.setContentsMargins(40, 36, 40, 40)
        self._dash_layout.setSpacing(20)
        self._scroll.setWidget(content)

        # ── Шапка ─────────────────────────────────────────────────────
        header_row = QHBoxLayout()
        name_col = QVBoxLayout()
        name_col.setSpacing(4)

        self._profile_name = QLabel()
        self._profile_name.setFont(QFont("Segoe UI", 24, QFont.Bold))
        self._profile_name.setStyleSheet(f"color: {styles.COLORS['text_dark']};")
        name_col.addWidget(self._profile_name)

        self._profile_details = QLabel()
        self._profile_details.setFont(QFont("Segoe UI", 13))
        self._profile_details.setStyleSheet(f"color: {styles.COLORS['text_mid']};")
        name_col.addWidget(self._profile_details)

        header_row.addLayout(name_col)
        header_row.addStretch()

        pdf_btn = QPushButton("📄 Экспорт в PDF")
        pdf_btn.setCursor(Qt.PointingHandCursor)
        pdf_btn.setFixedHeight(38)
        pdf_btn.setStyleSheet(styles.BUTTON_SECONDARY)
        pdf_btn.setFont(QFont("Segoe UI", 11))
        pdf_btn.clicked.connect(self._export_profile_pdf)
        header_row.addWidget(pdf_btn)

        edit_btn = QPushButton("✏️  Изменить")
        edit_btn.setCursor(Qt.PointingHandCursor)
        edit_btn.setFixedHeight(38)
        edit_btn.setStyleSheet(styles.BUTTON_SECONDARY)
        edit_btn.setFont(QFont("Segoe UI", 11))
        edit_btn.clicked.connect(self._toggle_edit)
        header_row.addWidget(edit_btn)

        logout_btn = QPushButton("Выйти")
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.setFixedHeight(38)
        logout_btn.setStyleSheet(styles.BUTTON_DANGER)
        logout_btn.setFont(QFont("Segoe UI", 11))
        logout_btn.clicked.connect(self._logout)
        header_row.addWidget(logout_btn)

        self._dash_layout.addLayout(header_row)

        # ── Форма редактирования — ВСЁ В ОДНОМ БЛОКЕ ─────────────────
        self._edit_frame = QFrame()
        self._edit_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {styles.COLORS['bg_soft']};
                border-radius: 14px;
                border: 1.5px solid {styles.COLORS['border']};
            }}
        """)
        ei = QVBoxLayout(self._edit_frame)
        ei.setContentsMargins(24, 18, 24, 18)
        ei.setSpacing(14)

        lbl_style = f"color: {styles.COLORS['text_dark']}; background: transparent; border: none;"

        # Строка: Никнейм
        nick_row = QHBoxLayout()
        nick_row.setSpacing(10)
        nl = QLabel("Никнейм:")
        nl.setFont(QFont("Segoe UI", 12))
        nl.setFixedWidth(80)
        nl.setStyleSheet(lbl_style)
        nick_row.addWidget(nl)

        self._nick_input = QLineEdit()
        self._nick_input.setMaxLength(16)
        self._nick_input.setFixedHeight(44)
        self._nick_input.setMinimumWidth(140)
        self._nick_input.setMaximumWidth(260)
        self._nick_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._nick_input.setStyleSheet(styles.INPUT_STYLE + "QLineEdit { padding: 10px 14px; }")
        self._nick_input.setFont(QFont("Segoe UI", 12))
        nick_row.addWidget(self._nick_input)
        nick_row.addStretch()
        ei.addLayout(nick_row)

        # Строка: Возраст + Пол
        info_row = QHBoxLayout()
        info_row.setSpacing(10)

        al = QLabel("Возраст:")
        al.setFont(QFont("Segoe UI", 12))
        al.setFixedWidth(80)
        al.setStyleSheet(lbl_style)
        info_row.addWidget(al)

        self._age_input = QLineEdit()
        self._age_input.setMaxLength(3)
        self._age_input.setFixedWidth(70)
        self._age_input.setFixedHeight(38)
        self._age_input.setStyleSheet(styles.INPUT_STYLE)
        self._age_input.setFont(QFont("Segoe UI", 12))
        info_row.addWidget(self._age_input)

        gl = QLabel("Пол:")
        gl.setFont(QFont("Segoe UI", 12))
        gl.setStyleSheet(f"color: {styles.COLORS['text_dark']}; background: transparent; border: none; margin-left: 12px;")
        info_row.addWidget(gl)

        self._gender_combo = QComboBox()
        self._gender_combo.addItems(["Мужчина", "Женщина"])
        self._gender_combo.setFixedHeight(38)
        self._gender_combo.setFixedWidth(130)
        self._gender_combo.setFont(QFont("Segoe UI", 12))
        self._gender_combo.setStyleSheet(f"""
            QComboBox {{
                padding: 6px 10px;
                border: 1.5px solid {styles.COLORS['border']};
                border-radius: 8px;
                background: white;
                color: {styles.COLORS['text_dark']};
            }}
            QComboBox:hover {{ border-color: {styles.COLORS['accent_yellow']}; }}
            QComboBox::drop-down {{ border: none; width: 24px; }}
            QComboBox QAbstractItemView {{
                background: white;
                border: 1.5px solid {styles.COLORS['border']};
                border-radius: 8px;
                selection-background-color: {styles.COLORS['accent_yellow']};
            }}
        """)
        info_row.addWidget(self._gender_combo)
        info_row.addStretch()
        ei.addLayout(info_row)

        # Нижняя строка: ОДНА кнопка «Сохранить всё» + «Удалить»
        bottom_row = QHBoxLayout()
        save_all_btn = QPushButton("💾  Сохранить всё")
        save_all_btn.setCursor(Qt.PointingHandCursor)
        save_all_btn.setFixedHeight(42)
        save_all_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        save_all_btn.setStyleSheet(styles.BUTTON_SUCCESS)
        save_all_btn.clicked.connect(self._save_all)
        bottom_row.addWidget(save_all_btn)
        bottom_row.addStretch()

        del_btn = QPushButton("🗑  Удалить аккаунт")
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setFixedHeight(34)
        del_btn.setFont(QFont("Segoe UI", 10))
        del_btn.setStyleSheet(f"""
            QPushButton {{
                color: {styles.COLORS['accent_red']};
                background: transparent;
                border: none;
                text-decoration: underline;
            }}
            QPushButton:hover {{ color: #b91c1c; }}
        """)
        del_btn.clicked.connect(self._delete_account)
        bottom_row.addWidget(del_btn)
        ei.addLayout(bottom_row)

        # Метка ошибок редактирования
        self._edit_error = QLabel("")
        self._edit_error.setFont(QFont("Segoe UI", 11))
        self._edit_error.setStyleSheet(f"color: {styles.COLORS['accent_red']}; background: transparent; border: none;")
        self._edit_error.setWordWrap(True)
        ei.addWidget(self._edit_error)

        self._edit_frame.hide()
        self._dash_layout.addWidget(self._edit_frame)

        # ── Разделитель ───────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {styles.COLORS['border']}; border: none;")
        self._dash_layout.addWidget(sep)

        # ── Карточки статистики ───────────────────────────────────────
        stats_row = QHBoxLayout()
        stats_row.setSpacing(14)
        self._stat_cards = []
        card_defs = [
            ("—", "Среднее время реакции (мс)"),
            ("—", "Лучшая реакция (мс)"),
            ("—", "Тренировок проведено"),
            ("—", "Тренировок без ошибок"),
        ]
        for val, lbl in card_defs:
            card, v_lbl, l_lbl = self._make_stat_card(val, lbl)
            self._stat_cards.append((card, v_lbl, l_lbl))
            stats_row.addWidget(card)
        self._dash_layout.addLayout(stats_row)

        # ── Графики ───────────────────────────────────────────────────
        charts_title = QLabel("📈 Прогресс по тренировкам")
        charts_title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        charts_title.setStyleSheet(f"color: {styles.COLORS['text_dark']};")
        self._dash_layout.addWidget(charts_title)

        self._chart_frame = QFrame()
        self._chart_frame.setStyleSheet(
            f"QFrame {{ background-color: white; border-radius: 14px; border: 1.5px solid {styles.COLORS['border']}; }}"
        )
        self._chart_layout = QVBoxLayout(self._chart_frame)
        self._chart_layout.setContentsMargins(16, 16, 16, 16)
        self._dash_layout.addWidget(self._chart_frame)

        # ── История тренировок ────────────────────────────────────────
        hist_title = QLabel("🗂  История тренировок")
        hist_title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        hist_title.setStyleSheet(f"color: {styles.COLORS['text_dark']};")
        self._dash_layout.addWidget(hist_title)

        self._table = self._build_table()
        self._table.setMinimumHeight(160)
        self._table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self._dash_layout.addWidget(self._table)
        self._dash_layout.addSpacing(20)

        return w

    def _make_stat_card(self, value, label):
        frame = QFrame()
        frame.setStyleSheet(
            f"QFrame {{ background-color: white; border-radius: 12px; border: 1.5px solid {styles.COLORS['border']}; }}"
        )
        fl = QVBoxLayout(frame)
        fl.setContentsMargins(20, 16, 20, 16)
        fl.setSpacing(4)
        v = QLabel(value)
        v.setFont(QFont("Segoe UI", 20, QFont.Bold))
        v.setStyleSheet(f"color: {styles.COLORS['text_dark']};")
        v.setAlignment(Qt.AlignCenter)
        l = QLabel(label)
        l.setFont(QFont("Segoe UI", 10))
        l.setStyleSheet(f"color: {styles.COLORS['text_soft']};")
        l.setAlignment(Qt.AlignCenter)
        l.setWordWrap(True)
        fl.addWidget(v)
        fl.addWidget(l)
        return frame, v, l

    def _build_table(self):
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "Дата / Время", "Сред. реакция", "Лучшее", "Худшее", "Вариативность", "Ошибки"
        ])
        table.setShowGrid(False)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setStyleSheet(f"""
            QTableWidget {{
                border: 1.5px solid {styles.COLORS['border']};
                border-radius: 12px; background-color: white;
                font-size: 12px; outline: none; gridline-color: transparent;
            }}
            QTableWidget::item {{
                padding: 10px 14px; color: {styles.COLORS['text_dark']};
                border-bottom: 1px solid {styles.COLORS['bg_soft']};
            }}
            QTableWidget::item:selected {{ background-color: {styles.COLORS['bg_soft']}; color: {styles.COLORS['text_dark']}; }}
            QTableWidget::item:alternate {{ background-color: {styles.COLORS['bg_white']}; }}
            QHeaderView::section {{
                background-color: {styles.COLORS['bg_soft']}; color: {styles.COLORS['text_mid']};
                padding: 10px 14px; border: none; font-weight: bold; font-size: 11px;
            }}
        """)
        hdr = table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        for i in range(1, 6):
            hdr.setSectionResizeMode(i, QHeaderView.Stretch)
        return table

    # ─── Загрузка данных ──────────────────────────────────────────────
    def refresh(self):
        user = self.main_window.current_user
        if user:
            self._outer.setCurrentIndex(1)
            self._load_user_data(user)
        else:
            self._outer.setCurrentIndex(0)
            self._login_input.clear()
            self._login_error.setText("")

    def _load_user_data(self, user):
        self._profile_name.setText(f"👁️  {user['username']}")
        age_str    = age_label(user.get('age'))
        gender_str = user.get('gender') or "Пол не указан"
        self._profile_details.setText(f"{age_str}   ·   {gender_str}")

        self._nick_input.setText(user['username'])
        self._age_input.setText(str(user['age']) if user.get('age') is not None else "")
        gender_idx = 0 if user.get('gender') != "Женщина" else 1
        self._gender_combo.setCurrentIndex(gender_idx)
        self._edit_error.setText("")

        sessions = self.db.get_user_sessions(user['id'])
        self._fill_stat_cards(sessions)
        self._fill_table(sessions)
        self._draw_charts(sessions)
        self._adjust_table_height(len(sessions))

    def _adjust_table_height(self, rows):
        hdr_h = self._table.horizontalHeader().height()
        h = hdr_h + max(rows, 1) * 44 + 8
        self._table.setMinimumHeight(min(h, 480))

    def _fill_stat_cards(self, sessions):
        labels = [
            "Среднее время реакции (мс)",
            "Лучшая реакция (мс)",
            "Тренировок проведено",
            "Тренировок без ошибок",
        ]
        if not sessions:
            for i, (_, v, l) in enumerate(self._stat_cards):
                v.setText("—")
                l.setText(labels[i])
            return

        best_reaction = min(s['min_reaction'] for s in sessions)
        perfect       = sum(1 for s in sessions if s['total_wrong'] == 0)
        valid_avgs    = [s['avg_reaction'] for s in sessions if s.get('avg_reaction') and s['avg_reaction'] > 0]
        account_avg   = sum(valid_avgs) / len(valid_avgs) if valid_avgs else None

        values = [
            f"{account_avg:.2f}" if account_avg else "—",
            f"{best_reaction:.2f}",
            str(len(sessions)),
            str(perfect),
        ]
        for i, (_, v, l) in enumerate(self._stat_cards):
            v.setText(values[i])
            l.setText(labels[i])

    def _draw_charts(self, sessions):
        for i in reversed(range(self._chart_layout.count())):
            ww = self._chart_layout.itemAt(i).widget()
            if ww:
                ww.deleteLater()

        if not sessions or len(sessions) < 2:
            ph = QLabel("Проведи хотя бы 2 тренировки, чтобы увидеть графики прогресса.")
            ph.setAlignment(Qt.AlignCenter)
            ph.setFont(QFont("Segoe UI", 12))
            ph.setStyleSheet(f"color: {styles.COLORS['text_soft']}; padding: 28px;")
            self._chart_layout.addWidget(ph)
            return

        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
            from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
            from datetime import datetime

            rev = list(reversed(sessions))
            dates = []
            for s in rev:
                try:
                    dates.append(datetime.fromisoformat(s['date'][:19]))
                except Exception:
                    dates.append(datetime.now())

            best_times = [s['min_reaction'] for s in rev]
            avg_times  = [s['avg_reaction']  for s in rev]
            errors     = [s['total_wrong']   for s in rev]

            fig, axes = plt.subplots(1, 3, figsize=(12, 3.2))
            fig.patch.set_facecolor('white')
            green, yellow, red, soft, dark = '#22C55E', '#F5C842', '#EF4444', '#94A3B8', '#0F172A'

            def style_ax(ax, title):
                ax.set_title(title, fontsize=11, fontweight='bold', color=dark, pad=10)
                ax.set_facecolor('white')
                for spine in ['top', 'right']:
                    ax.spines[spine].set_visible(False)
                ax.spines['left'].set_color('#E2E8F0')
                ax.spines['bottom'].set_color('#E2E8F0')
                ax.tick_params(colors=soft, labelsize=9)
                ax.grid(axis='y', color='#F2F4F7', linewidth=1)
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
                ax.xaxis.set_major_locator(mdates.AutoDateLocator())
                plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha='right')

            def line_plot(ax, color, data, title, ylabel):
                ax.plot(dates, data, color=color, linewidth=2.5,
                        marker='o', markersize=6,
                        markerfacecolor='white', markeredgecolor=color, markeredgewidth=2)
                ax.fill_between(dates, data, alpha=0.10, color=color)
                style_ax(ax, title)
                ax.set_ylabel(ylabel, fontsize=9, color=soft)

            line_plot(axes[0], green,  best_times, 'Лучшее время реакции (мс)', 'мс')
            line_plot(axes[1], yellow, avg_times,  'Среднее время реакции (мс)', 'мс')
            line_plot(axes[2], red,    errors,     'Количество ошибок', 'шт.')
            axes[2].yaxis.set_major_locator(plt.MaxNLocator(integer=True))

            plt.tight_layout(pad=2.0)
            canvas = FigureCanvas(fig)
            canvas.setFixedHeight(290)
            self._chart_layout.addWidget(canvas)
            plt.close(fig)

        except ImportError:
            ph = QLabel("⚠️ Установи matplotlib: pip install matplotlib")
            ph.setAlignment(Qt.AlignCenter)
            ph.setFont(QFont("Segoe UI", 11))
            ph.setStyleSheet(f"color: {styles.COLORS['text_soft']}; padding: 20px;")
            self._chart_layout.addWidget(ph)

    def _fill_table(self, sessions):
        self._table.setRowCount(0)
        if not sessions:
            self._table.setRowCount(1)
            item = QTableWidgetItem("Пока нет тренировок — начни первую!")
            item.setTextAlignment(Qt.AlignCenter)
            item.setForeground(QColor(styles.COLORS['text_soft']))
            self._table.setSpan(0, 0, 1, 6)
            self._table.setItem(0, 0, item)
            self._table.setRowHeight(0, 60)
            return

        self._table.setRowCount(len(sessions))
        for row, s in enumerate(sessions):
            date_str = s['date'][:16].replace('T', ' ')
            values = [
                date_str,
                f"{s['avg_reaction']:.2f} мс",
                f"{s['min_reaction']:.2f} мс",
                f"{s['max_reaction']:.2f} мс",
                f"±{s['std_deviation']:.2f} мс",
                str(s['total_wrong'])
            ]
            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                if col == 5:
                    item.setForeground(QColor(
                        styles.COLORS['accent_green'] if s['total_wrong'] == 0
                        else styles.COLORS['accent_red']
                    ))
                self._table.setItem(row, col, item)
            self._table.setRowHeight(row, 44)

    # ─── Авторизация ──────────────────────────────────────────────────
    def _validate_nick(self, username, error_label):
        username = username.strip()
        if len(username) < 2:
            if error_label:
                error_label.setText("Никнейм слишком короткий (минимум 2 символа)")
            return False
        if len(username) > 16:
            if error_label:
                error_label.setText("Никнейм слишком длинный (максимум 16 символов)")
            return False
        return True

    def _register(self):
        username = self._login_input.text().strip()
        if not self._validate_nick(username, self._login_error):
            return
        if self.db.username_exists(username):
            self._login_error.setText("Пользователь с таким ником уже существует")
            return
        user_id = self.db.create_user(username)
        if user_id:
            user = self.db.get_user(username)
            self.main_window.on_user_changed(user)
            self.refresh()
        else:
            self._login_error.setText("Ошибка при создании пользователя")

    def _login(self):
        username = self._login_input.text().strip()
        if not self._validate_nick(username, self._login_error):
            return
        user = self.db.get_user(username)
        if user:
            self.db.set_active_user(user['id'])
            self.main_window.on_user_changed(user)
            self.refresh()
        else:
            self._login_error.setText("Пользователь не найден — попробуй зарегистрироваться")

    def _logout(self):
        self.db.clear_active_user()
        self.main_window.on_user_changed(None)
        self.refresh()

    def _toggle_edit(self):
        self._editing = not self._editing
        self._edit_frame.setVisible(self._editing)

    # ─── ОДНА кнопка сохранения ───────────────────────────────────────
    def _save_all(self):
        """Сохраняет никнейм + возраст + пол одной кнопкой."""
        self._edit_error.setText("")
        user = self.main_window.current_user
        if not user:
            return

        # 1. Никнейм
        new_nick = self._nick_input.text().strip()
        if not self._validate_nick(new_nick, self._edit_error):
            return

        if new_nick != user['username']:
            if self.db.username_exists(new_nick):
                self._edit_error.setText("Пользователь с таким ником уже существует")
                return
            success = self.db.update_username(user['id'], new_nick)
            if not success:
                self._edit_error.setText("Не удалось изменить никнейм")
                return
            user['username'] = new_nick
            self.main_window.current_user = user

        # 2. Возраст
        age_text = self._age_input.text().strip()
        age = None
        if age_text:
            try:
                age = int(age_text)
                if not (0 <= age <= 120):
                    self._edit_error.setText("Введи корректный возраст (0–120)")
                    return
            except ValueError:
                self._edit_error.setText("Возраст должен быть числом")
                return

        # 3. Пол
        gender = self._gender_combo.currentText()

        # 4. Сохраняем возраст + пол
        self.db.update_user_profile(user['id'], age, gender)
        user['age']    = age
        user['gender'] = gender
        self.main_window.current_user = user

        # Обновляем отображение
        self.main_window.on_user_changed(user)
        self._load_user_data(user)
        self._edit_frame.hide()
        self._editing = False

    # Оставляем для совместимости
    def _save_username(self):
        self._save_all()

    def _save_profile(self):
        self._save_all()

    def _delete_account(self):
        user = self.main_window.current_user
        reply = QMessageBox.question(
            self, "Удалить аккаунт",
            f"Ты уверен, что хочешь удалить аккаунт «{user['username']}»?\n\n"
            "Все данные тренировок будут безвозвратно удалены.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.db.delete_user(user['id'])
            self.main_window.on_user_changed(None)
            self.refresh()

    # ─── PDF-экспорт профиля ─────────────────────────────────────────
    def _export_profile_pdf(self):
        user = self.main_window.current_user
        if not user:
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить профиль в PDF",
            f"profile_{user['username']}.pdf",
            "PDF Files (*.pdf)"
        )
        if not path:
            return

        try:
            from reportlab.pdfgen import canvas as rl_canvas
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            from datetime import datetime
            import os

            font_name = "Helvetica"
            for fp in [
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
                "C:/Windows/Fonts/arial.ttf",
            ]:
                if os.path.exists(fp):
                    try:
                        pdfmetrics.registerFont(TTFont("CustomFont", fp))
                        font_name = "CustomFont"
                    except Exception:
                        pass
                    break

            sessions = self.db.get_user_sessions(user['id'])
            c = rl_canvas.Canvas(path, pagesize=A4)
            w_pg, h_pg = A4

            def draw_text(x, y, text, size=12, bold=False, color=(0.06, 0.09, 0.16)):
                fn = font_name
                if bold and font_name == "Helvetica":
                    fn = "Helvetica-Bold"
                c.setFont(fn, size)
                c.setFillColorRGB(*color)
                c.drawString(x, y, text)

            # Заголовок
            draw_text(50, h_pg - 55, "Детектор реакции - Профиль пользователя", 20, bold=True)
            draw_text(50, h_pg - 78, f"Дата экспорта: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
                      11, color=(0.58, 0.67, 0.72))

            c.setStrokeColorRGB(0.89, 0.91, 0.94)
            c.line(50, h_pg - 92, w_pg - 50, h_pg - 92)

            # Данные пользователя
            y = h_pg - 118
            draw_text(50, y, "Информация о пользователе:", 14, bold=True)
            y -= 22
            draw_text(60, y, f"Никнейм: {user['username']}", 12)
            y -= 18
            draw_text(60, y, f"Возраст: {age_label(user.get('age'))}", 12)
            y -= 18
            draw_text(60, y, f"Пол: {user.get('gender') or 'Не указан'}", 12)
            y -= 26

            c.line(50, y, w_pg - 50, y)
            y -= 22

            # Общая статистика
            draw_text(50, y, "Общая статистика:", 14, bold=True)
            y -= 22
            if sessions:
                best_reaction = min(s['min_reaction'] for s in sessions)
                avg_all = sum(s['avg_reaction'] for s in sessions) / len(sessions)
                perfect = sum(1 for s in sessions if s['total_wrong'] == 0)
                total_wrong = sum(s['total_wrong'] for s in sessions)
                draw_text(60, y, f"Всего тренировок: {len(sessions)}", 12);      y -= 18
                draw_text(60, y, f"Лучшая реакция: {best_reaction:.2f} мс", 12); y -= 18
                draw_text(60, y, f"Среднее по всем тренировкам: {avg_all:.2f} мс", 12); y -= 18
                draw_text(60, y, f"Тренировок без ошибок: {perfect}", 12);       y -= 18
                draw_text(60, y, f"Всего ошибок: {total_wrong}", 12);            y -= 26
            else:
                draw_text(60, y, "Тренировок ещё не было.", 12, color=(0.58, 0.67, 0.72))
                y -= 26

            c.line(50, y, w_pg - 50, y)
            y -= 22

            # История тренировок
            draw_text(50, y, "История тренировок:", 14, bold=True)
            y -= 22

            if sessions:
                headers = ["Дата",         "Среднее", "Лучшее",  "Худшее",  "±Вар.", "Ошибки"]
                col_x   = [60, 185, 270,   345,       420,       490]
                col_w   = [120, 80, 70,    70,        65,        55]

                # Шапка таблицы
                c.setFillColorRGB(0.95, 0.96, 0.97)
                c.rect(50, y - 4, w_pg - 100, 18, fill=1, stroke=0)
                for i, h_txt in enumerate(headers):
                    draw_text(col_x[i], y, h_txt, 10, bold=True, color=(0.28, 0.34, 0.41))
                y -= 20

                for s in sessions[:30]:  # max 30 строк
                    if y < 60:
                        c.showPage()
                        y = h_pg - 60
                    date_str = s['date'][:16].replace('T', ' ')
                    row_vals = [
                        date_str,
                        f"{s['avg_reaction']:.1f} мс",
                        f"{s['min_reaction']:.1f} мс",
                        f"{s['max_reaction']:.1f} мс",
                        f"±{s['std_deviation']:.1f}",
                        str(s['total_wrong'])
                    ]
                    for i, val in enumerate(row_vals):
                        col = (0.80, 0.10, 0.10) if i == 5 and s['total_wrong'] > 0 \
                              else (0.10, 0.55, 0.20) if i == 5 \
                              else (0.06, 0.09, 0.16)
                        draw_text(col_x[i], y, val, 10, color=col)
                    y -= 17
                    c.setStrokeColorRGB(0.93, 0.94, 0.96)
                    c.line(50, y + 3, w_pg - 50, y + 3)
            else:
                draw_text(60, y, "Нет данных.", 11, color=(0.58, 0.67, 0.72))

            c.save()
            QMessageBox.information(self, "Готово", f"PDF сохранён:\n{path}")

        except ImportError:
            QMessageBox.warning(
                self, "Ошибка",
                "Не установлен reportlab.\nВыполни: pip install reportlab"
            )
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать PDF:\n{str(e)}")
