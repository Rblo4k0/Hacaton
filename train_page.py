from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QProgressBar, QMessageBox, QSlider, QSizePolicy,
    QFileDialog
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QImage, QPixmap
import cv2
import styles
from trainer_logic import DIFFICULTY_SETTINGS


DIFF_STYLES = {
    "easy":   {"bg": "#F0FDF4", "border": "#22C55E", "text": "#15803D"},
    "medium": {"bg": "#FFFBEB", "border": "#F5C842", "text": "#92400E"},
    "hard":   {"bg": "#FFF1F2", "border": "#EF4444", "text": "#991B1B"},
}


class DifficultyCard(QFrame):
    def __init__(self, key, settings, parent=None):
        super().__init__(parent)
        self.key = key
        self._selected = False
        self._ds = DIFF_STYLES[key]
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(100)
        self._on_click = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 12, 18, 12)
        layout.setSpacing(4)

        top = QHBoxLayout()
        top.setSpacing(8)
        emoji = QLabel(settings["emoji"])
        emoji.setFont(QFont("Segoe UI Emoji", 16))
        emoji.setStyleSheet("border: none; background: transparent;")
        top.addWidget(emoji)

        lbl = QLabel(settings["label"])
        lbl.setFont(QFont("Segoe UI", 13, QFont.Bold))
        lbl.setStyleSheet(f"color: {self._ds['text']}; border: none; background: transparent;")
        top.addWidget(lbl)
        top.addStretch()
        layout.addLayout(top)

        desc = QLabel(settings["description"])
        desc.setFont(QFont("Segoe UI", 10))
        desc.setStyleSheet(f"color: {styles.COLORS['text_soft']}; border: none; background: transparent;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self._update_style()

    def set_selected(self, val):
        self._selected = val
        self._update_style()

    def _update_style(self):
        if self._selected:
            self.setStyleSheet(f"""
                DifficultyCard {{
                    background-color: {self._ds['bg']};
                    border-radius: 14px;
                    border: 2.5px solid {self._ds['border']};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                DifficultyCard {{
                    background-color: white;
                    border-radius: 14px;
                    border: 1.5px solid {styles.COLORS['border']};
                }}
            """)

    def mousePressEvent(self, event):
        if self._on_click:
            self._on_click()
        super().mousePressEvent(event)


class TrainPage(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.db = main_window.db
        self._selected_difficulty = "medium"
        self._session_active = False
        self._waiting = False
        self._round_active = False
        self._last_gesture = None
        self._neutral_held = False     # держит ли пользователь нейтральный жест
        self._session_ended = False
        self._last_stats = None        # для PDF-экспорта
        self.cap = None
        self.detector = None
        self.trainer = None
        self._build()
        self._video_timer = QTimer()
        self._video_timer.timeout.connect(self._update_frame)
        self._next_timer = QTimer()
        self._next_timer.timeout.connect(self._next_round)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── IDLE ──────────────────────────────────────────────────────
        self._idle_widget = QWidget()
        idle = QVBoxLayout(self._idle_widget)
        idle.setContentsMargins(48, 36, 48, 36)
        idle.setSpacing(0)

        title = QLabel("🎯 Настройка тренировки")
        title.setFont(QFont("Segoe UI", 22, QFont.Bold))
        title.setStyleSheet(f"color: {styles.COLORS['text_dark']};")
        idle.addWidget(title)

        sub = QLabel("Выбери уровень сложности и количество раундов")
        sub.setFont(QFont("Segoe UI", 13))
        sub.setStyleSheet(f"color: {styles.COLORS['text_soft']}; margin-top: 4px;")
        idle.addWidget(sub)
        idle.addSpacing(28)

        diff_lbl = QLabel("Уровень сложности")
        diff_lbl.setFont(QFont("Segoe UI", 13, QFont.Bold))
        diff_lbl.setStyleSheet(f"color: {styles.COLORS['text_dark']};")
        idle.addWidget(diff_lbl)
        idle.addSpacing(10)

        diff_row = QHBoxLayout()
        diff_row.setSpacing(12)
        self._diff_cards = {}
        for key, settings in DIFFICULTY_SETTINGS.items():
            card = DifficultyCard(key, settings)
            card._on_click = lambda k=key: self._select_difficulty(k)
            self._diff_cards[key] = card
            diff_row.addWidget(card)
        idle.addLayout(diff_row)
        idle.addSpacing(28)

        # ── Ползунок раундов ──────────────────────────────────────────
        rounds_lbl = QLabel("Количество раундов")
        rounds_lbl.setFont(QFont("Segoe UI", 13, QFont.Bold))
        rounds_lbl.setStyleSheet(f"color: {styles.COLORS['text_dark']};")
        idle.addWidget(rounds_lbl)
        idle.addSpacing(8)

        slider_container = QWidget()
        slider_container.setFixedWidth(420)
        # Увеличиваем верхний отступ, чтобы пузырёк не обрезался
        slider_container.setContentsMargins(0, 0, 0, 0)
        sc_layout = QVBoxLayout(slider_container)
        sc_layout.setContentsMargins(0, 0, 0, 0)
        sc_layout.setSpacing(2)

        # Пузырёк с числом — фиксированная высота, не обрезается
        bubble_wrap = QWidget()
        bubble_wrap.setFixedHeight(32)
        bubble_wrap.setStyleSheet("background: transparent;")
        self._bubble_wrap = bubble_wrap

        self._rounds_value_label = QLabel("10", bubble_wrap)
        self._rounds_value_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self._rounds_value_label.setAlignment(Qt.AlignCenter)
        self._rounds_value_label.setFixedSize(38, 26)
        self._rounds_value_label.setStyleSheet(f"""
            color: white;
            background-color: {styles.COLORS['accent_yellow']};
            border-radius: 10px;
        """)
        self._rounds_value_label.move(0, 3)

        sc_layout.addWidget(bubble_wrap)

        self._slider = QSlider(Qt.Horizontal)
        self._slider.setMinimum(5)
        self._slider.setMaximum(50)
        self._slider.setValue(10)
        self._slider.setTickPosition(QSlider.NoTicks)
        self._slider.setFixedHeight(32)
        self._slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                height: 6px;
                background: {styles.COLORS['border']};
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {styles.COLORS['accent_yellow']};
                border: 2px solid white;
                width: 22px; height: 22px;
                margin: -8px 0;
                border-radius: 11px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {styles.COLORS['accent_orange']};
            }}
            QSlider::sub-page:horizontal {{
                background: {styles.COLORS['accent_yellow']};
                border-radius: 3px;
                height: 6px;
            }}
        """)
        self._slider.valueChanged.connect(self._on_slider_change)
        sc_layout.addWidget(self._slider)

        # Подписи мин/макс
        minmax_row = QHBoxLayout()
        min_lbl = QLabel("5")
        min_lbl.setFont(QFont("Segoe UI", 10))
        min_lbl.setStyleSheet(f"color: {styles.COLORS['text_soft']};")
        max_lbl = QLabel("50")
        max_lbl.setFont(QFont("Segoe UI", 10))
        max_lbl.setStyleSheet(f"color: {styles.COLORS['text_soft']};")
        minmax_row.addWidget(min_lbl)
        minmax_row.addStretch()
        minmax_row.addWidget(max_lbl)
        sc_layout.addLayout(minmax_row)

        idle.addWidget(slider_container)
        # Обновляем позицию после добавления в layout
        QTimer.singleShot(0, self._update_bubble_position)

        idle.addSpacing(32)

        btn_row = QHBoxLayout()
        self._start_btn = QPushButton("Начать тренировку")
        self._start_btn.setCursor(Qt.PointingHandCursor)
        self._start_btn.setFixedHeight(54)
        self._start_btn.setFixedWidth(240)
        self._start_btn.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self._start_btn.setStyleSheet(styles.BUTTON_PRIMARY)
        self._start_btn.clicked.connect(self._start_session)
        btn_row.addWidget(self._start_btn)
        btn_row.addStretch()
        idle.addLayout(btn_row)

        self._idle_guest_hint = QLabel("")
        self._idle_guest_hint.setFont(QFont("Segoe UI", 11))
        self._idle_guest_hint.setStyleSheet(f"color: {styles.COLORS['text_soft']}; margin-top: 8px;")
        idle.addWidget(self._idle_guest_hint)
        idle.addStretch()
        root.addWidget(self._idle_widget)

        # ── ACTIVE ────────────────────────────────────────────────────
        self._active_widget = QWidget()
        self._active_widget.hide()
        active = QHBoxLayout(self._active_widget)
        active.setContentsMargins(24, 20, 24, 20)
        active.setSpacing(16)

        self._stim_frame = QFrame()
        self._stim_frame.setMinimumWidth(360)
        stim_l = QVBoxLayout(self._stim_frame)
        stim_l.setAlignment(Qt.AlignCenter)

        self._stim_label = QLabel("●")
        self._stim_label.setFont(QFont("Segoe UI", 80))
        self._stim_label.setAlignment(Qt.AlignCenter)
        stim_l.addWidget(self._stim_label)

        self._color_hint = QLabel("")
        self._color_hint.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self._color_hint.setAlignment(Qt.AlignCenter)
        stim_l.addWidget(self._color_hint)
        active.addWidget(self._stim_frame, 1)

        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(12)

        self._video_label = QLabel()
        self._video_label.setFixedSize(440, 330)
        self._video_label.setStyleSheet(
            f"background-color: #0F172A; border-radius: 14px; border: 2px solid {styles.COLORS['border']};"
        )
        self._video_label.setAlignment(Qt.AlignCenter)
        rl.addWidget(self._video_label)

        self._hand_status = QLabel("Рука не обнаружена")
        self._hand_status.setFont(QFont("Segoe UI", 11))
        self._hand_status.setStyleSheet(f"color: {styles.COLORS['text_soft']};")
        self._hand_status.setAlignment(Qt.AlignCenter)
        rl.addWidget(self._hand_status)

        stats_frame = QFrame()
        stats_frame.setStyleSheet(
            f"QFrame {{ background-color: white; border-radius: 12px; border: 1.5px solid {styles.COLORS['border']}; }}"
        )
        si = QHBoxLayout(stats_frame)
        si.setContentsMargins(16, 12, 16, 12)
        self._time_lbl    = self._stat_lbl("⏱ 0.00 мс", "Среднее")
        self._wrong_lbl   = self._stat_lbl("❌ 0",       "Ошибки")
        self._progress_lbl = self._stat_lbl("0 / 10",    "Раундов")
        si.addWidget(self._time_lbl[0])
        si.addWidget(self._make_div())
        si.addWidget(self._wrong_lbl[0])
        si.addWidget(self._make_div())
        si.addWidget(self._progress_lbl[0])
        rl.addWidget(stats_frame)

        self._progress_bar = QProgressBar()
        self._progress_bar.setMaximum(10)
        self._progress_bar.setValue(0)
        self._progress_bar.setFixedHeight(8)
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setStyleSheet(f"""
            QProgressBar {{ border-radius: 4px; background-color: {styles.COLORS['bg_soft']}; border: none; }}
            QProgressBar::chunk {{ border-radius: 4px; background-color: {styles.COLORS['accent_yellow']}; }}
        """)
        rl.addWidget(self._progress_bar)
        # Кнопка досрочного завершения УДАЛЕНА по требованию

        active.addWidget(right, 1)
        root.addWidget(self._active_widget)

        self._select_difficulty("medium")
        self._update_idle_hint()
        self._reset_round_style()

    # ─── Ползунок ────────────────────────────────────────────────────
    def _on_slider_change(self, value):
        self._rounds_value_label.setText(str(value))
        self._update_bubble_position()

    def _update_bubble_position(self):
        """Позиционируем пузырёк над ползунком (абсолютно внутри bubble_wrap)."""
        if not hasattr(self, '_slider') or not hasattr(self, '_bubble_wrap'):
            return
        val = self._slider.value()
        mn, mx = self._slider.minimum(), self._slider.maximum()
        ratio = (val - mn) / (mx - mn)
        # Ширина дорожки ≈ ширина слайдера минус поля handle
        track_w = self._slider.width() - 22
        px = int(ratio * track_w)
        bw = self._rounds_value_label.width()
        x = max(0, min(px - bw // 2 + 11, self._bubble_wrap.width() - bw))
        self._rounds_value_label.move(x, 3)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_bubble_position()

    # ─── Helpers ─────────────────────────────────────────────────────
    def _stat_lbl(self, value, label):
        frame = QWidget()
        fl = QVBoxLayout(frame)
        fl.setContentsMargins(8, 0, 8, 0)
        fl.setSpacing(2)
        fl.setAlignment(Qt.AlignCenter)
        v = QLabel(value)
        v.setFont(QFont("Segoe UI", 14, QFont.Bold))
        v.setStyleSheet(f"color: {styles.COLORS['text_dark']};")
        v.setAlignment(Qt.AlignCenter)
        l = QLabel(label)
        l.setFont(QFont("Segoe UI", 9))
        l.setStyleSheet(f"color: {styles.COLORS['text_soft']};")
        l.setAlignment(Qt.AlignCenter)
        fl.addWidget(v)
        fl.addWidget(l)
        return frame, v

    def _make_div(self):
        d = QFrame()
        d.setFrameShape(QFrame.VLine)
        d.setFixedWidth(1)
        d.setStyleSheet(f"color: {styles.COLORS['border']};")
        return d

    def _select_difficulty(self, key):
        self._selected_difficulty = key
        for k, card in self._diff_cards.items():
            card.set_selected(k == key)

    def update_idle_hint(self):
        user = self.main_window.current_user
        if not user:
            self._idle_guest_hint.setText("⚠️ Войди в профиль, чтобы результаты сохранялись")
        else:
            self._idle_guest_hint.setText(f"✅ Результаты сохранятся для {user['username']}")

    def _update_idle_hint(self):
        self.update_idle_hint()

    def _get_rounds(self):
        return self._slider.value()

    # ─── Тренировка ───────────────────────────────────────────────────
    def _start_session(self):
        import HandTracking as ht
        from trainer_logic import ReactionTrainer

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            QMessageBox.critical(self, "Ошибка", "Камера не найдена.")
            return

        max_trials = self._get_rounds()
        self.trainer = ReactionTrainer(difficulty=self._selected_difficulty, max_trials=max_trials)
        self.detector = ht.HandDetector()
        self._session_active = True
        self._session_ended = False
        self._waiting = False
        self._round_active = False
        self._last_gesture = None
        self._last_processed_gesture = None
        self._neutral_held = False

        self._progress_bar.setMaximum(max_trials)
        self._progress_bar.setValue(0)
        self._progress_lbl[1].setText(f"0 / {max_trials}")
        self._time_lbl[1].setText("⏱ 0.00 мс")
        self._wrong_lbl[1].setText("❌ 0")

        self._idle_widget.hide()
        self._active_widget.show()
        self._video_timer.start(15)
        self._show_neutral_hint()
        # Даём 1.5 сек на подготовку, затем ждём нейтральный жест
        QTimer.singleShot(1500, self._wait_for_neutral_then_start)

    def _wait_for_neutral_then_start(self):
        """Запускаем первый раунд только после того, как пользователь примет нейтральный жест."""
        self._neutral_held = False
        # Проверка нейтрального жеста идёт в _update_frame
        self._waiting_for_neutral = True

    def _end_session(self, aborted=False):
        self._video_timer.stop()
        self._next_timer.stop()
        self._session_active = False
        self._session_ended = True
        if self.cap:
            self.cap.release()
            self.cap = None
        if not aborted and self.trainer:
            stats, trials_data = self.trainer.reset_session()
            user = self.main_window.current_user
            if user:
                self.db.save_session(user['id'], stats, trials_data)
            self._last_stats = stats
            self._show_results(stats)
        else:
            self._active_widget.hide()
            self._idle_widget.show()
            self._update_idle_hint()

    def _show_results(self, stats):
        self._active_widget.hide()
        self._idle_widget.show()
        self._update_idle_hint()

        diff_key   = stats.get('difficulty', 'medium')
        diff_label = stats.get('difficulty_label', 'Средний')
        diff_emoji = DIFFICULTY_SETTINGS[diff_key]['emoji']

        msg = QMessageBox(self)
        msg.setWindowTitle("Результаты тренировки")
        msg.setStyleSheet(f"""
            QMessageBox {{ background-color: white; }}
            QMessageBox QLabel {{
                color: {styles.COLORS['text_dark']};
                font-size: 13px; padding: 16px; min-width: 320px;
            }}
            QPushButton {{
                background-color: {styles.COLORS['accent_yellow']};
                color: {styles.COLORS['text_dark']};
                border: none; border-radius: 10px;
                padding: 8px 28px; font-weight: bold; font-size: 13px;
            }}
            QPushButton:hover {{ background-color: {styles.COLORS['accent_orange']}; color: white; }}
        """)
        msg.setText(
            f"{diff_emoji}  Уровень: {diff_label}\n\n"
            f"📊  Раундов сыграно: {stats.get('total_rounds', stats.get('total_rounds', 0))}\n"
            f"❌  Ошибок: {stats['total_wrong']}\n"
            f"⏱  Среднее время реакции: {stats['avg_reaction_time']:.2f} мс\n"
            f"⚡  Лучшее время реакции: {stats['min_reaction']:.2f} мс\n"
            f"📈  Вариативность: ±{stats['std_deviation']:.2f} мс"
        )

        pdf_btn = msg.addButton("📄 Экспорт в PDF", QMessageBox.ActionRole)
        ok_btn  = msg.addButton("В профиль →",     QMessageBox.AcceptRole)
        msg.exec()

        if msg.clickedButton() == pdf_btn:
            self._export_pdf(stats)
            # После экспорта всё равно переходим в профиль
        self.main_window.navigate_to(2)

    # ─── Нейтральный жест ────────────────────────────────────────────
    def _show_neutral_hint(self):
        self._reset_round_style()
        self._stim_label.setFont(QFont("Segoe UI Emoji", 80))
        self._stim_label.setText("☝️")
        self._color_hint.setText("Держи нейтральный жест — один палец вверх")
        self._color_hint.setStyleSheet(
            f"color: {styles.COLORS['text_mid']}; font-size: 14px; font-weight: bold;"
        )

    # ─── Кадры камеры ────────────────────────────────────────────────
    def _update_frame(self):
        if not self.cap or not self.cap.isOpened():
            return
        ret, frame = self.cap.read()
        if not ret:
            return

        # Отзеркаливаем по горизонтали — движение руки совпадает с реальным
        frame = cv2.flip(frame, 1)
        frame    = self.detector.find_hands(frame)
        lm_list  = self.detector.find_position(frame)

        if lm_list:
            gesture = self.detector.recognize_gesture()
            # Статус руки
            if gesture == "neutral":
                self._hand_status.setText("☝️ Нейтральный жест")
                self._hand_status.setStyleSheet(f"color: {styles.COLORS['accent_blue']};")
            elif gesture in ("rock", "scissors", "paper"):
                emoji_map = {"rock": "✊", "scissors": "✌️", "paper": "🖐️"}
                self._hand_status.setText(f"{emoji_map[gesture]} Жест распознан")
                self._hand_status.setStyleSheet(f"color: {styles.COLORS['accent_green']};")
            else:
                self._hand_status.setText("✋ Рука видна")
                self._hand_status.setStyleSheet(f"color: {styles.COLORS['text_mid']};")
        else:
            gesture = "unknown"
            self._hand_status.setText("Рука не видна")
            self._hand_status.setStyleSheet(f"color: {styles.COLORS['text_soft']};")

        # ── Ждём нейтральный жест перед первым/следующим раундом ──
        if hasattr(self, '_waiting_for_neutral') and self._waiting_for_neutral:
            if gesture == "neutral":
                if not self._neutral_held:
                    self._neutral_held = True
                    # Нейтральный взят — запускаем раунд через небольшую паузу
                    self._waiting_for_neutral = False
                    delay = self.trainer.get_delay()
                    self._next_timer.start(int(delay * 1000))
            else:
                self._neutral_held = False
            # Пока ждём нейтраль — не обрабатываем жесты для раунда
            self._draw_frame(frame)
            return

        # ── Активный раунд: ждём ответного жеста ──────────────────
        if self._round_active and self._waiting and not self._session_ended:
            if gesture in ("rock", "scissors", "paper"):
                # Засчитываем жест только если он ИЗМЕНИЛСЯ по сравнению с последним
                # обработанным жестом. Это позволяет:
                # - не засчитывать один удерживаемый жест многократно
                # - исправлять ошибки любое количество раз без возврата в нейтраль
                # Нейтраль и unknown сбрасывают блокировку → готов к новому жесту.
                if gesture != self._last_processed_gesture:
                    self._last_processed_gesture = gesture
                    correct, reaction, _ = self.trainer.check_response(gesture)
                    if correct:
                        self._last_processed_gesture = None
                        self._waiting = False
                        self._round_active = False
                        self._reset_round_frame()
                        self._update_stats()
                        if self.trainer.is_session_complete():
                            self._session_ended = True
                            self._next_timer.stop()
                            self._video_timer.stop()
                            if self.cap:
                                self.cap.release()
                                self.cap = None
                            QTimer.singleShot(400, lambda: self._end_session(aborted=False))
                        else:
                            self._show_neutral_hint()
                            self._waiting_for_neutral = True
                            self._neutral_held = False
                    else:
                        self._wrong_lbl[1].setText(f"❌ {self.trainer.total_wrong_in_session}")
                        # Оставляем _last_processed_gesture = gesture.
                        # Смена на любой другой жест → сразу засчитается.
            elif gesture in ("neutral", "unknown"):
                # Сброс блокировки: теперь любой следующий жест засчитается
                self._last_processed_gesture = None

        self._draw_frame(frame)

    def _draw_frame(self, frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame_rgb.shape
        qt_img = QImage(frame_rgb.data, w, h, ch * w, QImage.Format_RGB888)
        self._video_label.setPixmap(
            QPixmap.fromImage(qt_img).scaled(440, 330, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )

    # ─── Раунды ──────────────────────────────────────────────────────
    def _next_round(self):
        if self._session_ended:
            return
        self._next_timer.stop()
        gesture, color = self.trainer.generate_round()
        emoji_map = {"rock": "🪨", "scissors": "✂️", "paper": "🧻"}
        # Начальное состояние нового раунда
        self._last_gesture = None
        self._last_processed_gesture = None
        self._waiting = True
        self._round_active = True

        if color == "green":
            bg, border   = "rgba(34,197,94,0.12)", styles.COLORS['accent_green']
            hint_text    = "🟢 Go — покажи жест, который ПОБЕЖДАЕТ"
            hint_color   = styles.COLORS['accent_green']
        else:
            bg, border   = "rgba(239,68,68,0.12)", styles.COLORS['accent_red']
            hint_text    = "🔴 No-Go — покажи жест, который ПРОИГРЫВАЕТ"
            hint_color   = styles.COLORS['accent_red']

        self._stim_frame.setStyleSheet(
            f"QFrame {{ background-color: {bg}; border-radius: 20px; border: 3px solid {border}; }}"
        )
        self._stim_label.setFont(QFont("Segoe UI Emoji", 110))
        self._stim_label.setText(emoji_map[gesture])
        self._color_hint.setText(hint_text)
        self._color_hint.setStyleSheet(f"color: {hint_color}; font-size: 14px; font-weight: bold;")

    # Псевдоним для совместимости
    def _next_stimulus(self):
        self._next_round()

    def _reset_round_frame(self):
        self._reset_round_style()
        self._stim_label.setFont(QFont("Segoe UI Emoji", 80))
        self._stim_label.setText("☝️")
        self._color_hint.setText("Вернись в нейтральный жест — следующий раунд скоро...")
        self._color_hint.setStyleSheet(f"color: {styles.COLORS['text_soft']}; font-size: 12px;")

    def _reset_round_style(self):
        self._stim_frame.setStyleSheet(
            f"QFrame {{ background-color: white; border-radius: 20px; border: 2px solid {styles.COLORS['border']}; }}"
        )

    # Псевдонимы
    def _reset_stim_frame(self):
        self._reset_round_frame()

    def _reset_stim_style(self):
        self._reset_round_style()

    def _update_stats(self):
        stats = self.trainer.get_stats()
        self._time_lbl[1].setText(f"⏱ {stats['avg_reaction_time']:.2f} мс")
        self._wrong_lbl[1].setText(f"❌ {stats['total_wrong']}")
        self._progress_lbl[1].setText(f"{stats['trials_completed']} / {stats['total_trials']}")
        self._progress_bar.setValue(stats['trials_completed'])

    # ─── PDF-экспорт ─────────────────────────────────────────────────
    def _export_pdf(self, stats=None):
        if stats is None:
            stats = self._last_stats
        if stats is None:
            QMessageBox.warning(self, "Нет данных", "Нет данных для экспорта.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить результат в PDF", "training_result.pdf",
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

            # Пытаемся подключить шрифт с поддержкой кириллицы
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

            c = rl_canvas.Canvas(path, pagesize=A4)
            w, h = A4

            # Заголовок
            c.setFont(font_name, 22)
            c.setFillColorRGB(0.06, 0.09, 0.16)
            c.drawString(50, h - 60, "Детектор реакции - Результат тренировки")

            c.setFont(font_name, 11)
            c.setFillColorRGB(0.58, 0.67, 0.72)
            c.drawString(50, h - 82, datetime.now().strftime("%d.%m.%Y %H:%M"))

            # Линия
            c.setStrokeColorRGB(0.89, 0.91, 0.94)
            c.line(50, h - 96, w - 50, h - 96)

            # Данные
            diff_key   = stats.get('difficulty', 'medium')
            diff_label = stats.get('difficulty_label', 'Средний')
            rows = [
                ("Уровень сложности",        diff_label),
                ("Раундов сыграно",           str(stats.get('total_rounds', stats.get('total_stimuli', '—')))),
                ("Среднее время реакции (мс)",f"{stats['avg_reaction_time']:.2f}"),
                ("Лучшее время реакции (мс)", f"{stats['min_reaction']:.2f}"),
                ("Худшее время реакции (мс)", f"{stats['max_reaction']:.2f}"),
                ("Вариативность (±мс)",       f"{stats['std_deviation']:.2f}"),
                ("Ошибок",                    str(stats['total_wrong'])),
            ]

            y = h - 130
            c.setFont(font_name, 13)
            for label, value in rows:
                c.setFillColorRGB(0.28, 0.34, 0.41)
                c.drawString(60, y, label + ":")
                c.setFillColorRGB(0.06, 0.09, 0.16)
                c.setFont(font_name + "-Bold" if font_name == "Helvetica" else font_name, 13)
                c.drawString(310, y, value)
                c.setFont(font_name, 13)
                y -= 28

            # Анализ
            y -= 10
            c.setStrokeColorRGB(0.89, 0.91, 0.94)
            c.line(50, y, w - 50, y)
            y -= 24

            c.setFont(font_name, 14)
            c.setFillColorRGB(0.06, 0.09, 0.16)
            c.drawString(60, y, "Анализ результатов:")
            y -= 22

            c.setFont(font_name, 11)
            c.setFillColorRGB(0.28, 0.34, 0.41)

            avg = stats['avg_reaction_time']
            total_wrong = stats['total_wrong']

            if avg > 0 and avg < 200:
                analysis = "Отличное время реакции! Скорость выше среднего."
            elif avg < 350:
                analysis = "Хорошее время реакции. Есть потенциал для улучшения."
            elif avg > 0:
                analysis = "Время реакции можно улучшить — тренируйся регулярно."
            else:
                analysis = "Нет данных для анализа времени реакции."

            c.drawString(60, y, analysis)
            y -= 18

            if total_wrong == 0:
                c.drawString(60, y, "Тренировка без ошибок — отличная концентрация!")
            elif total_wrong <= 3:
                c.drawString(60, y, f"Допущено {total_wrong} ошибки — следи за точностью.")
            else:
                c.drawString(60, y, f"Допущено {total_wrong} ошибок — работай над точностью.")

            c.save()
            QMessageBox.information(self, "Готово", f"PDF сохранён:\n{path}")

        except ImportError:
            QMessageBox.warning(
                self, "Ошибка",
                "Не установлен reportlab.\nВыполни: pip install reportlab"
            )
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать PDF:\n{str(e)}")
