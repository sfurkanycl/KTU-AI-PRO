import json
import random
import re
import sqlite3
import time
import unicodedata
from uuid import uuid4
from learning_engine.turkish_text import restore_payload


def normalize_text(text):
    """Convert Turkish letters and common punctuation to ASCII."""
    replacements = str.maketrans({
        "\u00e7": "c", "\u00c7": "C",
        "\u011f": "g", "\u011e": "G",
        "\u0131": "i", "\u0130": "I",
        "\u00f6": "o", "\u00d6": "O",
        "\u015f": "s", "\u015e": "S",
        "\u00fc": "u", "\u00dc": "U",
        "\u2026": "...",
        "\u2013": "-", "\u2014": "-",
        "\u201c": '"', "\u201d": '"',
        "\u2018": "'", "\u2019": "'",
    })
    return text.translate(replacements)


def normalize_payload(value):
    """Preserve Turkish Unicode; repair known legacy text fields only."""
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value)
    if isinstance(value, list):
        return [normalize_payload(item) for item in value]
    if isinstance(value, dict):
        return restore_payload({
            key: normalize_payload(item)
            for key, item in value.items()
        })
    return value


class LocalQuestionProvider:
    SUPPORTED = {
        "matematik": ("fraction_compare", "addition"),
        "fen": ("living_needs", "matter_states"),
        "sosyal": ("traffic", "directions"),
    }

    def supports(self, subject, skill):
        return skill in self.SUPPORTED.get(subject, ())

    def generate(self, grade, subject, skill, used_signatures):
        if not self.supports(subject, skill):
            raise ValueError("Bu ders ve konu henüz desteklenmiyor.")

        if skill == "fraction_compare":
            return self._fraction_question(used_signatures)

        if subject != "matematik":
            from learning_engine.school_content import local_question
            return local_question(skill, used_signatures)

        return self._addition_question(grade, used_signatures)

    def generate_similar(self, grade, subject, skill, used, previous):
        if subject != "matematik":
            from learning_engine.school_content import local_question
            return local_question(skill, used, previous.get("concept"))
        return self.generate(grade, subject, skill, used)

    def _fraction_question(self, used):
        candidates = [
            (a, b)
            for a in range(2, 21)
            for b in range(a + 1, 21)
            if f"fraction:{a}:{b}" not in used
        ]

        if not candidates:
            raise ValueError("Yeni kesir sorusu kalmadi.")

        smaller, larger = random.choice(candidates)
        a, b = random.sample([smaller, larger], 2)

        answer = ">" if a < b else "<"
        options = [">", "<", "="]
        random.shuffle(options)

        return {
            "signature": f"fraction:{smaller}:{larger}",
            "prompt": (
                f"1/{a} ile 1/{b} arasına hangi isaret gelir?"
            ),
            "options": options,
            "correct_index": options.index(answer),
            "hint": (
                "Payları 1 olan kesirlerde payda büyüdükçe "
                "parça küçülür."
            ),
            "explanation": (
                "Aynı büyüklükteki bütünlerde, paylar 1 ise "
                "payda büyüdükçe parça küçülür. "
                f"Bu yüzden 1/{a} {answer} 1/{b}."
            ),
            "example": (
                "Örnek: 1/3 > 1/8. Aynı pizzanın üçte biri, "
                "sekizde birinden büyüktür."
            ),
        }

    def _addition_question(self, grade, used):
        upper = 20 if grade <= 2 else 100

        candidates = [
            (a, b)
            for a in range(1, upper + 1)
            for b in range(a, upper + 1)
            if f"addition:{a}:{b}" not in used
        ]

        if not candidates:
            raise ValueError("Yeni toplama sorusu kalmadi.")

        a, b = random.choice(candidates)
        total = a + b

        options = [
            str(total),
            str(total + 1),
            str(total - 1),
            str(total + 10),
        ]
        random.shuffle(options)

        return {
            "signature": f"addition:{a}:{b}",
            "prompt": f"{a} + {b} isleminin sonucu kactir?",
            "options": options,
            "correct_index": options.index(str(total)),
            "hint": (
                "İkinci sayıyı onlar ve birler olarak ayırıp "
                "sırayla ekleyebilirsin."
            ),
            "explanation": (
                f"{a} sayisinin uzerine {b} ekledigimizde "
                f"{total} elde ederiz."
            ),
            "example": (
                "Örnek: 12 + 15 = 12 + 10 + 5 = 27."
            ),
        }


