
import sqlite3
from pathlib import Path

# Veritabani dosyasi proje icindeki data klasorunde tutulur.
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR
# Keep the two incompatible schemas in distinct databases; never overwrite sessions.
import os
DB_PATH = Path(os.getenv("OM_SCHOOL_DB_PATH", str(DATA_DIR / "school_records.db")))


class _ClosingConnection(sqlite3.Connection):
    def __exit__(self, *args):
        try:
            return super().__exit__(*args)
        finally:
            self.close()


def get_connection():
    """Veritabanina baglanti acar."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH, timeout=10, factory=_ClosingConnection)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Gerekli tablolari ilk kez olusturur."""

    with get_connection() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            display_name TEXT NOT NULL,
            role TEXT NOT NULL
                CHECK(role IN ('parent', 'teacher')),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            grade INTEGER NOT NULL CHECK(grade BETWEEN 1 AND 12),
            teacher_id INTEGER NOT NULL,
            FOREIGN KEY (teacher_id) REFERENCES users(id),
            UNIQUE(name, grade, teacher_id)
        );

        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alias TEXT NOT NULL,
            grade INTEGER NOT NULL CHECK(grade BETWEEN 1 AND 12),
            parent_id INTEGER NOT NULL,
            FOREIGN KEY (parent_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS class_students (
            class_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            PRIMARY KEY (class_id, student_id),
            FOREIGN KEY (class_id) REFERENCES classes(id),
            FOREIGN KEY (student_id) REFERENCES students(id)
        );

        CREATE TABLE IF NOT EXISTS topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subject TEXT NOT NULL,
            grade INTEGER NOT NULL CHECK(grade BETWEEN 1 AND 12),
            learning_objective TEXT DEFAULT '',
            created_by_user_id INTEGER NOT NULL,
            creator_role TEXT NOT NULL
                CHECK(creator_role IN ('parent', 'teacher')),
            student_id INTEGER,
            class_id INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by_user_id) REFERENCES users(id),
            FOREIGN KEY (student_id) REFERENCES students(id),
            FOREIGN KEY (class_id) REFERENCES classes(id),
            CHECK(student_id IS NULL OR class_id IS NULL)
        );

        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            topic_id INTEGER NOT NULL,
            created_by_user_id INTEGER NOT NULL,
            class_id INTEGER,
            student_id INTEGER,
            question_count INTEGER NOT NULL DEFAULT 5
                CHECK(question_count BETWEEN 1 AND 100),
            difficulty TEXT NOT NULL DEFAULT 'Orta'
                CHECK(difficulty IN ('Kolay', 'Orta', 'Zor')),
            due_date TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (topic_id) REFERENCES topics(id),
            FOREIGN KEY (created_by_user_id) REFERENCES users(id),
            FOREIGN KEY (class_id) REFERENCES classes(id),
            FOREIGN KEY (student_id) REFERENCES students(id),
            CHECK(class_id IS NULL OR student_id IS NULL)
        );

        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            assignment_id INTEGER NOT NULL,
            question_text TEXT NOT NULL,
            options_json TEXT DEFAULT '[]',
            correct_answer TEXT NOT NULL,
            explanation TEXT DEFAULT '',
            FOREIGN KEY (assignment_id)
                REFERENCES assignments(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS student_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            assignment_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            answer_text TEXT DEFAULT '',
            is_correct INTEGER NOT NULL
                CHECK(is_correct IN (0, 1)),
            hint_used INTEGER NOT NULL DEFAULT 0
                CHECK(hint_used IN (0, 1)),
            answered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(id),
            FOREIGN KEY (assignment_id) REFERENCES assignments(id),
            FOREIGN KEY (question_id) REFERENCES questions(id)
        );

        CREATE TABLE IF NOT EXISTS parent_settings (
            student_id INTEGER PRIMARY KEY,
            game_minutes INTEGER NOT NULL DEFAULT 30
                CHECK(game_minutes BETWEEN 1 AND 180),
            break_minutes INTEGER NOT NULL DEFAULT 5
                CHECK(break_minutes BETWEEN 1 AND 30),
            target_correct INTEGER NOT NULL DEFAULT 2
                CHECK(target_correct BETWEEN 1 AND 10),
            pin_hash TEXT DEFAULT '',
            FOREIGN KEY (student_id) REFERENCES students(id)
        );
        """)


def create_user(username, display_name, role):
    """Veli veya ogretmen kaydeder; yeni kullanicinin ID'sini dondurur."""
    if role not in ("parent", "teacher"):
        raise ValueError("Rol parent veya teacher olmali.")

    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO users (username, display_name, role)
               VALUES (?, ?, ?)""",
            (username.strip(), display_name.strip(), role)
        )
        return cursor.lastrowid


def create_class(name, grade, teacher_id):
    """Ogretmen icin sinif olusturur."""
    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO classes (name, grade, teacher_id)
               SELECT ?, ?, id FROM users
               WHERE id = ? AND role = 'teacher'""",
            (name.strip(), grade, teacher_id)
        )

        if cursor.rowcount == 0:
            raise ValueError("Ogretmen bulunamadi veya kullanici ogretmen degil.")

        return cursor.lastrowid


