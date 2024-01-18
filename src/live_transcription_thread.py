
import numpy as np
import pyaudio
from PyQt5.QtCore import QThread, pyqtSignal
from whisper import transcribe

class LiveTranscriptionThread(QThread):
    signal = pyqtSignal('PyQt_PyObject')

    def __init__(self, sample_rate=16000, buffer_size=16000, whisper_path = "../models/whisper_base_en"):
        QThread.__init__(self)
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.whisper_path = whisper_path
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=pyaudio.paFloat32,
                                  channels=1,
                                  rate=self.sample_rate,
                                  input=True,
                                  frames_per_buffer=1024)
        self.buffer = np.array([])
        self.running = True

    def run(self):
        while self.running:
            try:
                audio_data = self.stream.read(1024, exception_on_overflow=False)  # Prevent OSError
                audio_data = np.frombuffer(audio_data, dtype=np.float32)
                self.buffer = np.concatenate((self.buffer, audio_data))

                if len(self.buffer) >= self.buffer_size:
                    print("Transcribing buffer...")  # Debugging print
                    result = transcribe(self.buffer[:self.buffer_size], model_path=self.whisper_path)['text']
                    self.signal.emit(result)
                    self.buffer = self.buffer[self.buffer_size:]  # Shift the buffer
            except Exception as e:
                print(f"Error occurred: {e}")  # Improved error handling

    def stop(self):
        self.running = False
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()