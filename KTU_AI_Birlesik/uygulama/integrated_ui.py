"""Join the contributed animated UI to the preserved Windows learning loop."""
import time
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QPointF, QSize
from PyQt6.QtGui import QPainter, QFont, QFontMetrics, QPalette
from PyQt6.QtWidgets import (QLabel, QPushButton, QProgressBar, QVBoxLayout,
                            QHBoxLayout, QScrollArea, QWidget, QDialog,
                            QPlainTextEdit, QTabWidget, QGridLayout, QInputDialog, QCheckBox,
                            QStyleOptionButton, QStyle)
import homework_ui as ui
from data import database as db
from pin_security import pin_limiter
from audio_narrator import start_narration, stop_narration
from quiz_tools import QUIZ_QSS, WritingPad, VoiceRequest, LessonScene, InkRecognition

_VOICE_WORKERS = set()


def shutdown_voice_requests():
    for worker in list(_VOICE_WORKERS):
        worker.wait(30000)


_asset_names = {'veli.png': 'parent.png', 'ogretmen.png': 'teacher.png',
                'kızögrenci.png': 'student_girl.png', 'kızogrenci.png': 'student_girl.png',
                'erkekögrenci.png': 'student_boy.png', 'erkekogrenci.png': 'student_boy.png'}
_old_path = ui.gorsel_yol


def _asset_path(name):
    from pathlib import Path
    import unicodedata
    simple = ''.join(c for c in unicodedata.normalize('NFD', name) if not unicodedata.combining(c)).replace('ı', 'i').lower()
    if simple.startswith('kiz'):
        mapped = 'student_girl.png'
    elif simple.startswith('erkek'):
        mapped = 'student_boy.png'
    else:
        mapped = _asset_names.get(name, _asset_names.get(simple))
    return str(Path(__file__).parent / 'assets' / mapped) if mapped else _old_path(name)


ui.gorsel_yol = _asset_path


def _verified_parent_exit(page):
    ok, message = pin_limiter.verify(page._pin_satiri.text().strip())
    page._pin_satiri.clear()
    page._pin_sonuc.setText('Ebeveyn doğrulandı.' if ok else message)
    if ok:
        page.ana.bridge.guvenli_emit('veli_cikisi')


ui.VeliPaneli._veli_pin_cikis = _verified_parent_exit


class WrappedAnswerButton(QPushButton):
    """Keep full answer text readable, including longer offline explanations."""
    def sizeHint(self):return QSize(240,110)
    def minimumSizeHint(self):return QSize(100,96)
    def paintEvent(self,event):
        option=QStyleOptionButton();self.initStyleOption(option)
        text=option.text;option.text=''
        painter=QPainter(self)
        self.style().drawControl(QStyle.ControlElement.CE_PushButton,option,painter,self)
        area=self.rect().adjusted(14,10,-14,-10)
        flags=Qt.AlignmentFlag.AlignCenter.value|Qt.TextFlag.TextWordWrap.value
        font=QFont(self.font())
        if font.pointSizeF()<0 and font.pixelSize()>0:
            font.setPointSizeF(font.pixelSize()*72/self.logicalDpiY())
        while QFontMetrics(font).boundingRect(area,flags,text).height()>area.height() and font.pointSizeF()>11:
            font.setPointSizeF(font.pointSizeF()-1)
        painter.setFont(font)
        painter.setPen(option.palette.color(QPalette.ColorRole.ButtonText))
        painter.drawText(area,flags,text)


