"""Applied MEB themes, original English exercises and optional Gemini practice."""
import hashlib,json,random
from functools import lru_cache
from PyQt6.QtCore import QThread,pyqtSignal

_WORKERS=set()

def shutdown_workers():
    for w in list(_WORKERS):w.wait(65000)

@lru_cache(maxsize=4)
def topics(grade):
    from curriculum import catalogue
    result=[]
    for c in catalogue(grade):
        for index,u in enumerate(c['units']):
            key=hashlib.sha256((c['subject']+'|'+u['title']).encode()).hexdigest()[:12]
            result.append(dict(skill=f'cur_{grade}_{key}',grade=grade,subject=c['subject'],name=u['title'],
                title=u['title'],url=u['url'],context=u.get('context',''),unit_index=index))
    return result

def skill_details(skill):
    for grade in range(1,5):
        for t in topics(grade):
            if t['skill']==skill:return t
    raise ValueError('Bu konu güncel sınıf programında bulunamadı.')

def skills_for_grade(grade):
    return [(t['skill'],dict(grade=grade,name=t['title'],subject=t['subject'])) for t in topics(grade)]

# Authored exercises, not copied MEB test questions.
WORDS={
 'school':[('school','okul'),('teacher','öğretmen'),('student','öğrenci'),('friend','arkadaş')],
 'classroom':[('book','kitap'),('pencil','kurşun kalem'),('desk','sıra'),('ruler','cetvel')],
 'personal':[('happy','mutlu'),('sad','üzgün'),('tall','uzun boylu'),('young','genç')],
 'family':[('mother','anne'),('father','baba'),('sister','kız kardeş'),('brother','erkek kardeş')],
 'home':[('kitchen','mutfak'),('bedroom','yatak odası'),('door','kapı'),('window','pencere')],
 'city':[('park','park'),('hospital','hastane'),('library','kütüphane'),('street','sokak')],
 'rules':[('Open your book.','Kitabını aç.'),('Close the door.','Kapıyı kapat.'),('Be quiet, please.','Lütfen sessiz ol.'),('Sit down.','Otur.')],
 'nationality':[('Turkish','Türk'),('British','Britanyalı'),('Japanese','Japon'),('German','Alman')],
 'abilities':[('I can swim.','Yüzebilirim.'),('I can jump.','Zıplayabilirim.'),('I can sing.','Şarkı söyleyebilirim.'),('I can run.','Koşabilirim.')],
 'hobbies':[('reading','okuma'),('swimming','yüzme'),('dancing','dans etme'),('drawing','resim çizme')],
 'day':[('morning','sabah'),('afternoon','öğleden sonra'),('evening','akşam'),('night','gece')],
 'science':[('water','su'),('ice','buz'),('mix','karıştırmak'),('melt','erimek')],
 'jobs':[('doctor','doktor'),('teacher','öğretmen'),('farmer','çiftçi'),('pilot','pilot')],
 'clothes':[('shirt','gömlek'),('trousers','pantolon'),('shoes','ayakkabı'),('hat','şapka')],
 'friends':[('curly hair','kıvırcık saç'),('straight hair','düz saç'),('blue eyes','mavi gözler'),('brown eyes','kahverengi gözler')],
 'food':[('apple','elma'),('bread','ekmek'),('milk','süt'),('cheese','peynir')],
}

def offline_bank(skill):
    t=skill_details(skill)
    if t['subject']!='İngilizce':
        from authored_topics import bank as authored_bank
        bank=authored_bank(t)
        from curriculum import legacy_ready_skills
        ready=legacy_ready_skills(t['subject'],t['title'],t['grade'])
        import questions as qb
        for old_skill in ready:
            for q in qb.reviewed_bank(old_skill,t['grade']):
                q=dict(q,skill=skill,curriculum=dict(grade=t['grade'],subject=t['subject'],title=t['title'],source=t['url']))
                bank.append(q)
        return bank
    keys=['school','classroom','personal','family','home','city'] if t['grade']<4 else ['rules','nationality','abilities','hobbies','day','science','jobs','clothes','friends','food']
    pairs=WORDS[keys[t['unit_index']]];result=[]
    for word,meaning in pairs:
        choices=[v for _,v in pairs]
        result.append(dict(skill=skill,text=f'“{word}” ifadesinin Türkçe karşılığı hangisidir?',choices=choices,
            answer=choices.index(meaning),hint='Bu sözcüğü veya ifadeyi hangi durumda kullandığını düşün.',
            explanation=f'“{word}” Türkçede “{meaning}” anlamına gelir.',visual=None,
            concept=keys[t['unit_index']],verified=True,source='authored-english',
            curriculum=dict(grade=t['grade'],subject=t['subject'],title=t['title'],source=t['url'])))
    # Reverse vocabulary recognition adds a distinct exercise for the same vocabulary.
    for word,meaning in pairs:
        choices=[w for w,_ in pairs]
        result.append(dict(skill=skill,text=f'“{meaning}” ifadesinin İngilizce karşılığı hangisidir?',choices=choices,
            answer=choices.index(word),hint='İngilizce sözcükleri anlamlarıyla eşleştir.',
            explanation=f'“{meaning}” ifadesinin İngilizcesi “{word}” olur.',visual=None,
            concept=keys[t['unit_index']],verified=True,source='authored-english',
            curriculum=dict(grade=t['grade'],subject=t['subject'],title=t['title'],source=t['url'])))
    return result


