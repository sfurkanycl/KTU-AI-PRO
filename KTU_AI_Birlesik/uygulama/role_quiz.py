"""Use the existing illustrated quiz for authenticated student accounts."""
import random
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QInputDialog, QLineEdit, QMessageBox
from student_panel import BreakWindow
from data import education_database as school
import role_store as store


def practice_questions(identity, count=12, skills=None):
    if isinstance(count,bool) or not isinstance(count,int) or not 1 <= count <= 1000:
        raise ValueError('Soru sayısı 1 ile 1000 arasında olmalı.')
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


def semantic_key(question):
    import re,json
    visual=question.get('visual') or {}
    if visual.get('scene_id'): return 'scene:'+visual['scene_id']
    if visual: return 'visual:'+json.dumps(visual,sort_keys=True)
    return re.sub(r'\W+',' ',question['text'].casefold()).strip()


def concept_of(question):
    from learning_engine.school_content import SCENES
    return question.get('concept') or SCENES.get((question.get('visual') or {}).get('scene_id'),{}).get('concept') or question['skill']


class AccountSession:
    def __init__(self, identity, questions, assignment_id=None,enable_support=False,continuous=False,practice_skills=None):
        if not questions:
            raise ValueError('Bu görevde çözülmemiş soru kalmadı.')
        self.identity = identity
        self.continuous=bool(continuous and assignment_id is None)
        self.practice_skills=practice_skills
        self.questions = list(questions)
        self.enable_support=enable_support
        self.base_answered=0;self.support_attempts=0;self._support_added=0
        self._seen=set();self._wrong_streak={}
        self.assignment_id = assignment_id
        self.skills = list(dict.fromkeys(q['skill'] for q in questions))
        self.current = None
        self.attempts = 0
        self.max_attempts = len(questions)
        self.goal = len(questions)
        self.correct = 0
        self._recorded = False

    def next_question(self):
        if self.continuous and self.attempts >= len(self.questions):
            self.questions.extend(practice_questions(self.identity,24,self.practice_skills or self.skills))
            self.max_attempts=len(self.questions)
        if self.goal_reached():
            return None
        self.current = self.questions[self.attempts]
        self._seen.add(semantic_key(self.current))
        self._recorded = False
        return self.current

    def answer(self, choice, seconds, hint_used=False):
        if self._recorded:
            raise ValueError('Bu soru zaten cevaplandı.')
        support=bool(self.current.get('_support_question'))
        correct = store.save_answer(self.identity, self.current, choice, hint_used,
            None if support else self.assignment_id,seconds=seconds)
        self._recorded = True
        self.attempts += 1
        self.correct += int(correct)
        if support: self.support_attempts+=1
        else: self.base_answered+=1
        concept=concept_of(self.current)
        self._wrong_streak[concept]=0 if correct else self._wrong_streak.get(concept,0)+1
        stage=self._wrong_streak[concept]
        text=self.current.get('explanation','')
        title='Doğru!' if correct else 'Birlikte öğrenelim'
        if not correct:
            if stage==1 and self.current.get('hint'):
                title='Bir ipucuyla düşünelim';text=self.current['hint']
            elif stage>=3 and self.current.get('example'):
                title='Çözümlü bir örneğe bakalım';text=self.current['example']
            else:
                text+='\nDoğru cevap: '+self.current['choices'][self.current['answer']]
            if self.enable_support: self._prefer_same_concept(concept)
        return dict(correct=correct,title=title,text=text,visual=None,
                    kind='ok' if correct else 'hint' if stage==1 else 'worked' if stage>=3 else 'explanation',
                    skill_done=False,fast_warning=not correct and seconds<4)

    def _prefer_same_concept(self,concept):
        for index in range(self.attempts,len(self.questions)):
            q=self.questions[index]
            if concept_of(q)==concept and semantic_key(q) not in self._seen:
                self.questions.insert(self.attempts,self.questions.pop(index));return
        if self._support_added>=2: return
        import questions as qb
        grade=store.require_student(self.identity,self.identity.student_id)['grade']
        candidates=qb.reviewed_bank(self.current['skill'],grade)
        # Locally reviewed banks may supplement practice. Document questions stay within their approved pack.
        if self.current.get('source')=='teacher-reviewed': return
        from learning_engine.school_content import SCENES
        for scene_id,scene in SCENES.items():
            if scene['skill']==self.current['skill'] and scene['concept']==concept:
                candidates.append(dict(skill=self.current['skill'],text=scene['question'],choices=scene['options'],answer=0,
                    explanation=scene['explanation'],hint='Görseli incele ve soruyu dikkatle oku.',
                    visual={'scene_id':scene_id},concept=concept,verified=True,source='local'))
        q=next((dict(q) for q in candidates if concept_of(q)==concept and semantic_key(q) not in self._seen
            and all(semantic_key(q)!=semantic_key(p) for p in self.questions[self.attempts:])),None)
        if q is None and self.current['skill'] in ('m3_toplama','m3_carpma','m4_kesir','m4_bolme'):
            from learning_engine.learning_core import LocalQuestionProvider
            provider=LocalQuestionProvider()
            for _ in range(20):
                skill=self.current['skill']
                if skill in ('m3_carpma','m4_bolme'): candidate=qb._original_make_question(skill,set())
                else:
                    raw=provider.generate(grade,'matematik','addition' if skill=='m3_toplama' else 'fraction_compare',set())
                    candidate=dict(skill=skill,text=raw['prompt'],choices=raw['options'],answer=raw['correct_index'],
                        explanation=raw.get('explanation',''),hint=raw.get('hint',''),visual=raw.get('visual'))
                candidate['concept']=concept
                if semantic_key(candidate) not in self._seen and all(semantic_key(candidate)!=semantic_key(p) for p in self.questions[self.attempts:]):
                    q=candidate;break
        if q is None:return
        self._support_added+=1
        q.update(_support_question=True,id=f'support:{self._support_added}',curriculum=self.current.get('curriculum'))
        self.questions.insert(self.attempts,q)
        self.max_attempts=len(self.questions)

    def goal_reached(self):
        return not self.continuous and self.attempts >= len(self.questions)

    def limit_reached(self):
        return False

    def current_skill(self):
        return self.current['skill'] if self.current else self.skills[0]

    def current_clean(self):
        return self.correct

    def done_count(self):
        return self.correct

    def progress_value(self):
        return self.base_answered, self.goal


