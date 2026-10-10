"""Review-first teaching workflow, shared by document and manual authoring."""
from pathlib import Path
from copy import deepcopy
from PyQt6.QtCore import Qt,QThread,pyqtSignal
from PyQt6.QtWidgets import (QWidget,QDialog,QVBoxLayout,QHBoxLayout,QFormLayout,QScrollArea,
    QLineEdit,QPlainTextEdit,QPushButton,QComboBox,QSpinBox,QLabel,QListWidget,QFileDialog,QMessageBox)
import teaching_materials as materials
from curriculum import catalogue

_WORKERS=set()


def shutdown_material_workers():
    for worker in list(_WORKERS): worker.wait(65000)


class MaterialWorker(QThread):
    done=pyqtSignal(object)
    failed=pyqtSignal(str)
    def __init__(self,mode,args):
        super().__init__();self.mode=mode;self.args=args
    def run(self):
        try:
            result=materials.extract_text(*self.args) if self.mode=='read' else materials.generate_questions(*self.args)
            self.done.emit(result)
        except Exception as error: self.failed.emit(str(error))


class QuestionComposer(QWidget):
    changed=pyqtSignal()
    def __init__(self,parent=None):
        super().__init__(parent);self.questions=[]
        layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,0)
        self.list=QListWidget();self.list.setWordWrap(True);self.list.setMinimumHeight(130)
        self.list.setMaximumHeight(240);layout.addWidget(self.list)
        row=QHBoxLayout()
        for text,callback in [('Soru ekle',lambda:self.edit()),('Düzenle',lambda:self.edit(self.list.currentRow())),('Kaldır',self.remove)]:
            b=QPushButton(text);b.clicked.connect(callback);row.addWidget(b)
        layout.addLayout(row)
        self.list.itemDoubleClicked.connect(lambda _:self.edit(self.list.currentRow()))
        note=QLabel('Soruyu açarak seçenekleri, doğru cevabı, ipucunu ve açıklamayı kontrol edin. İstemediğiniz soruları kaldırabilirsiniz.')
        note.setWordWrap(True);layout.addWidget(note)
    def set_questions(self,questions):
        self.questions=deepcopy(questions);self.refresh()
    def refresh(self):
        self.list.clear()
        for index,q in enumerate(self.questions):
            self.list.addItem(f"{index+1}. {q['text']}\nDoğru cevap: {q['choices'][q['answer']]} · Kazanım: {q.get('concept','genel')}")
        self.changed.emit()
    def remove(self):
        index=self.list.currentRow()
        if 0<=index<len(self.questions): self.questions.pop(index);self.refresh()
    def edit(self,index=None):
        if index is not None and not 0<=index<len(self.questions): return
        q=self.questions[index] if index is not None else {}
        d=QDialog(self);d.setWindowTitle('Soruyu incele ve düzenle');d.resize(650,700)
        if self.screen(): d.setMaximumHeight(self.screen().availableGeometry().height()-60)
        outer=QVBoxLayout(d);scroll=QScrollArea();scroll.setWidgetResizable(True);body=QWidget();f=QFormLayout(body)
        scroll.setWidget(body);outer.addWidget(scroll)
        error=QLabel();error.setWordWrap(True);error.setStyleSheet('color:#b53c48');f.addRow(error)
        text=QPlainTextEdit(q.get('text',''));text.setMaximumHeight(85);f.addRow('Soru',text)
        choices=[]
        for i in range(4):
            edit=QLineEdit(q.get('choices',['']*4)[i]);choices.append(edit);f.addRow(f'{chr(65+i)} seçeneği',edit)
        answer=QComboBox();answer.addItems(['A','B','C','D']);answer.setCurrentIndex(q.get('answer',0));f.addRow('Doğru seçenek',answer)
        hint=QLineEdit(q.get('hint',''));f.addRow('İpucu',hint)
        concept=QLineEdit(q.get('concept','genel'));f.addRow('Kazanım etiketi',concept)
        f.addRow(QLabel('Aynı öğrenme hedefine ait farklı sorularda aynı etiketi kullanın.'))
        explanation=QPlainTextEdit(q.get('explanation',''));explanation.setMaximumHeight(85);f.addRow('Çözüm açıklaması',explanation)
        example=QPlainTextEdit(q.get('example',''));example.setMaximumHeight(70);f.addRow('Farklı çözümlü örnek',example)
        def save():
            try:
                result=materials.validate_questions([dict(text=text.toPlainText(),choices=[e.text() for e in choices],
                    answer=answer.currentIndex(),hint=hint.text(),concept=concept.text(),
                    explanation=explanation.toPlainText(),example=example.toPlainText())])[0]
                if index is None:
                    if len(self.questions)>=30: raise ValueError('Bir pakette en fazla 30 soru olabilir.')
                    self.questions.append(result)
                else: self.questions[index]=result
                self.refresh();d.accept()
            except ValueError as exc: error.setText(str(exc))
        b=QPushButton('Soruyu kaydet');b.clicked.connect(save);outer.addWidget(b);d.exec()


