"""Run an explicit live API smoke test and retain a key-free report.

Usage: python check_question_api.py living_needs traffic
Successful packs are saved through the normal generator + reviewer workflow.
"""
import json
import sys
import time
from pathlib import Path

from learning_engine.gemini_questions import prepare_pack, CachedGeminiProvider
from learning_engine.learning_core import LearningEngine
from learning_engine.school_content import TOPICS


def check(skill):
    start = time.monotonic()
    result = {"skill": skill, "grade": 4}
    try:
        result["accepted"] = prepare_pack(4, skill)
        provider = CachedGeminiProvider()
        engine = LearningEngine(":memory:", provider)
        try:
            student = engine.create_student("API test", 4)
            session = engine.start_session(student, TOPICS[skill][0], skill)
            first = engine.next_question(session)
            payload = json.loads(engine.db.execute("SELECT payload FROM learning_questions WHERE id=?", (first["id"],)).fetchone()["payload"])
            engine.submit_answer(session, first["id"], (payload["correct_index"] + 1) % len(payload["options"]))
            second = engine.next_question(session)
            next_payload = json.loads(engine.db.execute("SELECT payload FROM learning_questions WHERE id=?", (second["id"],)).fetchone()["payload"])
            result.update(status="ok", first=first, next_after_wrong=second,
                          first_source=payload.get("source", "gemini"),
                          next_source=next_payload.get("source", "gemini"),
                          same_concept=payload.get("concept") == next_payload.get("concept"),
                          different_question=payload["signature"] != next_payload["signature"])
        finally:
            engine.close()
    except Exception as error:
        # Do not persist raw API exceptions: URLs can contain credentials.
        result.update(status="failed", error_type=type(error).__name__, code=getattr(error, "code", None))
        if isinstance(error, ValueError):
            result["validation_error"] = str(error)[:200]
    result["elapsed_seconds"] = round(time.monotonic() - start, 2)
    return result


if __name__ == "__main__":
    skills = sys.argv[1:] or ["living_needs", "traffic"]
    if any(skill not in TOPICS for skill in skills):
        raise SystemExit("Desteklenmeyen konu.")
    results = [check(skill) for skill in skills]
    path = Path(__file__).with_name("api_test_report.json")
    previous = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    merged = {r["skill"]: r for r in previous}
    merged.update({r["skill"]: r for r in results})
    path.write_text(json.dumps(list(merged.values()), ensure_ascii=False, indent=2), encoding="utf-8")
    for result in results:
        print(json.dumps(result, ensure_ascii=True))
    raise SystemExit(int(any(r["status"] != "ok" for r in results)))