def add_student(alias, grade, parent_id):
    """Veliye bagli ogrenci ekler."""
    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO students (alias, grade, parent_id)
               SELECT ?, ?, id FROM users
               WHERE id = ? AND role = 'parent'""",
            (alias.strip(), grade, parent_id)
        )

        if cursor.rowcount == 0:
            raise ValueError("Veli bulunamadi veya kullanici veli degil.")

        student_id = cursor.lastrowid
        conn.execute(
            "INSERT INTO parent_settings (student_id) VALUES (?)",
            (student_id,)
        )
        return student_id


def enroll_student(class_id, student_id):
    """Ogrenciyi sinifa ekler."""
    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO class_students (class_id, student_id)
               SELECT c.id, s.id
               FROM classes c, students s
               WHERE c.id = ? AND s.id = ? AND c.grade = s.grade""",
            (class_id, student_id)
        )

        if cursor.rowcount == 0:
            raise ValueError(
                "Sinif veya ogrenci bulunamadi ya da sinif duzeyleri uyusmuyor."
            )


def add_topic(title, subject, grade, created_by_user_id,
              student_id=None, class_id=None, learning_objective=""):
    """Veli cocuguna, ogretmen sinifina konu ekler."""
    if (student_id is None) == (class_id is None):
        raise ValueError(
            "Yalnizca student_id veya class_id verilmelidir."
        )

    with get_connection() as conn:
        user = conn.execute(
            "SELECT role FROM users WHERE id = ?",
            (created_by_user_id,)
        ).fetchone()

        if user is None:
            raise ValueError("Kullanici bulunamadi.")

        role = user["role"]

        if role == "parent":
            if student_id is None:
                raise ValueError("Veli konuyu bir cocuga eklemelidir.")

            allowed = conn.execute(
                "SELECT id FROM students WHERE id = ? AND parent_id = ?",
                (student_id, created_by_user_id)
            ).fetchone()

            if allowed is None:
                raise ValueError("Bu cocuk belirtilen veliye ait degil.")

        elif role == "teacher":
            if class_id is None:
                raise ValueError("Ogretmen konuyu bir sinifa eklemelidir.")

            allowed = conn.execute(
                "SELECT id FROM classes WHERE id = ? AND teacher_id = ?",
                (class_id, created_by_user_id)
            ).fetchone()

            if allowed is None:
                raise ValueError("Bu sinif belirtilen ogretmene ait degil.")

        with get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO topics
                   (title, subject, grade, learning_objective,
                    created_by_user_id, creator_role, student_id, class_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (title.strip(), subject.strip(), grade,
                 learning_objective.strip(), created_by_user_id,
                 role, student_id, class_id)
            )
            return cursor.lastrowid


