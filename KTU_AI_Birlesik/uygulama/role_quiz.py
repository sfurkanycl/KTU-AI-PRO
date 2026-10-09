"""Use the existing illustrated quiz for authenticated student accounts."""
import random
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QInputDialog, QLineEdit, QMessageBox
from student_panel import BreakWindow
from data import education_database as school
import role_store as store


def practice_questions(identity, count=12, skills=None):
    import questions as qb
    student = store.require_student(identity, identity.student_id)
    grade = student['grade']
    skills = skills or store.practice_skills(identity,identity.student_id)
    banks = {skill: qb.reviewed_bank(skill, grade) for skill in skills}
    from learning_engine.learning_core import LocalQuestionProvider
    from learning_engine.school_content import TOPICS
    provider = LocalQuestionProvider()
    for skill in skills:
        if banks[skill] or skill in qb.HOMEWORK_SKILLS:
            continue
        if skill in ('m3_carpma','m4_bolme'):
            avoid = set()
            for _ in range(max(2,count//len(skills)+1)):
                q = qb._original_make_question(skill,avoid)
                avoid.add(q['qkey'])
                banks[skill].append(q)
            continue
        mapped = 'addition' if skill == 'm3_toplama' else skill
        used = set()
        for _ in range(max(2, count // len(skills) + 1)):
            raw = provider.generate(grade, TOPICS[mapped][0], mapped, used)
            used.add(raw['signature'])
            banks[skill].append(dict(skill=skill, text=raw['prompt'], choices=raw['options'],
                answer=raw['correct_index'], explanation=raw.get('explanation',''),
                hint=raw.get('hint',''), visual=raw.get('visual'), qkey=raw['signature']))
    banks = {skill: bank for skill, bank in banks.items() if bank}
    if not banks:
        raise ValueError('Bu sınıf için hazır alıştırma bulunamadı. Velinden görev iste.')
    result = []
    for index in range(count):
        skill = list(banks)[index % len(banks)]
        q = dict(banks[skill][(index // len(banks)) % len(banks[skill])])
        q['id'] = index
        result.append(q)
    return result


class AccountSession:
    def __init__(self, identity, questions, assignment_id=None):
        if not questions:
            raise ValueError('Bu görevde çözülmemiş soru kalmadı.')
        self.identity = identity
        self.questions = questions
        self.assignment_id = assignment_id
        self.skills = list(dict.fromkeys(q['skill'] for q in questions))
        self.current = None
        self.attempts = 0
        self.max_attempts = len(questions)
        self.goal = len(questions)
        self.correct = 0
        self._recorded = False

    def next_question(self):
        if self.goal_reached():
            return None
        self.current = self.questions[self.attempts]
        self._recorded = False
        return self.current

    def answer(self, choice, seconds, hint_used=False):
        if self._recorded:
            raise ValueError('Bu soru zaten cevaplandı.')
        correct = store.save_answer(self.identity, self.current, choice, hint_used, self.assignment_id)
        self._recorded = True
        self.attempts += 1
        self.correct += int(correct)
        return dict(correct=correct, title='Doğru!' if correct else 'Birlikte öğrenelim',
                    text=self.current.get('explanation', ''), visual=None,
                    kind='ok' if correct else 'wrong', skill_done=False, fast_warning=False)

    def goal_reached(self):
        return self.attempts >= len(self.questions)

    def limit_reached(self):
        return False

    def current_skill(self):
        return self.current['skill'] if self.current else self.skills[0]

    def current_clean(self):
        return self.correct

    def done_count(self):
        return self.correct

    def progress_value(self):
        return self.attempts, len(self.questions)


class StudentQuiz(BreakWindow):
    def __init__(self, identity, questions, assignment_id=None):
        self.identity = identity
        self.verified_parent = None
        super().__init__(AccountSession(identity, questions, assignment_id), 30*60)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowTitle('Öğrenme Molası · Öğrenci')
        self.card.profil_guncelle(identity.name, 'kiz' if store.avatar_for(identity.student_id)=='student_girl.png' else 'erkek')
        self.setObjectName('ChildQuiz')
        self.setStyleSheet(self.styleSheet()+'''\nQWidget#ChildQuiz { background: #fff7df; }
            QLabel#SoruAlani { background: #fff; color: #503278; border: 2px solid #c9adef; border-radius: 22px; }
            QPushButton#CevapButon { background: #f1e8ff; color: #493065; border: 2px solid #c8a8f1; font-size: 24px; font-weight: 700; }
            QPushButton#CevapButon:hover { background: #e1ceff; border-color: #8652d6; }''')
        from keyboard_guard import guard
        self._role_guard = guard
        self._role_guard.start(max_seconds=30*60)

    def _finish(self,status):
        if hasattr(self,'_role_guard'):
            self._role_guard.stop()
        super()._finish(status)

    def keyPressEvent(self,event):
        if event.key() == Qt.Key.Key_Escape or (event.key()==Qt.Key.Key_F4 and event.modifiers() & Qt.KeyboardModifier.AltModifier):
            event.ignore()
            return
        super().keyPressEvent(event)

    def _update_progress(self):
        count, total = self.learning.progress_value()
        self.progress.setMaximum(total)
        self.progress.setValue(count)
        self.progress_lbl.setText(f'{count} / {total} soru tamamlandı   ·   {self.learning.correct} doğru   ·   {count-self.learning.correct} yanlış')

    def _celebrate(self):
        self._update_progress()
        self.question.setText(f'Çalışmanı tamamladın, {self.identity.name}!\n{self.learning.correct} doğru · {self.learning.attempts-self.learning.correct} yanlış')
        self.visual.hide()
        self.bars.hide()
        for button in self.choice_btns:
            button.hide()
        self.next_btn.hide()
        self.info.setText('Sonuçların kaydedildi. Görevlerine dönüyoruz…')
        self.info.show()
        QTimer.singleShot(1800, lambda: self._finish('tamamlandi'))

    def _ask_pin(self):
        password, ok = QInputDialog.getText(self, 'Ebeveyn doğrulaması', 'Veli hesabının şifresi:', QLineEdit.EchoMode.Password)
        if not ok:
            return
        with school.get_connection() as c:
            row = c.execute('''SELECT a.username FROM login_accounts a JOIN students s ON s.parent_id=a.user_id
                               WHERE s.id=? AND a.role='parent' ''', (self.identity.student_id,)).fetchone()
        try:
            if row is None:
                raise ValueError('Bağlı veli hesabı bulunamadı.')
            self.verified_parent = store.authenticate(row['username'], password)
            self._finish('veli_cikisi')
        except ValueError as error:
            QMessageBox.warning(self, 'Giriş yapılamadı', str(error))

    def closeEvent(self, event):
        if not self._allow_close:
            event.ignore()
            self._ask_pin()
        else:
            super().closeEvent(event)
