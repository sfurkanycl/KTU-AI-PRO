"""Expose the contributed parent/teacher/class/assignment database in the UI."""
import json
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTabWidget, QFormLayout,
                            QLineEdit, QComboBox, QPushButton, QLabel, QPlainTextEdit,
                            QTableWidget, QTableWidgetItem, QDialog, QMessageBox)
from data import education_database as school


class EducationPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        school.init_db()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('Veli ve öğretmen kayıtları, sınıflar, konular ve ödevler'))
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        self._form('Kullanıcı', [('username', 'Kullanıcı adı'), ('display_name', 'Görünen ad'),
                                ('role', 'Rol', ['parent', 'teacher'])], school.create_user)
        self._form('Sınıf', [('name', 'Sınıf adı'), ('grade', 'Sınıf düzeyi', int),
                            ('teacher_id', 'Öğretmen kayıt no', int)], school.create_class)
        self._form('Öğrenci', [('alias', 'Öğrenci adı'), ('grade', 'Sınıf düzeyi', int),
                              ('parent_id', 'Veli kayıt no', int)], school.add_student)
        self._form('Sınıfa ekle', [('class_id', 'Sınıf kayıt no', int),
                                  ('student_id', 'Öğrenci kayıt no', int)], school.enroll_student)
        self._form('Konu', [('title', 'Konu'), ('subject', 'Ders'), ('grade', 'Sınıf düzeyi', int),
                           ('created_by_user_id', 'Oluşturan kullanıcı no', int),
                           ('student_id', 'Öğrenci no (veli için)', 'optional'),
                           ('class_id', 'Sınıf no (öğretmen için)', 'optional'),
                           ('learning_objective', 'Kazanım')], school.add_topic)
        self._form('Ödev', [('title', 'Ödev adı'), ('topic_id', 'Konu no', int),
                           ('created_by_user_id', 'Oluşturan kullanıcı no', int),
                           ('question_count', 'Soru sayısı', int),
                           ('difficulty', 'Zorluk', ['Kolay', 'Orta', 'Zor']),
                           ('student_id', 'Öğrenci no (veli için)', 'optional'),
                           ('class_id', 'Sınıf no (öğretmen için)', 'optional'),
                           ('due_date', 'Teslim tarihi (isteğe bağlı)')], school.create_assignment)
        self._form('Soru', [('assignment_id', 'Ödev no', int), ('question_text', 'Soru'),
                           ('correct_answer', 'Doğru cevap'), ('options_json', 'Seçenekler (JSON liste)'),
                           ('explanation', 'Açıklama')], school.add_question)
        self._form('Ödev çöz', [('student_id', 'Öğrenci no', int),
                               ('assignment_id', 'Ödev no', int)], self._solve)
        self._form('Öğrenci raporu', [('student_id', 'Öğrenci no', int)], self._report)
        records = QWidget()
        rl = QVBoxLayout(records)
        self.record_type = QComboBox()
        self.record_type.addItems(['users', 'classes', 'students', 'topics', 'assignments', 'questions'])
        rl.addWidget(self.record_type)
        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        rl.addWidget(self.table)
        refresh = QPushButton('Kayıtları yenile')
        refresh.clicked.connect(self.refresh)
        rl.addWidget(refresh)
        self.tabs.addTab(records, 'Kayıt listesi')
        self.record_type.currentIndexChanged.connect(self.refresh)
        self.refresh()

    def _form(self, title, fields, operation):
        page = QWidget()
        layout = QFormLayout(page)
        widgets = {}
        for field in fields:
            key, label = field[:2]
            kind = field[2] if len(field) > 2 else str
            if isinstance(kind, list):
                widget = QComboBox()
                widget.addItems(kind)
            else:
                widget = QLineEdit()
            layout.addRow(label, widget)
            widgets[key] = (widget, kind)
        status = QLabel()
        status.setWordWrap(True)
        status.setTextFormat(__import__('PyQt6.QtCore', fromlist=['Qt']).Qt.TextFormat.PlainText)
        button = QPushButton('Aç' if title in ('Ödev çöz', 'Öğrenci raporu') else 'Kaydet')

        def apply():
            try:
                args = {}
                for key, (w, kind) in widgets.items():
                    value = w.currentText() if isinstance(w, QComboBox) else w.text().strip()
                    args[key] = (int(value) if value else None) if kind == 'optional' else int(value) if kind is int else value
                result = operation(**args)
                status.setText('İşlem tamamlandı.' if result is None else f'Kayıt no: {result}')
                self.refresh()
            except Exception as error:
                status.setText(str(error))

        button.clicked.connect(apply)
        layout.addRow(button)
        layout.addRow(status)
        self.tabs.addTab(page, title)

    def refresh(self, *_):
        name = self.record_type.currentText()
        if name not in ('users', 'classes', 'students', 'topics', 'assignments', 'questions'):
            return
        with school.get_connection() as conn:
            cursor = conn.execute('SELECT * FROM ' + name + ' ORDER BY id')
            rows = cursor.fetchall()
            columns = [x[0] for x in cursor.description]
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, value in enumerate(row):
                self.table.setItem(r, c, QTableWidgetItem(str(value)))

    def _report(self, student_id):
        rows = school.get_student_report(student_id)
        dialog = QDialog(self)
        dialog.setWindowTitle('Öğrenci konu raporu')
        layout = QVBoxLayout(dialog)
        text = QPlainTextEdit()
        text.setReadOnly(True)
        text.setPlainText('\n'.join(f"{r['topic']}: {r['correct_count']} doğru, {r['wrong_count']} yanlış, {r['hint_count']} ipucu" for r in rows) or 'Henüz sonuç yok.')
        layout.addWidget(text)
        dialog.resize(600, 350)
        dialog.exec()

    def _solve(self, student_id, assignment_id):
        with school.get_connection() as conn:
            allowed = conn.execute('''SELECT a.id FROM assignments a WHERE a.id=? AND
                (a.student_id=? OR a.class_id IN (SELECT class_id FROM class_students WHERE student_id=?))''',
                (assignment_id, student_id, student_id)).fetchone()
            if not allowed:
                raise ValueError('Bu ödev öğrenciye veya öğrencinin sınıfına atanmış değil.')
            rows = [dict(r) for r in conn.execute('SELECT * FROM questions WHERE assignment_id=? ORDER BY id', (assignment_id,))]
        if not rows:
            raise ValueError('Bu ödeve henüz soru eklenmedi.')
        dialog = QDialog(self)
        dialog.setWindowTitle('Ödevimi çözüyorum')
        dialog.resize(650, 450)
        layout = QVBoxLayout(dialog)
        question, status = QLabel(), QLabel()
        question.setWordWrap(True)
        status.setWordWrap(True)
        layout.addWidget(question)
        buttons = []
        state = {'index': 0, 'answered': False, 'hint': False}
        hint = QPushButton('Açıklama göster')
        nxt = QPushButton('Sonraki soru')

        def answer(value):
            if state['answered']:
                return
            q = rows[state['index']]
            correct = value.strip().casefold() == q['correct_answer'].strip().casefold()
            school.record_result(student_id, assignment_id, q['id'], value, correct, state['hint'])
            state['answered'] = True
            status.setText(('Doğru! ' if correct else 'Birlikte tekrar düşünelim. ') + q['explanation'])
            for b in buttons:
                b.setEnabled(False)
            nxt.setEnabled(True)

        for _ in range(max(4, max(len(json.loads(q['options_json'])) for q in rows))):
            b = QPushButton()
            b.clicked.connect(lambda checked=False, b=b: answer(b.text()))
            buttons.append(b)
            layout.addWidget(b)
        free = QLineEdit()
        submit = QPushButton('Cevabı gönder')
        submit.clicked.connect(lambda: answer(free.text()))
        layout.addWidget(free)
        layout.addWidget(submit)
        layout.addWidget(hint)
        layout.addWidget(status)
        layout.addWidget(nxt)

        def show():
            if state['index'] == len(rows):
                dialog.accept()
                return
            q = rows[state['index']]
            state.update(answered=False, hint=False)
            question.setText(q['question_text'])
            options = json.loads(q['options_json'])
            for i, b in enumerate(buttons):
                b.setVisible(i < len(options))
                b.setEnabled(True)
                if i < len(options):
                    b.setText(str(options[i]))
            free.setVisible(not options)
            submit.setVisible(not options)
            free.clear()
            status.clear()
            nxt.setEnabled(False)

        def explain():
            state['hint'] = True
            status.setText(rows[state['index']]['explanation'])

        hint.clicked.connect(explain)
        nxt.clicked.connect(lambda: (state.update(index=state['index']+1), show()))
        show()
        dialog.exec()
