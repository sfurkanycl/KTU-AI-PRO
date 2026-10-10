"""Qt narration bridge to the selected Jessica service; retains workers safely."""
import io
import threading
from PyQt6.QtCore import QThread, pyqtSignal
from learning_engine.audio_service import synthesize

_ACTIVE_WORKERS = set()
_PLAY_LOCK = threading.Lock()
_CHANNEL = None


def stop_narration():
    global _CHANNEL
    with _PLAY_LOCK:
        if _CHANNEL is not None:
            _CHANNEL.stop()
            _CHANNEL = None
        for worker in list(_ACTIVE_WORKERS):
            worker.requestInterruption()


def shutdown_narration():
    stop_narration()
    # Allow an in-flight HTTP timeout to finish before Qt destroys its QThreads.
    for worker in list(_ACTIVE_WORKERS):
        worker.wait(35000)


class NarrationWorker(QThread):
    succeeded = pyqtSignal()
    playback_finished = pyqtSignal()
    failed = pyqtSignal(str)

    def __init__(self, text):
        super().__init__()
        self.text = text

    def run(self):
        global _CHANNEL
        try:
            audio = synthesize(self.text)
            if self.isInterruptionRequested():
                return
            import pygame
            with _PLAY_LOCK:
                if self.isInterruptionRequested():
                    return
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
                if _CHANNEL is not None:
                    _CHANNEL.stop()
                sound = pygame.mixer.Sound(file=io.BytesIO(audio))
                channel = sound.play()
                if channel is None:
                    raise RuntimeError("Ses oynatma kanalı açılamadı.")
                _CHANNEL = channel
            self.succeeded.emit()
            while channel.get_busy() and not self.isInterruptionRequested():
                self.msleep(25)
            if not self.isInterruptionRequested():
                self.playback_finished.emit()
        except Exception as exc:
            self.failed.emit(str(exc))


def start_narration(text, on_success=None, on_error=None, on_finished=None):
    stop_narration()
    worker = NarrationWorker(text)
    _ACTIVE_WORKERS.add(worker)
    if on_success:
        worker.succeeded.connect(lambda: on_success() if not worker.isInterruptionRequested() else None)
    if on_error:
        worker.failed.connect(lambda message: on_error(message) if not worker.isInterruptionRequested() else None)
    if on_finished:
        worker.playback_finished.connect(lambda: on_finished() if not worker.isInterruptionRequested() else None)
    worker.finished.connect(lambda: _ACTIVE_WORKERS.discard(worker))
    worker.start()
    return worker
