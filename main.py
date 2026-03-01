import sys
from PySide6.QtWidgets import QApplication
import styles
from main_window import MainWindow


if __name__ == "__main__":
    app = QApplication(sys.argv)
    styles.apply_global_style(app)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())
