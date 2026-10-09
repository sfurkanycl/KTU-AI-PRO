import io
import json
import math
import queue
import re
import threading
import tkinter as tk

from concurrent.futures import ThreadPoolExecutor
from tkinter import messagebox

import pygame

from learning_engine.audio_service import AudioUnavailable, synthesize
from learning_engine.learning_core import normalize_text
from learning_engine.lesson_service import prepare_question


AUDIO_POOL = ThreadPoolExecutor(max_workers=1)


def make_lesson(question):
    # General lessons prepared by lesson_service.
    if "_lesson" in question:
        return question["_lesson"]

    prompt = question["prompt"]

    addition = re.search(
        r"(\d+)\s*\+\s*(\d+)",
        prompt,
    )
    fractions = re.search(
        r"1/(\d+).*1/(\d+)",
        prompt,
    )

    if addition:
        a, b = map(int, addition.groups())

        if not (
            0 <= a <= 100
            and 0 <= b <= 100
        ):
            raise ValueError(
                "Nesneli toplama anlatımı "
                "0-100 arasındaki sayıları destekliyor."
            )

        units_a = a % 10
        units_b = b % 10
        units_total = units_a + units_b
        carry = units_total // 10
        units_result = units_total % 10

        tens_a = (a // 10) % 10
        tens_b = (b // 10) % 10
        tens_total = tens_a + tens_b + carry
        tens_result = tens_total % 10

        hundreds = (
            a // 100
            + b // 100
            + tens_total // 10
        )

        steps = [
            (
                "setup",
                f"{a} artı {b} işlemini birlikte yapalım. "
                "Sayıları alt alta yazıyoruz. "
                "Birler birlerin, onlar onların altında olmalı. "
                "Toplamaya sağdan, birler basamağından başlarız."
            ),
            (
                "units",
                f"Birler basamağına bakalım. "
                f"{units_a} artı {units_b}, "
                f"eşittir {units_total}."
            ),
        ]

        if carry:
            steps.append((
                "carry",
                f"{units_total} birlik, bir onluk ve "
                f"{units_result} birlik eder. "
                f"Birler basamağına {units_result} yazıyoruz. "
                "Bir onluğu, elde olarak onlar basamağına "
                "taşıyoruz. Elde, on tane birliğin "
                "oluşturduğu bir onluktur."
            ))
        else:
            steps.append((
                "carry",
                f"{units_total}, ondan küçük. "
                f"Birler basamağına {units_result} yazıyoruz. "
                "On tane birlik oluşmadığı için "
                "bu adımda elde yok."
            ))

        steps.append((
            "tens",
            (
                f"Şimdi onlar basamağı. "
                f"{tens_a} onluk artı {tens_b} onluk"
                + (
                    " ve birlerden gelen bir onluk"
                    if carry else ""
                )
                + f", toplam {tens_total} onluk eder."
            )
        ))

        if tens_total >= 10:
            steps.append((
                "hundreds",
                f"{tens_total} onluk, bir yüzlük ve "
                f"{tens_result} onluk eder. "
                f"Onlar basamağına {tens_result} yazıyoruz. "
                "Oluşan yüzlüğü yüzler basamağına taşıyoruz."
            ))

        if a >= 100 or b >= 100:
            steps.append((
                "hundreds",
                "Yüzler basamağındaki sayıları ve varsa "
                "onlardan gelen yüzlüğü topluyoruz. "
                f"Toplam {hundreds} yüzlük var."
            ))

        steps.extend([
            (
                "result",
                f"Basamakları birleştirelim. "
                f"{hundreds} yüzlük, {tens_result} onluk "
                f"ve {units_result} birlik. "
                f"Sonucumuz {a + b}. "
                f"{a} artı {b}, eşittir {a + b}."
            ),
            (
                "toys",
                f"Şimdi bunu oyuncaklarla düşünelim. "
                f"Senin {a} oyuncağın var. "
                f"Arkadaşın {b} oyuncak daha getiriyor. "
                "Her on oyuncağı bir pakete, "
                "her on paketi bir büyük kutuya koyabiliriz. "
                f"Sonunda {hundreds} büyük kutu, "
                f"{tens_result} paket ve "
                f"{units_result} tek oyuncak var. "
                f"Toplam {a + b} oyuncak!"
            ),
        ])

        return {
            "kind": "addition",
            "a": a,
            "b": b,
            "carry": carry,
            "units_total": units_total,
            "units_result": units_result,
            "tens_total": tens_total,
            "tens_result": tens_result,
            "hundreds": hundreds,
            "steps": steps,
        }

    if fractions:
        a, b = map(int, fractions.groups())

        if not (
            2 <= a <= 30
            and 2 <= b <= 30
        ):
            raise ValueError(
                "Pizza paydaları 2-30 arasında olmalı."
            )

        symbol = (
            ">" if a < b
            else "<" if a > b
            else "="
        )

        conclusion = (
            f"{min(a, b)} dilime ayrılan pizzanın "
            "bir dilimi daha büyük. "
            "Aynı pizzayı daha çok dilime ayırırsak "
            "dilimler küçülür."
            if a != b else
            "Pizzalar aynı boyda ve aynı sayıda "
            "dilime ayrıldı. Birer dilimleri eşit."
        )

        return {
            "kind": "fraction",
            "a": a,
            "b": b,
            "symbol": symbol,
            "steps": [
                (
                    "whole",
                    "İki arkadaşın aynı boyda birer pizzası var. "
                    "Kesirleri karşılaştırırken bütünlerin "
                    "aynı büyüklükte olması önemli."
                ),
                (
                    "slices",
                    f"Birinci pizzayı {a} eşit dilime, "
                    f"ikinci pizzayı {b} eşit dilime ayıralım."
                ),
                (
                    "highlight",
                    "Her pizzadan bir dilimi renklendirelim. "
                    "Renkli dilimlerden hangisi daha büyük?"
                ),
                ("result", conclusion),
            ],
        }

    raise ValueError(
        "Bu soru için önce genel anlatım hazırlanmalı."
    )


class VisualHelp:
    def __init__(self, parent, question):
        self.lesson = make_lesson(question)
        self.steps = self.lesson["steps"]

        self.step = 0
        self.closed = False
        self.playing = False
        self.audio_started = False
        self.current_audio = None
        self.audio_channel = None
        self.transition_job = None
        self.poll_job = None

        self.window = tk.Toplevel(parent)
        self.window.title("Adım adım öğrenelim")
        self.window.geometry("940x760")
        self.window.minsize(900, 720)
        self.window.configure(bg="#fff9ed")
        self.window.transient(parent.winfo_toplevel())
        self.window.protocol(
            "WM_DELETE_WINDOW",
            self.close,
        )

        tk.Label(
            self.window,
            text="Birlikte öğrenelim",
            font=("Arial", 25, "bold"),
            bg="#fff9ed",
            fg="#374785",
        ).pack(pady=12)

        self.progress = tk.Label(
            self.window,
            bg="#fff9ed",
            font=("Arial", 11),
        )
        self.progress.pack()

        self.canvas = tk.Canvas(
            self.window,
            width=900,
            height=380,
            bg="white",
            highlightthickness=0,
        )
        self.canvas.pack(padx=15, pady=10)

        self.caption = tk.Label(
            self.window,
            font=("Arial", 14),
            wraplength=870,
            bg="#fff9ed",
            justify="left",
        )
        self.caption.pack(padx=20, pady=10)

        self.status = tk.Label(
            self.window,
            bg="#fff9ed",
            fg="#666666",
            wraplength=870,
        )
        self.status.pack(pady=5)

        controls = tk.Frame(
            self.window,
            bg="#fff9ed",
        )
        controls.pack(pady=8)

        self.previous_button = tk.Button(
            controls,
            text="Önceki adım",
            command=self.previous,
        )
        self.previous_button.pack(
            side=tk.LEFT,
            padx=5,
        )

        tk.Button(
            controls,
            text="Tekrar dinle",
            command=self.replay,
        ).pack(side=tk.LEFT, padx=5)

        self.next_button = tk.Button(
            controls,
            text="Sonraki adım",
            command=self.advance,
        )
        self.next_button.pack(
            side=tk.LEFT,
            padx=5,
        )

        tk.Button(
            controls,
            text="Anlatımı kapat",
            command=self.close,
        ).pack(side=tk.LEFT, padx=5)

        self.auto = tk.BooleanVar(value=True)

        tk.Checkbutton(
            self.window,
            text="Ses bitince otomatik ilerle",
            variable=self.auto,
            command=self.auto_changed,
            bg="#fff9ed",
        ).pack()

        # Queue only the current scene. Preparing an entire old lesson used to
        # block the first audio of a newly opened lesson behind stale requests.
        self.futures = [None] * len(self.steps)

        self.window.grab_set()
        self.show_step()
        self.poll()

    def stop_audio(self):
        self.playing = False

        try:
            if pygame.mixer.get_init() and self.audio_channel is not None:
                self.audio_channel.stop()
        except pygame.error:
            pass

        self.audio_channel = None
        self.current_audio = None

    def play_audio(self, audio):
        # Sound owns decoded audio; each window stops only its own channel.
        for attempt in range(2):
            try:
                if not pygame.mixer.get_init():
                    pygame.mixer.init(frequency=24000, size=-16, channels=1)
                self.current_audio = pygame.mixer.Sound(file=io.BytesIO(audio))
                self.audio_channel = self.current_audio.play()
                if self.audio_channel is None:
                    raise pygame.error("Boş ses kanali bulunamadı.")
                return
            except pygame.error:
                self.stop_audio()
                if attempt:
                    raise
                # Reopen a disconnected audio device once.
                pygame.mixer.quit()

    def cancel_transition(self):
        if self.transition_job is not None:
            self.window.after_cancel(
                self.transition_job
            )
            self.transition_job = None

    def show_step(self):
        if self.closed:
            return

        self.cancel_transition()
        self.stop_audio()
        self.audio_started = False

        if self.futures[self.step] is None:
            self.futures[self.step] = AUDIO_POOL.submit(synthesize, self.steps[self.step][1])

        stage, spoken_text = self.steps[self.step]

        self.progress.config(
            text=(
                f"Adım {self.step + 1}/"
                f"{len(self.steps)}"
            )
        )

        # Preserve the same Turkish spelling on screen and in speech.
        self.caption.config(
            text=spoken_text
        )

        self.previous_button.config(
            state=(
                tk.NORMAL
                if self.step > 0
                else tk.DISABLED
            )
        )

        self.next_button.config(
            text=(
                "Soruya dön"
                if self.step == len(self.steps) - 1
                else "Sonraki adım"
            )
        )

        self.canvas.delete("all")

        kind = self.lesson["kind"]

        if kind == "addition":
            self.draw_addition(stage)
        elif kind == "fraction":
            self.draw_fraction(stage)
        else:
            self.draw_general()

        self.status.config(
            text=(
                "Görseli inceleyebilirsin; "
                "ses hazırlanıyor..."
            )
        )

    def draw_addition(self, stage):
        data = self.lesson
        a, b = data["a"], data["b"]

        if stage == "toys":
            self.draw_toys()
            return

        columns = [
            ("Yüzler", 270),
            ("Onlar", 360),
            ("Birler", 450),
        ]

        active = (
            "Birler" if stage in ("units", "carry")
            else "Onlar" if stage == "tens"
            else "Yüzler" if stage == "hundreds"
            else None
        )

        for title, x in columns:
            if title == active:
                self.canvas.create_rectangle(
                    x - 38,
                    65,
                    x + 38,
                    285,
                    fill="#fff0b3",
                    outline="",
                )

            self.canvas.create_text(
                x,
                35,
                text=title,
                font=("Arial", 14, "bold"),
            )

        for number, y in ((a, 130), (b, 190)):
            digits = [
                number // 100,
                (number // 10) % 10,
                number % 10,
            ]

            for index, (_, x) in enumerate(columns):
                if index == 0 and digits[index] == 0:
                    continue

                self.canvas.create_text(
                    x,
                    y,
                    text=str(digits[index]),
                    font=("Arial", 36, "bold"),
                )

        self.canvas.create_text(
            195,
            190,
            text="+",
            font=("Arial", 32),
        )

        self.canvas.create_line(
            215,
            225,
            495,
            225,
            width=3,
        )

        if stage in (
            "carry", "tens",
            "hundreds", "result",
        ):
            self.canvas.create_text(
                450,
                265,
                text=str(data["units_result"]),
                font=("Arial", 36, "bold"),
                fill="#137333",
            )

        if stage in ("hundreds", "result"):
            self.canvas.create_text(
                360,
                265,
                text=str(data["tens_result"]),
                font=("Arial", 36, "bold"),
                fill="#137333",
            )

        if stage == "result" and data["hundreds"]:
            self.canvas.create_text(
                270,
                265,
                text=str(data["hundreds"]),
                font=("Arial", 36, "bold"),
                fill="#137333",
            )

        if data["carry"] and stage in (
            "carry", "tens", "hundreds", "result"
        ):
            self.canvas.create_text(
                360,
                85,
                text="1",
                font=("Arial", 19, "bold"),
                fill="#d65f28",
            )

        if stage == "units":
            text = (
                f"{a % 10} + {b % 10}"
                f" = {data['units_total']}"
            )

        elif stage == "carry":
            text = (
                f"{data['units_total']} birlik\n"
                f"{data['carry']} onluk + "
                f"{data['units_result']} birlik"
            )

        elif stage == "tens":
            text = (
                f"{(a // 10) % 10} + "
                f"{(b // 10) % 10}"
                + (" + 1 elde" if data["carry"] else "")
                + f"\n= {data['tens_total']} onluk"
            )

        elif stage == "hundreds":
            text = (
                "10 onluk = 1 yüzlük\n"
                f"Toplam yüzlük: {data['hundreds']}"
            )

        elif stage == "result":
            text = f"{a} + {b} = {a + b}"

        else:
            text = "Basamakları hızala.\nSagdan başla."

        self.canvas.create_text(
            690,
            195,
            text=text,
            font=("Arial", 19, "bold"),
            fill="#374785",
            width=285,
        )

    def draw_toys(self):
        data = self.lesson

        self.canvas.create_text(
            450,
            30,
            text=(
                f"{data['a']} oyuncak + "
                f"{data['b']} oyuncak = "
                f"{data['a'] + data['b']} oyuncak"
            ),
            font=("Arial", 22, "bold"),
        )

        groups = [
            (
                "büyük kutu",
                data["hundreds"],
                100,
                "#8d75c4",
            ),
            (
                "paket",
                data["tens_result"],
                10,
                "#438ddd",
            ),
            (
                "tek oyuncak",
                data["units_result"],
                1,
                "#e68b32",
            ),
        ]

        for group_index, group in enumerate(groups):
            title, count, value, color = group
            left = 45 + group_index * 290

            self.canvas.create_text(
                left + 115,
                95,
                text=f"{count} {title}",
                font=("Arial", 16, "bold"),
            )

            for index in range(count):
                x = left + (index % 5) * 48
                y = 140 + (index // 5) * 65

                self.canvas.create_rectangle(
                    x,
                    y,
                    x + 38,
                    y + 40,
                    fill=color,
                    outline="#444444",
                    width=2,
                )

                self.canvas.create_rectangle(
                    x + 8,
                    y - 6,
                    x + 30,
                    y,
                    fill=color,
                    outline="#444444",
                )

                self.canvas.create_text(
                    x + 19,
                    y + 20,
                    text=str(value),
                    fill="white",
                    font=("Arial", 12, "bold"),
                )

            self.canvas.create_text(
                left + 115,
                315,
                text=f"Her biri {value} oyuncak",
                font=("Arial", 12),
            )

    def draw_fraction(self, stage):
        a = self.lesson["a"]
        b = self.lesson["b"]

        for cx, denominator in ((240, a), (660, b)):
            cy = 170
            radius = 105

            box = (
                cx - radius,
                cy - radius,
                cx + radius,
                cy + radius,
            )

            self.canvas.create_oval(
                cx - 113,
                cy - 113,
                cx + 113,
                cy + 113,
                fill="#cf8132",
                outline="#a85e20",
            )

            self.canvas.create_oval(
                *box,
                fill="#ffd875",
                outline="",
            )

            if stage in ("highlight", "result"):
                self.canvas.create_arc(
                    *box,
                    start=90,
                    extent=-360 / denominator,
                    style=tk.PIESLICE,
                    fill="#ff865c",
                    outline="",
                )

            for index in range(9):
                angle = math.radians(
                    index * 40 + 15
                )

                x = cx + math.cos(angle) * 65
                y = cy + math.sin(angle) * 65

                self.canvas.create_oval(
                    x - 6,
                    y - 6,
                    x + 6,
                    y + 6,
                    fill="#c94b36",
                    outline="",
                )

            if stage != "whole":
                for index in range(denominator):
                    angle = math.radians(
                        90 - index * 360 / denominator
                    )

                    self.canvas.create_line(
                        cx,
                        cy,
                        cx + radius * math.cos(angle),
                        cy - radius * math.sin(angle),
                        fill="#9b6426",
                        width=2,
                    )

            label = (
                "Aynı boy pizza"
                if stage == "whole"
                else f"{denominator} eşit dilim"
                if stage == "slices"
                else f"Bir dilim: 1/{denominator}"
            )

            self.canvas.create_text(
                cx,
                315,
                text=label,
                font=("Arial", 17, "bold"),
            )

        if stage == "result":
            self.canvas.create_text(
                450,
                170,
                text=self.lesson["symbol"],
                font=("Arial", 40, "bold"),
                fill="#137333",
            )

    def draw_general(self):
        title, narration = self.steps[self.step]

        self.canvas.create_rectangle(
            65,
            45,
            835,
            335,
            fill="#edf4ff",
            outline="#a7bfe8",
            width=2,
        )

        self.canvas.create_oval(
            90,
            65,
            150,
            125,
            fill="#438ddd",
            outline="",
        )

        self.canvas.create_text(
            120,
            95,
            text=str(self.step + 1),
            fill="white",
            font=("Arial", 24, "bold"),
        )

        self.canvas.create_text(
            180,
            95,
            text=title,
            anchor="w",
            width=600,
            font=("Arial", 20, "bold"),
            fill="#374785",
        )

        self.canvas.create_text(
            450,
            225,
            text=narration,
            width=690,
            font=("Arial", 16),
            fill="#333333",
        )

    def poll(self):
        if self.closed:
            return

        future = self.futures[self.step]

        if not self.audio_started and future.done():
            self.audio_started = True

            try:
                audio = future.result()

                self.play_audio(audio)

                self.playing = True
                next_step = self.step + 1
                if next_step < len(self.steps) and self.futures[next_step] is None:
                    self.futures[next_step] = AUDIO_POOL.submit(synthesize, self.steps[next_step][1])
                self.status.config(
                    text="Anlatımı dinle..."
                )

            except Exception as error:
                self.stop_audio()
                self.status.config(
                    text=(
                        str(error) if isinstance(error, AudioUnavailable) else
                        "Ses kullanılamadı. "
                        "Tekrar dinle veya Sonraki adım "
                        "ile devam edebilirsin."
                    )
                )

        if self.playing:
            try:
                if not pygame.mixer.get_init() or self.audio_channel is None:
                    raise pygame.error("Ses aygıtı bağlantısı kesildi.")
                busy = self.audio_channel.get_busy()
            except pygame.error:
                self.stop_audio()
                busy = True  # Failed playback must not advance the lesson.
                self.status.config(
                    text="Ses aygıtı kullanılamadı. Tekrar dinle ile yeniden deneyebilirsin."
                )
            if not busy:
                self.playing = False

                self.status.config(
                    text="Anlatım tamamlandı."
                )

                if (
                    self.auto.get()
                    and self.step < len(self.steps) - 1
                ):
                    self.transition_job = self.window.after(
                        200,
                        self.auto_advance,
                    )

        self.poll_job = self.window.after(
            100,
            self.poll,
        )

    def auto_changed(self):
        if not self.auto.get():
            self.cancel_transition()

    def auto_advance(self):
        self.transition_job = None

        if not self.closed and self.auto.get():
            self.advance()

    def replay(self):
        if self.closed:
            return

        self.cancel_transition()
        self.stop_audio()

        future = self.futures[self.step]

        if future.cancelled() or (
            future.done()
            and future.exception() is not None
        ):
            _, spoken_text = self.steps[self.step]

            self.futures[self.step] = AUDIO_POOL.submit(
                synthesize,
                spoken_text,
            )

        self.audio_started = False

        self.status.config(
            text="Ses hazırlanıyor veya yeniden oynatılıyor..."
        )

    def previous(self):
        if self.closed:
            return

        self.cancel_transition()

        if self.step > 0:
            self.step -= 1
            self.show_step()

    def advance(self):
        if self.closed:
            return

        self.cancel_transition()

        if self.step == len(self.steps) - 1:
            self.close()
            return

        self.step += 1
        self.show_step()

    def close(self):
        if self.closed:
            return

        self.closed = True
        self.cancel_transition()

        if self.poll_job is not None:
            self.window.after_cancel(self.poll_job)
            self.poll_job = None

        self.stop_audio()

        # Running requests may finish; queued ones are cancelled.
        for future in self.futures:
            if future is not None:
                future.cancel()

        self.window.destroy()


def add_help_controls(app):
    question_id = app.question["id"]
    events = queue.Queue()

    listening = False
    preparing = False
    help_window = None

    frame = tk.Frame(app.root)
    frame.pack(pady=5)

    status = tk.Label(
        frame,
        wraplength=700,
    )

    def is_current():
        try:
            return (
                bool(frame.winfo_exists())
                and app.question["id"] == question_id
            )
        except tk.TclError:
            return False

    def open_help():
        nonlocal help_window, preparing

        if (
            not is_current()
            or app.answer_submitted
            or preparing
        ):
            return

        if (
            help_window is not None
            and not help_window.closed
        ):
            help_window.window.lift()
            return

        try:
            app.engine.request_hint(
                app.session_id,
                question_id,
            )

            app.hint_button.config(
                state=tk.DISABLED
            )

            app.feedback.config(
                text=(
                    "Anlatım hazırlanıyor. "
                    "Bu cevap yardımlı sayılacak."
                ),
                fg="#805000",
            )

            # Read SQLite on its owning UI thread.
            row = app.engine.db.execute(
                """SELECT payload
                   FROM learning_questions
                   WHERE id=?""",
                (question_id,),
            ).fetchone()

            question = dict(app.question)

            if row is not None:
                payload = json.loads(row["payload"])

                for field in (
                    "hint",
                    "explanation",
                    "example",
                ):
                    question[field] = payload.get(field)

            preparing = True

            status.config(
                text="Anlatım planı hazırlanıyor..."
            )

            def build():
                try:
                    prepared = prepare_question(question)
                    events.put(("lesson", prepared))

                except Exception:
                    events.put((
                        "lesson_error",
                        "Anlatım hazırlanamadı.",
                    ))

            threading.Thread(
                target=build,
                daemon=True,
            ).start()

        except Exception as error:
            preparing = False

            messagebox.showerror(
                "Hata",
                str(error),
                parent=app.root,
            )

    def recognize():
        try:
            import speech_recognition as sr

            recognizer = sr.Recognizer()
            recognizer.operation_timeout = 15

            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(
                    source,
                    duration=0.5,
                )

                events.put((
                    "status",
                    "Şimdi 'Anlamadım' veya "
                    "'Anlatır misin' de.",
                ))

                audio = recognizer.listen(
                    source,
                    timeout=6,
                    phrase_time_limit=5,
                )

            text = recognizer.recognize_google(
                audio,
                language="tr-TR",
            )

            normalized = normalize_text(text).lower()

            triggers = (
                "anlamadim",
                "anlat",
                "yardim",
                "acikla",
                "anlayamadim",
            )

            if any(
                word in normalized
                for word in triggers
            ):
                events.put(("help", None))

            else:
                events.put((
                    "status",
                    "Yardım isteği algılanmadı. "
                    "Tekrar deneyebilirsin.",
                ))

        except Exception:
            events.put((
                "status",
                "Ses veya mikrofon kullanılamadı. "
                "Anlatım butonuna tıklayabilirsin.",
            ))

        finally:
            events.put(("done", None))

    def start_listening():
        nonlocal listening

        if (
            listening
            or preparing
            or app.answer_submitted
        ):
            return

        listening = True

        status.config(
            text="Mikrofon hazırlanıyor..."
        )

        threading.Thread(
            target=recognize,
            daemon=True,
        ).start()

    def poll():
        nonlocal listening, preparing, help_window

        if not is_current():
            return

        try:
            while True:
                event, value = events.get_nowait()

                if event == "status":
                    status.config(text=value)

                elif event == "help":
                    if not app.answer_submitted:
                        open_help()

                elif event == "lesson":
                    preparing = False

                    if not app.answer_submitted:
                        try:
                            help_window = VisualHelp(
                                app.root,
                                value,
                            )
                            app.help_window = help_window

                            status.config(
                                text="Anlatım hazır."
                            )

                        except Exception as error:
                            status.config(
                                text=(
                                    "Anlatım açılamadı: "
                                    + str(error)
                                )
                            )

                elif event == "lesson_error":
                    preparing = False
                    status.config(text=value)

                elif event == "done":
                    listening = False

        except queue.Empty:
            pass

        disabled = (
            listening
            or preparing
            or app.answer_submitted
        )

        voice_button.config(
            state=(
                tk.DISABLED
                if disabled
                else tk.NORMAL
            )
        )

        explain_button.config(
            state=(
                tk.DISABLED
                if disabled
                else tk.NORMAL
            )
        )

        app.root.after(100, poll)

    explain_button = tk.Button(
        frame,
        text="Anlamadım - Adım adım anlat",
        command=open_help,
    )
    explain_button.pack(pady=3)

    voice_button = tk.Button(
        frame,
        text="Konuşarak yardım iste",
        command=start_listening,
    )
    voice_button.pack(pady=3)

    status.pack(pady=3)
    poll()
