from PyQt5.QtWidgets import QWidget, QPushButton, QVBoxLayout, QTextEdit, QMessageBox, QTableView, QLineEdit, QMainWindow
from PyQt5.QtSql import QSqlDatabase, QSqlTableModel, QSqlQuery
from PyQt5.QtCore import pyqtSignal
from setup_screen import SetupScreen
from app import App
import os

class DatabaseView(QWidget):
    sessionCreated = pyqtSignal(str, str, int, int, bool)
    sessionLoaded = pyqtSignal(str, str, int, int, bool)
    requestSetupScreen = pyqtSignal(QWidget)

    def __init__(self):
        super().__init__()

        self.db = QSqlDatabase.addDatabase('QSQLITE')
        # The database is stored in the db folder from the root directory
        self.db.setDatabaseName(os.path.join(os.path.dirname(os.getcwd()), 'db/sessions.db'))
        self.db.open()

        self.model = QSqlTableModel()
        self.model.setTable('sessions')
        self.model.select()

        self.view = QTableView()
        self.view.setModel(self.model)
        self.view.setSelectionBehavior(QTableView.SelectRows)  # Select entire rows instead of individual cells
        self.view.setSelectionMode(QTableView.SingleSelection)  # Allow only one row to be selected at a time

        self.newSessionButton = QPushButton('New Session')
        self.newSessionButton.clicked.connect(self.new_session)

        self.refreshButton = QPushButton('Refresh')
        self.refreshButton.clicked.connect(self.refresh)

        self.loadSessionButton = QPushButton('Load Session')
        self.loadSessionButton.clicked.connect(self.load_session)

        self.deleteButton = QPushButton('Delete Entry')
        self.deleteButton.clicked.connect(self.delete_entry)

        self.clearButton = QPushButton('Clear Database')
        self.clearButton.clicked.connect(self.clear_database)

        self.searchLineEdit = QLineEdit()
        self.searchButton = QPushButton('Search')
        self.searchButton.clicked.connect(self.search)

        layout = QVBoxLayout()
        layout.addWidget(self.view)
        layout.addWidget(self.newSessionButton)
        layout.addWidget(self.refreshButton)
        layout.addWidget(self.loadSessionButton)  # Add the load session button to the layout
        layout.addWidget(self.deleteButton)
        layout.addWidget(self.clearButton)
        layout.addWidget(self.searchLineEdit)
        layout.addWidget(self.searchButton)
        self.setLayout(layout)

    def new_session(self):
        self.setupScreen = SetupScreen()
        self.setupScreen.sessionStarted.connect(self.session_start_handler)
        self.requestSetupScreen.emit(self.setupScreen)

    def session_start_handler(self, session_id, patient_id, buffer_size, chunk_size, auto_summarize):
        self.sessionCreated.emit(session_id, patient_id, buffer_size, chunk_size, auto_summarize)

    def refresh(self):
        self.model.select()

    def load_session(self):
        selected_indexes = self.view.selectionModel().selectedRows()
        if selected_indexes:
            selected_row = selected_indexes[0].row()
            session_id = self.model.record(selected_row).value("id")
            patient_id = self.model.record(selected_row).value("patient_id")
            buffer_size = 16000 * 60  # Default value
            chunk_size = 1000  # Default value
            auto_summarize = False  # Default value
            self.transcriptionScreen = App(session_id, patient_id, buffer_size, chunk_size, auto_summarize)
            self.transcriptionScreen.show()
            self.sessionLoaded.emit(session_id, patient_id, buffer_size, chunk_size, auto_summarize)
        else:
            QMessageBox.warning(self, 'Warning', 'Please select a session to load.')

    def delete_entry(self):
        selected_indexes = self.view.selectionModel().selectedRows()
        if selected_indexes:
            selected_row = selected_indexes[0].row()
            session_id = self.model.record(selected_row).value("id")

            query = QSqlQuery()
            query.prepare("DELETE FROM sessions WHERE id = ?")
            query.addBindValue(session_id)
            query.exec_()

            self.refresh()  # Refresh the view to reflect the deletion
        else:
            QMessageBox.warning(self, 'Warning', 'Please select a session to delete.')

    def clear_database(self):
        query = QSqlQuery()
        query.prepare("DELETE FROM sessions")
        query.exec_()

        self.refresh()  # Refresh the view to reflect the deletion

    def search(self):
        search_term = self.searchLineEdit.text()
        self.model.setFilter(f"patient_id LIKE '%{search_term}%' OR id LIKE '%{search_term}%'")