class MaterialDialog(QDialog):
    def __init__(self,identity,grade,parent=None):
        super().__init__(parent);self.identity=identity;self.worker=None;self.document_name='';self.saved_pack_id=None
        from role_ui import STYLE
        self.setStyleSheet(STYLE+'''QListWidget { background:white; color:#1b304a; border:1px solid #bccde2; border-radius:10px; padding:8px; }
            QListWidget::item { padding:10px; border-bottom:1px solid #edf2fa; }
            QListWidget::item:selected { background:#e5efff; color:#183153; }''')
        self.setWindowTitle('Ders materyalleri ve soru atölyesi');self.resize(900,780)
        if self.screen(): self.setMaximumHeight(self.screen().availableGeometry().height()-50)
        outer=QVBoxLayout(self);scroll=QScrollArea();scroll.setWidgetResizable(True);body=QWidget();layout=QVBoxLayout(body)
        scroll.setWidget(body);outer.addWidget(scroll)
        title=QLabel('Ders belgesinden öğrenme görevine');title.setStyleSheet('font-size:24px;font-weight:700;color:#244b76');layout.addWidget(title)
        note=QLabel('1. Ders ve temayı seç   →   2. Soruları hazırla ve düzenle   →   3. Onaylayıp görev olarak ata')
        note.setWordWrap(True);layout.addWidget(note)
        form=QFormLayout();layout.addLayout(form)
        self.title=QLineEdit();self.title.setPlaceholderText('Örneğin: Doğayı keşfediyoruz')
        self.grade=QComboBox()
        for g in range(1,5): self.grade.addItem(f'{g}. sınıf',g)
        self.grade.setCurrentIndex(grade-1)
        self.subject=QComboBox();self.unit=QComboBox()
        self.count=QSpinBox();self.count.setRange(2,30);self.count.setValue(12)
        for name,widget in [('Paket adı',self.title),('Sınıf düzeyi',self.grade),('Ders',self.subject),('MEB tema / öğrenme alanı',self.unit),('Üretilecek soru sayısı',self.count)]: form.addRow(name,widget)
        self.program_note=QLabel();self.program_note.setWordWrap(True);layout.addWidget(self.program_note)
        self.load=QPushButton('PDF / Word / metin belgesi seç');self.load.clicked.connect(self.choose_document);layout.addWidget(self.load)
        self.text=QPlainTextEdit();self.text.setPlaceholderText('Belgenin ilgili bölümünü buraya da yapıştırabilirsiniz.');self.text.setMaximumHeight(150);layout.addWidget(self.text)
        self.offline=QPushButton('Seçili konunun hazır sorularını getir · İnternetsiz');self.offline.clicked.connect(self.load_ready);layout.addWidget(self.offline)
        self.settings=QPushButton('Ses ve yapay zekâ bağlantısını ayarla');self.settings.clicked.connect(self.open_settings);layout.addWidget(self.settings)
        self.ai=QPushButton('PDF sorularını analiz et · Benzer taslaklar üret');self.ai.clicked.connect(self.generate);layout.addWidget(self.ai)
        disclosure=QLabel('Bu düğmeye bastığınızda yukarıdaki metin Gemini hizmetine gönderilir. Öğrenci adı gibi kişisel bilgileri çıkarın. Elle soru eklemek internet gerektirmez.')
        disclosure.setWordWrap(True);layout.addWidget(disclosure)
        self.status=QLabel();self.status.setWordWrap(True);layout.addWidget(self.status)
        self.composer=QuestionComposer();layout.addWidget(self.composer)
        self.approve=QPushButton('Soruları kontrol ettim · Paketi onayla ve kaydet');self.approve.clicked.connect(self.save);outer.addWidget(self.approve)
        self.grade.currentIndexChanged.connect(self.reload_subjects);self.subject.currentIndexChanged.connect(self.reload_units);self.reload_subjects()
    def reload_subjects(self):
        self.subject.blockSignals(True);self.subject.clear()
        for course in catalogue(self.grade.currentData()): self.subject.addItem(course['subject'],course)
        self.subject.blockSignals(False);self.reload_units()
    def reload_units(self):
        self.unit.clear();course=self.subject.currentData()
        if course:
            for unit in course['units']: self.unit.addItem(unit['title'],unit)
        self.program_note.setText(course['active_model'] if course else 'Bu sınıf için MEB önbelleği bulunamadı.')
    def run_worker(self,mode,args):
        if self.worker and self.worker.isRunning(): return
        for w in (self.ai,self.offline,self.settings,self.load,self.approve,self.grade,self.subject,self.unit,self.composer,self.text,self.count): w.setEnabled(False)
        self.status.setText('Belge okunuyor…' if mode=='read' else 'Taslak sorular hazırlanıyor… Öğretmen onayı olmadan öğrenciye gösterilmez.')
        worker=MaterialWorker(mode,args);self.worker=worker;_WORKERS.add(worker)
        def done(value):
            if mode=='read': self.text.setPlainText(value);self.status.setText(f'{self.document_name} · {len(value)} karakter okundu.')
            else:
                self.composer.set_questions(value)
                types=len({q.get('concept','genel') for q in value})
                self.status.setText(f'{len(value)} benzer taslak soru · {types} soru türü/kazanım. Aynı türdeki sorular öğrenme takibinde birlikte değerlendirilir. Doğru cevapları ve açıklamaları kontrol edip onaylayın.')
        def failed(message): self.status.setText(message)
        def finished():
            for w in (self.ai,self.offline,self.settings,self.load,self.approve,self.grade,self.subject,self.unit,self.composer,self.text,self.count): w.setEnabled(True)
            _WORKERS.discard(worker)
        worker.done.connect(done);worker.failed.connect(failed);worker.finished.connect(finished);worker.start()
    def choose_document(self):
        path,_=QFileDialog.getOpenFileName(self,'Ders belgesi seç','','Ders belgeleri (*.pdf *.docx *.txt *.md)')
        if path:
            self.document_name=Path(path).name;self.run_worker('read',(path,))
    def open_settings(self):
        owner=self.parentWidget()
        while owner is not None:
            if hasattr(owner,'ai_settings'):
                owner.ai_settings();return
            owner=owner.parentWidget()
        self.status.setText('Veli veya öğretmen ana ekranındaki Hesap ve sınıflar bölümünden bağlantıyı ayarlayabilirsiniz.')
    def load_ready(self,checked=False,confirm=True):
        if self.worker and self.worker.isRunning():return
        if confirm and self.composer.questions and QMessageBox.question(self,'Hazır sorular','Mevcut taslağın yerine seçili konunun hazır soruları getirilsin mi?')!=QMessageBox.StandardButton.Yes:return
        from curriculum_practice import topics,offline_bank
        unit=self.unit.currentData()
        topic=next((t for t in topics(self.grade.currentData()) if unit and t['subject']==self.subject.currentText() and t['title']==unit['title']),None)
        if not topic:self.status.setText('Önce ders ve MEB temasını seçin.');return
        from copy import deepcopy
        bank=offline_bank(topic['skill']);seen=set();questions=[]
        for q in bank:
            text=' '.join(q['text'].casefold().split())
            if text in seen:continue
            seen.add(text);questions.append(deepcopy(q))
            if len(questions)>=self.count.value():break
        if not questions:self.status.setText('Bu tema için hazır soru bulunamadı. Elle soru ekleyebilirsiniz.');return
        self.composer.set_questions(questions)
        if not self.title.text().strip():self.title.setText(self.subject.currentText()+' · '+unit['title'])
        self.document_name=''
        self.status.setText(f'{len(questions)} hazır soru getirildi. Bunlar seçili MEB konusunun soru bankasındandır; yüklediğiniz belgeden üretilmedi. Kontrol edip paketi kaydedebilirsiniz.')

    def generate(self):
        if self.composer.questions and QMessageBox.question(self,'Taslağı yenile','Mevcut taslak soruların yerine yeni sorular üretilecek. Devam edilsin mi?')!=QMessageBox.StandardButton.Yes: return
        unit=self.unit.currentData()
        if not unit: self.status.setText('Önce MEB temasını seçin.');return
        import os
        if not os.getenv('GEMINI_GENERATOR_KEY','').strip():
            self.load_ready(confirm=False)
            self.status.setText('Belgeden yeni soru üretmek için yapay zekâ bağlantısı gerekir. '+self.status.text())
            return
        self.run_worker('generate',(self.text.toPlainText(),self.grade.currentData(),self.subject.currentText(),unit['title'],self.count.value()))
    def save(self):
        try:
            unit=self.unit.currentData()
            if not unit: raise ValueError('MEB tema seçimi gerekli.')
            self.saved_pack_id=materials.save_pack(self.identity,self.title.text(),self.grade.currentData(),self.subject.currentText(),unit['title'],unit['url'],self.document_name,self.composer.questions)
            self.accept()
        except ValueError as error: self.status.setText(str(error))
    def reject(self):
        if self.worker and self.worker.isRunning():
            self.status.setText('İşlem devam ediyor; tamamlandıktan sonra pencereyi kapatabilirsiniz.');return
        super().reject()
