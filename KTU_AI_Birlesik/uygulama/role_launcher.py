"""Default role-specific application entry point."""
import argparse
import os
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--env', type=Path)
    parser.add_argument('--no-native-guard', action='store_true')
    parser.add_argument('--legacy-admin', action='store_true')
    parser.add_argument('--schedule-id', type=int)
    parser.add_argument('--smoke-test',action='store_true',help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.legacy_admin:
        sys.argv.remove('--legacy-admin')
        from main import legacy_main
        return legacy_main()
    if sys.version_info[:2] != (3, 12):
        raise SystemExit('Korunan Windows modülleri Python 3.12 gerektiriyor.')
    from dotenv import load_dotenv
    settings_path=Path(__file__).with_name('.env')
    if getattr(sys,'frozen',False):
        local_data=Path(os.environ.get('LOCALAPPDATA',str(Path.home())))/'OgrenmeMolasi'
        local_data.mkdir(parents=True,exist_ok=True)
        os.environ.setdefault('OM_LOCAL_DATA_DIR',str(local_data))
        os.environ.setdefault('OM_SCHOOL_DB_PATH',str(local_data/'school_records.db'))
        settings_path=local_data/'.env'
    load_dotenv(args.env or settings_path)
    if not os.getenv('AUDIO_PROVIDER') or (os.getenv('AUDIO_PROVIDER', '').lower() == 'elevenlabs' and not os.getenv('ELEVENLABS_API_KEY', '').strip()):
        os.environ['AUDIO_PROVIDER'] = 'elevenlabs' if os.getenv('ELEVENLABS_API_KEY', '').strip() else 'piper'
    os.environ.setdefault('LOCAL_TTS_VOICE', 'dfki')
    os.environ.setdefault('ELEVENLABS_VOICE', 'jessica')
    from contextlib import nullcontext
    from unittest.mock import patch
    native = patch('ctypes.CDLL', side_effect=OSError('Preview')) if args.no_native_guard else nullcontext()
    with native:
        from PyQt6.QtWidgets import QApplication
        from data import database as db
        if getattr(sys,'frozen',False):
            db.DATA_DIR=Path(os.environ['OM_LOCAL_DATA_DIR'])
            db.DB_PATH=db.DATA_DIR/'legacy_sessions.db'
        db.init_db()
        app = QApplication(sys.argv)
        from PyQt6.QtNetwork import QLocalServer, QLocalSocket
        from data import education_database as school
        import hashlib
        endpoint='LearningBreak_'+hashlib.sha256(str(school.DB_PATH).encode()).hexdigest()[:20]
        listener=QLocalServer()
        if not listener.listen(endpoint):
            socket=QLocalSocket()
            socket.connectToServer(endpoint)
            if socket.waitForConnected(1000):
                socket.write(b'open');socket.waitForBytesWritten(1000);socket.disconnectFromServer()
                return 0
            QLocalServer.removeServer(endpoint)
            listener.listen(endpoint)
        from ui_fonts import configure_fonts
        configure_fonts(app)
        from role_ui import RoleWindow
        window = RoleWindow()
        window._instance_server=listener
        def incoming():
            while listener.hasPendingConnections():
                socket=listener.nextPendingConnection()
                socket.close();socket.deleteLater()
            window.check_schedules()
            if window.quiz and not window.quiz._allow_close:
                window.quiz.showFullScreen();window.quiz.raise_();window.quiz.activateWindow()
            else:
                window.show();window.raise_();window.activateWindow()
        listener.newConnection.connect(incoming)
        window.show()
        if args.smoke_test:
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(1500,app.quit)
        if args.schedule_id:
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(300,window.check_schedules)
        from audio_narrator import shutdown_narration
        from integrated_ui import shutdown_voice_requests
        app.aboutToQuit.connect(shutdown_narration)
        app.aboutToQuit.connect(shutdown_voice_requests)
        from material_ui import shutdown_material_workers
        app.aboutToQuit.connect(shutdown_material_workers)
        from curriculum_practice import shutdown_workers
        app.aboutToQuit.connect(shutdown_workers)
        from keyboard_guard import guard
        app.aboutToQuit.connect(guard.stop)
        app.aboutToQuit.connect(listener.close)
        return app.exec()
