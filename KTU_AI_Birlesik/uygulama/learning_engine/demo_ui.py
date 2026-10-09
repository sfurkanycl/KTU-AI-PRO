import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from pathlib import Path
from learning_engine.gemini_questions import CachedGeminiProvider
from learning_engine.visual_help import add_help_controls

from learning_engine.learning_core import LearningEngine
from learning_engine.school_content import TOPICS, draw_scene
from learning_engine.audio_service import warmup_audio, synthesize
from learning_engine.visual_help import AUDIO_POOL


class LearningDemo:
    def __init__(self, root):
        self.root = root
        self.root.title("Öğrenme Motoru - Demo")
        self.root.geometry("950x950")
        self.root.minsize(800, 800)

        # Keep the database beside this Python file.
        db_path = Path(__file__).resolve().parent / "learning.db"
        self.engine = LearningEngine(str(db_path),provider=CachedGeminiProvider(),)

        self.student_id = self.engine.create_student(
            "Demo öğrenci", 4
        )
        self.grade_var = tk.StringVar(value="4")

        self.session_id = None
        self.question = None
        self.option_buttons = []
        self.answer_submitted = False
        self.preload_future = None

        self.drawing_tool = "pen"
        self.last_point = None

        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.host = root
        viewport = tk.Canvas(root, highlightthickness=0)
        self.viewport = viewport
        scrollbar = ttk.Scrollbar(root, orient="vertical", command=viewport.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        viewport.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        viewport.configure(yscrollcommand=scrollbar.set)
        self.root = tk.Frame(viewport)
        page = viewport.create_window((0, 0), window=self.root, anchor="nw")
        self.root.bind("<Configure>", lambda event: viewport.configure(scrollregion=viewport.bbox("all")))
        viewport.bind("<Configure>", lambda event: viewport.itemconfigure(page, width=event.width))
        root.bind("<MouseWheel>", lambda event: viewport.yview_scroll(-int(event.delta / 120), "units"))
        self.show_menu()
        # Load the local voice while the child chooses a topic.
        AUDIO_POOL.submit(warmup_audio)

    def clear(self):
        if self.preload_future is not None:
            self.preload_future.cancel()
            self.preload_future = None
        self.viewport.yview_moveto(0)
        if getattr(self, "help_window", None) is not None and not self.help_window.closed:
            self.help_window.close()
        for widget in self.root.winfo_children():
            widget.destroy()

        self.option_buttons = []
        self.last_point = None

    def show_menu(self):
        self.clear()

        tk.Label(
            self.root,
            text="Öğrenme Molası",
            font=("Arial", 28, "bold"),
        ).pack(pady=(60, 15))

        tk.Label(
            self.root,
            text="Çalışmak istediğin konuyu seç.",
            font=("Arial", 15),
        ).pack(pady=10)

        tk.Label(self.root, text="Sınıfın").pack()
        ttk.Combobox(self.root, textvariable=self.grade_var,
                     values=["1", "2", "3", "4"], state="readonly", width=8).pack(pady=6)
        for skill, (subject, label) in TOPICS.items():
            tk.Button(self.root, text=label, font=("Arial", 15), width=38,
                      command=lambda s=skill: self.start(s)).pack(pady=7)

        tk.Label(
            self.root,
            text=(
                "Hedef: Altı soruyu yardımsız doğru cevaplamak.\n"
                "İşlem alanında fareyle yazı yazabilirsin."
            ),
            font=("Arial", 13),
            fg="#555555",
        ).pack(pady=25)

    def start(self, skill):
        try:
            self.student_id = self.engine.create_student("Demo öğrenci", int(self.grade_var.get()))
            self.engine.provider = CachedGeminiProvider()
            self.session_id = self.engine.start_session(
                student_id=self.student_id,
                subject=TOPICS[skill][0],
                skill=skill,
                target=6,
                max_attempts=18,
            )
            self.show_question()
        except Exception as error:
            messagebox.showerror("Hata", str(error))

    def show_question(self):
        try:
            question = self.engine.next_question(
                self.session_id
            )
            session = self.engine.get_session(
                self.session_id
            )
        except Exception as error:
            messagebox.showerror("Hata", str(error))
            return

        self.question = question
        self.answer_submitted = False
        self.clear()

        self.progress_label = tk.Label(
            self.root,
            text=(
                f"Tamamlanan soru: "
                f"{session['streak']}/{session['target']}"
                f"    |    Kalan deneme: "
                f"{session['max_attempts'] - session['attempts']}"
            ),
            font=("Arial", 12),
        )
        self.progress_label.pack(pady=(12, 5))

        if question.get("practice"):
            tk.Label(self.root, text="Aynı konudan bir alıştırma daha yapalım!",
                     font=("Arial", 12), fg="#805000").pack()

        if question.get("visual"):
            picture = tk.Canvas(self.root, width=740, height=170, highlightthickness=0)
            picture.pack(pady=5)
            draw_scene(picture, question["visual"])

        tk.Label(
            self.root,
            text=question["prompt"],
            font=("Arial", 21, "bold"),
            wraplength=740,
        ).pack(padx=20, pady=15)

        options_frame = tk.Frame(self.root)
        options_frame.pack()

        for index, option in enumerate(question["options"]):
            button = tk.Button(
                options_frame,
                text=option,
                font=("Arial", 15),
                width=24,
                wraplength=270,
                command=lambda selected=index: self.answer(
                    selected
                ),
            )
            button.grid(
                row=index // 2,
                column=index % 2,
                padx=8,
                pady=8,
            )
            self.option_buttons.append(button)

        self.hint_button = tk.Button(
            self.root,
            text="İpucu göster",
            font=("Arial", 12),
            command=self.show_hint,
        )
        self.hint_button.pack(pady=8)

        self.feedback = tk.Label(
            self.root,
            text="Bir seçeneğe tıkla veya işlem alanını kullan.",
            font=("Arial", 12),
            wraplength=740,
            justify="left",
            fg="#555555",
        )
        self.feedback.pack(
            fill=tk.X,
            padx=25,
            pady=10,
        )

        self.next_button = tk.Button(
            self.root,
            text="Sonraki soru",
            font=("Arial", 13),
            state=tk.DISABLED,
            command=self.show_question,
        )
        self.next_button.pack(pady=8)
        
        add_help_controls(self)
        self.create_scratchpad()
        # The first local general-lesson narration is the question itself.
        # Prepare it while the child reads, before the help button is pressed.
        if question.get("visual", {}).get("scene_id"):
            self.preload_future = AUDIO_POOL.submit(synthesize, question["prompt"])

    def show_hint(self):
        if self.answer_submitted:
            return

        try:
            result = self.engine.request_hint(
                self.session_id,
                self.question["id"],
            )
        except Exception as error:
            messagebox.showerror("Hata", str(error))
            return

        self.feedback.config(
            text=(
                result["hint"]
                + "\n\n"
                + result["example"]
                + "\n\nBu soru yardımlı cevap olarak sayılacak."
            ),
            fg="#805000",
        )
        self.hint_button.config(state=tk.DISABLED)

    def answer(self, selected_index):
        if self.answer_submitted:
            return

        try:
            result = self.engine.submit_answer(
                self.session_id,
                self.question["id"],
                selected_index,
            )
        except Exception as error:
            messagebox.showerror("Hata", str(error))
            return

        self.answer_submitted = True

        for button in self.option_buttons:
            button.config(state=tk.DISABLED)

        self.hint_button.config(state=tk.DISABLED)

        if result["correct"]:
            title = "Dogru!"
            color = "#137333"

            if not result["independent"]:
                title += (
                    " İpucu ile tamamladın.\n"
                    "Hedef için yardımsız doğru cevap gerekiyor."
                )
        else:
            title = "Birlikte tekrar deneyelim."
            color = "#a12828"

        text = title + "\n\n" + result["explanation"]

        if result["example"]:
            text += "\n\n" + result["example"]

        self.progress_label.config(
            text=(
                f"Yardımsız doğru sayısı: "
                f"{result['streak']}/{result['target']}"
                f"    |    Kalan deneme: "
                f"{result['attempts_remaining']}"
            )
        )

        if result["status"] == "completed":
            text += "\n\nOgrenme molası tamamlandı!"
            self.next_button.config(
                text="Konu seçimine dön",
                state=tk.NORMAL,
                command=self.show_menu,
            )

        elif result["status"] == "needs_parent":
            text += "\n\nVelinden destek iste."
            self.next_button.config(
                text="Konu seçimine dön",
                state=tk.NORMAL,
                command=self.show_menu,
            )

        else:
            self.next_button.config(
                text="Sonraki soru",
                state=tk.NORMAL,
                command=self.show_question,
            )

        self.feedback.config(text=text, fg=color)

    def create_scratchpad(self):
        self.drawing_tool = "pen"
        self.last_point = None

        panel = tk.LabelFrame(
            self.root,
            text="İşlem alanı - Fareyle çizebilirsin",
            font=("Arial", 12),
            padx=8,
            pady=8,
        )
        panel.pack(
            fill=tk.BOTH,
            expand=True,
            padx=20,
            pady=(5, 15),
        )

        toolbar = tk.Frame(panel)
        toolbar.pack(fill=tk.X, pady=(0, 6))

        tk.Button(
            toolbar,
            text="Kalem",
            command=lambda: self.set_drawing_tool("pen"),
        ).pack(side=tk.LEFT, padx=4)

        tk.Button(
            toolbar,
            text="Silgi",
            command=lambda: self.set_drawing_tool("eraser"),
        ).pack(side=tk.LEFT, padx=4)

        tk.Button(
            toolbar,
            text="Tümünü temizle",
            command=self.clear_scratchpad,
        ).pack(side=tk.LEFT, padx=4)

        self.tool_label = tk.Label(
            toolbar,
            text="Seçili: Kalem",
        )
        self.tool_label.pack(side=tk.RIGHT, padx=8)

        self.scratch_canvas = tk.Canvas(
            panel,
            bg="white",
            height=220,
            highlightthickness=1,
            highlightbackground="#bbbbbb",
            cursor="pencil",
        )
        self.scratch_canvas.pack(
            fill=tk.BOTH,
            expand=True,
        )

        self.scratch_canvas.bind(
            "<ButtonPress-1>",
            self.start_drawing,
        )
        self.scratch_canvas.bind(
            "<B1-Motion>",
            self.draw,
        )
        self.scratch_canvas.bind(
            "<ButtonRelease-1>",
            self.stop_drawing,
        )
        self.scratch_canvas.bind(
            "<Leave>",
            self.stop_drawing,
        )

    def set_drawing_tool(self, tool):
        self.drawing_tool = tool
        self.last_point = None

        if tool == "pen":
            self.tool_label.config(text="Seçili: Kalem")
            self.scratch_canvas.config(cursor="pencil")
        else:
            self.tool_label.config(text="Seçili: Silgi")
            self.scratch_canvas.config(cursor="crosshair")

    def start_drawing(self, event):
        self.last_point = (event.x, event.y)

        radius = (
            2 if self.drawing_tool == "pen" else 12
        )
        color = (
            "#202020"
            if self.drawing_tool == "pen"
            else "white"
        )

        self.scratch_canvas.create_oval(
            event.x - radius,
            event.y - radius,
            event.x + radius,
            event.y + radius,
            fill=color,
            outline=color,
        )

    def draw(self, event):
        if self.last_point is None:
            self.start_drawing(event)
            return

        previous_x, previous_y = self.last_point
        is_pen = self.drawing_tool == "pen"

        self.scratch_canvas.create_line(
            previous_x,
            previous_y,
            event.x,
            event.y,
            fill="#202020" if is_pen else "white",
            width=4 if is_pen else 24,
            capstyle=tk.ROUND,
            joinstyle=tk.ROUND,
        )

        self.last_point = (event.x, event.y)

    def stop_drawing(self, event):
        self.last_point = None

    def clear_scratchpad(self):
        self.scratch_canvas.delete("all")
        self.last_point = None

    def close(self):
        if getattr(self, "help_window", None) is not None and not self.help_window.closed:
            self.help_window.close()
        self.engine.close()
        self.host.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = LearningDemo(root)
    root.mainloop()
