"""Writing surface, microphone worker and Qt lesson illustrations."""
from PyQt6.QtCore import Qt, QPointF, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QPen, QFont, QPainter, QPainterPath
from PyQt6.QtWidgets import QWidget, QGraphicsView, QGraphicsScene


QUIZ_QSS = """
QWidget { background-color: #f0f5fc; color: #183153; font-family: 'Segoe UI'; font-size: 17px; }
QLabel { background: transparent; }
QScrollArea { border: none; }
QLabel#QuizHeading { font-size: 21px; font-weight: 700; color: #183153; }
QLabel#QuizScore { background: #fff1bb; color: #725000; border-radius: 12px; padding: 8px 16px; font-weight: 700; }
QPushButton#QuietButton { background: transparent; color: #31577d; border: 1px solid #bdcee3; font-weight: 500; padding: 8px 12px; }
QPushButton { background: #245ca6; color: white; border: none; border-radius: 10px; padding: 12px; font-weight: 600; min-height: 28px; }
QPushButton:hover { background: #194780; }
QPushButton:disabled { background: #dce4ef; color: #526176; }
QPushButton#CevapButon { background: white; color: #183153; border: 2px solid #aac8ed; font-size: 24px; font-weight: 600; text-align: center; }
QPushButton#CevapButon:hover { background: #e1efff; }
QPushButton#CevapButon:disabled { color: #455975; background: #edf2f8; }
QPlainTextEdit { background: white; color: #183153; border: 2px solid #aac8ed; border-radius: 10px; padding: 10px; font-size: 20px; }
QProgressBar { background: #dce7f6; color: #183153; border: none; border-radius: 7px; min-height: 18px; text-align: center; }
QProgressBar::chunk { background: #3b82c4; border-radius: 7px; }
"""


