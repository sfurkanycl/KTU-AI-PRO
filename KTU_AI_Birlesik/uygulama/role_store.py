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
        c.execute('CREATE TABLE IF NOT EXISTS student_avatars(student_id INTEGER PRIMARY KEY,asset TEXT NOT NULL)')


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
            task['completed_students'] = len(recipients & completed_students)
            if student_id is not None or identity.role == 'student':
                sid = student_id or identity.student_id
                task['completed'] = c.execute('''SELECT COUNT(DISTINCT question_id) FROM student_results
                    WHERE student_id=? AND assignment_id=?''', (sid, task['id'])).fetchone()[0]
            planned=c.execute('SELECT starts_at,status,system_error FROM task_schedules WHERE assignment_id=? ORDER BY id DESC LIMIT 1',(task['id'],)).fetchone()
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
    if len(bank) < count:
        raise ValueError(f'Bu konuda {len(bank)} hazır soru var. Soru sayısını azaltın.')
    label = qb.skill_name(skill)
    subject = 'Türkçe' if 'turkce' in skill else 'Fen Bilimleri' if skill in ('living_needs','matter_states','homework_science') else 'Sosyal Bilgiler' if skill in ('traffic','directions','homework_general') else 'Matematik'
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
        rows = c.execute('''SELECT q.*,d.payload FROM questions q LEFT JOIN question_details d ON d.question_id=q.id
            WHERE q.assignment_id=? AND q.id NOT IN (SELECT question_id FROM student_results WHERE student_id=? AND assignment_id=?)
            ORDER BY q.id''', (assignment_id, identity.student_id, assignment_id)).fetchall()
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


def save_answer(identity, question, choice, hint, assignment_id=None):
    if identity.role != 'student':
        raise ValueError('Yalnızca öğrenci cevap kaydedebilir.')
    if not 0 <= choice < len(question['choices']):
        raise ValueError('Geçersiz cevap.')
    correct = choice == question['answer']
    if assignment_id is not None:
        allowed = task_questions(identity, assignment_id)
        if not any(q['id'] == question['id'] for q in allowed):
            raise ValueError('Soru tamamlanmış veya bu göreve ait değil.')
        school.record_result(identity.student_id, assignment_id, question['id'], question['choices'][choice], correct, hint)
    else:
        import questions as qb
        with school.get_connection() as c:
            c.execute('''INSERT INTO practice_attempts(student_id,skill,topic,question_text,is_correct,hint_used)
                VALUES (?,?,?,?,?,?)''', (identity.student_id, question['skill'], qb.skill_name(question['skill']),
                                         question['text'], int(correct), int(hint)))
    return correct


def analytics(identity, student_id=None, class_id=None):
    if student_id is not None:
        require_student(identity, student_id)
    ids = [student_id] if student_id else [s['id'] for s in students(identity, class_id)]
    if not ids:
        return {'total': 0, 'correct': 0, 'wrong': 0, 'rate': 0, 'topics': [], 'trend': [], 'students': []}
    placeholders = ','.join('?' for _ in ids)
    with school.get_connection() as c:
        query = f'''SELECT r.student_id,t.title topic,r.is_correct,r.hint_used,r.answered_at FROM student_results r
            JOIN assignments a ON a.id=r.assignment_id JOIN topics t ON t.id=a.topic_id WHERE r.student_id IN ({placeholders})
            UNION ALL SELECT student_id,topic,is_correct,hint_used,answered_at FROM practice_attempts WHERE student_id IN ({placeholders})'''
        rows = [dict(r) for r in c.execute(query, ids + ids)]
    topics, people, days = {}, {}, {}
    for r in rows:
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
    return dict(total=total, correct=correct, wrong=total-correct, rate=round(100*correct/total) if total else 0,
                topics=[dict(topic=k, **v) for k,v in topics.items()], trend=trend,
                students=[dict(s, **people.get(s['id'], {'total':0,'correct':0,'wrong':0,'hints':0})) for s in roster if s['id'] in ids])