def generate_topic(skill,count=12):
    t=skill_details(skill)
    from teaching_materials import generate_questions
    context=t['context'] or ('Ders: '+t['subject']+'; konu: '+t['title']+'. Bu konu için sınıf düzeyine uygun temel öğrenme hedefleri kapsamında çalışılacaktır. ')*2
    result=generate_questions(context,t['grade'],t['subject'],t['title'],max(2,min(30,count)))
    for index,q in enumerate(result):
        q.update(skill=skill,id=index,source='ai-practice',verified=False,
            curriculum=dict(grade=t['grade'],subject=t['subject'],title=t['title'],source=t['url']))
    return result


def offline_similar(question,grade,count=6):
    """Distinct reviewed practice from the same curriculum unit; prefer same concept."""
    import questions as qb
    from copy import deepcopy
    skill=question['skill']
    candidates=qb.reviewed_bank(skill,grade)
    # Teacher-authored questions may carry a legacy skill as a storage fallback.
    # Use their actual curriculum unit instead of that unrelated fallback skill.
    metadata=question.get('curriculum') or {}
    if metadata.get('subject') and metadata.get('title'):
        match=next((t for t in topics(grade) if t['subject']==metadata['subject'] and t['title']==metadata['title']),None)
        if match:candidates=offline_bank(match['skill'])
        elif not skill.startswith('cur_'):candidates=[]
    normalize=lambda text:' '.join(str(text).casefold().split())
    seen={normalize(question['text'])};result=[]
    candidates=sorted(candidates,key=lambda q:qb.concept_of(q)!=qb.concept_of(question))
    for q in candidates:
        key=normalize(q['text'])
        if key in seen:continue
        seen.add(key);result.append(dict(deepcopy(q),id=len(result),source='offline-remediation'))
        if len(result)>=count:break
    if not result:raise ValueError('Bu soru için farklı bir hazır alıştırma bulunamadı. Aynı soruyu tekrar çözebilir veya velinden Soru atölyesine bu konuda soru eklemesini isteyebilirsin.')
    return result


def generate_similar(question,grade,count=6):
    from teaching_materials import generate_questions
    from curriculum import subject_for_skill
    subject=(question.get('curriculum') or {}).get('subject') or subject_for_skill(question['skill'],grade)
    title=(question.get('curriculum') or {}).get('title') or question.get('concept') or subject
    context=json.dumps(dict(question=question['text'],choices=question['choices'],correct=question['choices'][question['answer']],
        explanation=question.get('explanation',''),concept=question.get('concept',title),
        already_used_questions=question.get('_avoid_texts',[])),ensure_ascii=False)
    result=generate_questions(context,grade,subject,str(title)+' — aynı kazanım, farklı bağlam ve değerler; kaynak soruyu tekrar etme',count)
    if any(q['text'].strip().casefold()==question['text'].strip().casefold() for q in result):
        raise ValueError('Üretimde kaynak soru tekrarlandı. Yeniden deneyin.')
    for i,q in enumerate(result):q.update(skill=question['skill'],id=i,source='ai-remediation',verified=False,curriculum=question.get('curriculum'))
    return result


class PracticeWorker(QThread):
    ready=pyqtSignal(list);failed=pyqtSignal(str)
    def __init__(self,mode,payload,grade=3,count=12):
        super().__init__();self.mode=mode;self.payload=payload;self.grade=grade;self.count=count
        _WORKERS.add(self);self.finished.connect(lambda:_WORKERS.discard(self))
    def run(self):
        try:
            if self.mode=='auto-similar':
                result=generate_similar(self.payload,self.grade,self.count)
            elif self.mode=='similar':
                import os
                if os.getenv('GEMINI_GENERATOR_KEY','').strip():
                    try:result=generate_similar(self.payload,self.grade,self.count)
                    except Exception:result=offline_similar(self.payload,self.grade,self.count)
                else:result=offline_similar(self.payload,self.grade,self.count)
            else:result=generate_topic(self.payload,self.count)
            self.ready.emit(result)
        except Exception as e:self.failed.emit(str(e))
