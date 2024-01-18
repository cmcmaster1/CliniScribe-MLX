from PyQt5.QtWidgets import QWidget, QLabel, QComboBox, QSpinBox, QCheckBox, QPushButton, QVBoxLayout, QMessageBox, QLineEdit, QFileDialog
from PyQt5.QtSql import QSqlQuery
from PyQt5.QtCore import pyqtSignal
import numpy as np
import datetime
from app import App

class SetupScreen(QWidget):
    sessionStarted = pyqtSignal(str, str, int, int, bool)

    def __init__(self):
        super().__init__()

        self.patientIdLabel = QLabel('Patient ID:')
        self.patientIdComboBox = QComboBox()
        self.patientIdComboBox.setEditable(True)  # Allow the user to enter a new ID

        # Populate the combo box with existing patient IDs
        query = QSqlQuery("SELECT DISTINCT patient_id FROM sessions")
        while query.next():
            patient_id = query.value(0)
            self.patientIdComboBox.addItem(patient_id)

        self.bufferSizeLabel = QLabel('Buffer Size (in minutes):')
        self.bufferSizeSpinBox = QSpinBox()
        self.bufferSizeSpinBox.setRange(1, 30)
        self.bufferSizeSpinBox.setSingleStep(1)
        self.bufferSizeSpinBox.setValue(10)

        self.chunkSizeLabel = QLabel('Chunk Size (in words):')
        self.chunkSizeSpinBox = QSpinBox()
        self.chunkSizeSpinBox.setRange(100, 10000)
        self.chunkSizeSpinBox.setSingleStep(100)
        self.chunkSizeSpinBox.setValue(1000)

        self.autoSummarizeCheckBox = QCheckBox("Summarize in chunks as you go")


        self.startButton = QPushButton('Start Session')
        self.startButton.clicked.connect(self.start_session)
        self.cancelButton = QPushButton('Cancel')
        self.cancelButton.clicked.connect(self.close)


        layout = QVBoxLayout()
        layout.addWidget(self.patientIdLabel)
        layout.addWidget(self.patientIdComboBox)
        layout.addWidget(self.bufferSizeLabel)
        layout.addWidget(self.bufferSizeSpinBox)
        layout.addWidget(self.chunkSizeLabel)
        layout.addWidget(self.chunkSizeSpinBox)
        layout.addWidget(self.autoSummarizeCheckBox)
        layout.addWidget(self.startButton)
        layout.addWidget(self.cancelButton)
        self.setLayout(layout)

    def start_session(self):
        patient_id = self.patientIdComboBox.currentText()
        if not patient_id:
            QMessageBox.warning(self, 'Warning', 'Please enter a patient ID.')
            return

        buffer_size = self.bufferSizeSpinBox.value() * 16000 * 60
        chunk_size = self.chunkSizeSpinBox.value()
        auto_summarize = self.autoSummarizeCheckBox.isChecked()

        # Generate a unique session ID
        session_id = str(np.random.randint(100000, 999999))
        query = QSqlQuery()
        query.prepare("SELECT * FROM sessions WHERE id = ?")
        query.addBindValue(session_id)
        query.exec_()
        while query.next():  # If the session ID already exists, generate a new one
            session_id = str(np.random.randint(100000, 999999))
            query.addBindValue(session_id)
            query.exec_()

        # Get the current timestamp
        timestamp = str(datetime.datetime.now())

        # Insert the new session into the database
        query = QSqlQuery()
        query.prepare("INSERT INTO sessions (id, patient_id, timestamp) VALUES (?, ?, ?)")
        query.addBindValue(session_id)
        query.addBindValue(patient_id)
        query.addBindValue(timestamp)
        query.exec_()

        # Start the transcription session
        self.transcriptionScreen = App(session_id, patient_id, buffer_size, chunk_size, auto_summarize)  # Pass the model path to App
        self.transcriptionScreen.show()
        self.close()
        # Emit the sessionStarted signal with the appropriate values
        self.sessionStarted.emit(session_id, patient_id, buffer_size, chunk_size, auto_summarize)
