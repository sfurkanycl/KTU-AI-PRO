"""Preserved Windows implementation; see legacy_runtime/README.md."""
from legacy_loader import load_into
load_into(globals(), 'learning')

# Explicit bindings also let static analysis see the legacy module's dependencies.
import random
import questions as qb
from data import database as db

_PackagedLearningSession = globals()['LearningSession']


class LearningSession(_PackagedLearningSession):
    """Keep completion/report rules; prefer the missed concept on the next item."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._preferred_concept = None
        self._preferred_concepts = {}
        self._skill_cursor = 0
        self._selected_skill = None
        self._bank = {}
        grade = (db.get_student() or {}).get('grade', 4)
        for skill in self.skills:
            self._bank[skill] = qb.reviewed_bank(skill, grade)

    def current_skill(self):
        if self._selected_skill and not self.state[self._selected_skill]['done']:
            return self._selected_skill
        return next((s for s in self.skills if not self.state[s]['done']), None)

    def next_question(self):
        skill = None
        for offset in range(len(self.skills)):
            index = (self._skill_cursor + offset) % len(self.skills)
            candidate = self.skills[index]
            if not self.state[candidate]['done']:
                skill = candidate
                self._skill_cursor = (index + 1) % len(self.skills)
                break
        self._selected_skill = skill
        self._preferred_concept = self._preferred_concepts.get(skill)
        if not skill:
            return None
        pool = [q for q in db.approved_questions(skill) + self._bank.get(skill, [])
                if q['qkey'] not in self.asked and q.get('verified', False)]
        same = [q for q in pool if qb.concept_of(q) == self._preferred_concept]
        if same:
            q = random.choice(same)
        elif self._preferred_concept and skill in ('living_needs', 'matter_states', 'traffic', 'directions'):
            raw = qb.school_content.local_question(skill, set(), self._preferred_concept)
            q = dict(skill=skill, text=raw['prompt'], choices=raw['options'],
                     answer=raw['correct_index'], hint=raw['hint'], explanation=raw['explanation'],
                     visual=raw.get('visual'), source='concept-practice', verified=True)
            q['qkey'] = qb.make_key(skill, q['text'], q['choices'])
            if q['qkey'] in self.asked:
                q = random.choice(pool) if pool else qb.make_question(skill, self.asked)
        else:
            q = random.choice(pool) if pool else qb.make_question(skill, self.asked)
        self.current = q
        self.asked.add(q['qkey'])
        return q

    def answer(self, choice, seconds, hint_used=False):
        question = self.current
        result = super().answer(choice, seconds, hint_used)
        self._preferred_concept = qb.concept_of(question) if (not result['correct'] or hint_used) else None
        self._preferred_concepts[question['skill']] = self._preferred_concept
        return result
