"""Idempotent, explicitly labelled demonstration records. Never overwrite real accounts."""
from datetime import datetime,timedelta,timezone
import random
import role_store as store
from data import education_database as school

PASSWORD='Demo123!'


def account(username,name,role):
    with school.get_connection() as c:
        exists=c.execute('SELECT id FROM login_accounts WHERE username=?',(username,)).fetchone()
    return store.authenticate(username,PASSWORD) if exists else store.register(username,PASSWORD,name,role)


def seed():
    store.init();store.init_extras()
    with school.get_connection() as c:
        if c.execute("SELECT 1 FROM demo_seed WHERE version='colour-v1'").fetchone():
            return 'Örnek veriler zaten mevcut; tekrar eklenmedi.'
    teachers=[account('demo.ogretmen','Deniz Öğretmen · Örnek','teacher'),account('demo.ogretmen2','Ece Öğretmen · Örnek','teacher')]
    parents=[account('demo.veli','Yücel · Örnek Veli','parent'),account('demo.veli2','Selin · Örnek Veli','parent'),account('demo.veli3','Mert · Örnek Veli','parent')]
    class_ids={}
    for grade in range(1,5):
        teacher=teachers[(grade+1)%2]
        name=f'{grade}-A · Örnek sınıf'
        existing=next((r for r in store.classes(teacher) if r['name']==name),None)
        cid=existing['id'] if existing else store.add_class(teacher,name,grade)
        class_ids[grade]=(teacher,cid,next(r['code'] for r in store.classes(teacher) if r['id']==cid))
    children=[]
    for i,(name,grade) in enumerate([('Furkan',3),('Elif',3),('Zeynep',1),('Ali',2),('Defne',4),('Aras',4)]):
        parent=parents[i//2]
        alias=name+' · Örnek'
        existing=next((r for r in store.students(parent) if r['alias']==alias),None)
        sid=existing['id'] if existing else store.add_child(parent,alias,grade)
        store.set_avatar(parent,sid,'student_girl.png' if name in ('Elif','Zeynep','Defne') else 'student_boy.png')
        store.join_class(parent,sid,class_ids[grade][2])
        children.append((parent,sid,grade))
    rng=random.Random(181)
    now=datetime.now(timezone.utc)
    with school.get_connection() as c:
        for i,(_,sid,grade) in enumerate(children):
            # All demo attempts have an explicit demo label and bounded relative timestamps.
            if c.execute("SELECT 1 FROM practice_attempts WHERE student_id=? AND question_text LIKE '[Örnek veri]%'",(sid,)).fetchone(): continue
            for day in range(7):
                for j in range(6+i+day):
                    subject,skill=rng.choice([('Matematik','m3_toplama'),('Türkçe','homework_turkce'),('Hayat Bilgisi' if grade<4 else 'Sosyal Bilgiler','traffic')])
                    when=(now-timedelta(days=day,minutes=j+30)).strftime('%Y-%m-%d %H:%M:%S')
                    c.execute('''INSERT INTO practice_attempts(student_id,skill,topic,question_text,is_correct,hint_used,answered_at)
                        VALUES (?,?,?,?,?,?,?)''',(sid,skill,subject+' · Örnek ilerleme','[Örnek veri] Temsili alıştırma',int(rng.random()<.65+i*.035),int(rng.random()<.12),when))
    for grade,(teacher,cid,_) in class_ids.items():
        if not store.tasks(teacher) or not any(t['class_id']==cid for t in store.tasks(teacher)):
            store.create_task(teacher,'Güvenli yaşam keşfi · Örnek','traffic',3,class_id=cid,due_date=(now+timedelta(days=7)).date().isoformat())
    for parent,sid,grade in children:
        if not store.tasks(parent,sid):
            store.create_task(parent,'Günün keşfi · Örnek','traffic',3,student_id=sid)
    for teacher,cid,_ in class_ids.values(): store.share_class(teacher,cid)
    with school.get_connection() as c: c.execute("INSERT INTO demo_seed VALUES ('colour-v1')")
    return '2 öğretmen, 3 veli, 6 öğrenci, 4 sınıf ve 7 günlük örnek ilerlemeler hazır.'


if __name__=='__main__': print(seed())
