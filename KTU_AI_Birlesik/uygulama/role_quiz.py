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
    from curriculum_practice import offline_bank
    banks = {skill: store.student_topic_bank(identity,skill) if skill.startswith('cur_') else qb.reviewed_bank(skill, grade) for skill in skills}
    from learning_engine.learning_core import LocalQuestionProvider
    from learning_engine.school_content import TOPICS
    provider = LocalQuestionProvider()
    for skill in skills:
        if banks[skill] or skill in qb.HOMEWORK_SKILLS:
            continue
        if skill.startswith('cur_'):
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
        raise ValueError('Bu konu için hazır soru yok. Yapay zekâ üretimi için GEMINI_GENERATOR_KEY ayarlanmalı.')
    for bank in banks.values():random.shuffle(bank)
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
        self._practice_seed=[dict(q) for q in questions]
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
        self.on_wrong = None

    def add_generated_review(self, seed, questions):
        """Insert fresh variants without replacing a question currently on screen."""
        used=self._seen | {semantic_key(q) for q in self.questions[self.attempts:]}
        insert_at=self.attempts + int(not self._recorded)
        added=0
        for candidate in questions:
            key=semantic_key(candidate)
            if key in used:continue
            used.add(key);self._support_added+=1
            q=dict(candidate,skill=seed['skill'],concept=concept_of(seed),
                curriculum=seed.get('curriculum'),_support_question=True,
                source='ai-remediation',verified=False,id=f'gemini:{self._support_added}')
            self.questions.insert(insert_at+added,q);added+=1
        self.max_attempts=len(self.questions)
        return added

    def next_question(self):
        if self.continuous and self.attempts >= len(self.questions):
            try:batch=practice_questions(self.identity,24,self.practice_skills or self.skills)
            except ValueError:batch=[dict(q) for q in self._practice_seed]
            self.questions.extend(batch)
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
            if self.on_wrong:self.on_wrong(dict(self.current))
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
        from curriculum_practice import offline_similar
        try:
            candidates += [dict(q,skill=self.current['skill'],curriculum=self.current.get('curriculum'))
                for q in offline_similar(self.current,grade,1000)]
        except ValueError:pass
        # Locally reviewed banks may supplement practice. Document questions stay within their approved pack.
        # Keep only the same concept; curriculum matching is handled by offline_similar.
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
        self.voluntary = assignment_id is None
        self.identity = identity
        self.verified_parent = None
        if assignment_id is not None:
            from mastery_session import MasterySession
            session=MasterySession(identity,questions,assignment_id)
        else:session=AccountSession(identity,questions,assignment_id,enable_support=True,continuous=continuous,practice_skills=practice_skills)
        self._remediation_worker=None
        self._remediation_pending=[]
        super().__init__(session,30*60)
        session.on_wrong=self._request_gemini_review
        flags=Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint
        if not self.voluntary:flags|=Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setWindowTitle('Öğrenme Molası · Öğrenci')
        self.card.profil_guncelle(identity.name, 'kiz' if store.avatar_for(identity.student_id)=='student_girl.png' else 'erkek')
        self.setObjectName('ChildQuiz')
        from pastel_design import QUIZ_PASTEL
        self.setStyleSheet(self.styleSheet()+QUIZ_PASTEL)
        from keyboard_guard import guard
        self._role_guard = guard
        if not self.voluntary:
            self._role_guard.start(max_seconds=30*60)
        else:
            from PyQt6.QtWidgets import QPushButton
            for b in self.findChildren(QPushButton):
                if b.text()=='Ebeveyn girişi':
                    b.setText('Çalışmadan çık');b.clicked.disconnect();b.clicked.connect(self.leave_practice)
            self.card.on_parent_exit=self.leave_practice

    def _request_gemini_review(self, seed):
        import os
        if not os.getenv('GEMINI_GENERATOR_KEY','').strip():return
        if self._allow_close or self.learning.goal_reached():return
        # One request at a time; retain different weak concepts during generation.
        if self._remediation_worker is not None:
            if not any(concept_of(q)==concept_of(seed) and q['skill']==seed['skill'] for q in self._remediation_pending):
                self._remediation_pending.append(seed)
            return
        from curriculum_practice import PracticeWorker
        grade=store.require_student(self.identity,self.identity.student_id)['grade']
        payload=dict(seed,_avoid_texts=[q['text'] for q in self.learning.questions if q['skill']==seed['skill']][-40:])
        worker=PracticeWorker('auto-similar',payload,grade,3)
        self._remediation_worker=worker
        worker.ready.connect(lambda questions:self._receive_gemini_review(seed,questions))
        worker.failed.connect(self._gemini_review_failed)
        worker.finished.connect(self._gemini_review_finished)
        worker.start()

    def _receive_gemini_review(self, seed, questions):
        if self._allow_close or self.learning.goal_reached():return
        added=self.learning.add_generated_review(seed,questions)
        if added:
            self.info.setText(f'Gemini aynı kazanımdan {added} yeni pekiştirme sorusu hazırladı.');self.info.show()

    def _gemini_review_failed(self, message):
        if not self._allow_close:
            self.info.setText('Yeni benzer sorular üretilemedi. Hazır alıştırmalarla devam ediyoruz. '+str(message));self.info.show()

    def _gemini_review_finished(self):
        self._remediation_worker=None
        if self._remediation_pending and not self._allow_close and not self.learning.goal_reached():
            self._request_gemini_review(self._remediation_pending.pop(0))
        else:self._remediation_pending.clear()

    def _finish(self,status):
        if hasattr(self,'_role_guard'):
            self._role_guard.stop()
        super()._finish(status)

    def _load_question(self):
        super()._load_question()
        if not self._allow_close and self.learning.current and self.learning.current.get('source','').startswith('ai-'):
            self.info.setText('Yapay zekâ alıştırması · Yanıt veya açıklama şüpheliyse velinle/öğretmeninle kontrol edebilirsin.');self.info.show()
        if not self._allow_close and self.learning.current and self.learning.current.get('_support_question'):
            label='Gemini pekiştirmesi' if self.learning.current.get('source')=='ai-remediation' else 'Mini tekrar'
            self.info.setText(label+' · Aynı kazanımdan farklı bir alıştırma. '+('Yapay zekâ yanıtında şüphe varsa velinle/öğretmeninle kontrol et.' if label=='Gemini pekiştirmesi' else 'Bu soru ek destek olarak kaydedilir.'))
            self.info.show()

    def leave_practice(self):
        if self.voluntary and not self._allow_close:
            self._finish('serbest_cikis')

    def keyPressEvent(self,event):
        if getattr(self.learning,'mastery_mode',False) and self.learning.goal_reached() and (event.key()==Qt.Key.Key_Escape or (event.key()==Qt.Key.Key_F4 and event.modifiers() & Qt.KeyboardModifier.AltModifier)):
            self.exit_application();event.accept();return
        if self.voluntary and (event.key()==Qt.Key.Key_Escape or (event.key()==Qt.Key.Key_F4 and event.modifiers() & Qt.KeyboardModifier.AltModifier)):
            self.leave_practice();event.accept();return
        if event.key() == Qt.Key.Key_Escape or (event.key()==Qt.Key.Key_F4 and event.modifiers() & Qt.KeyboardModifier.AltModifier):
            event.ignore()
            return
        super().keyPressEvent(event)

    def _on_tick_label(self):
        if getattr(self.learning,'mastery_mode',False):self.timer_lbl.setText('Öğrenme hedefi: %80')
        else:self.timer_lbl.setText('Serbest keşif · İstediğin zaman çıkabilirsin')
    def _on_tick(self):
        self._on_tick_label()
    def exit_application(self):
        from PyQt6.QtWidgets import QApplication
        self._finish('ogrenildi_cikis');QApplication.instance().quit()

    def _update_progress(self):
        count, total = self.learning.progress_value()
        if getattr(self.learning,'mastery_mode',False):
            self.progress.setMaximum(100);self.progress.setValue(count)
            pending=sum(len(self.learning.evidence.get(k,[]))<n or self.learning.rates()[k]<.8 for k,n in self.learning.requirements.items())
            self.progress_lbl.setText(f'Öğrenme göstergesi: %{count} · Hedef: her soru türünde %80 · Pekiştirilecek {pending} soru türü · {self.learning.attempts} yanıt')
            return
        self.progress.setMaximum(0 if self.learning.continuous else total)
        self.progress.setValue(count)
        self.progress_lbl.setText(f'{count} / {"∞" if self.learning.continuous else total} {"alıştırma" if self.learning.assignment_id is None else "görev"} sorusu   ·   {self.learning.correct} doğru   ·   {self.learning.attempts-self.learning.correct} yanlış   ·   {self.learning.support_attempts} ek destek alıştırması')

    def _celebrate(self):
        if getattr(self.learning,'mastery_mode',False):
            self._update_progress()
            from audio_narrator import stop_narration
            stop_narration()
            if hasattr(self,'_role_guard'):self._role_guard.stop()
            self.question.setText(f'Harikasın, {self.identity.name}!\nÖğrenme hedefini tamamladın: %{self.learning.mastery_percent()}')
            self.visual.hide();self.bars.hide()
            for b in self.choice_btns:b.hide()
            self.info.setText('Yanlış yaptığın soru türlerini de pekiştirdin. Artık uygulamadan çıkabilirsin.');self.info.show()
            self.next_btn.show();self.next_btn.setEnabled(True);self.next_btn.setText('Uygulamadan çık')
            try:self.next_btn.clicked.disconnect()
            except TypeError:pass
            self.next_btn.clicked.connect(self.exit_application)
            return
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
        if getattr(self.learning,'mastery_mode',False) and self.learning.goal_reached():
            self.exit_application();return
        if self.voluntary:
            self.leave_practice();return
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
        if self.voluntary and not self._allow_close:
            self.leave_practice();event.accept();return
        if not self._allow_close:
            event.ignore()
            self._ask_pin()
        else:
            super().closeEvent(event)