class StudentQuiz(BreakWindow):
    def __init__(self, identity, questions, assignment_id=None,continuous=False,practice_skills=None):
        self.identity = identity
        self.verified_parent = None
        super().__init__(AccountSession(identity, questions, assignment_id,enable_support=True,continuous=continuous,practice_skills=practice_skills), 30*60)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowTitle('Öğrenme Molası · Öğrenci')
        self.card.profil_guncelle(identity.name, 'kiz' if store.avatar_for(identity.student_id)=='student_girl.png' else 'erkek')
        self.setObjectName('ChildQuiz')
        from pastel_design import QUIZ_PASTEL
        self.setStyleSheet(self.styleSheet()+QUIZ_PASTEL)
        from keyboard_guard import guard
        self._role_guard = guard
        self._role_guard.start(max_seconds=30*60)

    def _finish(self,status):
        if hasattr(self,'_role_guard'):
            self._role_guard.stop()
        super()._finish(status)

    def _load_question(self):
        super()._load_question()
        if not self._allow_close and self.learning.current and self.learning.current.get('_support_question'):
            self.info.setText('Mini tekrar · Aynı kazanımdan farklı bir alıştırmayla pekiştirelim. Bu soru ek destek olarak kaydedilir.')
            self.info.show()

    def keyPressEvent(self,event):
        if event.key() == Qt.Key.Key_Escape or (event.key()==Qt.Key.Key_F4 and event.modifiers() & Qt.KeyboardModifier.AltModifier):
            event.ignore()
            return
        super().keyPressEvent(event)

    def _update_progress(self):
        count, total = self.learning.progress_value()
        self.progress.setMaximum(0 if self.learning.continuous else total)
        self.progress.setValue(count)
        self.progress_lbl.setText(f'{count} / {"∞" if self.learning.continuous else total} {"alıştırma" if self.learning.assignment_id is None else "görev"} sorusu   ·   {self.learning.correct} doğru   ·   {self.learning.attempts-self.learning.correct} yanlış   ·   {self.learning.support_attempts} ek destek alıştırması')

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
