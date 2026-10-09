"""Presentation adapted from homework 2.zip; no account or learning logic imported."""
from pathlib import Path
from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QPixmap, QPainter, QColor, QRadialGradient, QPainterPath
from PyQt6.QtWidgets import QWidget

ASSETS = Path(__file__).parent / 'assets'
ROLE_COLORS = {'parent': ('#ffd6a5','#ffbf78','#6b3e02'),
               'teacher': ('#bdb2ff','#a495ff','#2d1b69'),
               'student': ('#caffbf','#9ef594','#1b4332')}


def portrait(name, size=130, color='#caffbf'):
    result = QPixmap(size,size); result.fill(Qt.GlobalColor.transparent)
    painter = QPainter(result); painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    path = QPainterPath(); path.addEllipse(2,2,size-4,size-4)
    painter.setClipPath(path)
    gradient = QRadialGradient(size*.4,size*.3,size)
    gradient.setColorAt(0,QColor(color).lighter(115));gradient.setColorAt(1,QColor(color))
    painter.fillRect(result.rect(),gradient)
    image = QPixmap(str(ASSETS/name))
    if not image.isNull():
        image = image.scaled(size-24,size-24,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)
        painter.drawPixmap((size-image.width())//2,(size-image.height())//2,image)
    painter.end();return result


class WelcomeBackdrop(QWidget):
    """Orange/purple/mint background from the supplied role selection screen."""
    def paintEvent(self,event):
        super().paintEvent(event)
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(),QColor('#faf9f6'))
        for x,color in [(0.02,'#ffd6a5'),(.50,'#bdb2ff'),(.98,'#caffbf')]:
            g=QRadialGradient(QPointF(self.width()*x,self.height()*.55),max(self.width(),self.height())*.85)
            c=QColor(color);c.setAlpha(180);g.setColorAt(0,c)
            c.setAlpha(0);g.setColorAt(1,c);p.fillRect(self.rect(),g)
        p.end()


PASTEL_QSS = """
QWidget { font-family: 'Segoe UI'; font-size: 15px; color: #1d3557; background: #f6f8fd; }
QLabel { background: transparent; }
QFrame#Card { background: white; border: 2px solid #ded8f4; border-radius: 22px; }
QFrame#Sidebar { background: #f0ecfc; border: none; border-right: 1px solid #ded8f4; }
QLabel#Brand { color: #4c3a91; font-size: 25px; font-weight: 700; }
QLabel#SidebarCaption { color: #625487; }
QLabel#Title { color: #1d3557; font-size: 28px; font-weight: 700; }
QLabel#Section { color: #4c3a91; font-size: 19px; font-weight: 700; }
QLabel#Muted { color: #62718a; font-size: 14px; }
QLabel#Metric { color: #6550b5; font-size: 32px; font-weight: 700; }
QLabel#Error { color: #b33f50; }
QPushButton { background: #6550b5; color: white; border: none; border-radius: 14px; padding: 11px 17px; font-weight: 600; }
QPushButton:hover { background: #514098; }
QPushButton:disabled { background: #e0e4ef; color: #67748a; }
QPushButton#Secondary { background: #eee9fb; color: #514098; }
QPushButton#Nav { color: #554477; background: transparent; text-align: left; padding: 14px; }
QPushButton#Nav:checked, QPushButton#Nav:hover { background: #dcd4f4; color: #39265d; }
QLineEdit, QComboBox, QSpinBox, QDateEdit, QTimeEdit, QPlainTextEdit { background: white; color: #1d3557; border: 2px solid #ded8f4; border-radius: 11px; padding: 9px; min-height: 20px; }
QComboBox QAbstractItemView { background: white; color: #1d3557; selection-background-color: #eee9fb; selection-color: #39265d; }
QScrollArea, QStackedWidget { border: none; background: transparent; }
QTableWidget { background: white; alternate-background-color: #f8f6fd; color: #1d3557; border: none; gridline-color: #eee9f6; selection-background-color: #eee9fb; selection-color: #39265d; }
QHeaderView::section { background: #eee9fb; color: #554477; border: none; padding: 12px; font-weight: 600; }
QDialog { background: #f6f8fd; }
QFrame#ParentSidebar { background: #fff1e6; border-right: 1px solid #ffd6a5; }
QFrame#ParentSidebar QLabel#Brand { color: #784619; }
QFrame#ParentSidebar QLabel#SidebarCaption { color: #835f40; }
QFrame#ParentSidebar QPushButton#Nav { background: transparent; color: #784619; text-align: left; }
QFrame#ParentSidebar QPushButton#Nav:checked, QFrame#ParentSidebar QPushButton#Nav:hover { background: #ffd6a5; }
"""

STUDENT_QSS = """
QWidget { background: #f1fbf3; color: #1d3557; }
QLabel { background: transparent; }
QFrame#Card { background: white; border: 2px solid #c2e7d0; border-radius: 24px; }
QLabel#Title { color: #23664e; font-size: 30px; font-weight: 700; }
QLabel#Section { color: #1d3557; }
QPushButton { background: #2b8064; color: white; border-radius: 16px; padding: 13px; font-size: 17px; }
QPushButton:hover { background: #21664f; }
QPushButton#Secondary { background: #dcf2e4; color: #23664e; }
QComboBox, QSpinBox { background: white; color: #1d3557; border: 2px solid #c2e7d0; border-radius: 12px; padding: 9px; }
QScrollArea { background: transparent; border: none; }
"""

QUIZ_PASTEL = """
QWidget#ChildQuiz { background: #f1fbf3; }
QLabel#QuizHeading { background: #fff; color: #1d3557; border: 2px solid #bde0fe; border-radius: 18px; padding: 12px; }
QLabel#SoruAlani { background: #fff; color: #1d3557; border: 2px solid #a8dadc; border-radius: 22px; padding: 18px; }
QPushButton#CevapButon { background: #fff; color: #1d3557; border: 2px solid #bde0fe; border-radius: 18px; font-size: 23px; font-weight: 600; }
QPushButton#CevapButon:hover { background: #e0f2fe; border-color: #7dd3fc; }
QPushButton#CevapButon:disabled { background: #edf4f8; color: #455975; }
"""
