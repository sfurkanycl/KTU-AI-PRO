"""Account-scoped school services. Legacy databases remain intact."""
from dataclasses import dataclass
import hashlib
import hmac
import json
import secrets
from datetime import date, timedelta
from data import education_database as school


@dataclass(frozen=True)
class Identity:
    account_id: int
    role: str
    name: str
    user_id: int | None
    student_id: int | None


def init():
    school.init_db()
    init_extras()
    with school.get_connection() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS login_accounts (
            id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL,
            salt TEXT NOT NULL, password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('parent','teacher','student')),
            user_id INTEGER UNIQUE REFERENCES users(id),
            student_id INTEGER UNIQUE REFERENCES students(id),
            failed_attempts INTEGER NOT NULL DEFAULT 0, locked_until TEXT,
            CHECK((role='student' AND student_id IS NOT NULL AND user_id IS NULL)
               OR (role IN ('parent','teacher') AND user_id IS NOT NULL AND student_id IS NULL)));
        CREATE TABLE IF NOT EXISTS class_invites (
            class_id INTEGER PRIMARY KEY REFERENCES classes(id), code TEXT UNIQUE NOT NULL);
        CREATE TABLE IF NOT EXISTS assignment_targets (
            assignment_id INTEGER REFERENCES assignments(id), student_id INTEGER REFERENCES students(id),
            PRIMARY KEY(assignment_id,student_id));
        CREATE TABLE IF NOT EXISTS question_details (
            question_id INTEGER PRIMARY KEY REFERENCES questions(id), payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS practice_attempts (
            id INTEGER PRIMARY KEY, student_id INTEGER NOT NULL REFERENCES students(id),
            skill TEXT NOT NULL, topic TEXT NOT NULL, question_text TEXT NOT NULL,
            is_correct INTEGER NOT NULL, hint_used INTEGER NOT NULL,
            answered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        CREATE TABLE IF NOT EXISTS legacy_imports (
            source_key TEXT PRIMARY KEY, student_id INTEGER NOT NULL REFERENCES students(id));
        CREATE TABLE IF NOT EXISTS student_practice_preferences (
            student_id INTEGER PRIMARY KEY REFERENCES students(id), skills_json TEXT NOT NULL);
        ''')
        for row in c.execute('SELECT id FROM classes WHERE id NOT IN (SELECT class_id FROM class_invites)').fetchall():
            c.execute('INSERT INTO class_invites VALUES (?,?)',(row[0],secrets.token_hex(4).upper()))


def _password(value, salt):
    return hashlib.pbkdf2_hmac('sha256', value.encode(), bytes.fromhex(salt), 200000).hex()


def _account(c, username, password, role, user_id=None, student_id=None):
    username = username.strip().casefold()
    if len(username) < 3 or len(password) < 6:
        raise ValueError('Kullanıcı adı en az 3, şifre en az 6 karakter olmalı.')
    salt = secrets.token_hex(16)
    return c.execute('''INSERT INTO login_accounts
        (username,salt,password_hash,role,user_id,student_id) VALUES (?,?,?,?,?,?)''',
        (username, salt, _password(password, salt), role, user_id, student_id)).lastrowid


def register(username, password, name, role):
    if role not in ('parent', 'teacher') or not name.strip():
        raise ValueError('Ad ve hesap türünü kontrol edin.')
    with school.get_connection() as c:
        uid = c.execute('INSERT INTO users(username,display_name,role) VALUES (?,?,?)',
                        (username.strip().casefold(), name.strip(), role)).lastrowid
        _account(c, username, password, role, user_id=uid)
    return authenticate(username, password)


def authenticate(username, password):
    # Lockout state is committed even when authentication fails.
    error = None
    identity = None
    with school.get_connection() as c:
        row = c.execute('''SELECT a.*, COALESCE(u.display_name,s.alias) name,
                           CASE WHEN locked_until > CURRENT_TIMESTAMP THEN 1 ELSE 0 END locked
                           FROM login_accounts a LEFT JOIN users u ON u.id=a.user_id
                           LEFT JOIN students s ON s.id=a.student_id WHERE a.username=?''',
                        (username.strip().casefold(),)).fetchone()
        if row and row['locked']:
            error = 'Çok fazla deneme yapıldı. Beş dakika sonra yeniden deneyin.'
        elif not row or not hmac.compare_digest(row['password_hash'], _password(password, row['salt'])):
            if row:
                failures = row['failed_attempts'] + 1
                c.execute('''UPDATE login_accounts SET failed_attempts=?,
                    locked_until=CASE WHEN ?>=5 THEN datetime('now','+5 minutes') ELSE NULL END WHERE id=?''',
                    (failures, failures, row['id']))
            error = 'Kullanıcı adı veya şifre hatalı.'
        else:
            c.execute('UPDATE login_accounts SET failed_attempts=0,locked_until=NULL WHERE id=?', (row['id'],))
            identity = Identity(row['id'], row['role'], row['name'], row['user_id'], row['student_id'])
    if error:
        raise ValueError(error)
    return identity


def classes(identity):
    if identity.role != 'teacher':
        return []
    with school.get_connection() as c:
        return [dict(r) for r in c.execute('''SELECT c.*,i.code FROM classes c
            LEFT JOIN class_invites i ON i.class_id=c.id WHERE c.teacher_id=? ORDER BY c.name''', (identity.user_id,))]


def students(identity, class_id=None):
    with school.get_connection() as c:
        if identity.role == 'parent':
            rows = c.execute('SELECT * FROM students WHERE parent_id=? ORDER BY alias', (identity.user_id,))
        elif identity.role == 'student':
            rows = c.execute('SELECT * FROM students WHERE id=?', (identity.student_id,))
        elif identity.role == 'teacher':
            rows = c.execute('''SELECT DISTINCT s.* FROM students s JOIN class_students cs ON cs.student_id=s.id
                JOIN classes cl ON cl.id=cs.class_id WHERE cl.teacher_id=? AND (? IS NULL OR cl.id=?) ORDER BY s.alias''',
                (identity.user_id, class_id, class_id))
        else:
            return []
        return [dict(r) for r in rows]


def require_student(identity, student_id):
    row = next((s for s in students(identity) if s['id'] == student_id), None)
    if row is None:
        raise ValueError('Bu öğrenci kaydına erişiminiz yok.')
    return row


def add_child(identity, name, grade, username=None, password=None):
    if identity.role != 'parent' or not name.strip():
        raise ValueError('Yalnızca veli çocuk hesabı oluşturabilir.')
    with school.get_connection() as c:
        sid = c.execute('INSERT INTO students(alias,grade,parent_id) VALUES (?,?,?)',
                        (name.strip(), grade, identity.user_id)).lastrowid
        c.execute('INSERT INTO parent_settings(student_id) VALUES (?)', (sid,))
        _account(c, username or f'child_{sid}_{secrets.token_hex(3)}', password or secrets.token_urlsafe(24), 'student', student_id=sid)
    return sid


def update_child(identity,student_id,name,grade):
    child=require_student(identity,student_id)
    if identity.role!='parent' or not name.strip() or grade not in range(1,5):raise ValueError('Çocuk bilgilerini kontrol edin.')
    with school.get_connection() as c:
        levels={r[0] for r in c.execute('SELECT cl.grade FROM classes cl JOIN class_students cs ON cs.class_id=cl.id WHERE cs.student_id=?',(student_id,))}
        if levels and levels!={grade}:raise ValueError('Sınıfa bağlı çocuğun düzeyi, sınıfından farklı olamaz.')
        c.execute('UPDATE students SET alias=?,grade=? WHERE id=? AND parent_id=?',(name.strip(),grade,child['id'],identity.user_id))


def update_class(identity,class_id,name,grade):
    if identity.role!='teacher' or class_id not in {c['id'] for c in classes(identity)} or not name.strip() or grade not in range(1,5):raise ValueError('Sınıf bilgilerini kontrol edin.')
    with school.get_connection() as c:
        levels={r[0] for r in c.execute('SELECT s.grade FROM students s JOIN class_students cs ON cs.student_id=s.id WHERE cs.class_id=?',(class_id,))}
        if levels and levels!={grade}:raise ValueError('Öğrenciler kayıtlıyken sınıf düzeyi öğrencilerden farklı olamaz.')
        c.execute('UPDATE classes SET name=?,grade=? WHERE id=? AND teacher_id=?',(name.strip(),grade,class_id,identity.user_id))


def child_profiles():
    """Local device's child chooser; no adult data or credentials are exposed."""
    with school.get_connection() as c:
        return [dict(r) for r in c.execute('SELECT id,alias,grade FROM students ORDER BY alias')]


def student_identity(student_id):
    with school.get_connection() as c:
        row = c.execute("SELECT s.alias,a.id FROM students s LEFT JOIN login_accounts a ON a.student_id=s.id WHERE s.id=?",(student_id,)).fetchone()
    if row is None:
        raise ValueError('Öğrenci bulunamadı.')
    return Identity(row['id'] or 0,'student',row['alias'],None,student_id)


def share_class(identity, class_id):
    classroom = next((r for r in classes(identity) if r['id']==class_id),None)
    if identity.role != 'teacher' or not classroom:
        raise ValueError('Bu sınıfı paylaşamazsınız.')
    init_extras()
    with school.get_connection() as c:
        parents = c.execute("SELECT id FROM users WHERE role='parent'").fetchall()
        for parent in parents:
            c.execute('''INSERT INTO parent_notifications(user_id,class_id,message,read_at) VALUES (?,?,?,NULL)
                ON CONFLICT(user_id,class_id) DO UPDATE SET message=excluded.message,read_at=NULL''',
                (parent[0],class_id,f"{identity.name}, {classroom['name']} ({classroom['grade']}. sınıf) sınıfına davet ediyor. Katılım kodu: {classroom['code']}"))
    return len(parents)


def init_extras():
    with school.get_connection() as c:
        c.executescript('''CREATE TABLE IF NOT EXISTS parent_notifications(
            id INTEGER PRIMARY KEY,user_id INTEGER NOT NULL,class_id INTEGER NOT NULL,message TEXT NOT NULL,read_at TEXT,
            UNIQUE(user_id,class_id));
            CREATE TABLE IF NOT EXISTS task_schedules(id INTEGER PRIMARY KEY,assignment_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,starts_at TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'pending',system_error TEXT);
            CREATE TABLE IF NOT EXISTS demo_seed(version TEXT PRIMARY KEY);''')
        c.execute("""CREATE TABLE IF NOT EXISTS answer_snapshots (
            record_kind TEXT NOT NULL, record_id INTEGER NOT NULL, student_id INTEGER NOT NULL,
            fingerprint TEXT NOT NULL, payload TEXT NOT NULL, is_correct INTEGER NOT NULL, recorded_order INTEGER NOT NULL DEFAULT 0,
            answered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(record_kind,record_id))""")
        if 'recorded_order' not in {r[1] for r in c.execute('PRAGMA table_info(answer_snapshots)')}:
            c.execute('ALTER TABLE answer_snapshots ADD COLUMN recorded_order INTEGER NOT NULL DEFAULT 0')
        c.execute('''CREATE TABLE IF NOT EXISTS student_school_numbers(student_id INTEGER PRIMARY KEY REFERENCES students(id), school_number TEXT NOT NULL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS assignment_learning_state(assignment_id INTEGER NOT NULL,student_id INTEGER NOT NULL,payload TEXT NOT NULL,rate INTEGER NOT NULL DEFAULT 0,mastered INTEGER NOT NULL DEFAULT 0,PRIMARY KEY(assignment_id,student_id))''')
        c.execute('CREATE TABLE IF NOT EXISTS student_avatars(student_id INTEGER PRIMARY KEY,asset TEXT NOT NULL)')
        c.execute('''CREATE TABLE IF NOT EXISTS answer_metadata(record_kind TEXT NOT NULL,record_id INTEGER NOT NULL,
            subject TEXT NOT NULL,concept TEXT NOT NULL,seconds REAL NOT NULL DEFAULT 0,is_support INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY(record_kind,record_id))''')


def avatar_for(student_id):
    init_extras()
    with school.get_connection() as c:
        row=c.execute('SELECT asset FROM student_avatars WHERE student_id=?',(student_id,)).fetchone()
    return row[0] if row else 'student_boy.png'


def set_avatar(identity,student_id,asset):
    if identity.role!='parent' or asset not in ('student_boy.png','student_girl.png'):
        raise ValueError('Öğrenci görselini yalnızca veli seçebilir.')
    require_student(identity,student_id);init_extras()
    with school.get_connection() as c:
        c.execute('INSERT INTO student_avatars VALUES (?,?) ON CONFLICT(student_id) DO UPDATE SET asset=excluded.asset',(student_id,asset))


def notifications(identity, acknowledge=False):
    if identity.role != 'parent':
        return []
    init_extras()
    with school.get_connection() as c:
        rows = [dict(r) for r in c.execute('SELECT * FROM parent_notifications WHERE user_id=? AND read_at IS NULL',(identity.user_id,))]
        if acknowledge:
            c.execute('UPDATE parent_notifications SET read_at=CURRENT_TIMESTAMP WHERE user_id=?',(identity.user_id,))
    return rows


def add_class(identity, name, grade):
    if identity.role != 'teacher' or not name.strip():
        raise ValueError('Sınıfı yalnızca öğretmen oluşturabilir.')
    with school.get_connection() as c:
        cid = c.execute('INSERT INTO classes(name,grade,teacher_id) VALUES (?,?,?)',
                        (name.strip(), grade, identity.user_id)).lastrowid
        code = secrets.token_hex(4).upper()
        c.execute('INSERT INTO class_invites VALUES (?,?)', (cid, code))
    return cid


def reset_child_password(identity, student_id, password):
    if identity.role != 'parent':
        raise ValueError('Şifreyi yalnızca veli yenileyebilir.')
    require_student(identity, student_id)
    if len(password) < 6:
        raise ValueError('Şifre en az 6 karakter olmalı.')
    salt = secrets.token_hex(16)
    with school.get_connection() as c:
        row = c.execute('SELECT id FROM login_accounts WHERE student_id=?', (student_id,)).fetchone()
        if not row:
            raise ValueError('Bu eski öğrenci kaydının henüz giriş hesabı yok.')
        c.execute('''UPDATE login_accounts SET salt=?,password_hash=?,failed_attempts=0,locked_until=NULL WHERE id=?''',
                  (salt, _password(password, salt), row['id']))


def import_legacy_history(identity, student_id, pin):
    """An explicit, PIN-verified one-time mapping of the former single-child log."""
    if identity.role != 'parent':
        raise ValueError('Eski raporları yalnızca veli bağlayabilir.')
    require_student(identity, student_id)
    from pin_security import pin_limiter
    ok, message = pin_limiter.verify(pin)
    if not ok:
        raise ValueError(message)
    from data import database as legacy
    import sqlite3
    import questions as qb
    source = sqlite3.connect(legacy.DB_PATH)
    source.row_factory = sqlite3.Row
    try:
        rows = source.execute('''SELECT a.*,COALESCE(q.text,'Eski çalışma') question_text
            FROM attempts a LEFT JOIN questions q ON q.qkey=a.qkey ORDER BY a.id''').fetchall()
    finally:
        source.close()
    count = 0
    with school.get_connection() as c:
        for row in rows:
            key = f'{legacy.DB_PATH.resolve()}:{row["id"]}'
            exists = c.execute('SELECT student_id FROM legacy_imports WHERE source_key=?',(key,)).fetchone()
            if exists:
                if exists[0] != student_id:
                    raise ValueError('Bu eski raporlar daha önce başka bir çocuk hesabına bağlanmış.')
                continue
            c.execute('INSERT INTO legacy_imports VALUES (?,?)',(key,student_id))
            c.execute('''INSERT INTO practice_attempts(student_id,skill,topic,question_text,is_correct,hint_used,answered_at)
                VALUES (?,?,?,?,?,?,?)''', (student_id,row['skill'],qb.skill_name(row['skill']),row['question_text'],
                                           row['correct'],row['hint_used'],row['created_at']))
            count += 1
    return count


def join_class(identity, student_id, code):
    if identity.role != 'parent':
        raise ValueError('Sınıfa katılımı veli yapmalı.')
    student = require_student(identity, student_id)
    with school.get_connection() as c:
        classroom = c.execute('''SELECT cl.* FROM classes cl JOIN class_invites i ON i.class_id=cl.id
                                 WHERE i.code=?''', (code.strip().upper(),)).fetchone()
        if not classroom or classroom['grade'] != student['grade']:
            raise ValueError('Sınıf kodu geçersiz veya sınıf düzeyi uyuşmuyor.')
        c.execute('INSERT OR IGNORE INTO class_students VALUES (?,?)', (classroom['id'], student_id))


def practice_skills(identity, student_id):
    require_student(identity, student_id)
    with school.get_connection() as c:
        row = c.execute('SELECT skills_json FROM student_practice_preferences WHERE student_id=?',(student_id,)).fetchone()
    return json.loads(row[0]) if row else ['m3_toplama','living_needs','matter_states','traffic','directions','homework_turkce']


def set_practice_skills(identity, student_id, skills):
    if identity.role != 'parent':
        raise ValueError('Çalışma derslerini veli belirler.')
    child = require_student(identity,student_id)
    import questions as qb
    if not skills or not set(skills) <= dict(qb.skills_for_grade(child['grade'])).keys():
        raise ValueError('En az bir uygun ders / konu seçin.')
    with school.get_connection() as c:
        c.execute('INSERT OR REPLACE INTO student_practice_preferences VALUES (?,?)',
                  (student_id,json.dumps(list(dict.fromkeys(skills)))))


def tasks(identity, student_id=None):
    if student_id is not None:
        require_student(identity, student_id)
    with school.get_connection() as c:
        rows = [dict(r) for r in c.execute('''SELECT a.*,t.title topic,t.subject,
            (SELECT COUNT(*) FROM questions q WHERE q.assignment_id=a.id) actual_count
            FROM assignments a JOIN topics t ON t.id=a.topic_id ORDER BY a.id DESC''')]
        allowed_students = {s['id'] for s in students(identity)}
        selected = {student_id} if student_id else allowed_students
        result = []
        for task in rows:
            recipients = {task['student_id']} if task['student_id'] else {
                r[0] for r in c.execute('SELECT student_id FROM class_students WHERE class_id=?', (task['class_id'],))}
            targets = {r[0] for r in c.execute('SELECT student_id FROM assignment_targets WHERE assignment_id=?', (task['id'],))}
            if targets:
                recipients &= targets
            if identity.role == 'teacher' and student_id is None:
                if task['created_by_user_id'] != identity.user_id:
                    continue
            else:
                if not recipients & selected:
                    continue
            task['recipient_count'] = len(recipients)
            completed_students = {r[0] for r in c.execute('''SELECT student_id FROM student_results WHERE assignment_id=?
                GROUP BY student_id HAVING COUNT(DISTINCT question_id)>=?''', (task['id'], max(1,task['actual_count'])))}
            learning_rows=c.execute('SELECT student_id,rate,mastered FROM assignment_learning_state WHERE assignment_id=?',(task['id'],)).fetchall()
            completed_students-={r['student_id'] for r in learning_rows if not r['mastered']}
            completed_students|={r['student_id'] for r in learning_rows if r['mastered']}
            task['completed_students'] = len(recipients & completed_students)
            if student_id is not None or identity.role == 'student':
                sid = student_id or identity.student_id
                learning_row=next((r for r in learning_rows if r['student_id']==sid),None)
                task['mastered']=bool(learning_row and learning_row['mastered'])
                task['mastery_rate']=learning_row['rate'] if learning_row else None
                task['completed'] = c.execute('''SELECT COUNT(DISTINCT question_id) FROM student_results
                    WHERE student_id=? AND assignment_id=?''', (sid, task['id'])).fetchone()[0]
            schedule_student=student_id or (identity.student_id if identity.role=='student' else None)
            planned=c.execute('SELECT starts_at,status,system_error FROM task_schedules WHERE assignment_id=? AND student_id=? AND status!=? ORDER BY id DESC LIMIT 1',
                (task['id'],schedule_student,'cancelled')).fetchone() if schedule_student else None
            if planned:
                task.update(scheduled_at=planned['starts_at'],schedule_status=planned['status'],schedule_error=planned['system_error'])
            result.append(task)
        return result


def create_task(identity, title, skill, count, student_id=None, class_id=None, due_date=None, curriculum=None, custom_questions=None):
    import questions as qb
    from learning_engine.learning_core import LocalQuestionProvider
    if not title.strip() or not 1 <= count <= 30:
        raise ValueError('Görev adı ve soru sayısını kontrol edin.')
    if identity.role == 'parent':
        child = require_student(identity, student_id)
        grade, target = child['grade'], {'student_id': student_id}
    elif identity.role == 'teacher':
        classroom = next((cl for cl in classes(identity) if cl['id'] == class_id), None)
        if not classroom:
            raise ValueError('Bu sınıfa erişiminiz yok.')
        if student_id is not None and student_id not in {s['id'] for s in students(identity, class_id)}:
            raise ValueError('Öğrenci seçili sınıfa ait değil.')
        grade, target = classroom['grade'], {'class_id': class_id}
    else:
        raise ValueError('Öğrenci görev oluşturamaz.')
    if skill not in dict(qb.skills_for_grade(grade)):
        raise ValueError('Konu bu sınıf düzeyinde kullanılamıyor.')
    if custom_questions is not None:
        from teaching_materials import validate_questions
        custom_questions=validate_questions(custom_questions)
        if len(custom_questions)!=count: raise ValueError('Soru sayısı hazırlanan paketle uyuşmuyor.')
    bank = list(custom_questions) if custom_questions else qb.reviewed_bank(skill, grade)
    mapping = {'m3_toplama': 'addition', 'm4_kesir': 'fraction_compare'}
    mapped = mapping.get(skill, skill)
    provider = LocalQuestionProvider()
    used = set()
    while len(bank) < count and mapped in provider.SUPPORTED.get('matematik', ()) + provider.SUPPORTED.get('fen', ()) + provider.SUPPORTED.get('sosyal', ()):
        from learning_engine.school_content import TOPICS
        raw = provider.generate(grade, TOPICS[mapped][0], mapped, used)
        used.add(raw['signature'])
        bank.append(dict(text=raw['prompt'], choices=raw['options'], answer=raw['correct_index'],
                         explanation=raw.get('explanation', ''), hint=raw.get('hint', ''), visual=raw.get('visual')))
    if skill in ('m3_carpma','m4_bolme'):
        avoid = set()
        while len(bank) < count:
            q = qb._original_make_question(skill,avoid)
            avoid.add(q['qkey'])
            bank.append(q)
    if skill.startswith('cur_') and bank and not custom_questions:
        import random
        bank=list(bank)
        random.shuffle(bank)
        originals=list(bank)
        # Larger assignments are deliberate review of this unit, never filler
        # from a different subject. Original attempts still get separate IDs.
        while len(bank)<count:
            bank.append(dict(originals[(len(bank)-len(originals))%len(originals)],repeat_review=True))
    if len(bank) < count:
        raise ValueError(f'Bu konuda {len(bank)} hazır soru var. Soru sayısını azaltın.')
    label = qb.skill_name(skill)
    from curriculum import subject_for_skill
    subject=subject_for_skill(skill,grade)
    if curriculum:
        if curriculum.get('grade') != grade:
            raise ValueError('Müfredat sınıf düzeyi uyuşmuyor.')
        from curriculum import catalogue,ready_skills
        if not any(course['subject']==curriculum['subject'] and any(unit['url']==curriculum['source'] and unit['title']==curriculum['title'] for unit in course['units']) for course in catalogue(grade)):
            raise ValueError('MEB katalog kaydı bulunamadı.')
        if not custom_questions and skill not in ready_skills(curriculum['subject'],curriculum['title'],grade):
            raise ValueError('Bu tema için öğretmen soruları gerekli.')
        label,subject = curriculum['title'],curriculum['subject']
    for q in bank[:count]:
        if not q.get('text') or not 2<=len(q.get('choices',[]))<=4 or not isinstance(q.get('answer'),int) or not 0<=q['answer']<len(q['choices']):
            raise ValueError('Soru ve doğru seçenek bilgilerini kontrol edin.')
    # Topic, task and all questions are created atomically.
    with school.get_connection() as c:
        tid = c.execute('''INSERT INTO topics(title,subject,grade,created_by_user_id,creator_role,student_id,class_id)
            VALUES (?,?,?,?,?,?,?)''', (label, subject, grade, identity.user_id, identity.role,
                                        target.get('student_id'), target.get('class_id'))).lastrowid
        aid = c.execute('''INSERT INTO assignments(title,topic_id,created_by_user_id,student_id,class_id,question_count,due_date)
            VALUES (?,?,?,?,?,?,?)''', (title.strip(), tid, identity.user_id, target.get('student_id'),
                                      target.get('class_id'), count, due_date)).lastrowid
        if identity.role == 'teacher' and student_id:
            c.execute('INSERT INTO assignment_targets VALUES (?,?)', (aid, student_id))
        for q in bank[:count]:
            qid = c.execute('''INSERT INTO questions(assignment_id,question_text,options_json,correct_answer,explanation)
                VALUES (?,?,?,?,?)''', (aid, q['text'], json.dumps(q['choices'], ensure_ascii=False),
                                        q['choices'][q['answer']], q.get('explanation', ''))).lastrowid
            payload = dict(q, skill=skill, id=qid, qkey=f'assignment:{aid}:{qid}',curriculum=curriculum)
            c.execute('INSERT INTO question_details VALUES (?,?)', (qid, json.dumps(payload, ensure_ascii=False)))
    return aid


def task_questions(identity, assignment_id):
    if identity.role != 'student' or not any(t['id'] == assignment_id for t in tasks(identity)):
        raise ValueError('Bu göreve erişiminiz yok.')
    with school.get_connection() as c:
        state=c.execute('SELECT mastered FROM assignment_learning_state WHERE assignment_id=? AND student_id=?',(assignment_id,identity.student_id)).fetchone()
        if state and state['mastered']:return []
        rows = c.execute('''SELECT q.*,d.payload FROM questions q LEFT JOIN question_details d ON d.question_id=q.id
            WHERE q.assignment_id=? AND q.id NOT IN (SELECT question_id FROM student_results WHERE student_id=? AND assignment_id=?)
            ORDER BY q.id''', (assignment_id, identity.student_id, assignment_id)).fetchall()
        if not rows and state:
            rows=c.execute('SELECT q.*,d.payload FROM questions q LEFT JOIN question_details d ON d.question_id=q.id WHERE q.assignment_id=? ORDER BY q.id',(assignment_id,)).fetchall()
            rows=[dict(r,payload=json.dumps(dict(json.loads(r['payload']),_support_question=True))) if r['payload'] else r for r in rows]
        result = []
        for r in rows:
            if r['payload']:
                result.append(json.loads(r['payload']))
            else:
                options = json.loads(r['options_json'])
                if not options:
                    options = [r['correct_answer']]
                result.append(dict(id=r['id'], skill='homework_general', text=r['question_text'], choices=options,
                                   answer=options.index(r['correct_answer']), hint='', explanation=r['explanation'],
                                   visual=None, qkey=f"assignment:{assignment_id}:{r['id']}"))
        return result


def save_answer(identity, question, choice, hint, assignment_id=None,seconds=0):
    if identity.role != 'student':
        raise ValueError('Yalnızca öğrenci cevap kaydedebilir.')
    if not 0 <= choice < len(question['choices']):
        raise ValueError('Geçersiz cevap.')
    if assignment_id is not None:
        allowed = task_questions(identity, assignment_id)
        original=next((q for q in allowed if q['id']==question['id']),None)
        if original is None:
            raise ValueError('Soru tamamlanmış veya bu göreve ait değil.')
        question=original
    import questions as qb
    from curriculum import subject_for_skill
    curriculum=question.get('curriculum') or {}
    topic=curriculum.get('title') or question.get('topic') or qb.skill_name(question['skill'])
    grade=require_student(identity,identity.student_id)['grade']
    subject=curriculum.get('subject') or subject_for_skill(question['skill'],grade)
    concept=question.get('concept') or topic
    correct=choice==question['answer']
    with school.get_connection() as c:
        c.execute('BEGIN IMMEDIATE')
        if assignment_id is not None:
            if c.execute('SELECT 1 FROM student_results WHERE student_id=? AND assignment_id=? AND question_id=?',
                         (identity.student_id,assignment_id,question['id'])).fetchone(): raise ValueError('Bu soru zaten cevaplandı.')
            cursor=c.execute('''INSERT INTO student_results(student_id,assignment_id,question_id,answer_text,is_correct,hint_used)
                VALUES (?,?,?,?,?,?)''',(identity.student_id,assignment_id,question['id'],question['choices'][choice],int(correct),int(hint)))
            kind='task'
        else:
            cursor=c.execute('''INSERT INTO practice_attempts(student_id,skill,topic,question_text,is_correct,hint_used)
                VALUES (?,?,?,?,?,?)''',(identity.student_id,question['skill'],topic,question['text'],int(correct),int(hint)))
            kind='practice'
        payload=dict(question)
        fingerprint=question_fingerprint(question)
        import time
        c.execute('INSERT INTO answer_snapshots(record_kind,record_id,student_id,fingerprint,payload,is_correct,recorded_order) VALUES (?,?,?,?,?,?,?)',
            (kind,cursor.lastrowid,identity.student_id,fingerprint,json.dumps(payload,ensure_ascii=False),int(correct),time.time_ns()))
        c.execute('INSERT INTO answer_metadata(record_kind,record_id,subject,concept,seconds,is_support) VALUES (?,?,?,?,?,?)',
            (kind,cursor.lastrowid,subject,concept,max(0,float(seconds)),int(bool(question.get('_support_question')))))
    return correct


def analytics(identity, student_id=None, class_id=None,period_days=None):
    if student_id is not None:
        require_student(identity, student_id)
    ids = [student_id] if student_id else [s['id'] for s in students(identity, class_id)]
    if not ids:
        return {'total': 0, 'correct': 0, 'wrong': 0, 'rate': 0, 'topics': [], 'trend': [], 'students': [],'subjects':[],'concepts':[]}
    placeholders = ','.join('?' for _ in ids)
    with school.get_connection() as c:
        query = f'''SELECT r.student_id,t.title topic,r.is_correct,r.hint_used,r.answered_at,t.subject,
            COALESCE(m.concept,t.title) concept,COALESCE(m.is_support,0) is_support,m.seconds,t.grade,NULL skill
            FROM student_results r JOIN assignments a ON a.id=r.assignment_id JOIN topics t ON t.id=a.topic_id
            LEFT JOIN answer_metadata m ON m.record_kind='task' AND m.record_id=r.id WHERE r.student_id IN ({placeholders})
            UNION ALL SELECT p.student_id,p.topic,p.is_correct,p.hint_used,p.answered_at,m.subject,
            COALESCE(m.concept,p.topic),COALESCE(m.is_support,0),m.seconds,s.grade,p.skill FROM practice_attempts p
            JOIN students s ON s.id=p.student_id LEFT JOIN answer_metadata m ON m.record_kind='practice' AND m.record_id=p.id
            WHERE p.student_id IN ({placeholders})'''
        rows = [dict(r) for r in c.execute(query, ids + ids)]
    if period_days is not None:
        if period_days not in (7,30):raise ValueError("Geçersiz rapor dönemi.")
        from datetime import datetime,timezone
        cutoff=(datetime.now(timezone.utc)-timedelta(days=period_days)).replace(tzinfo=None)
        rows=[r for r in rows if datetime.fromisoformat(r["answered_at"])>=cutoff]
    topics, people, days = {}, {}, {}
    concepts,subjects={},{}
    for r in rows:
        from curriculum import subject_for_skill
        subject=r['subject'] or subject_for_skill(r['skill'],r['grade'])
        for collection,key in ((subjects,subject),(concepts,(subject,r['topic'],r['concept']))):
            bucket=collection.setdefault(key,dict(total=0,correct=0,wrong=0,hints=0,clean=0,support=0))
            bucket['total']+=1;bucket['correct']+=r['is_correct'];bucket['wrong']+=1-r['is_correct']
            bucket['hints']+=r['hint_used'];bucket['clean']+=int(r['is_correct'] and not r['hint_used']);bucket['support']+=r['is_support']
        for collection, key in ((topics, r['topic']), (people, r['student_id'])):
            bucket = collection.setdefault(key, {'total': 0, 'correct': 0, 'wrong': 0, 'hints': 0})
            bucket['total'] += 1
            bucket['correct'] += r['is_correct']
            bucket['wrong'] += 1-r['is_correct']
            bucket['hints'] += r['hint_used']
        day = r['answered_at'][:10]
        days[day] = days.get(day, 0) + 1
    total = len(rows)
    correct = sum(r['is_correct'] for r in rows)
    # SQLite timestamps are UTC; daily graph uses the user's Istanbul date.
    from datetime import datetime, timezone
    istanbul = timezone(timedelta(hours=3))
    local_days = {}
    for r in rows:
        parsed = datetime.fromisoformat(r['answered_at']).replace(tzinfo=timezone.utc).astimezone(istanbul)
        key = parsed.date().isoformat()
        local_days[key] = local_days.get(key, 0) + 1
    today = datetime.now(istanbul).date()
    trend = [( (today-timedelta(days=i)).strftime('%d.%m'), local_days.get((today-timedelta(days=i)).isoformat(), 0)) for i in reversed(range(7))]
    roster = students(identity, class_id)
    def assessment(v):
        rate=round(v['correct']*100/max(1,v['total']))
        status='Veri birikiyor' if v['total']<5 else 'Tekrar önerilir' if rate<60 or v['hints']/v['total']>.5 else 'Güçleniyor' if rate>=80 and v['clean']/v['total']>=.6 else 'Pekiştiriliyor'
        return dict(v,rate=rate,status=status)
    return dict(total=total, correct=correct, wrong=total-correct, rate=round(100*correct/total) if total else 0,
                topics=[dict(topic=k, **v) for k,v in topics.items()], trend=trend,
                subjects=[dict(subject=k,**assessment(v)) for k,v in subjects.items()],
                concepts=[dict(subject=k[0],topic=k[1],concept=k[2],**assessment(v)) for k,v in concepts.items()],
                students=[dict(s, **people.get(s['id'], {'total':0,'correct':0,'wrong':0,'hints':0})) for s in roster if s['id'] in ids])


def question_fingerprint(question):
    value=[question['skill'],question['text'].strip(),question['choices'],question['answer']]
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True).encode()).hexdigest()


def wrong_questions(identity):
    """Latest result per exact question, strictly scoped to the signed-in child."""
    if identity.role!='student':raise ValueError('Öğrenci hesabı gerekli.')
    require_student(identity,identity.student_id)
    latest={}
    with school.get_connection() as c:
        # Old assignment attempts remain reconstructable from their immutable question details.
        rows=c.execute("""SELECT d.payload,r.is_correct,r.answered_at FROM student_results r
            JOIN question_details d ON d.question_id=r.question_id
            WHERE r.student_id=? ORDER BY r.answered_at,r.id""",(identity.student_id,)).fetchall()
        snapshots=c.execute('SELECT payload,is_correct,answered_at,recorded_order FROM answer_snapshots WHERE student_id=? ORDER BY answered_at,recorded_order',
            (identity.student_id,)).fetchall()
        legacy_practice=c.execute('''SELECT p.* FROM practice_attempts p LEFT JOIN answer_snapshots s
            ON s.record_kind='practice' AND s.record_id=p.id WHERE p.student_id=? AND s.record_id IS NULL
            ORDER BY p.answered_at,p.id''',(identity.student_id,)).fetchall()
        import questions as qb
        grade=require_student(identity,identity.student_id)['grade']
        banks={}
        reconstructed=[]
        for attempt in legacy_practice:
            skill=attempt['skill']
            if skill not in banks:
                try:banks[skill]={q['text']:q for q in qb.reviewed_bank(skill,grade)}
                except ValueError:banks[skill]={}
            q=banks[skill].get(attempt['question_text'])
            if q:reconstructed.append(dict(payload=json.dumps(q,ensure_ascii=False),is_correct=attempt['is_correct'],answered_at=attempt['answered_at']))
        for row in sorted([*rows,*reconstructed,*snapshots],key=lambda r:(r['answered_at'],dict(r).get('recorded_order',0))):
            q=json.loads(row['payload']);key=question_fingerprint(q)
            latest[key]=(bool(row['is_correct']),q,row['answered_at'])
    return [dict(q,_review=True,_wrong_at=when) for correct,q,when in latest.values() if not correct]


def school_number(student_id):
    with school.get_connection() as c:
        row=c.execute('SELECT school_number FROM student_school_numbers WHERE student_id=?',(student_id,)).fetchone()
    return row[0] if row else ''


def enter_student_by_number(name, number, class_code=''):
    """Passwordless local student entry. Class code scopes first-time registration."""
    name=name.strip();number=number.strip();class_code=class_code.strip().upper()
    if not 2<=len(name)<=80 or not number.isascii() or not number.isdigit() or not 1<=len(number)<=10:
        raise ValueError('Adını ve 1–10 rakamdan oluşan okul numaranı gir.')
    with school.get_connection() as c:
        classroom=None
        if class_code:
            classroom=c.execute('SELECT cl.* FROM classes cl JOIN class_invites i ON i.class_id=cl.id WHERE i.code=?',(class_code,)).fetchone()
            if classroom is None:raise ValueError('Sınıf kodunu kontrol et. Öğretmeninden öğrenebilirsin.')
        rows=c.execute('SELECT s.* FROM students s JOIN student_school_numbers n ON n.student_id=s.id WHERE n.school_number=?',(number,)).fetchall()
        matched=[r for r in rows if r['alias'].casefold()==name.casefold() and (classroom is None or c.execute('SELECT 1 FROM class_students WHERE class_id=? AND student_id=?',(classroom['id'],r['id'])).fetchone())]
        if len(matched)>1:raise ValueError('Sınıf kodunu da girerek kendi sınıfını seç.')
        if matched:sid=matched[0]['id']
        else:
            if classroom is None:raise ValueError('İlk girişinde öğretmeninin verdiği sınıf kodunu da gir.')
            occupied=c.execute('SELECT 1 FROM student_school_numbers n JOIN class_students cs ON cs.student_id=n.student_id WHERE cs.class_id=? AND n.school_number=?',(classroom['id'],number)).fetchone()
            if occupied:raise ValueError('Bu numara sınıfta kayıtlı. Adını ve numaranı kontrol et.')
            candidates=[r for r in c.execute('SELECT s.* FROM students s JOIN class_students cs ON cs.student_id=s.id LEFT JOIN student_school_numbers n ON n.student_id=s.id WHERE cs.class_id=? AND n.student_id IS NULL',(classroom['id'],)) if r['alias'].casefold()==name.casefold()]
            if len(candidates)>1:raise ValueError('Aynı isimli kayıtlar var. Öğretmeninden yardım iste.')
            if candidates:sid=candidates[0]['id']
            else:
                # A local placeholder preserves the mandatory parent foreign key; no adult login is created.
                owner=c.execute("SELECT id FROM users WHERE username='__local_student_profiles__'").fetchone()
                uid=owner[0] if owner else c.execute("INSERT INTO users(username,display_name,role) VALUES ('__local_student_profiles__','Yerel öğrenci profilleri','parent')").lastrowid
                sid=c.execute('INSERT INTO students(alias,grade,parent_id) VALUES (?,?,?)',(name,classroom['grade'],uid)).lastrowid
                c.execute('INSERT INTO parent_settings(student_id) VALUES (?)',(sid,))
                c.execute('INSERT INTO class_students VALUES (?,?)',(classroom['id'],sid))
            c.execute('INSERT INTO student_school_numbers VALUES (?,?)',(sid,number))
    return student_identity(sid)


def student_topic_bank(identity, skill):
    child=require_student(identity,identity.student_id)
    from curriculum_practice import skill_details,offline_bank
    topic=skill_details(skill)
    if topic['grade']!=child['grade']:raise ValueError('Konu sınıfına uygun değil.')
    from teaching_materials import init as init_packs
    init_packs()
    with school.get_connection() as c:
        rows=c.execute("""SELECT p.questions_json FROM teaching_packs p WHERE p.grade=? AND p.subject=? AND p.unit_title=?
            AND (p.owner_id=? OR p.owner_id IN (SELECT cl.teacher_id FROM classes cl JOIN class_students cs ON cs.class_id=cl.id WHERE cs.student_id=?))""",(child['grade'],topic['subject'],topic['title'],child['parent_id'],child['id'])).fetchall()
    result=list(offline_bank(skill))
    for row in rows:
        for q in json.loads(row[0]):
            result.append(dict(q,skill=skill,verified=True,source='adult-approved',curriculum=dict(grade=topic['grade'],subject=topic['subject'],title=topic['title'],source=topic['url'])))
    return result