class LearningEngine:
    def __init__(self, db_path="learning.db", provider=None):
        self.provider = provider or LocalQuestionProvider()

        self.db = sqlite3.connect(db_path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys = ON")

        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS learning_students (
            id TEXT PRIMARY KEY,
            nickname TEXT NOT NULL,
            grade INTEGER NOT NULL CHECK(grade BETWEEN 1 AND 8)
        );

        CREATE TABLE IF NOT EXISTS learning_sessions (
            id TEXT PRIMARY KEY,
            student_id TEXT NOT NULL
                REFERENCES learning_students(id),
            subject TEXT NOT NULL,
            skill TEXT NOT NULL,
            target INTEGER NOT NULL,
            max_attempts INTEGER NOT NULL,
            streak INTEGER NOT NULL DEFAULT 0,
            attempts INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'active',
            created_at REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS learning_questions (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL
                REFERENCES learning_sessions(id),
            payload TEXT NOT NULL,
            signature TEXT NOT NULL,
            shown_at REAL NOT NULL,
            hint_used INTEGER NOT NULL DEFAULT 0,
            answered INTEGER NOT NULL DEFAULT 0,
            UNIQUE(session_id, signature)
        );

        CREATE UNIQUE INDEX IF NOT EXISTS one_pending_question
        ON learning_questions(session_id)
        WHERE answered = 0;

        CREATE TABLE IF NOT EXISTS learning_answers (
            question_id TEXT PRIMARY KEY
                REFERENCES learning_questions(id),
            selected_index INTEGER NOT NULL,
            correct INTEGER NOT NULL,
            independent INTEGER NOT NULL,
            quick_wrong INTEGER NOT NULL,
            elapsed_seconds REAL NOT NULL,
            created_at REAL NOT NULL
        );
        """)

    def close(self):
        self.db.close()

    def create_student(self, nickname, grade):
        nickname = unicodedata.normalize("NFC", nickname).strip()

        if not nickname:
            raise ValueError("Öğrenci takma adı gerekli.")

        if type(grade) is not int or not 1 <= grade <= 8:
            raise ValueError("Sınıf 1-8 arasında olmalı.")

        student_id = uuid4().hex

        with self.db:
            self.db.execute(
                "INSERT INTO learning_students VALUES (?, ?, ?)",
                (student_id, nickname, grade),
            )

        return student_id

    def start_session(
        self,
        student_id,
        subject="matematik",
        skill="fraction_compare",
        target=2,
        max_attempts=10,
    ):
        subject = normalize_text(subject).strip().lower()

        if not self.provider.supports(subject, skill):
            raise ValueError("Desteklenmeyen ders veya konu.")

        if (
            type(target) is not int
            or type(max_attempts) is not int
            or not 1 <= target <= max_attempts <= 100
        ):
            raise ValueError("Hedef veya deneme sınırı geçersiz.")

        student = self.db.execute(
            "SELECT id FROM learning_students WHERE id=?",
            (student_id,),
        ).fetchone()

        if student is None:
            raise ValueError("Öğrenci bulunamadı.")

        session_id = uuid4().hex

        with self.db:
            self.db.execute(
                """INSERT INTO learning_sessions
                   (id, student_id, subject, skill,
                    target, max_attempts, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    session_id,
                    student_id,
                    subject,
                    skill,
                    target,
                    max_attempts,
                    time.time(),
                ),
            )

        return session_id

    def get_session(self, session_id):
        row = self.db.execute(
            "SELECT * FROM learning_sessions WHERE id=?",
            (session_id,),
        ).fetchone()

        if row is None:
            raise ValueError("Oturum bulunamadı.")

        return dict(row)

    def _active_question(self, session_id, question_id):
        session = self.get_session(session_id)

        if session["status"] != "active":
            raise ValueError("Oturum aktif değil.")

        question = self.db.execute(
            """SELECT * FROM learning_questions
               WHERE id=? AND session_id=? AND answered=0""",
            (question_id, session_id),
        ).fetchone()

        if question is None:
            raise ValueError(
                "Soru bulunamadı veya zaten cevaplandı."
            )

        return session, question

    @staticmethod
    def _public_question(question_id, payload):
        # Do not expose the answer key to the child UI.
        payload = normalize_payload(payload)
        visual = payload.get("visual")
        if not visual:
            addition = re.search(r"(\d+)\s*\+\s*(\d+)", payload["prompt"])
            fractions = re.search(r"1/(\d+).*1/(\d+)", payload["prompt"])
            if addition:
                visual = {"math_kind": "addition", "values": list(map(int, addition.groups()))}
            elif fractions:
                visual = {"math_kind": "fraction", "values": list(map(int, fractions.groups()))}
        return {
            "id": question_id,
            "prompt": payload["prompt"],
            "options": payload["options"],
            "visual": visual,
            "practice": payload.get("practice", False),
        }

    def next_question(self, session_id):
        session = self.get_session(session_id)

        if session["status"] != "active":
            raise ValueError("Oturum aktif değil.")

        pending = self.db.execute(
            """SELECT * FROM learning_questions
               WHERE session_id=? AND answered=0""",
            (session_id,),
        ).fetchone()

        if pending is not None:
            return self._public_question(
                pending["id"],
                json.loads(pending["payload"]),
            )

        student = self.db.execute(
            "SELECT grade FROM learning_students WHERE id=?",
            (session["student_id"],),
        ).fetchone()

        used = {
            row["signature"]
            for row in self.db.execute(
                """SELECT signature FROM learning_questions
                   WHERE session_id=?""",
                (session_id,),
            )
        }

        previous = self.db.execute(
            """SELECT q.payload, a.correct, a.independent
               FROM learning_questions q JOIN learning_answers a ON a.question_id=q.id
               WHERE q.session_id=? ORDER BY a.created_at DESC, q.rowid DESC LIMIT 1""",
            (session_id,),
        ).fetchone()
        needs_practice = previous is not None and not previous["independent"]
        similar = getattr(self.provider, "generate_similar", None)
        if needs_practice and similar:
            payload = similar(student["grade"], session["subject"], session["skill"],
                              used, json.loads(previous["payload"]))
            payload["practice"] = True
        else:
            payload = self.provider.generate(
            student["grade"],
            session["subject"],
            session["skill"],
            used,
            )

        payload = normalize_payload(payload)
        self._validate_payload(payload)

        question_id = uuid4().hex

        with self.db:
            self.db.execute(
                """INSERT INTO learning_questions
                   (id, session_id, payload, signature, shown_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    question_id,
                    session_id,
                    json.dumps(payload, ensure_ascii=True),
                    payload["signature"],
                    time.time(),
                ),
            )

        return self._public_question(question_id, payload)

    @staticmethod
    def _validate_payload(payload):
        required_texts = (
            "signature", "prompt", "hint",
            "explanation", "example",
        )

        for key in required_texts:
            value = payload.get(key)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Geçersiz soru alanı: {key}")

        options = payload.get("options")
        if (
            not isinstance(options, list)
            or len(options) < 2
            or any(
                not isinstance(option, str) or not option.strip()
                for option in options
            )
            or len(set(options)) != len(options)
        ):
            raise ValueError("Soru seçenekleri geçersiz.")

        index = payload.get("correct_index")
        if type(index) is not int or not 0 <= index < len(options):
            raise ValueError("Doğru cevap indeksi geçersiz.")

        # This checks structure, not factual correctness.
        # Local templates calculate their own answer keys.

    def request_hint(self, session_id, question_id):
        _, question = self._active_question(
            session_id, question_id
        )
        payload = normalize_payload(json.loads(question["payload"]))

        with self.db:
            self.db.execute(
                """UPDATE learning_questions
                   SET hint_used=1 WHERE id=?""",
                (question_id,),
            )

        return {
            "hint": payload["hint"],
            "example": payload["example"],
        }

    def submit_answer(
        self, session_id, question_id, selected_index
    ):
        session, question = self._active_question(
            session_id, question_id
        )
        payload = normalize_payload(json.loads(question["payload"]))

        if (
            type(selected_index) is not int
            or not 0 <= selected_index < len(payload["options"])
        ):
            raise ValueError("Geçersiz seçenek indeksi.")

        correct = selected_index == payload["correct_index"]
        independent = correct and not bool(question["hint_used"])

        elapsed = max(
            0.0, time.time() - question["shown_at"]
        )
        quick_wrong = not correct and elapsed < 3.0

        # Keep completed progress after a wrong or assisted answer.
        streak = session["streak"] + int(independent)
        attempts = session["attempts"] + 1

        if streak >= session["target"]:
            status = "completed"
        elif attempts >= session["max_attempts"]:
            status = "needs_parent"
        else:
            status = "active"

        with self.db:
            self.db.execute(
                """INSERT INTO learning_answers
                   (question_id, selected_index, correct,
                    independent, quick_wrong,
                    elapsed_seconds, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    question_id,
                    selected_index,
                    int(correct),
                    int(independent),
                    int(quick_wrong),
                    elapsed,
                    time.time(),
                ),
            )

            self.db.execute(
                """UPDATE learning_questions
                   SET answered=1 WHERE id=?""",
                (question_id,),
            )

            self.db.execute(
                """UPDATE learning_sessions
                   SET streak=?, attempts=?, status=?
                   WHERE id=?""",
                (streak, attempts, status, session_id),
            )

        return {
            "correct": correct,
            "independent": independent,
            "status": status,
            "streak": streak,
            "target": session["target"],
            "attempts_remaining": (
                session["max_attempts"] - attempts
            ),
            "quick_wrong_signal": quick_wrong,
            "explanation": payload["explanation"],
            "example": (
                payload["example"] if not correct else None
            ),
        }

    def get_report(self, student_id):
        rows = self.db.execute(
            """SELECT
                   s.subject,
                   s.skill,
                   COUNT(a.question_id) AS answered,
                   COALESCE(SUM(a.correct), 0) AS correct,
                   COALESCE(SUM(a.independent), 0)
                       AS independent_correct,
                   COALESCE(SUM(a.quick_wrong), 0)
                       AS quick_wrong_signals,
                   COALESCE(SUM(q.hint_used), 0) AS hints_used
               FROM learning_sessions s
               LEFT JOIN learning_questions q
                   ON q.session_id = s.id
               LEFT JOIN learning_answers a
                   ON a.question_id = q.id
               WHERE s.student_id=?
               GROUP BY s.subject, s.skill
               ORDER BY s.subject, s.skill""",
            (student_id,),
        )

        return [dict(row) for row in rows]


def run_demo():
    engine = LearningEngine("learning.db")

    try:
        student_id = engine.create_student("Demo öğrenci", 4)

        print("1) Kesir karşılaştırma")
        print("2) Toplama")
        choice = input("Konu seç: ").strip()

        skill = (
            "addition" if choice == "2" else "fraction_compare"
        )

        session_id = engine.start_session(
            student_id=student_id,
            subject="matematik",
            skill=skill,
            target=2,
            max_attempts=10,
        )

        print("\nIpucu almak için i, çıkmak için q yaz.")
        print("Hedef: Art arda iki yardımsız doğru cevap.")

        while True:
            question = engine.next_question(session_id)
            print("\n" + question["prompt"])

            for number, option in enumerate(
                question["options"], start=1
            ):
                print(f"{number}) {option}")

            entry = input("Cevap: ").strip().lower()

            if entry == "q":
                break

            if entry == "i":
                help_data = engine.request_hint(
                    session_id, question["id"]
                )
                print(help_data["hint"])
                print(help_data["example"])
                continue

            try:
                result = engine.submit_answer(
                    session_id,
                    question["id"],
                    int(entry) - 1,
                )
            except ValueError as error:
                print(error)
                continue

            print(
                "Dogru!"
                if result["correct"]
                else "Açıklamayı inceleyip tekrar deneyelim."
            )

            if result["correct"] and not result["independent"]:
                print(
                    "İpucu kullanıldı. Tamamlama için "
                    "yardımsız doğru cevap gerekiyor."
                )

            print(result["explanation"])

            if result["example"]:
                print(result["example"])

            print(
                f"Ilerleme: {result['streak']}/"
                f"{result['target']}"
            )

            if result["status"] == "completed":
                print("Öğrenme molası tamamlandı!")
                break

            if result["status"] == "needs_parent":
                print("Velinden destek iste.")
                break

        print("\nRapor:")
        for row in engine.get_report(student_id):
            print(row)

    finally:
        engine.close()


if __name__ == "__main__":
    run_demo()