class QuizCard(ui.OgrenciQuizEkrani):
    """Use all contributed quiz graphics; answer state belongs to LearningSession."""
    def _arayuz_olustur(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(12)
        header = QHBoxLayout()
        self.baslik = QLabel('Öğrenme zamanı')
        self.baslik.setObjectName('QuizHeading')
        self.yildiz_lbl = QLabel('⭐ 0')
        self.yildiz_lbl.setObjectName('QuizScore')
        header.addWidget(self.baslik, 1)
        header.addWidget(self.yildiz_lbl)
        layout.addLayout(header)
        self.soru_lbl = QLabel('Soru hazırlanıyor…')
        self.soru_lbl.setObjectName('SoruAlani')
        self.soru_lbl.setWordWrap(True)
        self.soru_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.soru_lbl.setMinimumHeight(90)
        layout.addWidget(self.soru_lbl)
        grid = QGridLayout()
        grid.setSpacing(12)
        for index in range(4):
            button = WrappedAnswerButton()
            button.setObjectName('CevapButon')
            button.clicked.connect(lambda _, i=index: self.cevap_secildi(i))
            grid.addWidget(button, index // 2, index % 2)
            self.butonlar.append(button)
        layout.addLayout(grid)
        self._ozet_lbl = QLabel()
        self._ozet_lbl.hide()
        self._bitir_sonuc = QLabel()

    def giris_animasyonu_baslat(self, sure_ms=360):
        # The scroll area owns card geometry; moving it clips the right edge.
        if self._eff_opak is None:
            return
        if self._anim_gecis is not None:
            self._anim_gecis.stop()
        self._anim_gecis = QPropertyAnimation(self._eff_opak, b'opacity', self)
        self._anim_gecis.setDuration(sure_ms)
        self._anim_gecis.setStartValue(0.0)
        self._anim_gecis.setEndValue(1.0)
        self._anim_gecis.start()

    def yeni_soru(self):
        pass  # Original constructor calls this before a LearningSession is attached.

    def cevap_secildi(self, index):
        self.on_answer(index)

    def _quiz_bitir(self):
        self.on_parent_exit()


def enhance_break_window(base_class, bars_class):
    class IntegratedBreakWindow(base_class):
        def _build(self):
            self.setStyleSheet(ui.GLOBAL_QSS + QUIZ_QSS)
            outer = QVBoxLayout(self)
            outer.setContentsMargins(24, 18, 24, 18)
            outer.setSpacing(10)
            top = QHBoxLayout()
            self.skill_lbl = QLabel()
            self.timer_lbl = QLabel()
            top.addWidget(self.skill_lbl)
            top.addStretch(1)
            top.addWidget(self.timer_lbl)
            exit_button = QPushButton('Ebeveyn girişi')
            exit_button.setObjectName('QuietButton')
            exit_button.clicked.connect(self._ask_pin)
            top.addWidget(exit_button)
            outer.addLayout(top)
            self.progress = QProgressBar()
            self.progress_lbl = QLabel()
            outer.addWidget(self.progress)
            outer.addWidget(self.progress_lbl)
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            card = QuizCard(self)
            self.card = card
            card.on_answer = self._on_choice
            card.on_parent_exit = self._ask_pin
            profile = db.get_student() or {}
            card.profil_guncelle(profile.get('nickname', 'Öğrenci'), profile.get('gender', 'kiz'))
            self.question = card.soru_lbl
            self.question.setTextFormat(Qt.TextFormat.PlainText)
            self.choice_btns = card.butonlar
            for button in self.choice_btns:
                button.setMinimumHeight(96)
                button.setMaximumHeight(160)
            self.bars = bars_class()
            card.layout().insertWidget(2, self.bars)
            self.visual = LessonScene(card)
            self.visual.setMinimumHeight(140)
            self.visual.setMaximumHeight(180)
            self.visual.hide()
            card.layout().insertWidget(2, self.visual)
            self.info = QLabel()
            self.info.setWordWrap(True)
            self.info.setTextFormat(Qt.TextFormat.PlainText)
            card.layout().addWidget(self.info)
            dock = QWidget(self)
            dock.setObjectName('QuizActions')
            dock_layout=QVBoxLayout(dock)
            dock_layout.setContentsMargins(0,4,0,0)
            controls = QGridLayout()
            self.hint_btn = QPushButton('İpucu göster')
            self.hint_btn.clicked.connect(self._on_hint)
            self.audio_btn = QPushButton('Soruyu sesli dinle')
            self.audio_btn.clicked.connect(self._speak_question)
            self.explain_btn = QPushButton('Sesli ve görselli anlat')
            self.explain_btn.clicked.connect(self._explain)
            self.next_btn = QPushButton('Sonraki soru')
            self.next_btn.clicked.connect(self._load_question)
            self.support_btn = QPushButton('Ebeveyn desteği')
            self.support_btn.clicked.connect(self._ask_pin)
            self.support_btn.hide()
            self.parent_btn = QPushButton('Ebeveyn girişi')
            self.parent_btn.clicked.connect(self._ask_pin)
            self.voice_btn = QPushButton('Mikrofonla yardım iste')
            self.voice_btn.clicked.connect(self._voice_request)
            self.writing_btn = QPushButton('Yazı ve çizim alanı')
            self.writing_btn.clicked.connect(self._open_writing)
            self.parent_btn.hide()
            self.audio_btn.setText('Soruyu dinle')
            self.explain_btn.setText('Birlikte öğrenelim')
            self.writing_btn.setText('Çalışma defterim')
            for index, b in enumerate((self.audio_btn, self.writing_btn, self.explain_btn)):
                controls.addWidget(b, 0, index)
            dock_layout.addLayout(controls)
            self.help_toggle = QPushButton('Daha fazla yardım ▾')
            self.help_toggle.setObjectName('QuietButton')
            self.help_toggle.setCheckable(True)
            dock_layout.addWidget(self.help_toggle)
            self.help_panel = QWidget(dock)
            help_row = QHBoxLayout(self.help_panel)
            help_row.setContentsMargins(0, 0, 0, 0)
            for b in (self.hint_btn, self.voice_btn, self.support_btn):
                help_row.addWidget(b)
            self.help_panel.hide()
            self.help_toggle.toggled.connect(self.help_panel.setVisible)
            dock_layout.addWidget(self.help_panel)
            dock_layout.addWidget(self.next_btn)
            card.layout().addStretch(1)
            scroll.setWidget(card)
            outer.addWidget(scroll, 1)
            outer.addWidget(dock)
            self._explanation_dialog = None
            self._speech_generation = 0
            self._writing_dialog = None
            self._voice_worker = None
            self._advance_timer = QTimer(self)
            self._advance_timer.setSingleShot(True)
            self._advance_timer.setInterval(1100)
            self._advance_timer.timeout.connect(self._advance_correct)

        def _advance_correct(self):
            if not self._allow_close and not self._support and self._answered:
                self._load_question()

        def _open_writing(self):
            if self._writing_dialog is not None:
                self._writing_dialog.show()
                self._writing_dialog.raise_()
                return
            dialog = QDialog(self)
            dialog.setWindowTitle('Yazarak ve çizerek çalışalım')
            dialog.resize(760, 490)
            layout = QVBoxLayout(dialog)
            self.writing_question = QLabel(self.question.text())
            self.writing_question.setWordWrap(True)
            layout.addWidget(self.writing_question)
            tabs = QTabWidget()
            self.notes = QPlainTextEdit()
            self.notes.setPlaceholderText('İşlemini veya anlamadığın yeri buraya yaz…')
            self.pad = WritingPad()
            tabs.addTab(self.notes, 'Klavyeyle yaz')
            tabs.addTab(self.pad, 'Kalemle / fareyle çiz')
            layout.addWidget(tabs)
            row = QHBoxLayout()
            convert = QPushButton('Rakamı düzgün yazıya çevir')
            undo = QPushButton('Son çizgiyi geri al')
            undo.clicked.connect(self.pad.undo)
            row.addWidget(convert)
            row.addWidget(undo)
            clear = QPushButton('Alanı temizle')
            clear.clicked.connect(lambda: (self.notes.clear(), self.pad.clear()))
            help_button = QPushButton('Bu soruyu anlat')
            help_button.clicked.connect(self._explain)
            row.addWidget(clear)
            row.addWidget(help_button)
            layout.addLayout(row)
            recognition_status = QLabel('Rakamını çiz, ardından düzgün yazıya çevir düğmesine bas.')
            recognition_status.setWordWrap(True)
            layout.addWidget(recognition_status)
            auto = QCheckBox('Yazdıklarımı otomatik dönüştür')
            auto.setChecked(True)
            layout.addWidget(auto)
            recognition_status.setText('Yazmaya devam edebilirsin. Kısa bir duraklamada rakamların otomatik dönüşür.')
            ink_timer = QTimer(dialog)
            ink_timer.setSingleShot(True)
            ink_timer.setInterval(850)
            busy = [False]
            retry = [False]

            def recognize(automatic=False):
                if busy[0]:
                    retry[0] = True
                    return
                if self.pad.active is not None:
                    if automatic:
                        ink_timer.start()
                    return
                if not self.pad.strokes:
                    if not automatic:
                        recognition_status.setText('Önce kalem alanına bir rakam veya sayı yaz.')
                    return
                generation = self._speech_generation
                snapshot = [[QPointF(p) for p in stroke] for stroke in self.pad.strokes]
                worker = InkRecognition(snapshot)
                _VOICE_WORKERS.add(worker)
                busy[0] = True
                convert.setEnabled(False)
                recognition_status.setText('El yazısı okunuyor…')

                def done(value):
                    if self._allow_close or generation != self._speech_generation:
                        return
                    if snapshot != self.pad.strokes:
                        retry[0] = True
                        return
                    accepted = True
                    if not automatic:
                        value, accepted = QInputDialog.getText(dialog, 'Okunan sayıyı kontrol et',
                                                              'Doğru değilse düzelt:', text=value)
                    if accepted and value.strip():
                        if snapshot != self.pad.strokes:
                            return
                        self.pad.commit_text(value.strip())
                        tabs.setCurrentWidget(self.pad)
                        recognition_status.setText('Dönüştürüldü. Yanına veya altına yazmaya devam edebilirsin; geri al ile düzeltebilirsin.')
                    else:
                        recognition_status.setText('El yazın korundu.')

                worker.recognized.connect(done)
                def failed(message):
                    if generation == self._speech_generation:
                        recognition_status.setText(message)

                def finished():
                    busy[0] = False
                    convert.setEnabled(True)
                    if retry[0] and auto.isChecked() and dialog.isVisible():
                        retry[0] = False
                        ink_timer.start()

                worker.failed.connect(failed)
                worker.finished.connect(finished)
                worker.finished.connect(lambda: _VOICE_WORKERS.discard(worker))
                worker.start()

            convert.clicked.connect(lambda: recognize(False))
            ink_timer.timeout.connect(lambda: recognize(True) if auto.isChecked() else None)
            self.pad.strokes_changed.connect(lambda: ink_timer.start() if auto.isChecked() else None)
            auto.toggled.connect(lambda checked: ink_timer.start() if checked else ink_timer.stop())
            dialog.finished.connect(lambda _: ink_timer.stop())
            layout.addWidget(QLabel('Bu alan çalışma defterindir. Cevabını soru ekranındaki seçeneklerden seç.'))
            self._writing_dialog = dialog
            dialog.show()

        def _voice_request(self):
            if self._voice_worker is not None and self._voice_worker.isRunning():
                return
            generation = self._speech_generation
            self.info.setText('Mikrofon açık: anlamadığın yeri söyle veya “anlatır mısın” de.')
            self.info.show()
            self.voice_btn.setEnabled(False)
            worker = VoiceRequest()
            self._voice_worker = worker
            _VOICE_WORKERS.add(worker)

            def recognized(text):
                if self._allow_close or generation != self._speech_generation:
                    return
                self.info.setText('Söylediğin: ' + text)
                self._explain()

            def failed(message):
                if not self._allow_close and generation == self._speech_generation:
                    self.info.setText(message)
                    self.info.show()

            worker.recognized.connect(recognized)
            worker.failed.connect(failed)
            worker.finished.connect(lambda: _VOICE_WORKERS.discard(worker))
            worker.finished.connect(lambda: self.voice_btn.setEnabled(True))
            worker.start()

        def _load_question(self):
            self._advance_timer.stop()
            stop_narration()
            self._speech_generation += 1
            super()._load_question()
            if self._allow_close or self.learning.goal_reached() or self._support:
                return
            self.audio_btn.setText('Soruyu dinle')
            self.audio_btn.show()
            if self.learning.current:
                self.visual.show_visual(self.learning.current.get('visual') or {})
            if self._explanation_dialog:
                self._explanation_dialog.close()
            if self._writing_dialog is not None:
                self.writing_question.setText(self.question.text())
                self.notes.clear()
                self.pad.clear()
            self.card._ozet_lbl.setText(f'Öğrenme: %{self.learning.mastery_percent()} · Hedef %80' if getattr(self.learning,'mastery_mode',False) else f'Deneme: {self.learning.attempts}/{self.learning.max_attempts}')
            self.card.yildiz_lbl.setText(f'⭐ {self.learning.done_count()}')
            self.help_toggle.setChecked(False)
            self.card.giris_animasyonu_baslat()

        def _on_choice(self, index):
            if self._answered or self._support:
                return
            correct = index == self.learning.current['answer']
            super()._on_choice(index)
            self.card._alan_flash('dogru' if correct else 'yanlis')
            self.card._ozet_lbl.setText(f'Öğrenme: %{self.learning.mastery_percent()} · Hedef %80' if getattr(self.learning,'mastery_mode',False) else f'Deneme: {self.learning.attempts}/{self.learning.max_attempts}')
            self.card.yildiz_lbl.setText(f'⭐ {self.learning.done_count()}')
            if correct:
                self.next_btn.hide()
                self.info.setText('Harika, doğru cevap! Sonraki soruya geçiyoruz…')
                self._advance_timer.start()
            else:
                self.help_toggle.setChecked(True)

        def _on_hint(self):
            super()._on_hint()
            if self.learning.current and (self.learning.current.get('visual') or {}).get('scene_id'):
                self.bars.hide()

        def _update_progress(self):
            super()._update_progress()
            from learning_engine.turkish_text import restore_text
            self.progress_lbl.setText(restore_text(self.progress_lbl.text()))

        def _speak_question(self):
            if not self.learning.current:
                return
            generation = self._speech_generation
            self.audio_btn.setEnabled(False)
            self.audio_btn.setText('Ses hazırlanıyor…')

            def done():
                if self._allow_close or generation != self._speech_generation:
                    return
                self.audio_btn.setText('Soruyu dinle')
                self.audio_btn.setEnabled(True)

            def failed(message):
                if self._allow_close or generation != self._speech_generation:
                    return
                done()
                self.info.setText(message)
                self.info.show()

            self._narration_worker = start_narration(self.learning.current['text'], done, failed)

        def _explain(self):
            q = self.learning.current
            if not q or self._support:
                return
            self._hint_used = True
            dialog = QDialog(self)
            dialog.setWindowTitle('Birlikte öğrenelim')
            if self._explanation_dialog is not None and self._explanation_dialog.isVisible():
                self._explanation_dialog.raise_()
                return
            dialog.resize(960, 720)
            layout = QVBoxLayout(dialog)
            from learning_engine.lesson_service import prepare_question
            lesson = prepare_question(dict(prompt=q['text'], options=q['choices'],
                                           correct_index=q['answer'], hint=q['hint'],
                                           explanation=q['explanation'], example=q.get('example', '')))
            from learning_engine.visual_help import make_lesson
            try:
                lesson = make_lesson(lesson)
            except ValueError:
                from learning_engine.lesson_service import local_lesson
                lesson = local_lesson(lesson)
            steps = lesson['steps']
            from animated_lessons import AnimatedLessonScene
            illustration = AnimatedLessonScene(q,dialog)
            layout.addWidget(illustration, 1)
            text = QLabel()
            text.setWordWrap(True)
            text.setTextFormat(Qt.TextFormat.PlainText)
            layout.addWidget(text)
            status = QLabel()
            status.setWordWrap(True)
            layout.addWidget(status)
            row = QHBoxLayout()
            prev, listen, nxt = QPushButton('Önceki adım'), QPushButton('Tekrar dinle'), QPushButton('Sonraki adım')
            for b in (prev, listen, nxt):
                row.addWidget(b)
            layout.addLayout(row)
            automatic=QCheckBox("Sesli anlatım bitince sonraki adıma geç");automatic.setChecked(True)
            layout.addWidget(automatic)
            state = [0]
            generation=[0]

            def show(delta=0):
                stop_narration()
                generation[0]+=1
                token=generation[0]
                state[0] = max(0, min(len(steps)-1, state[0]+delta))
                title, caption = steps[state[0]][:2]
                title = {'setup': 'İşlemi hazırlayalım', 'units': 'Birler basamağı',
                         'carry': 'Eldeyi anlayalım', 'tens': 'Onlar basamağı',
                         'hundreds': 'Yüzler basamağı', 'result': 'Sonucu bulalım',
                         'toys': 'Oyuncaklarla düşünelim', 'whole': 'Bütünleri inceleyelim',
                         'slices': 'Eşit parçalara ayıralım',
                         'highlight': 'Bir parçayı karşılaştıralım'}.get(title, title)
                text.setText(f'{title}\n\n{caption}')
                illustration.show_step(lesson, state[0])
                status.clear()
                prev.setEnabled(state[0] > 0)
                nxt.setEnabled(state[0] < len(steps)-1)
                def advance():
                    if dialog.isVisible() and token==generation[0] and automatic.isChecked() and state[0]<len(steps)-1:show(1)
                def audio_error(message):
                    if dialog.isVisible() and token == generation[0]:
                        status.setText(message)
                status.setText('Ses hazırlanıyor…')
                start_narration(caption,
                    on_success=lambda: status.clear() if dialog.isVisible() and token == generation[0] else None,
                    on_error=audio_error, on_finished=advance)

            prev.clicked.connect(lambda: show(-1))
            nxt.clicked.connect(lambda: show(1))
            listen.clicked.connect(lambda: show(0))
            def close_narration(_):
                generation[0] += 1
                stop_narration()
            dialog.finished.connect(close_narration)
            self._explanation_dialog = dialog
            show()
            dialog.show()
            import os
            from math_solution import is_math_question, MathSolutionWorker
            if is_math_question(q):
                cached = q.get('_worked_solution')
                if cached:
                    steps[:] = cached
                    state[0] = 0
                    show()
                elif os.getenv('GEMINI_GENERATOR_KEY', '').strip():
                    status.setText('Gemini işlemli çözümü hazırlıyor…')
                    worker = MathSolutionWorker(q)
                    if not hasattr(self, '_math_workers'):
                        self._math_workers = []
                    self._math_workers.append(worker)
                    def received(value):
                        q['_worked_solution'] = value
                        if self._explanation_dialog is dialog and dialog.isVisible() and self.learning.current is q:
                            steps[:] = value
                            state[0] = 0
                            listen.setEnabled(True)
                            show()
                    def failed(message):
                        if self._explanation_dialog is dialog and dialog.isVisible():
                            listen.setEnabled(True)
                            show()
                            status.setText(message)
                    def finished():
                        self._math_workers.remove(worker)
                        worker.deleteLater()
                    worker.ready.connect(received)
                    worker.failed.connect(failed)
                    worker.finished.connect(finished)
                    worker.start()

        def _finish(self, status):
            self._advance_timer.stop()
            stop_narration()
            if self._explanation_dialog:
                self._explanation_dialog.close()
            if self._writing_dialog:
                self._writing_dialog.close()
            super()._finish(status)

        def closeEvent(self, event):
            super().closeEvent(event)
            if event.isAccepted():
                self._advance_timer.stop()
                stop_narration()
                if self._explanation_dialog:
                    self._explanation_dialog.close()

    return IntegratedBreakWindow
