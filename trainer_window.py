from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QProgressBar, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QImage, QPixmap
import cv2
import time
import random
import styles
import HandTracking as ht
from trainer_logic import ReactionTrainer
from database import Database


class TrainerWindow(QMainWindow):
    def __init__(self, db=None, user=None):
        super().__init__()
        self.db = db if db else Database()
        self.user = user
        self.setWindowTitle("ReactionRPS - тренировка")
        self.setGeometry(100, 100, 1200, 800)

        self.trainer = ReactionTrainer()
        self.detector = ht.HandDetector()
        self.cap = cv2.VideoCapture(0)

        if not self.cap.isOpened():
            QMessageBox.critical(self, "Ошибка", "Камера не найдена")
            return

        self.waiting = False
        self.stimulus_active = False
        self.last_gesture = None
        self.wrong_count = 0
        self.session_ended = False

        self.init_ui()
        self.setup_timers()
        self.show_waiting_state()
        self.next_stimulus()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)

        self.left = QFrame()
        self.set_waiting_background()
        left_layout = QVBoxLayout(self.left)
        left_layout.setAlignment(Qt.AlignCenter)

        self.stimulus = QLabel("●")
        self.stimulus.setFont(QFont("Segoe UI", 100))
        self.stimulus.setAlignment(Qt.AlignCenter)
        left_layout.addWidget(self.stimulus)

        right = QFrame()
        right.setStyleSheet(styles.CARD_STYLE)
        right_layout = QVBoxLayout(right)

        self.video = QLabel()
        self.video.setFixedSize(480, 360)
        self.video.setStyleSheet("border: 3px solid #FFD166; border-radius: 10px; background-color: black;")
        right_layout.addWidget(self.video)

        self.hand_status = QLabel("Ожидание...")
        self.hand_status.setFont(styles.get_font_bold(14))
        self.hand_status.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.hand_status)

        stats = QHBoxLayout()

        self.time_label = QLabel("⏱ 0 мс")
        self.time_label.setFont(styles.get_font_bold(14))
        stats.addWidget(self.time_label)

        self.wrong_label = QLabel("❌ 0")
        self.wrong_label.setFont(styles.get_font_bold(14))
        stats.addWidget(self.wrong_label)

        right_layout.addLayout(stats)

        self.progress = QProgressBar()
        self.progress.setMaximum(10)
        right_layout.addWidget(self.progress)

        layout.addWidget(self.left, 1)
        layout.addWidget(right, 1)

    def setup_timers(self):
        self.video_timer = QTimer()
        self.video_timer.timeout.connect(self.update_frame)
        self.video_timer.start(15)

        self.next_timer = QTimer()
        self.next_timer.timeout.connect(self.next_stimulus)

    def update_frame(self):
        if self.session_ended:
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame.shape
                qt_img = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
                self.video.setPixmap(QPixmap.fromImage(qt_img).scaled(480, 360, Qt.KeepAspectRatio))
            return

        ret, frame = self.cap.read()
        if not ret:
            return

        frame = self.detector.find_hands(frame)
        lm_list = self.detector.find_position(frame)

        if lm_list:
            self.hand_status.setText("Рука обнаружена")
            gesture = self.detector.recognize_gesture()
        else:
            self.hand_status.setText("Рука не видна")
            gesture = "unknown"

        if self.stimulus_active and self.waiting:
            if gesture == "unknown":
                pass
            else:
                if self.last_gesture is None:
                    self.last_gesture = gesture
                elif gesture != self.last_gesture:
                    self.last_gesture = gesture

                    correct, reaction, _ = self.trainer.check_response(gesture)

                    if correct:
                        self.waiting = False
                        self.stimulus_active = False
                        self.show_waiting_state()
                        self.update_stats()

                        if self.trainer.is_session_complete() and not self.session_ended:
                            self.session_ended = True
                            # Останавливаем таймеры перед показом результатов
                            self.next_timer.stop()
                            self.video_timer.stop()
                            self.show_session_results()
                        else:
                            delay = random.uniform(2.0, 4.0)
                            self.next_timer.start(int(delay * 1000))
                    else:
                        self.wrong_count = self.trainer.total_wrong_in_session
                        self.wrong_label.setText(f"❌ {self.wrong_count}")

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        qt_img = QImage(frame.data, w, h, ch * w, QImage.Format_RGB888)
        self.video.setPixmap(QPixmap.fromImage(qt_img).scaled(480, 360, Qt.KeepAspectRatio))

    def show_waiting_state(self):
        self.set_waiting_background()
        self.stimulus.setFont(QFont("Segoe UI", 100))
        self.stimulus.setText("●")

    def next_stimulus(self):
        if self.session_ended:
            return

        self.next_timer.stop()

        gesture, color = self.trainer.generate_stimulus()

        emoji_map = {
            "rock": "🪨",
            "scissors": "✂️",
            "paper": "🧻"
        }

        self.last_gesture = None
        self.waiting = True
        self.stimulus_active = True

        self.set_colored_background(color)
        self.stimulus.setFont(QFont("Segoe UI Emoji", 180))
        self.stimulus.setText(emoji_map[gesture])

    def set_waiting_background(self):
        self.left.setStyleSheet("""
            QFrame {
                background-color: white;
                border: none;
                border-radius: 30px;
            }
        """)

    def set_colored_background(self, color):
        if color == "green":
            border = styles.COLORS['accent_green']
            bg = "rgba(6,214,160,0.2)"
        else:
            border = styles.COLORS['accent_red']
            bg = "rgba(239,71,111,0.2)"

        self.left.setStyleSheet(f"""
            QFrame {{
                background-color: {bg};
                border: 5px solid {border};
                border-radius: 30px;
            }}
        """)

    def update_stats(self):
        stats = self.trainer.get_stats()
        if stats:
            self.time_label.setText(f"⏱ {stats['avg_reaction_time']} мс")
            self.progress.setValue(stats['trials_completed'])
            self.wrong_label.setText(f"❌ {stats['total_wrong']}")

    def show_session_results(self):
        # Получаем финальную статистику и данные тренировки
        stats, trials_data = self.trainer.reset_session()

        # Сохраняем сессию в БД, если пользователь авторизован
        if self.user:
            self.db.save_session(self.user['id'], stats, trials_data)

        # Показываем результаты в красивом окне
        msg = QMessageBox(self)
        msg.setWindowTitle("🏆 Результаты тренировки")
        msg.setStyleSheet("""
            QMessageBox {
                background-color: white;
            }
            QMessageBox QLabel {
                color: """ + styles.COLORS['text_dark'] + """;
                font-size: 14px;
                padding: 15px;
                min-width: 300px;
            }
            QPushButton {
                background-color: """ + styles.COLORS['accent_green'] + """;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 8px 25px;
                font-weight: bold;
                font-size: 14px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #05b586;
            }
        """)

        # Формируем текст с результатами
        result_text = (
            f"📊 Всего показано стимулов: {stats['total_stimuli']}\n"
            f"✅ Правильных ответов: {stats['trials_completed']}\n"
            f"❌ Ошибок: {stats['total_wrong']}\n"
            f"🎯 Точность: {stats['accuracy']}%\n\n"
            f"⏱ Среднее время реакции: {stats['avg_reaction_time']} мс\n"
            f"⚡ Лучшее время: {stats['min_reaction']} мс\n"
            f"📈 Худшее время: {stats['max_reaction']} мс\n"
            f"📊 Вариативность: ±{stats['std_deviation']} мс"
        )

        msg.setText(result_text)
        msg.exec()

        # Возвращаемся в главное меню
        self.go_back_to_main()

    def go_back_to_main(self):
        from main_window import MainWindow
        self.main_window = MainWindow(self.db)
        self.main_window.show()
        self.close()

    def closeEvent(self, event):
        self.cap.release()
        event.accept()