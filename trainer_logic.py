import random
import time
from datetime import datetime
import statistics
import math


class ReactionTrainer:
    def __init__(self):
        self.current_stimulus = None
        self.stimulus_color = None
        self.start_ticks = 0
        self.reaction_times = []
        self.wrong_attempts = 0
        self.total_wrong_in_session = 0
        self.total_stimuli_presented = 0  # Всего показано стимулов (включая ошибочные попытки)
        self.correct_responses = 0  # Количество правильных ответов
        self.session_data = {
            "trials": [],
            "start_time": datetime.now().isoformat(),
            "end_time": None
        }
        self.trials_completed = 0
        self.max_trials = 10

        self.beats = {
            "rock": "scissors",
            "scissors": "paper",
            "paper": "rock"
        }

        self.gestures = ["rock", "scissors", "paper"]

    def generate_stimulus(self):
        self.current_stimulus = random.choice(self.gestures)
        self.stimulus_color = "green" if random.random() < 0.5 else "red"
        self.wrong_attempts = 0
        self.start_ticks = time.perf_counter_ns()
        self.total_stimuli_presented += 1  # Увеличиваем счетчик показанных стимулов
        return self.current_stimulus, self.stimulus_color

    def check_response(self, user_gesture):
        if user_gesture == "unknown":
            return False, 0, "unknown"

        # расчет реакции
        reaction_ms = (time.perf_counter_ns() - self.start_ticks) / 1_000_000

        # правильный жест
        winning_gesture = next(g for g, b in self.beats.items() if b == self.current_stimulus)
        losing_gesture = self.beats[self.current_stimulus]
        correct_gesture = winning_gesture if self.stimulus_color == "green" else losing_gesture

        if user_gesture == correct_gesture:
            self.trials_completed += 1
            self.correct_responses += 1
            self.reaction_times.append(reaction_ms)
            self.session_data["trials"].append({
                "stimulus": self.current_stimulus,
                "color": self.stimulus_color,
                "response": user_gesture,
                "reaction_time": round(reaction_ms, 3),
                "wrong_attempts": self.wrong_attempts,
                "timestamp": datetime.now().isoformat()
            })
            return True, round(reaction_ms, 3), "correct"
        else:
            self.wrong_attempts += 1
            self.total_wrong_in_session += 1
            # Не увеличиваем total_stimuli_presented при ошибке, так как стимул уже был показан
            return False, 0, "wrong"

    def get_stats(self):
        if not self.reaction_times:
            return {
                "avg_reaction_time": 0,
                "min_reaction": 0,
                "max_reaction": 0,
                "std_deviation": 0,
                "accuracy": 0,
                "total_wrong": self.total_wrong_in_session,
                "trials_completed": self.trials_completed,
                "total_trials": self.max_trials,
                "total_stimuli": self.total_stimuli_presented
            }

        # Расчет вариативности (стандартное отклонение)
        std_dev = statistics.stdev(self.reaction_times) if len(self.reaction_times) > 1 else 0

        # Расчет точности: правильные ответы / всего показанных стимулов * 100
        accuracy = (
                    self.correct_responses / self.total_stimuli_presented * 100) if self.total_stimuli_presented > 0 else 0

        return {
            "avg_reaction_time": round(sum(self.reaction_times) / len(self.reaction_times), 3),
            "min_reaction": round(min(self.reaction_times), 3),
            "max_reaction": round(max(self.reaction_times), 3),
            "std_deviation": round(std_dev, 3),
            "accuracy": round(accuracy, 1),
            "total_wrong": self.total_wrong_in_session,
            "trials_completed": self.trials_completed,
            "total_trials": self.max_trials,
            "total_stimuli": self.total_stimuli_presented
        }

    def is_session_complete(self):
        return self.trials_completed >= self.max_trials

    def reset_session(self):
        self.session_data["end_time"] = datetime.now().isoformat()
        final_stats = self.get_stats()
        trials_data = self.session_data["trials"].copy()
        self.__init__()
        return final_stats, trials_data