def create_assignment(title, topic_id, created_by_user_id,
                     question_count=5, difficulty="Orta",
                     class_id=None, student_id=None, due_date=None):
    """Bir konu icin sinif veya ogrenci calismasi olusturur."""
    if (class_id is None) == (student_id is None):
        raise ValueError(
            "Yalnizca class_id veya student_id verilmelidir."
        )

    with get_connection() as conn:
        user = conn.execute(
            "SELECT role FROM users WHERE id = ?",
            (created_by_user_id,)
        ).fetchone()

        if user is None:
            raise ValueError("Kullanici bulunamadi.")

        topic = conn.execute(
            "SELECT * FROM topics WHERE id = ?",
            (topic_id,)
        ).fetchone()

        if topic is None:
            raise ValueError("Konu bulunamadi.")

        if user["role"] == "teacher":
            if class_id is None or topic["class_id"] != class_id:
                raise ValueError("Ogretmen kendi sinifina ait konuyu secmeli.")

            owned_class = conn.execute(
                "SELECT id FROM classes WHERE id = ? AND teacher_id = ?",
                (class_id, created_by_user_id)
            ).fetchone()

            if owned_class is None:
                raise ValueError("Ogretmen bu sinifa erisemiyor.")

        elif user["role"] == "parent":
            if student_id is None or topic["student_id"] != student_id:
                raise ValueError("Veli kendi cocuguna ait konuyu secmeli.")

            child = conn.execute(
                "SELECT id FROM students WHERE id = ? AND parent_id = ?",
                (student_id, created_by_user_id)
            ).fetchone()

            if child is None:
                raise ValueError("Bu cocuk belirtilen veliye ait degil.")

        else:
            raise ValueError("Yetkisiz kullanici rolu.")

        cursor = conn.execute(
            """INSERT INTO assignments
               (title, topic_id, created_by_user_id, class_id, student_id,
                question_count, difficulty, due_date)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (title.strip(), topic_id, created_by_user_id,
             class_id, student_id, question_count, difficulty, due_date)
        )
        return cursor.lastrowid


def add_question(assignment_id, question_text, correct_answer,
                 options_json="[]", explanation=""):
    """Odev icin soru kaydeder. options_json JSON metni olmalidir."""
    import json
    json.loads(options_json)  # Gecersiz JSON'u kaydetmeden yakala.

    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO questions
               (assignment_id, question_text, options_json,
                correct_answer, explanation)
               VALUES (?, ?, ?, ?, ?)""",
            (assignment_id, question_text, options_json,
             correct_answer, explanation)
        )
        return cursor.lastrowid


def record_result(student_id, assignment_id, question_id,
                  answer_text, is_correct, hint_used=False):
    """Ogrencinin cevabini ve sonucunu kaydeder."""
    with get_connection() as conn:
        allowed = conn.execute(
            """SELECT id FROM assignments WHERE id=? AND
               (student_id=? OR class_id IN
                (SELECT class_id FROM class_students WHERE student_id=?))""",
            (assignment_id, student_id, student_id)
        ).fetchone()
        if allowed is None:
            raise ValueError("Ödev bu öğrenciye veya öğrencinin sınıfına atanmamış.")
        question = conn.execute(
            """SELECT id FROM questions
               WHERE id = ? AND assignment_id = ?""",
            (question_id, assignment_id)
        ).fetchone()

        if question is None:
            raise ValueError("Soru bu odeve ait degil.")

        cursor = conn.execute(
            """INSERT INTO student_results
               (student_id, assignment_id, question_id, answer_text,
                is_correct, hint_used)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (student_id, assignment_id, question_id, answer_text,
             int(bool(is_correct)), int(bool(hint_used)))
        )
        return cursor.lastrowid


def get_student_report(student_id):
    """Ogrencinin dogru, yanlis ve ipucu sayilarini dondurur."""
    with get_connection() as conn:
        return conn.execute(
            """SELECT t.title AS topic,
                      COUNT(r.id) AS answered,
                      COALESCE(SUM(r.is_correct), 0) AS correct_count,
                      COALESCE(SUM(1 - r.is_correct), 0) AS wrong_count,
                      COALESCE(SUM(r.hint_used), 0) AS hint_count
               FROM topics t
               JOIN assignments a
                 ON a.topic_id = t.id
               LEFT JOIN student_results r
                 ON r.assignment_id = a.id
                AND r.student_id = ?
               WHERE a.student_id = ? OR a.class_id IN (
                   SELECT class_id FROM class_students
                   WHERE student_id = ?
               )
               GROUP BY t.id, t.title
               ORDER BY t.title""",
            (student_id, student_id, student_id)
        ).fetchall()


if __name__ == "__main__":
    init_db()
    print("Veritabani hazir:", DB_PATH)
