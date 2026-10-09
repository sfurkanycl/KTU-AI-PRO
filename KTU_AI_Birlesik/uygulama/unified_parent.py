import os
from PyQt6.QtCore import QTimer, QThread, pyqtSignal
from PyQt6.QtWidgets import QMessageBox, QPushButton
from parent_panel import ParentPanel
from data import database as db
from education_panel import EducationPanel
import homework_ui
import questions


class GeminiPackWorker(QThread):
    done = pyqtSignal(list)
    failed = pyqtSignal(str)

    def __init__(self, grade, skills):
        super().__init__()
        self.grade, self.skills = grade, skills

    def run(self):
        try:
            from learning_engine.gemini_questions import prepare_pack
            mapping = {'m3_toplama': 'addition', 'm4_kesir': 'fraction_compare'}
            results = []
            for skill in self.skills:
                mapped = mapping.get(skill, skill)
                if mapped not in ('addition', 'fraction_compare', 'living_needs', 'matter_states', 'traffic', 'directions'):
                    raise ValueError('Gemini paketi bu kazanımda desteklenmiyor; yerel veya mevcut API üretimini kullanın.')
                prepare_pack(self.grade, mapped)
                results.extend(questions.reviewed_bank(skill, self.grade))
            self.done.emit(results)
        except Exception as error:
            self.failed.emit(str(error))


class UnifiedParent(ParentPanel):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Öğrenme Molası — Birleşik Uygulama')
        self.resize(1150, 800)
        for grade in (1, 2):
            if self.grade.findData(grade) < 0:
                self.grade.addItem(f'{grade}. sınıf', grade)
        self.school_panel = EducationPanel(self)
        self.tabs.addTab(self.school_panel, 'Sınıflar ve Ödevler')
        self.friendly = homework_ui.EgitimUygulamasi(self)
        self.friendly.get_guard().stop()
        self.friendly.get_bridge().finished.connect(self._friendly_finished)
        student = db.get_student() or {}
        self.friendly.profil_kaydet(
            student.get('nickname', 'Öğrenci'),
            student.get('gender', 'kiz'),
        )
        self.tabs.addTab(self.friendly, 'Renkli Giriş')
        self.gemini_btn = QPushButton('Gemini ile üret ve ikinci modelle kontrol et')
        self.gemini_btn.setEnabled(bool(os.getenv('GEMINI_GENERATOR_KEY') and os.getenv('GEMINI_REVIEWER_KEY')))
        self.gemini_btn.setToolTip('Yeni soru paketi için Gemini anahtarları gerekir; gerçek API kotası kullanır.')
        self.gen_api.parentWidget().layout().insertWidget(0, self.gemini_btn)
        self.gemini_btn.clicked.connect(self._generate_gemini)
        # The original navigation remains; student entry now starts the real recorded loop.
        original_screen = self.friendly.ekran_degistir

        def screen(key):
            if key == 'ogrenci':
                profile = self.friendly.profil_oku()
                grade = self.grade.currentData() or 4
                self.nick.setText(profile['ad'])
                db.save_student(profile['ad'], grade, profile['cinsiyet'])
                self._start_session()
                if self.runner and self.runner.active:
                    QTimer.singleShot(0, self.runner.start_break_now)
            else:
                original_screen(key)

        self.friendly.ekran_degistir = screen
        self.friendly.goruntu_degistir = screen
        self.friendly._mola_toggle_embed = self._start_break_now
        # Replace the contributed demo PIN, never retain its hard-coded bypass.
        self.friendly._sayfa_veli._pin_sonuc.setText('Çıkış için kayıtlı ebeveyn PIN’ini kullanın.')
        self.friendly._sayfa_veli._pin_satiri.setPlaceholderText('Ebeveyn PIN’i')

    def _friendly_finished(self, reason):
        if reason == 'veli_cikisi' and self.runner and self.runner.active:
            self.runner.stop()

    def _start_session(self):
        if self.runner and self.runner.active:
            return
        skills = self._checked_skills()
        if not skills:
            QMessageBox.warning(self, 'Ders seçimi', 'Önce en az bir ders veya kazanım seçin.')
            self.tabs.setCurrentIndex(0)
            return
        # Start with the current checkboxes, rather than an older saved selection.
        db.set_skills(skills)
        super()._start_session()

    def _save_profile(self):
        super()._save_profile()
        if hasattr(self, 'friendly'):
            p = db.get_student()
            self.friendly.profil_kaydet(p.get('nickname', 'Öğrenci'), p.get('gender', 'kiz'))

    def _generate_gemini(self):
        skills = self._checked_skills()
        if not skills:
            QMessageBox.information(self, 'Konu seçimi', 'Önce en az bir kazanım seçin.')
            return
        if self.worker and self.worker.isRunning():
            return
        self.gemini_btn.setEnabled(False)
        self.gen_local.setEnabled(False)
        self.gen_api.setEnabled(False)
        self.worker = GeminiPackWorker(self.grade.currentData(), skills)
        self.worker.done.connect(self._on_pack_ready)
        self.worker.failed.connect(self._on_pack_failed)
        self.worker.finished.connect(lambda: self.gemini_btn.setEnabled(True))
        self.worker.start()

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.statusBar().showMessage('Soru hazırlığı sürüyor; tamamlandıktan sonra kapatabilirsiniz.')
            event.ignore()
            return
        self.friendly.get_guard().stop()
        super().closeEvent(event)
