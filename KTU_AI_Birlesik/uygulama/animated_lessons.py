"""Subject animations adapted from the contributed learning_visuals module.
Stages follow the current spoken lesson step rather than an independent clock.
"""
import math
from PyQt6.QtCore import Qt,QTimer,QRectF
from PyQt6.QtGui import QPainter,QPen,QColor,QFont
from PyQt6.QtWidgets import QWidget,QVBoxLayout
from learning_engine import school_content
from quiz_tools import LessonScene

def _correct_answer(question):
    try:return str(question['choices'][question['answer']])
    except (KeyError,IndexError,TypeError):return ''

class _AnimationOverlay(QWidget):
    """Sabit soru çiziminin üstünde kazanıma uygun hareketli vurgu üretir."""

    def __init__(self, question, visual, parent=None):
        super().__init__(parent)
        self.question = question
        self.visual = visual
        self.answer = _correct_answer(question)
        self.step = 0
        self.phase = 0
        self.frame = 0
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.timer = QTimer(self); self.timer.setInterval(55)
        self.timer.timeout.connect(self._advance); self.timer.start()

    def _advance(self):
        self.frame = (self.frame + 1) % 120
        self.phase = min(2, self.step)
        self.update()

    def set_step(self, step):
        self.step = int(step); self.frame = 0; self.phase = min(2, self.step); self.update()

    def _bubble(self, painter, rect, text, color="#4361ee"):
        painter.setPen(QPen(QColor(color), 3)); painter.setBrush(QColor(255, 255, 255, 225))
        painter.drawRoundedRect(rect, 13, 13)
        size = 8 if len(str(text)) > 58 else 10
        painter.setPen(QColor("#1d3557")); painter.setFont(QFont("Segoe UI", size, QFont.Weight.Bold))
        flags = int(Qt.AlignmentFlag.AlignCenter) | int(Qt.TextFlag.TextWordWrap)
        painter.drawText(rect, flags, text)

    def paintEvent(self, _event):
        painter = QPainter(self); painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        t = (self.frame % 60) / 59.0
        pulse = 1.0 + 0.12 * math.sin(self.frame * math.pi / 15)
        scene_id = self.visual.get("scene_id", "")
        math_kind = self.visual.get("math_kind", "")
        if scene_id.startswith("map_"):
            self._paint_direction(painter, scene_id[4:], t)
        elif scene_id:
            self._paint_scene_motion(painter, scene_id, t, pulse)
        elif self.visual.get("type") == "fractions":
            self._paint_fraction_motion(painter, t)
        elif math_kind:
            self._paint_math_motion(painter, math_kind, t, pulse)
        else:
            self._paint_concept_flow(painter, t)
        painter.end()

    def _paint_direction(self, painter, direction, t):
        cx, cy, distance = self.width() * .25, self.height() * .52, 82
        dx, dy = {"north": (0, -distance), "south": (0, distance),
                  "east": (distance, 0), "west": (-distance, 0)}.get(direction, (0, 0))
        travel = 0.0 if self.phase == 0 else t if self.phase == 1 else 1.0
        end_x, end_y = cx + dx * travel, cy + dy * travel
        painter.setPen(QPen(QColor("#ff6b35"), 7, Qt.PenStyle.SolidLine,
                            Qt.PenCapStyle.RoundCap))
        painter.drawLine(int(cx), int(cy), int(end_x), int(end_y))
        painter.setBrush(QColor("#ff6b35")); painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(end_x-7, end_y-7, 14, 14))
        direction_name = {"north": "kuzey", "south": "güney",
                          "east": "doğu", "west": "batı"}.get(direction, "doğru yön")
        label = ("Okul başlangıç noktası" if self.phase == 0 else
                 f"Okuldan {direction_name} yönüne ilerle" if self.phase == 1 else
                 f"Park okulun {direction_name} yönündedir")
        self._bubble(painter, QRectF(self.width()*.58, self.height()-58, self.width()*.34, 42), label, "#ff6b35")

    def _paint_scene_motion(self, painter, scene_id, t, pulse):
        item = school_content.SCENES.get(scene_id, {})
        kind = item.get("kind", "")
        cx, cy = self.width() * .25, self.height() * .52
        painter.setPen(QPen(QColor(42, 157, 143, 210), 4))
        if kind == "plant":
            if "light" in scene_id:
                for angle in range(0, 360, 45):
                    a = math.radians(angle); radius = 48 + 16*t
                    painter.drawLine(int(cx+math.cos(a)*38), int(cy-35+math.sin(a)*38),
                                     int(cx+math.cos(a)*radius), int(cy-35+math.sin(a)*radius))
                caption = "Işık bitkiye ulaşır"
            else:
                painter.setBrush(QColor("#4dabf7")); painter.setPen(Qt.PenStyle.NoPen)
                for offset in (-28, 0, 28):
                    y = 12 + ((t*120 + offset) % 105)
                    painter.drawEllipse(QRectF(cx+offset-5, y, 10, 15))
                caption = "Su köklere ulaşır"
        elif kind in ("fish", "bird"):
            painter.setBrush(QColor("#74c0fc" if kind == "fish" else "#f6bd60"))
            for index in range(4):
                y = cy + 48 - ((t*90 + index*24) % 100)
                painter.drawEllipse(QRectF(cx+35+index*13, y, 9, 9))
            caption = "Yaşam ihtiyacını gözle"
        elif kind in ("water", "milk", "ice", "stone", "balloon", "ball"):
            radius = 62 * pulse
            painter.drawEllipse(QRectF(cx-radius, cy-radius, radius*2, radius*2))
            caption = "Maddenin şeklini ve hareketini incele"
        elif kind.startswith("traffic_"):
            color = "#e03131" if kind.endswith("red") else "#2f9e44"
            painter.setPen(QPen(QColor(color), 5)); radius = 34*pulse
            y = cy-35 if kind.endswith("red") else cy+25
            painter.drawEllipse(QRectF(cx-radius, y-radius, radius*2, radius*2))
            caption = "Işığın verdiği mesaja dikkat et"
        elif kind == "crossing":
            x = cx-95 + 190*t
            painter.setBrush(QColor("#ff9f1c")); painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(x-10, cy-15, 20, 20))
            painter.setPen(QPen(QColor("#ff9f1c"), 5)); painter.drawLine(int(x), int(cy+5), int(x), int(cy+30))
            caption = "Yaya geçidinden güvenle geç"
        elif kind == "belt":
            y = cy-55 + 110*t; x = cx-45 + 90*t
            painter.setBrush(QColor("#ff9f1c")); painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QRectF(x-10, y-10, 20, 20)); caption = "Kemer yolcuyu sabit tutar"
        else:
            painter.drawEllipse(QRectF(cx-62*pulse, cy-62*pulse, 124*pulse, 124*pulse))
            caption = "Görseldeki önemli ayrıntıyı izle"
        if self.phase == 0:
            caption = "Görsel: " + str(item.get("label", caption))
        elif self.phase == 1:
            caption = str(item.get("explanation", caption))
        else:
            caption = "Doğru cevap: " + (self.answer or str(item.get("answer", "")))
        self._bubble(painter, QRectF(self.width()*.52, self.height()-68, self.width()*.45, 54), caption, "#2a9d8f")

    def _paint_fraction_motion(self, painter, t):
        row = self.phase % 2
        y = 10 + row * 50
        painter.setPen(QPen(QColor("#ff6b35"), 5)); painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(QRectF(92, y-7, max(120, (self.width()-112)*t), 48), 10, 10)
        a, b = self.visual.get("a", [0, 1]), self.visual.get("b", [0, 1])
        left, right = a[0]*b[1], b[0]*a[1]
        caption = ("Boyalı parçaları karşılaştır" if self.phase == 0 else
                   f"Çapraz çarp: {a[0]}×{b[1]}={left} ve {b[0]}×{a[1]}={right}" if self.phase == 1 else
                   "Doğru cevap: " + self.answer)
        self._bubble(painter, QRectF(self.width()*.48, self.height()-60, self.width()*.49, 46), caption, "#ff6b35")

    def _paint_math_motion(self, painter, kind, t, pulse):
        values = self.visual.get("values", [0, 1])
        if kind == "division":
            total, divisor = int(values[0]), max(1, int(values[1]))
            quotient = total // divisor
            tens = (quotient // 10) * 10
            first_part = tens * divisor
            remainder = total - first_part
            ones = remainder // divisor
            painter.setPen(QColor("#1d3557")); painter.setFont(QFont("Segoe UI", 23, QFont.Weight.Bold))
            painter.drawText(QRectF(35, 18, self.width()-70, 42), int(Qt.AlignmentFlag.AlignCenter),
                             f"{total} ÷ {divisor} = ?")
            painter.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
            if self.phase >= 1:
                painter.setPen(QColor("#4361ee"))
                painter.drawText(QRectF(65, 72, self.width()-130, 36),
                                 int(Qt.AlignmentFlag.AlignCenter), f"{total} = {first_part} + {remainder}")
                painter.drawText(QRectF(65, 112, self.width()-130, 36),
                                 int(Qt.AlignmentFlag.AlignCenter),
                                 f"{first_part} ÷ {divisor} = {tens}     ve     {remainder} ÷ {divisor} = {ones}")
            if self.phase >= 2:
                result_rect = QRectF(self.width()*.25, 158, self.width()*.5, 50)
                painter.setPen(QPen(QColor("#2a9d8f"), 3)); painter.setBrush(QColor("#d8f3dc"))
                painter.drawRoundedRect(result_rect, 13, 13)
                painter.setPen(QColor("#1b4332")); painter.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
                painter.drawText(result_rect, int(Qt.AlignmentFlag.AlignCenter),
                                 f"{tens} + {ones} = {quotient}")
            caption = ("Bölüneni kolay bölünen parçalara ayır" if self.phase == 0 else
                       "Her parçayı bölen sayıya ayrı ayrı böl" if self.phase == 1 else
                       f"Parça sonuçlarını topla: doğru cevap {self.answer or quotient}")
            if self.phase == 0:
                self._bubble(painter, QRectF(self.width()*.25, 88, self.width()*.5, 52), caption, "#ff6b35")
            return
        elif kind == "multiplication":
            a, b = map(int, values)
            visible_groups = max(1, min(b, 8, int(t * min(b, 8)) + 1))
            gap = max(68, min(105, (self.width()-80) / max(1, min(b, 8))))
            start_x = 40
            for group in range(visible_groups):
                x = start_x + group * gap
                painter.setPen(QPen(QColor("#7b61ff"), 3)); painter.setBrush(QColor(239, 236, 255, 210))
                painter.drawRoundedRect(QRectF(x, 45, gap-12, 95), 13, 13)
                painter.setPen(QColor("#2d1b69")); painter.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
                painter.drawText(QRectF(x, 62, gap-12, 30), int(Qt.AlignmentFlag.AlignCenter), str(a))
                painter.setFont(QFont("Segoe UI", 8)); painter.drawText(
                    QRectF(x, 93, gap-12, 28), int(Qt.AlignmentFlag.AlignCenter), "öğe")
            caption = (f"Her kutuda {a} öğe var" if self.phase == 0 else
                       f"Toplam {b} eş grup var" if self.phase == 1 else
                       f"{a}×{b}={a*b}; doğru cevap {self.answer or a*b}")
        else:
            x = 300 + (self.phase % 3) * 125
            painter.setPen(QPen(QColor("#ff6b35"), 5)); painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(QRectF(x-16*pulse, 20, 120*pulse, self.height()-52), 16, 16)
            a, b = map(int, values)
            caption = ("Sayıları basamaklarına ayır" if self.phase == 0 else
                       "Birlikten başla, eldeyi onluğa taşı" if self.phase == 1 else
                       f"{a}+{b}={a+b}; doğru cevap {self.answer or a+b}")
        self._bubble(painter, QRectF(self.width()*.49, self.height()-62, self.width()*.48, 48), caption, "#ff6b35")

    def _paint_concept_flow(self, painter, t):
        subject = str(self.visual.get("subject", ""))
        if subject == "Türkçe":
            self._paint_turkish(painter, t); return
        if subject == "İngilizce":
            self._paint_english(painter, t); return
        if subject == "Fen Bilimleri":
            self._paint_science(painter, t); return
        if subject == "Hayat Bilgisi":
            self._paint_life(painter, t); return
        if subject == "Sosyal Bilgiler":
            self._paint_social(painter, t, "Toplum • yer • zaman"); return
        if subject == "İnsan Hakları, Vatandaşlık ve Demokrasi":
            self._paint_social(painter, t, "Hak • sorumluluk • adalet"); return
        if subject == "Din Kültürü ve Ahlak Bilgisi":
            self._paint_values(painter, t); return
        if subject == "Trafik Güvenliği":
            self._paint_traffic_lesson(painter, t); return
        if subject == "Görsel Sanatlar":
            self._paint_art(painter, t); return
        if subject == "Müzik":
            self._paint_music(painter, t); return
        if subject == "Beden Eğitimi ve Oyun":
            self._paint_movement(painter, t); return
        self._paint_generic_flow(painter, t)

    def _short(self, value, limit=62):
        value = " ".join(str(value).split())
        return value[:limit] + ("…" if len(value) > limit else "")

    def _lesson_texts(self):
        question_text = str(self.question.get("text", ""))
        hint = str(self.question.get("hint", "İpucunu uygula"))
        explanation = str(self.question.get("explanation", hint))
        return self._short(question_text), self._short(hint), self._short(explanation), self.answer

    def _paint_generic_flow(self, painter, t):
        question_text, hint, _explanation, answer = self._lesson_texts()
        labels = [question_text, hint, "Doğru cevap: " + (answer or "sonucu kontrol et")]
        width = min(190.0, (self.width()-120)/3)
        y = self.height()/2-32
        for index, label in enumerate(labels):
            x = 35 + index * (width+28)
            active = index <= self.phase
            self._bubble(painter, QRectF(x, y, width, 64), label, "#2a9d8f" if active else "#b8c2d8")
            if index < 2:
                progress = t if index == min(1, self.phase) else (1 if index < self.phase else 0)
                painter.setPen(QPen(QColor("#ff9f1c"), 5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                painter.drawLine(int(x+width), int(y+32), int(x+width+28*progress), int(y+32))

    def _paint_turkish(self, painter, t):
        question, hint, explanation, answer = self._lesson_texts()
        self._bubble(painter, QRectF(40, 20, self.width()-80, 58), question, "#7b61ff")
        words = [word.strip(".,?!:;\"'") for word in str(self.question.get("text", "")).split()]
        words = [word for word in words if len(word) >= 4][:6] or ["anahtar", "sözcük"]
        gap = (self.width()-100) / max(1, len(words))
        for index, word in enumerate(words):
            active = index <= int(t * len(words))
            self._bubble(painter, QRectF(50+index*gap, 98, gap-10, 42), word,
                         "#e76f51" if active else "#c7d2e8")
        final = hint if self.phase == 1 else "Doğru cevap: " + answer if self.phase == 2 else "Cümledeki önemli sözcükleri bul"
        self._bubble(painter, QRectF(self.width()*.18, 166, self.width()*.64, 52), final, "#2a9d8f")

    def _paint_english(self, painter, t):
        question, hint, _explanation, answer = self._lesson_texts()
        self._bubble(painter, QRectF(55, 25, self.width()*.42, 72), question, "#4361ee")
        painter.setPen(QPen(QColor("#ff9f1c"), 6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(int(self.width()*.5), 62, int(self.width()*(.53+.18*t)), 62)
        target = hint if self.phase < 2 else "Doğru sözcük: " + answer
        self._bubble(painter, QRectF(self.width()*.58, 25, self.width()*.36, 72), target, "#ff9f1c")
        self._bubble(painter, QRectF(self.width()*.25, 140, self.width()*.5, 58),
                     "Sözcüğü görsel, anlam ve cümleyle eşleştir", "#2a9d8f")

    def _paint_science(self, painter, t):
        question, hint, explanation, answer = self._lesson_texts()
        labels = [("Gözlem", question), ("Bilimsel neden", explanation), ("Sonuç", answer)]
        colors = ["#4dabf7", "#7b61ff", "#2a9d8f"]
        width = (self.width()-130)/3
        for index, (title, text) in enumerate(labels):
            x = 35 + index*(width+30)
            visible = index <= self.phase
            self._bubble(painter, QRectF(x, 58, width, 112),
                         f"{title}\n{self._short(text, 52)}" if visible else title, colors[index])
            if index < 2:
                painter.setPen(QPen(QColor("#ff9f1c"), 5))
                length = 30 * (t if index == self.phase else 1 if index < self.phase else 0)
                painter.drawLine(int(x+width), 114, int(x+width+length), 114)
        self._bubble(painter, QRectF(self.width()*.28, 184, self.width()*.44, 38), hint, "#4dabf7")

    def _paint_life(self, painter, t):
        question, hint, explanation, answer = self._lesson_texts()
        self._bubble(painter, QRectF(35, 24, self.width()-70, 58), "Durum: " + question, "#ff9f1c")
        painter.setPen(QPen(QColor("#e03131"), 3)); painter.setBrush(QColor("#ffe3e3"))
        painter.drawRoundedRect(QRectF(70, 110, self.width()*.32, 70), 14, 14)
        painter.setPen(QColor("#9b2226")); painter.drawText(QRectF(70, 110, self.width()*.32, 70),
                         int(Qt.AlignmentFlag.AlignCenter), "Riskli / uygun olmayan seçim")
        good = QRectF(self.width()*.58, 110, self.width()*.34, 70)
        self._bubble(painter, good, "Doğru davranış: " + (answer if self.phase == 2 else hint), "#2a9d8f")
        x = self.width()*.48 + self.width()*.08*t
        painter.setBrush(QColor("#2a9d8f")); painter.setPen(Qt.PenStyle.NoPen); painter.drawEllipse(QRectF(x, 135, 14, 14))

    def _paint_social(self, painter, t, rule_title):
        question, hint, explanation, answer = self._lesson_texts()
        for index, x in enumerate((100, 155, 210)):
            painter.setBrush(QColor("#ffd6a5")); painter.setPen(QPen(QColor("#b66a1f"), 2))
            painter.drawEllipse(QRectF(x, 35+8*(index%2), 34, 34)); painter.drawLine(x+17, 69, x+17, 112)
        self._bubble(painter, QRectF(290, 24, self.width()-325, 58), question, "#b66a1f")
        self._bubble(painter, QRectF(290, 96, self.width()-325, 52),
                     rule_title + ": " + (hint if self.phase < 2 else explanation), "#7b61ff")
        self._bubble(painter, QRectF(self.width()*.28, 169, self.width()*.44, 50),
                     "Doğru cevap: " + answer if self.phase == 2 else "Bilgiyi toplum ve yaşamla ilişkilendir", "#2a9d8f")

    def _paint_values(self, painter, t):
        question, hint, explanation, answer = self._lesson_texts()
        cx, cy = self.width()*.22, 105
        radius = 42 + 8*math.sin(self.frame*math.pi/15)
        painter.setBrush(QColor("#ffd6e0")); painter.setPen(QPen(QColor("#c9184a"), 3))
        painter.drawEllipse(QRectF(cx-radius, cy-radius, radius*2, radius*2))
        painter.setPen(QColor("#8c1535")); painter.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        painter.drawText(QRectF(cx-radius, cy-radius, radius*2, radius*2), int(Qt.AlignmentFlag.AlignCenter), "Değer")
        self._bubble(painter, QRectF(self.width()*.38, 30, self.width()*.57, 62), question, "#c9184a")
        text = hint if self.phase == 0 else explanation if self.phase == 1 else "Doğru cevap: " + answer
        self._bubble(painter, QRectF(self.width()*.38, 112, self.width()*.57, 70), text, "#2a9d8f")

    def _paint_traffic_lesson(self, painter, t):
        question, hint, explanation, answer = self._lesson_texts()
        painter.setBrush(QColor("#56616b")); painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRect(QRectF(25, 84, self.width()-50, 86))
        painter.setPen(QPen(QColor("white"), 5, Qt.PenStyle.DashLine)); painter.drawLine(35, 127, self.width()-35, 127)
        x = 55 + (self.width()-140)*t
        painter.setBrush(QColor("#ff9f1c")); painter.setPen(Qt.PenStyle.NoPen); painter.drawRoundedRect(QRectF(x, 98, 62, 38), 8, 8)
        self._bubble(painter, QRectF(35, 18, self.width()-70, 50), question, "#e76f51")
        text = hint if self.phase < 2 else "Güvenli seçim: " + answer
        self._bubble(painter, QRectF(self.width()*.28, 180, self.width()*.44, 40), text, "#2a9d8f")

    def _paint_art(self, painter, t):
        _question, hint, explanation, answer = self._lesson_texts()
        colors = ["#ef476f", "#ffd166", "#06d6a0", "#118ab2"]
        for index, color in enumerate(colors):
            size = 42 + (12*t if index == self.phase else 0)
            x = 80 + index*(self.width()-180)/3
            painter.setBrush(QColor(color)); painter.setPen(Qt.PenStyle.NoPen)
            if index % 2: painter.drawEllipse(QRectF(x-size/2, 55-size/2, size, size))
            else: painter.drawRoundedRect(QRectF(x-size/2, 55-size/2, size, size), 8, 8)
        self._bubble(painter, QRectF(45, 105, self.width()-90, 52), hint if self.phase < 2 else explanation, "#7b61ff")
        self._bubble(painter, QRectF(self.width()*.28, 175, self.width()*.44, 42), "Doğru cevap: " + answer, "#2a9d8f")

    def _paint_music(self, painter, t):
        _question, hint, explanation, answer = self._lesson_texts()
        painter.setPen(QPen(QColor("#52606d"), 2))
        for y in range(55, 136, 20): painter.drawLine(55, y, self.width()-55, y)
        notes = [(.18, 115), (.36, 95), (.54, 75), (.72, 105), (.86, 65)]
        for index, (ratio, y) in enumerate(notes):
            bounce = 10*math.sin((t+index*.12)*math.pi*2)
            x = self.width()*ratio
            painter.setBrush(QColor("#7b61ff")); painter.setPen(QPen(QColor("#2d1b69"), 2))
            painter.drawEllipse(QRectF(x-10, y+bounce-7, 20, 14)); painter.drawLine(int(x+9), int(y+bounce), int(x+9), int(y+bounce-42))
        text = hint if self.phase == 0 else explanation if self.phase == 1 else "Doğru cevap: " + answer
        self._bubble(painter, QRectF(self.width()*.22, 168, self.width()*.56, 52), text, "#2a9d8f")

    def _paint_movement(self, painter, t):
        _question, hint, explanation, answer = self._lesson_texts()
        x = 70 + (self.width()-150)*t; y = 112
        painter.setPen(QPen(QColor("#4361ee"), 6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawEllipse(QRectF(x-13, y-55, 26, 26)); painter.drawLine(int(x), y-29, int(x), y+22)
        painter.drawLine(int(x), y-10, int(x-25), y+5); painter.drawLine(int(x), y-10, int(x+25), y-25)
        painter.drawLine(int(x), y+22, int(x-20), y+50); painter.drawLine(int(x), y+22, int(x+24), y+44)
        text = hint if self.phase == 0 else explanation if self.phase == 1 else "Doğru cevap: " + answer
        self._bubble(painter, QRectF(self.width()*.24, 174, self.width()*.52, 48), text, "#2a9d8f")

class AnimatedLessonScene(QWidget):
    def __init__(self,question,parent=None):
        super().__init__(parent)
        self.setMinimumHeight(280)
        from curriculum import subject_for_skill
        visual=dict(question.get('visual') or {})
        visual['subject']=(question.get('curriculum') or {}).get('subject') or subject_for_skill(question.get('skill',''),question.get('grade',3))
        # Math and fractions retain the exact existing lesson drawing.
        self.base=LessonScene(self)
        from animated_story import StoryScene
        self.motion=StoryScene(question,self)
        self.motion.setMinimumHeight(280)
        layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,0)
        layout.addWidget(self.base);layout.addWidget(self.motion)
    def show_step(self,lesson,step):
        exact=lesson.get('kind') in ('addition','fraction')
        self.base.setVisible(exact);self.motion.setVisible(not exact)
        if exact:self.base.show_step(lesson,step)
        self.motion.set_step(min(2,round(step*2/max(1,len(lesson['steps'])-1))))
    def hideEvent(self,event):
        self.motion.timer.stop();super().hideEvent(event)
    def showEvent(self,event):
        self.motion.timer.start();super().showEvent(event)
