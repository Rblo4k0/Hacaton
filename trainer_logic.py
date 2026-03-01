import random
import time
from datetime import datetime
import statistics

DIFFICULTY_SETTINGS = {
    "easy": {
        "label": "Лёгкий",
        "emoji": "🟢",
        "delay_min": 3.0,
        "delay_max": 5.0,
        "description": "80% зелёных, 20% красных раундов",
        "green_ratio": 0.80,   # вероятность зелёного раунда
    },
    "medium": {
        "label": "Средний",
        "emoji": "🟡",
        "delay_min": 1.8,
        "delay_max": 3.5,
        "description": "65% зелёных, 35% красных раундов",
        "green_ratio": 0.65,
    },
    "hard": {
        "label": "Сложный",
        "emoji": "🔴",
        "delay_min": 0.8,
        "delay_max": 2.0,
        "description": "50% зелёных, 50% красных раундов",
        "green_ratio": 0.50,
    }
}


class ReactionTrainer:
    def __init__(self, difficulty="medium", max_trials=10):
        self.difficulty = difficulty
        self.diff_settings = DIFFICULTY_SETTINGS[difficulty]
        self.max_trials = max_trials

        self.current_round = None        # жест текущего раунда
        self.round_color = None          # цвет текущего раунда
        self.start_ticks = 0
        self.reaction_times = []
        self.wrong_attempts = 0
        self.total_wrong_in_session = 0
        self.total_rounds_presented = 0
        self.correct_responses = 0
        self.session_data = {
            "trials": [],
            "start_time": datetime.now().isoformat(),
            "end_time": None
        }
        self.trials_completed = 0

        self.beats = {
            "rock": "scissors",
            "scissors": "paper",
            "paper": "rock"
        }
        self.gestures = ["rock", "scissors", "paper"]

    def get_delay(self):
        s = self.diff_settings
        return random.uniform(s["delay_min"], s["delay_max"])

    def generate_round(self):
        """Генерирует новый раунд с учётом соотношения зелёный/красный."""
        self.current_round = random.choice(self.gestures)
        green_ratio = self.diff_settings.get("green_ratio", 0.5)
        self.round_color = "green" if random.random() < green_ratio else "red"
        self.wrong_attempts = 0
        self.start_ticks = time.perf_counter_ns()
        self.total_rounds_presented += 1
        return self.current_round, self.round_color

    # Оставляем псевдоним для обратной совместимости
    def generate_stimulus(self):
        return self.generate_round()

    def check_response(self, user_gesture):
        if user_gesture == "unknown":
            return False, 0, "unknown"

        reaction_ms = round((time.perf_counter_ns() - self.start_ticks) / 1_000_000, 2)

        winning_gesture = next(g for g, b in self.beats.items() if b == self.current_round)
        losing_gesture  = self.beats[self.current_round]
        correct_gesture = winning_gesture if self.round_color == "green" else losing_gesture

        if user_gesture == correct_gesture:
            self.trials_completed += 1
            self.correct_responses += 1
            self.reaction_times.append(reaction_ms)
            self.session_data["trials"].append({
                "round_gesture": self.current_round,
                "color": self.round_color,
                "response": user_gesture,
                "reaction_time": reaction_ms,
                "wrong_attempts": self.wrong_attempts,
                "timestamp": datetime.now().isoformat()
            })
            return True, reaction_ms, "correct"
        else:
            self.wrong_attempts += 1
            self.total_wrong_in_session += 1
            return False, 0, "wrong"

    def get_stats(self):
        if not self.reaction_times:
            return {
                "avg_reaction_time": 0.0,
                "min_reaction": 0.0,
                "max_reaction": 0.0,
                "std_deviation": 0.0,
                "total_wrong": self.total_wrong_in_session,
                "trials_completed": self.trials_completed,
                "total_trials": self.max_trials,
                "total_rounds": self.total_rounds_presented,
                "difficulty": self.difficulty,
                "difficulty_label": self.diff_settings["label"]
            }

        std_dev = statistics.stdev(self.reaction_times) if len(self.reaction_times) > 1 else 0.0

        return {
            "avg_reaction_time": round(sum(self.reaction_times) / len(self.reaction_times), 2),
            "min_reaction": round(min(self.reaction_times), 2),
            "max_reaction": round(max(self.reaction_times), 2),
            "std_deviation": round(std_dev, 2),
            "total_wrong": self.total_wrong_in_session,
            "trials_completed": self.trials_completed,
            "total_trials": self.max_trials,
            "total_rounds": self.total_rounds_presented,
            "difficulty": self.difficulty,
            "difficulty_label": self.diff_settings["label"]
        }

    def is_session_complete(self):
        return self.trials_completed >= self.max_trials

    def reset_session(self):
        self.session_data["end_time"] = datetime.now().isoformat()
        final_stats = self.get_stats()
        trials_data = self.session_data["trials"].copy()
        difficulty  = self.difficulty
        max_trials  = self.max_trials
        self.__init__(difficulty=difficulty, max_trials=max_trials)
        return final_stats, trials_data
