"""Register existing Windows fonts; also supports offscreen visual verification."""
import os
from pathlib import Path
from PyQt6.QtGui import QFont, QFontDatabase


def configure_fonts(app):
    if os.name == 'nt':
        directory = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts'
        for name in ('segoeui.ttf', 'segoeuib.ttf', 'arial.ttf', 'seguiemj.ttf'):
            path = directory / name
            if path.exists():
                QFontDatabase.addApplicationFont(str(path))
    app.setFont(QFont('Segoe UI', 11))
