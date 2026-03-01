from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QTableWidget,
    QTableWidgetItem, QHeaderView, QComboBox, QSlider, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
import styles


class LeadersPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.db = main_window.db
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 36, 40, 36)
        layout.setSpacing(16)

        title = QLabel("🏆 Таблица лидеров")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setStyleSheet(f"color: {styles.COLORS['text_dark']};")
        layout.addWidget(title)

        sub = QLabel("Лучшие результаты среди всех игроков")
        sub.setFont(QFont("Segoe UI", 13))
        sub.setStyleSheet(f"color: {styles.COLORS['text_soft']};")
        layout.addWidget(sub)

        # ── Фильтры ───────────────────────────────────────────────────
        filters_frame = QFrame()
        filters_frame.setStyleSheet(
            f"QFrame {{ background-color: {styles.COLORS['bg_soft']}; "
            f"border-radius: 12px; border: 1.5px solid {styles.COLORS['border']}; }}"
        )
        fi = QVBoxLayout(filters_frame)
        fi.setContentsMargins(18, 14, 18, 14)
        fi.setSpacing(10)

        combo_style = f"""
            QComboBox {{
                padding: 5px 10px;
                border: 1.5px solid {styles.COLORS['border']};
                border-radius: 8px;
                background: white;
                color: {styles.COLORS['text_dark']};
                font-size: 12px;
                min-width: 160px;
            }}
            QComboBox:hover {{ border-color: {styles.COLORS['accent_yellow']}; }}
            QComboBox::drop-down {{ border: none; width: 20px; }}
            QComboBox QAbstractItemView {{
                background: white;
                border: 1.5px solid {styles.COLORS['border']};
                selection-background-color: {styles.COLORS['accent_yellow']};
            }}
        """
        lbl_style = f"color: {styles.COLORS['text_dark']}; font-size: 12px; background: transparent; border: none;"

        # Строка 1: критерий + пол + сложность
        row1 = QHBoxLayout()
        row1.setSpacing(16)

        row1.addWidget(self._filter_label("Критерий:", lbl_style))
        self._criterion_combo = QComboBox()
        self._criterion_combo.addItems([
            "Среднее значение", "Лучший результат",
            "Тренировок", "Без ошибок"
        ])
        self._criterion_combo.setStyleSheet(combo_style)
        self._criterion_combo.currentIndexChanged.connect(self._apply_filters)
        row1.addWidget(self._criterion_combo)

        row1.addSpacing(8)
        row1.addWidget(self._filter_label("Пол:", lbl_style))
        self._gender_combo = QComboBox()
        self._gender_combo.addItems(["Все", "Мужчина", "Женщина"])
        self._gender_combo.setStyleSheet(combo_style)
        self._gender_combo.currentIndexChanged.connect(self._apply_filters)
        row1.addWidget(self._gender_combo)

        row1.addSpacing(8)
        row1.addWidget(self._filter_label("Сложность:", lbl_style))
        self._diff_combo = QComboBox()
        self._diff_combo.addItems(["Все", "Лёгкий", "Средний", "Сложный"])
        self._diff_combo.setStyleSheet(combo_style)
        self._diff_combo.currentIndexChanged.connect(self._apply_filters)
        row1.addWidget(self._diff_combo)

        row1.addStretch()
        fi.addLayout(row1)

        # Строка 2: возраст (два ползунка — «от» и «до»)
        row2 = QHBoxLayout()
        row2.setSpacing(12)
        row2.addWidget(self._filter_label("Возраст:", lbl_style))

        self._age_all_lbl = QLabel("Все возрасты")
        self._age_all_lbl.setFont(QFont("Segoe UI", 11))
        self._age_all_lbl.setStyleSheet(lbl_style)
        row2.addWidget(self._age_all_lbl)

        slider_style = f"""
            QSlider::groove:horizontal {{
                height: 5px;
                background: {styles.COLORS['border']};
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {styles.COLORS['accent_yellow']};
                border: 2px solid white;
                width: 18px; height: 18px;
                margin: -7px 0;
                border-radius: 9px;
            }}
            QSlider::handle:horizontal:hover {{ background: {styles.COLORS['accent_orange']}; }}
            QSlider::sub-page:horizontal {{
                background: {styles.COLORS['accent_yellow']};
                border-radius: 2px;
                height: 5px;
            }}
        """

        def make_age_slider_block(label_text, default_val):
            wrap = QWidget()
            wrap.setFixedWidth(220)
            layout = QVBoxLayout(wrap)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(2)

            top_row = QHBoxLayout()
            lbl = QLabel(label_text)
            lbl.setFont(QFont("Segoe UI", 10))
            lbl.setStyleSheet(lbl_style)
            bubble = QLabel(str(default_val) if default_val > 0 else "Все")
            bubble.setFont(QFont("Segoe UI", 10, QFont.Bold))
            bubble.setAlignment(Qt.AlignCenter)
            bubble.setFixedSize(44, 22)
            bubble.setStyleSheet(
                f"color: {styles.COLORS['text_dark']}; background-color: {styles.COLORS['accent_yellow']}; border-radius: 8px;"
            )
            top_row.addWidget(lbl)
            top_row.addStretch()
            top_row.addWidget(bubble)
            layout.addLayout(top_row)

            slider = QSlider(Qt.Horizontal)
            slider.setMinimum(0)
            slider.setMaximum(80)
            slider.setValue(default_val)
            slider.setFixedHeight(28)
            slider.setStyleSheet(slider_style)
            layout.addWidget(slider)

            minmax = QHBoxLayout()
            l0 = QLabel("Все"); l0.setFont(QFont("Segoe UI", 9)); l0.setStyleSheet(lbl_style)
            l80 = QLabel("80+"); l80.setFont(QFont("Segoe UI", 9)); l80.setStyleSheet(lbl_style)
            minmax.addWidget(l0); minmax.addStretch(); minmax.addWidget(l80)
            layout.addLayout(minmax)

            return wrap, slider, bubble

        from_wrap, self._age_from_slider, self._age_from_bubble = make_age_slider_block("От:", 0)
        to_wrap,   self._age_to_slider,   self._age_to_bubble   = make_age_slider_block("До:", 0)

        def on_age_from(val):
            # «от» не должен быть больше «до» (если «до» > 0)
            to_val = self._age_to_slider.value()
            if to_val > 0 and val > to_val:
                self._age_from_slider.setValue(to_val)
                return
            self._age_from_bubble.setText(str(val) if val > 0 else "Все")
            self._update_age_label()
            self._apply_filters()

        def on_age_to(val):
            from_val = self._age_from_slider.value()
            if val > 0 and val < from_val:
                self._age_to_slider.setValue(from_val)
                return
            self._age_to_bubble.setText(str(val) if val > 0 else "Все")
            self._update_age_label()
            self._apply_filters()

        self._age_from_slider.valueChanged.connect(on_age_from)
        self._age_to_slider.valueChanged.connect(on_age_to)

        row2.addWidget(from_wrap)
        row2.addSpacing(8)
        row2.addWidget(to_wrap)
        row2.addStretch()
        fi.addLayout(row2)

        layout.addWidget(filters_frame)

        # ── Таблица ───────────────────────────────────────────────────
        self._table = QTableWidget()
        self._table.setColumnCount(8)
        self._table.setHorizontalHeaderLabels([
            "#", "Игрок", "Возраст", "Пол", "Среднее значение (мс)",
            "Лучший результат (мс)", "Тренировок", "Без ошибок"
        ])
        self._table.setShowGrid(False)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setStyleSheet(f"""
            QTableWidget {{
                border: 1.5px solid {styles.COLORS['border']}; border-radius: 14px;
                background-color: white; font-size: 13px; outline: none; gridline-color: transparent;
            }}
            QTableWidget::item {{
                padding: 12px 16px; color: {styles.COLORS['text_dark']};
                border-bottom: 1px solid {styles.COLORS['bg_soft']};
            }}
            QTableWidget::item:selected {{
                background-color: {styles.COLORS['bg_soft']};
                color: {styles.COLORS['text_dark']};
            }}
            QTableWidget::item:alternate {{ background-color: {styles.COLORS['bg_white']}; }}
            QHeaderView::section {{
                background-color: {styles.COLORS['bg_soft']}; color: {styles.COLORS['text_mid']};
                padding: 10px 16px; border: none; font-weight: bold; font-size: 11px;
            }}
        """)
        hdr = self._table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.Fixed)
        self._table.setColumnWidth(0, 50)
        hdr.setSectionResizeMode(1, QHeaderView.Stretch)
        hdr.setMinimumSectionSize(90)
        for i in range(2, 8):
            hdr.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        layout.addWidget(self._table)

    def _filter_label(self, text, style):
        lbl = QLabel(text)
        lbl.setFont(QFont("Segoe UI", 12))
        lbl.setStyleSheet(style)
        return lbl

    def _update_age_label(self):
        from_val = self._age_from_slider.value()
        to_val   = self._age_to_slider.value()
        if from_val == 0 and to_val == 0:
            self._age_all_lbl.setText("Все возрасты")
        elif from_val == 0:
            self._age_all_lbl.setText(f"До {to_val} лет")
        elif to_val == 0:
            self._age_all_lbl.setText(f"От {from_val} лет")
        else:
            self._age_all_lbl.setText(f"{from_val} – {to_val} лет")

    def resizeEvent(self, event):
        super().resizeEvent(event)

    def refresh(self):
        self._apply_filters()

    def _apply_filters(self):
        """Читаем всех пользователей из БД, применяем фильтры, отображаем."""
        criterion_idx = self._criterion_combo.currentIndex()
        gender_filter = self._gender_combo.currentText()
        diff_filter   = self._diff_combo.currentText()
        age_from      = self._age_from_slider.value()  # 0 = не ограничено
        age_to        = self._age_to_slider.value()    # 0 = не ограничено

        # Маппинг сложностей
        diff_map = {
            "Лёгкий": "easy",
            "Средний": "medium",
            "Сложный": "hard",
        }
        diff_key = diff_map.get(diff_filter)  # None = все

        data = self.db.get_leaderboard_full(
            gender=None if gender_filter == "Все" else gender_filter,
            age_from=age_from if age_from > 0 else None,
            age_max=age_to if age_to > 0 else None,
            difficulty=diff_key,
            limit=100
        )

        # Сортировка по критерию
        if criterion_idx == 0:    # Среднее значение (min = лучше)
            data.sort(key=lambda x: x.get('avg_account') or 999999)
        elif criterion_idx == 1:  # Лучшая реакция (min = лучше)
            data.sort(key=lambda x: x.get('best_ever') or 999999)
        elif criterion_idx == 2:  # Кол-во тренировок (max = лучше)
            data.sort(key=lambda x: x.get('sessions_count', 0), reverse=True)
        elif criterion_idx == 3:  # Без ошибок (max = лучше)
            data.sort(key=lambda x: x.get('perfect_sessions', 0), reverse=True)

        self._fill_table(data)

    def _fill_table(self, leaderboard):
        user = self.main_window.current_user

        if not leaderboard:
            self._table.setRowCount(1)
            item = QTableWidgetItem("Нет результатов по выбранным фильтрам")
            item.setTextAlignment(Qt.AlignCenter)
            item.setForeground(QColor(styles.COLORS['text_soft']))
            self._table.setSpan(0, 0, 1, 8)
            self._table.setItem(0, 0, item)
            return

        medals = ["🥇", "🥈", "🥉"]
        self._table.clearSpans()
        self._table.setRowCount(len(leaderboard))
        for row, entry in enumerate(leaderboard):
            # Позиция всегда отражает место в текущей отфильтрованной таблице
            rank = medals[row] if row < 3 else str(row + 1)

            age_val    = entry.get('age')
            age_str    = str(age_val) if age_val else "—"
            gender_str = entry.get('gender') or "—"
            avg_acc    = entry.get('avg_account')
            best_ever  = entry.get('best_ever')

            values = [
                rank,
                entry.get('username', '—'),
                age_str,
                gender_str,
                f"{avg_acc:.2f}"   if avg_acc   else "—",
                f"{best_ever:.2f}" if best_ever  else "—",
                str(entry.get('sessions_count', 0)),
                str(entry.get('perfect_sessions', 0)),
            ]
            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                if user and entry.get('username') == user['username']:
                    item.setBackground(QColor("#FFFDF0"))
                    item.setForeground(QColor(styles.COLORS['accent_orange']))
                if col == 0 and row < 3:
                    item.setFont(QFont("Segoe UI Emoji", 16))
                self._table.setItem(row, col, item)
            self._table.setRowHeight(row, 50)
