from PyQt5.QtWidgets import QWidget, QTextEdit, QPushButton, QVBoxLayout, QLabel, QMessageBox
from PyQt5.QtCore import QTime, QTimer, QDateTime
from live_transcription_thread import LiveTranscriptionThread
from PyQt5.QtSql import QSqlQuery
from mlx_lm import load, generate
from threading import Thread
import os
from tqdm import tqdm
from whisper import transcribe
from config import WHISPER_DIR, SAMPLE_RATE, LLM

tqdm(disable=True, total=0)

class App(QWidget):
    def __init__(self, session_id, patient_id, buffer_size, chunk_size, auto_summarize):
        super().__init__()

        self.buffer_size = buffer_size
        self.chunk_size = chunk_size
        self.session_id = session_id
        self.patient_id = patient_id
        self.auto_summarize = auto_summarize
        self.whisper_path = os.path.join(os.path.dirname(os.getcwd()), 'models', WHISPER_DIR)

        # Add session name to the title
        self.setWindowTitle(f"Transcription - {self.session_id}")

        self.textEdit = QTextEdit()
        self.summaryTextEdit = QTextEdit()
        self.startButton = QPushButton('Start Transcription')
        self.startButton.clicked.connect(self.toggle_transcription)
        self.finishButton = QPushButton('Finish and Summarize')
        self.finishButton.clicked.connect(self.finish_transcription)

        self.indicatorLabel = QLabel()
        self.indicatorLabel.setFixedSize(20, 20)  # Set a fixed size for the indicator
        self.indicatorLabel.setStyleSheet("background-color: red")  # Red indicates "stopped"

        self.timer = QTimer()
        self.time = QTime(0, 0)
        self.timer.timeout.connect(self.update_time)
        self.timeLabel = QLabel()
        self.timeLabel.setText(self.time.toString())

        self.exitButton = QPushButton('Exit Session')
        self.exitButton.clicked.connect(self.close)

        self.loadingLabel = QLabel('Loading ML model, please wait...')

        layout = QVBoxLayout()
        layout.addWidget(self.textEdit)
        layout.addWidget(self.summaryTextEdit)
        layout.addWidget(self.startButton)
        layout.addWidget(self.finishButton)
        layout.addWidget(self.indicatorLabel)
        layout.addWidget(self.timeLabel)
        layout.addWidget(self.exitButton)
        layout.addWidget(self.loadingLabel)

        self.setLayout(layout)

        self.model_loading_thread = Thread(target=self.load_model)
        self.model_loading_thread.start()
        self.intermediate_prompt_template = "Summarize this intermediate transcript from a consultation between a doctor and a patient. Include anything that will be important to summarize the entire consultation. Transcript: {}"
        self.final_prompt_template = "Summarize this final transcript from a consultation between a doctor and a patient. Transcript: {}"
        self.word_cache = []
        self.summaries = []

        self.transcriptionThread = LiveTranscriptionThread(sample_rate=SAMPLE_RATE, buffer_size=self.buffer_size)


    def load_model(self):
        # Load the model and tokenizer
        self.model, self.tokenizer = load(LLM)
        # Hide the loading label once the model is loaded
        self.loadingLabel.hide()

    def toggle_transcription(self):
        if not hasattr(self, 'transcriptionThread') or not self.transcriptionThread.isRunning():
            self.start_transcription()
            self.startButton.setText('Pause Transcription')
        else:
            self.pause_transcription()
            self.startButton.setText('Start Transcription')

    def finish_transcription(self):
        # If not already paused, pause the transcription
        if hasattr(self, 'transcriptionThread') and self.transcriptionThread.isRunning():
            self.pause_transcription()

        # Finish transcribing whatever is in the current buffer
        remaining_text = transcribe(self.transcriptionThread.buffer, model_path=self.whisper_path)['text']
        self.textEdit.append(remaining_text)

        if self.auto_summarize:
            self.summaries.append(remaining_text)
        # if self.auto_summarize:
        #     # Update the cache and possibly do an intermediate summarization
        #     self.word_cache.extend(remaining_text.split())
        #     while len(self.word_cache) >= self.chunk_size:
        #         chunk_to_summarize = " ".join(self.word_cache[:self.chunk_size])
        #         prompt = self.tokenizer.apply_chat_template(
        #             [{"role": "user", "content": self.intermediate_prompt_template.format(chunk_to_summarize)}], tokenize=False)
        #         summary = generate(self.model, self.tokenizer, prompt=prompt)
        #         self.summaries.append(summary)
        #         self.word_cache = self.word_cache[self.chunk_size:]

        #     # If what's left in the cache is not enough to trigger an auto-summarize, add it to the intermediate summary list
        #     if self.word_cache:
        #         remaining_summary = " ".join(self.word_cache)
        #         self.summaries.append(remaining_summary)

        self.summarize_transcription()

    def start_transcription(self):
        self.transcriptionThread = LiveTranscriptionThread(sample_rate=16000, buffer_size=self.buffer_size)
        self.transcriptionThread.signal.connect(self.update_transcription)
        self.transcriptionThread.start()
        self.timer.start(1000)  # Update every second
        self.indicatorLabel.setStyleSheet("background-color: green")  # Green indicates "running"

    def pause_transcription(self):
        self.transcriptionThread.stop()
        self.timer.stop()
        self.indicatorLabel.setStyleSheet("background-color: red")  # Red indicates "stopped"

    def resume_transcription(self):
        self.transcriptionThread.start()
        self.timer.start(1000)
        self.indicatorLabel.setStyleSheet("background-color: green")  # Green indicates "running"

    def summarize_transcription(self):
        if self.auto_summarize:
            # Concatenate the intermediate summaries and use that as the input for the final summary
            transcription = " ".join(self.summaries) if self.summaries else ""
            # If transcription is empty, use the full transcription text
            if not transcription.strip():
                transcription = self.textEdit.toPlainText()
        else:
            # Use the full transcription text
            transcription = self.textEdit.toPlainText()

        if not transcription.strip():  # Check if the transcription is blank
            QMessageBox.warning(self, 'Transcription Error', 'The transcription is blank.')
            return

        prompt = self.tokenizer.apply_chat_template(
            [{"role": "user", "content": self.final_prompt_template.format(transcription)}], tokenize=False)
        summary = generate(self.model, self.tokenizer, prompt=prompt, max_tokens=1024)

        if not summary.strip():  # Check if the summary is blank
            QMessageBox.warning(self, 'Summary Error', 'The summary is blank.')
            return

        self.summaryTextEdit.setPlainText(summary)

        # Store the transcription and summary in the database
        query = QSqlQuery()
        query.prepare("UPDATE sessions SET patient_id = ?, timestamp = ?, transcription = ?, summary = ? WHERE id = ?")
        query.addBindValue(self.patient_id)
        query.addBindValue(QDateTime.currentDateTime())
        query.addBindValue(transcription)
        query.addBindValue(summary)
        query.addBindValue(self.session_id)
        if not query.exec_():  # If the query fails
            error = query.lastError().text()  # Get the error message
            QMessageBox.warning(self, 'Database Error', f'An error occurred when updating the database: {error}')

    def update_transcription(self, text):
        self.textEdit.append(text)
        if self.auto_summarize:
            self.word_cache.extend(text.split())
            while len(self.word_cache) >= self.chunk_size:
                chunk_to_summarize = " ".join(self.word_cache[:self.chunk_size])
                prompt = self.tokenizer.apply_chat_template(
                    [{"role": "user", "content": self.intermediate_prompt_template.format(chunk_to_summarize)}], tokenize=False)
                summary = generate(self.model, self.tokenizer, prompt=prompt, max_tokens=256)
                self.summaries.append(summary)
                self.word_cache = self.word_cache[self.chunk_size - 32:] if self.chunk_size > 32 else self.word_cache  # Keep an overlap of 32 words

    def update_time(self):
        self.time = self.time.addSecs(1)
        self.timeLabel.setText(self.time.toString())
