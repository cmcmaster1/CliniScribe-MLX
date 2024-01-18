
import sys
from PyQt5.QtWidgets import QApplication
from main_window import MainWindow  # Assuming you named the file main_window.py

app = QApplication(sys.argv)
main_window = MainWindow()
main_window.show()
sys.exit(app.exec_())
