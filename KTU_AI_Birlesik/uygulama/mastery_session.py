"""Recent, unaided evidence per question type controls assigned-session completion."""
from collections import Counter
import json
from copy import deepcopy
from role_quiz import AccountSession,concept_of,semantic_key
from data import education_database as school

class MasterySession(AccountSession):
    def __init__(self,identity,questions,assignment_id):
        super().__init__(identity,questions,assignment_id,enable_support=False)
        self.mastery_mode=True
        with school.get_connection() as c:
            rows=c.execute('SELECT payload FROM question_details WHERE question_id IN (SELECT id FROM questions WHERE assignment_id=?)',(assignment_id,)).fetchall()
            state=c.execute('SELECT payload FROM assignment_learning_state WHERE assignment_id=? AND student_id=?',(assignment_id,identity.student_id)).fetchone()
        self.pool=[json.loads(r[0]) for r in rows] or deepcopy(questions)
        self.requirements={key:min(5,n) for key,n in Counter(self.key(q) for q in self.pool).items()}
        payload=json.loads(state[0]) if state else {}
        self.evidence=payload.get('evidence',{})
        self.evidence_count=payload.get('count',0)
        self._history=payload.get('history',[])
        self._seen.update(self._history)
        self._persist()
    def key(self,q):
        meta=q.get('curriculum') or {}
        return '|'.join([q['skill'],meta.get('subject',''),meta.get('title',''),str(concept_of(q))])
    def rates(self):
        return {k:sum(self.evidence.get(k,[]))/max(1,len(self.evidence.get(k,[]))) for k in self.requirements}
    def mastery_percent(self):
        return int(100*sum(self.rates().values())/max(1,len(self.requirements)))
    def goal_reached(self):
        if not hasattr(self,'requirements'):return False
        return self.evidence_count>=min(5,len(self.pool)) and all(len(self.evidence.get(k,[]))>=n and self.rates()[k]>=.8 for k,n in self.requirements.items())
    def _persist(self):
        with school.get_connection() as c:
            c.execute('INSERT INTO assignment_learning_state VALUES (?,?,?,?,?) ON CONFLICT(assignment_id,student_id) DO UPDATE SET payload=excluded.payload,rate=excluded.rate,mastered=excluded.mastered',
                (self.assignment_id,self.identity.student_id,json.dumps(dict(evidence=self.evidence,count=self.evidence_count,history=self._history[-1000:])),self.mastery_percent(),int(self.goal_reached())))
            if self.goal_reached():c.execute("UPDATE task_schedules SET status='completed' WHERE assignment_id=? AND student_id=? AND status='started'",(self.assignment_id,self.identity.student_id))
    def answer(self,choice,seconds,hint_used=False):
        feedback=super().answer(choice,seconds,hint_used)
        key=self.key(self.current)
        self.evidence[key]=(self.evidence.get(key,[])+[int(feedback['correct'] and not hint_used)])[-5:]
        self.evidence_count+=1
        if not self.goal_reached():
            weak=min(self.requirements,key=lambda k:(self.rates()[k],len(self.evidence.get(k,[]))/self.requirements[k]))
            index=next((i for i in range(self.attempts,len(self.questions)) if self.key(self.questions[i])==weak and semantic_key(self.questions[i]) not in self._seen),None)
            if index is not None:self.questions.insert(self.attempts,self.questions.pop(index))
            elif self.attempts>=len(self.questions) or not feedback['correct']:
                self._add_review(weak)
        self._persist()
        return feedback
    def _add_review(self,key):
        candidates=[q for q in self.pool if self.key(q)==key]
        if not candidates:return
        seed=candidates[0]
        try:
            from curriculum_practice import offline_similar
            import role_store as store
            grade=store.require_student(self.identity,self.identity.student_id)['grade']
            for candidate in offline_similar(seed,grade,1000):
                # Imported packs can use a storage skill differing from their curriculum bank.
                candidate=dict(candidate,skill=seed['skill'],curriculum=seed.get('curriculum'))
                if self.key(candidate)==key:candidates.append(candidate)
        except ValueError:pass
        unique={semantic_key(q):q for q in candidates}
        candidates=list(unique.values())
        # Use every distinct variant before recycling, then space exhausted-bank reviews.
        recent={value:index for index,value in enumerate(self._history)}
        candidates.sort(key=lambda q:(semantic_key(q) in self._seen,
            (self.current is not None and semantic_key(q)==semantic_key(self.current)),recent.get(semantic_key(q),-1)))
        q=deepcopy(candidates[0]);self._support_added+=1
        q.update(_support_question=True,id=f'mastery:{self._support_added}')
        self.questions.insert(self.attempts,q);self.max_attempts=len(self.questions)
    def next_question(self):
        if not self.goal_reached() and (self.attempts>=len(self.questions) or semantic_key(self.questions[self.attempts]) in self._seen):
            weak=min(self.requirements,key=lambda k:self.rates()[k]);self._add_review(weak)
        question=super().next_question()
        if question is not None:
            self._history.append(semantic_key(question))
        return question
    def progress_value(self):return self.mastery_percent(),80
