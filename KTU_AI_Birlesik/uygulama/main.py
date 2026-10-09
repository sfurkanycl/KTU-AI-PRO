"""Unified launcher. Original inputs remain untouched under ../orijinaller."""
import argparse
from pathlib import Path
import sys


def legacy_main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--env', type=Path, help='Optional existing local .env; read only, never copied')
    parser.add_argument('--no-native-guard', action='store_true', help='Preview without loading native keyboard DLL')
    args = parser.parse_args()
    if sys.version_info[:2] != (3, 12):
        raise SystemExit('Bu birleşim, korunan Windows modülleri nedeniyle Python 3.12 gerektiriyor.')
    from dotenv import load_dotenv
    load_dotenv(args.env or Path(__file__).with_name('.env'))
    import os
    if not os.getenv('AUDIO_PROVIDER') or (
        os.getenv('AUDIO_PROVIDER', '').lower() == 'elevenlabs'
        and not os.getenv('ELEVENLABS_API_KEY', '').strip()
    ):
        os.environ['AUDIO_PROVIDER'] = 'elevenlabs' if os.getenv('ELEVENLABS_API_KEY', '').strip() else 'piper'
    os.environ.setdefault('LOCAL_TTS_VOICE', 'dfki')
    os.environ.setdefault('ELEVENLABS_VOICE', 'jessica')
    # A preview can explicitly suppress all native DLL loads before importing the guard.
    from contextlib import nullcontext
    from unittest.mock import patch
    native_context = patch('ctypes.CDLL', side_effect=OSError('Native guard disabled in preview')) if args.no_native_guard else nullcontext()
    with native_context:
        from PyQt6.QtWidgets import QApplication
        from data import database as db
        db.init_db()
        from unified_parent import UnifiedParent
        app = QApplication(sys.argv)
        from ui_fonts import configure_fonts
        configure_fonts(app)
        window = UnifiedParent()
        # Keep text readable regardless of the Windows light/dark theme.
        window.setStyleSheet(window.styleSheet() + """
        QWidget {
            color: #172b4d;
            background-color: #f4f7fb;
            font-family: "Segoe UI";
            font-size: 16px;
        }
        QLabel, QCheckBox, QRadioButton, QGroupBox {
            color: #172b4d;
        }
        QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox,
        QComboBox, QListWidget, QTreeWidget, QTableWidget {
            color: #172b4d;
            background-color: #ffffff;
            border: 1px solid #a6b4c8;
            border-radius: 6px;
            padding: 6px;
            selection-background-color: #d9e9ff;
            selection-color: #10294b;
        }
        QComboBox QAbstractItemView {
            color: #172b4d;
            background-color: #ffffff;
            selection-background-color: #d9e9ff;
            selection-color: #10294b;
        }
        QTabWidget::pane {
            border: 1px solid #b8c5d6;
            background-color: #f4f7fb;
        }
        QTabBar::tab {
            color: #243b5a;
            background-color: #e4ebf5;
            padding: 10px 14px;
            border: 1px solid #b8c5d6;
        }
        QTabBar::tab:selected {
            color: #ffffff;
            background-color: #245ca6;
        }
        QPushButton {
            color: #ffffff;
            background-color: #245ca6;
            border: 1px solid #1c4c8c;
            border-radius: 6px;
            padding: 9px 14px;
            font-weight: 600;
        }
        QPushButton:hover { background-color: #1c4c8c; }
        QPushButton:pressed { background-color: #153b70; }
        QPushButton:disabled {
            color: #526176;
            background-color: #e1e7ef;
            border-color: #b8c5d6;
        }
        QListWidget::item { padding: 6px; }
        QListWidget::item:selected {
            color: #10294b;
            background-color: #d9e9ff;
        }
        QToolTip {
            color: #172b4d;
            background-color: #ffffff;
            border: 1px solid #a6b4c8;
        }
        """)
        window.show()
        from audio_narrator import shutdown_narration
        app.aboutToQuit.connect(shutdown_narration)
        from integrated_ui import shutdown_voice_requests
        app.aboutToQuit.connect(shutdown_voice_requests)
        import keyboard_guard
        app.aboutToQuit.connect(keyboard_guard.guard.stop)
        return app.exec()


def main():
    from role_launcher import main as launch
    return launch()


if __name__ == '__main__':
    sys.exit(main())