class WritingPad(QWidget):
    strokes_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(180)
        self.strokes = []
        self.active = None
        self.smoothing = True
        self.typeset_text = ''
        self.committed = []

    def commit_text(self, text):
        if not self.strokes:
            return
        points = [p for stroke in self.strokes for p in stroke]
        left, top = min(p.x() for p in points), min(p.y() for p in points)
        height = max(p.y() for p in points) - top
        self.committed.append((text, left, top, max(24, min(72, height)), self.strokes))
        self.strokes = []
        self.typeset_text = ' '.join(item[0] for item in self.committed)
        self.update()

    def undo(self):
        if self.strokes:
            self.strokes.pop()
            self.active = None
            self.update()
            return
        if self.committed:
            self.strokes = self.committed.pop()[4]
            self.typeset_text = ' '.join(item[0] for item in self.committed)
            self.update()
            return
        if self.typeset_text:
            self.typeset_text = ''
            self.update()
            return
        self.active = None
        self.update()

    def set_smoothing(self, enabled):
        self.smoothing = enabled
        self.update()

    @staticmethod
    def stroke_path(stroke, smooth=True):
        path = QPainterPath(stroke[0])
        if not smooth or len(stroke) < 3:
            for point in stroke[1:]:
                path.lineTo(point)
            return path
        # Midpoint quadratic curves soften hand jitter while preserving loops.
        for index in range(1, len(stroke) - 1):
            midpoint = (stroke[index] + stroke[index + 1]) / 2
            path.quadTo(stroke[index], midpoint)
        path.lineTo(stroke[-1])
        return path

    def clear(self):
        self.strokes.clear()
        self.active = None
        self.typeset_text = ''
        self.committed.clear()
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.committed:
                self.typeset_text = ''
            self.active = [event.position()]
            self.strokes.append(self.active)
            self.update()

    def mouseMoveEvent(self, event):
        if self.active is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.active.append(event.position())
            self.update()

    def mouseReleaseEvent(self, event):
        self.active = None
        self.strokes_changed.emit()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor('white'))
        if self.typeset_text and not self.committed:
            painter.setPen(QColor('#183153'))
            painter.setFont(QFont('Segoe UI', 48))
            painter.drawText(self.rect().adjusted(20, 10, -20, -10),
                             Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                             self.typeset_text)
            return
        painter.setPen(QPen(QColor('#e1eaf5'), 1))
        for y in range(30, self.height(), 30):
            painter.drawLine(0, y, self.width(), y)
        for text, x, y, height, _ in self.committed:
            painter.setPen(QColor('#183153'))
            font = QFont('Segoe UI')
            font.setPixelSize(round(height))
            painter.setFont(font)
            painter.drawText(QPointF(x, y + height), text)
        painter.setPen(QPen(QColor('#183153'), 3, Qt.PenStyle.SolidLine,
                            Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        for stroke in self.strokes:
            if len(stroke) == 1:
                painter.drawPoint(stroke[0])
            else:
                painter.drawPath(self.stroke_path(stroke, self.smoothing))


class InkRecognition(QThread):
    recognized = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, strokes):
        super().__init__()
        self.strokes = [[[p.x(), p.y()] for p in stroke] for stroke in strokes]

    def run(self):
        import json
        import os
        import subprocess
        from pathlib import Path
        try:
            result = subprocess.run(
                ['powershell.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy',
                 'Bypass', '-File', str(Path(__file__).with_name('recognize_ink.ps1'))],
                input=json.dumps({'strokes': self.strokes}), capture_output=True,
                text=True, encoding='utf-8', timeout=25,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            payload = json.loads(result.stdout.strip().lstrip('\ufeff'))
            if result.returncode or not payload.get('text', '').strip():
                raise ValueError('No recognized number')
            self.recognized.emit(payload['text'].strip())
        except Exception:
            self.failed.emit('Rakam tanınamadı. Daha belirgin yazıp tekrar dene. Windows el yazısı tanıma motoru da kurulu olmalı.')


class VoiceRequest(QThread):
    recognized = pyqtSignal(str)
    failed = pyqtSignal(str)

    def run(self):
        try:
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            recognizer.operation_timeout = 15
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(source, timeout=6, phrase_time_limit=8)
            self.recognized.emit(recognizer.recognize_google(audio, language='tr-TR'))
        except ImportError:
            self.failed.emit('Sesli sorma için SpeechRecognition ve PyAudio kurulmalı. Yazı alanından yardım isteyebilirsin.')
        except Exception:
            self.failed.emit('Ses algılanamadı. Mikrofonu ve internet bağlantısını kontrol edip tekrar dene.')


class LessonScene(QGraphicsView):
    """Reuse the original lesson drawings without starting a Tk event loop."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScene(QGraphicsScene(self))
        self.setMinimumHeight(280)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)

    def _pen(self, options):
        color = options.get('outline', '#183153')
        return QPen(QColor(color), options.get('width', 1)) if color else QPen(Qt.PenStyle.NoPen)

    def create_rectangle(self, x1, y1, x2, y2, **options):
        from PyQt6.QtGui import QBrush
        self.scene().addRect(x1, y1, x2-x1, y2-y1, self._pen(options), QBrush(QColor(options['fill'])) if options.get('fill') else QBrush(Qt.BrushStyle.NoBrush))

    def create_oval(self, x1, y1, x2, y2, **options):
        from PyQt6.QtGui import QBrush
        self.scene().addEllipse(x1, y1, x2-x1, y2-y1, self._pen(options), QBrush(QColor(options.get('fill', 'white'))))

    def create_line(self, x1, y1, x2, y2, **options):
        self.scene().addLine(x1, y1, x2, y2, QPen(QColor(options.get('fill', '#183153')), options.get('width', 1)))

    def create_text(self, x, y, **options):
        font = options.get('font', ('Segoe UI', 16))
        item = self.scene().addText(str(options.get('text', '')), QFont(font[0], font[1], QFont.Weight.Bold if 'bold' in font else QFont.Weight.Normal))
        item.setDefaultTextColor(QColor(options.get('fill', '#183153')))
        if options.get('width'):
            item.setTextWidth(options['width'])
        rect = item.boundingRect()
        item.setPos(x if options.get('anchor') == 'w' else x - rect.width()/2, y - rect.height()/2)

    def create_arc(self, x1, y1, x2, y2, **options):
        from PyQt6.QtCore import QRectF
        from PyQt6.QtGui import QBrush
        path = QPainterPath(QPointF((x1+x2)/2, (y1+y2)/2))
        path.arcTo(QRectF(x1, y1, x2-x1, y2-y1), options.get('start', 0), options.get('extent', 90))
        path.closeSubpath()
        self.scene().addPath(path, self._pen(options), QBrush(QColor(options.get('fill', 'white'))))

    def create_polygon(self, *coords, **options):
        from PyQt6.QtGui import QBrush, QPolygonF
        points = QPolygonF([QPointF(coords[i], coords[i+1]) for i in range(0, len(coords), 2)])
        fill = QBrush(QColor(options['fill'])) if options.get('fill') else QBrush(Qt.BrushStyle.NoBrush)
        self.scene().addPolygon(points, self._pen(options), fill)

    def show_visual(self, visual):
        from learning_engine.school_content import draw_scene
        self.scene().clear()
        draw_scene(self, visual)
        self.scene().setSceneRect(0, 0, 740, 170)
        self.fitInView(self.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self.setVisible(bool(self.scene().items()))

    def show_step(self, lesson, step):
        from types import SimpleNamespace
        from learning_engine.visual_help import VisualHelp
        self.scene().clear()
        helper = SimpleNamespace(lesson=lesson, steps=lesson['steps'], step=step, canvas=self)
        helper.draw_toys = lambda: VisualHelp.draw_toys(helper)
        stage = lesson['steps'][step][0]
        if lesson['kind'] == 'addition':
            VisualHelp.draw_addition(helper, stage)
        elif lesson['kind'] == 'fraction':
            VisualHelp.draw_fraction(helper, stage)
        else:
            VisualHelp.draw_general(helper)
        self.scene().setSceneRect(0, 0, 900, 380)
        self.fitInView(self.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fitInView(self.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
