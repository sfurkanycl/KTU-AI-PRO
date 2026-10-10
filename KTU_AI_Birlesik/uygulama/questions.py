"""Preserved Windows implementation; see legacy_runtime/README.md."""
from legacy_loader import load_into
load_into(globals(), 'questions')

# Preserve the packaged generators and extend the catalogue to primary grades.
from pathlib import Path
import json
from learning_engine.turkish_text import restore_text

_original_skills_for_grade = skills_for_grade
_original_make_question = make_question
_original_make_pack = make_pack
HOMEWORK_SKILLS = {'homework_math': 'matematik', 'homework_turkce': 'türkçe',
                   'homework_general': 'genel', 'homework_science': 'fen'}
for _key, _label in HOMEWORK_SKILLS.items():
    SKILLS[_key] = {'grade': 1, 'name': f'Arkadaş soru havuzu — {_label}'}


def homework_bank(skill):
    records = json.loads((Path(__file__).parent / 'sorular.json').read_text(encoding='utf-8'))
    result = []
    for index, row in enumerate(records):
        if row.get('kategori') != HOMEWORK_SKILLS.get(skill):
            continue
        # Both "bilgisayar" and "pazartesi" are written together: preserve for review.
        ambiguous = 'hangisi birleşik yazılır' in row['soru'].lower()
        q = dict(skill=skill, text=row['soru'], choices=list(row['secenekler']),
                 answer=row['dogru'], hint='Soruyu yeniden oku ve seçenekleri tek tek karşılaştır.',
                 explanation='Doğru cevap: ' + row['secenekler'][row['dogru']],
                 visual=None, source=f'homework:{index}', verified=not ambiguous)
        if ambiguous:
            q['explanation'] = 'İnceleme gerekli: bilgisayar ve pazartesi seçeneklerinin ikisi de birleşik yazılır.'
        q['qkey'] = make_key(skill, q['text'], q['choices'])
        result.append(q)
    return result


def skills_for_grade(grade):
    result = dict(_original_skills_for_grade(grade))
    if 1 <= int(grade) <= 4:
        for key in ('living_needs', 'matter_states', 'traffic', 'directions'):
            result[key] = SKILLS[key]
        result.setdefault('m3_toplama', SKILLS['m3_toplama'])
        for key in HOMEWORK_SKILLS:
            result[key] = SKILLS[key]
    from curriculum_practice import skills_for_grade as curriculum_skills
    result.update(dict(curriculum_skills(grade)))
    return list(result.items())


def concept_of(q):
    scene = (q.get('visual') or {}).get('scene_id')
    return q.get('concept') or school_content.SCENES.get(scene, {}).get('concept') or q['skill']


def reviewed_bank(skill, grade):
    """Adapt existing reviewed packs without modifying source IDs or indices."""
    if skill.startswith('cur_'):
        from curriculum_practice import offline_bank
        return offline_bank(skill)
    if skill in HOMEWORK_SKILLS:
        return [q for q in homework_bank(skill) if q['verified']]
    keymap = {'m3_toplama': 'addition', 'm4_kesir': 'fraction_compare'}
    bank = json.loads((Path(__file__).parent / 'learning_engine/question_bank.json').read_text(encoding='utf-8'))
    result = []
    for key, pack in bank.get('packs', {}).items():
        parts = key.split(':')
        if len(parts) != 3 or parts[0] != str(grade) or parts[2] != keymap.get(skill, skill):
            continue
        for original in pack:
            choices = original.get('options', [])
            answer = original.get('correct_index')
            if not isinstance(answer, int) or not 0 <= answer < len(choices):
                continue
            q = dict(skill=skill, text=restore_text(original['prompt']),
                     choices=[restore_text(x) for x in choices], answer=answer,
                     hint=restore_text(original.get('hint', '')),
                     explanation=restore_text(original.get('explanation', '')),
                     visual=original.get('visual'), source='reviewed-gemini', verified=True,
                     concept=original.get('concept'), example=original.get('example', ''))
            q['qkey'] = make_key(skill, q['text'], q['choices'])
            if skill == 'm4_kesir' and not q['visual']:
                signature = original.get('signature', '').split(':')
                if len(signature) == 3 and signature[0] == 'fraction':
                    q['visual'] = {'type': 'fractions', 'a': [1, int(signature[1])], 'b': [1, int(signature[2])]}
            result.append(q)
    return result


def make_question(skill_id, avoid=()):
    if skill_id.startswith('cur_'):
        bank=reviewed_bank(skill_id,int(skill_id.split('_')[1]))
        if not bank:raise ValueError('Bu konuda hazır banka yok. Soru atölyesinde soru hazırlayın.')
        return dict(random.choice(bank))
    if skill_id in HOMEWORK_SKILLS:
        candidates = [q for q in homework_bank(skill_id) if q['verified']]
        unused = [q for q in candidates if q['qkey'] not in avoid]
        return dict(random.choice(unused or candidates))
    from data import database as db
    grade = db.get_student().get('grade', 3)
    if skill_id == 'm3_toplama' and grade in (1, 2):
        from learning_engine.learning_core import LocalQuestionProvider
        provider = LocalQuestionProvider()
        for _ in range(50):
            raw = provider.generate(grade, 'matematik', 'addition', set())
            q = dict(skill=skill_id, text=raw['prompt'], choices=raw['options'],
                     answer=raw['correct_index'], hint=raw['hint'], explanation=raw['explanation'],
                     visual=None, source='primary-local', verified=True)
            q['qkey'] = make_key(skill_id, q['text'], q['choices'])
            if q['qkey'] not in avoid:
                return q
    return _original_make_question(skill_id, avoid)


def make_pack(skill_id, count):
    if skill_id.startswith('cur_'):
        return reviewed_bank(skill_id,int(skill_id.split('_')[1]))[:count]
    if skill_id in HOMEWORK_SKILLS:
        return homework_bank(skill_id)[:count]
    return _original_make_pack(skill_id, count)


# Keep the preserved legacy engine registry limited to its supported generators.
_original_skill_name=skill_name
def skill_name(skill):
    if skill.startswith('cur_'):
        from curriculum_practice import skill_details
        return skill_details(skill)['title']
    return _original_skill_name(skill)
