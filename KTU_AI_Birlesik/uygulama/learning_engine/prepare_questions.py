import queue
import threading
import tkinter as tk
from tkinter import ttk
import os
import re

from learning_engine.gemini_questions import prepare_pack
from learning_engine.school_content import TOPICS


events = queue.Queue()
busy = False


def worker(grade, skill):
    try:
        prepare_pack(
            grade,
            skill,
            notify=lambda text: events.put(("message", text)),
        )

    except Exception as error:
        code = getattr(error, "code", None)
        detail = getattr(error, "message", None)

        if not detail:
            detail = str(error)

        detail = str(detail)

        # Hide configured API keys before displaying errors.
        for name in (
            "GEMINI_GENERATOR_KEY",
            "GEMINI_REVIEWER_KEY",
            "GEMINI_API_KEY",
            "GOOGLE_API_KEY",
        ):
            secret = os.getenv(name, "").strip()
            if secret:
                detail = detail.replace(secret, "[GIZLENDI]")

        detail = re.sub(
            r"AIza[A-Za-z0-9_-]+",
            "[GIZLENDI]",
            detail,
        )
        detail = re.sub(
            r"(?i)([?&]key=)[^&\s]+",
            r"\1[GIZLENDI]",
            detail,
        )

        text = f"Hata kodu: {code}\n{detail[:1800]}"
        events.put(("message", text))

        # Also show the sanitized detail in VS Code output.
        print(text)

    finally:
        events.put(("done", None))


def start():
    global busy

    if busy:
        return

    grade = int(grade_var.get())
    skill = next(skill for skill, (_, label) in TOPICS.items() if label == topic_var.get())

    busy = True
    start_button.config(state=tk.DISABLED)
    status_var.set("Baslatiliyor...")

    threading.Thread(
        target=worker,
        args=(grade, skill),
        daemon=True,
    ).start()


def poll():
    global busy

    try:
        while True:
            event, value = events.get_nowait()

            if event == "message":
                status_var.set(value)
            elif event == "done":
                busy = False
                start_button.config(state=tk.NORMAL)
    except queue.Empty:
        pass

    root.after(100, poll)


root = tk.Tk()
root.title("Gemini - Soru Paketi Hazırlama")
root.geometry("650x350")

tk.Label(
    root,
    text="Kontrollü soru paketi hazırla",
    font=("Arial", 19, "bold"),
).pack(pady=20)

grade_var = tk.StringVar(value="4")
topic_var = tk.StringVar(value=TOPICS["living_needs"][1])
status_var = tk.StringVar(value="Sınıf ve konu seç.")

tk.Label(root, text="Sınıf").pack()
ttk.Combobox(
    root,
    textvariable=grade_var,
    values=[str(number) for number in range(1, 5)],
    state="readonly",
).pack(pady=5)

tk.Label(root, text="Konu").pack()
ttk.Combobox(
    root,
    textvariable=topic_var,
    values=[label for _, label in TOPICS.values()],
    state="readonly",
    width=48,
).pack(pady=5)

start_button = tk.Button(
    root,
    text="Üret ve kontrol et",
    command=start,
)
start_button.pack(pady=15)

tk.Label(
    root,
    textvariable=status_var,
    wraplength=600,
).pack(padx=15, pady=10)

poll()
root.mainloop()
