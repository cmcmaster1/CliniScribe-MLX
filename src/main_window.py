from PyQt5.QtWidgets import QMainWindow, QSplitter, QWidget
from PyQt5.QtCore import Qt
from app import App
from database_view import DatabaseView

w = 1200
h = 800
half_w = int(w/2)
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.app = None
        self.resize(w, h)
        self.splitter = QSplitter(Qt.Horizontal)
        self.database_view = DatabaseView()
        self.session_placeholder = QWidget()  # Placeholder for session creation/app view
        self.splitter.addWidget(self.database_view)
        self.splitter.addWidget(self.session_placeholder)
        self.setCentralWidget(self.splitter)
        self.database_view.sessionCreated.connect(self.openSession)
        self.database_view.sessionLoaded.connect(self.openSession)
        self.database_view.requestSetupScreen.connect(self.showSetupScreen)

        # Set the initial sizes of the widgets in the splitter to be even
        self.splitter.setSizes([half_w, half_w])

    def openSession(self, session_id, patient_id, buffer_size, chunk_size, auto_summarize):
        if not self.app:  # Create App instance if it doesn't exist
            self.app = App(session_id, patient_id, buffer_size, chunk_size, auto_summarize)
        else:  # Update the existing App instance with new session details
            self.app.updateSession(session_id, patient_id, buffer_size, chunk_size, auto_summarize)
        self.splitter.replaceWidget(1, self.app)  # Replace placeholder with app view

    def showSetupScreen(self, setupScreen):
        self.splitter.replaceWidget(1, setupScreen)

    def returnToDatabaseView(self):
        if self.app:
            self.app.hide()  # Hide the app widget
        self.splitter.replaceWidget(1, self.session_placeholder)  # Revert to session creation view
