"""Small, reviewed scene vocabulary shared by local questions and Gemini.

Drawings are rendered locally so a question never depends on an image URL.
"""
import random

TOPICS = {
    "addition": ("matematik", "Matematik - Toplama"),
    "fraction_compare": ("matematik", "Matematik - Kesirler"),
    "living_needs": ("fen", "Fen / Hayat Bilgisi - Canlılar"),
    "matter_states": ("fen", "Fen - Maddenin hâlleri"),
    "traffic": ("sosyal", "Sosyal / Hayat Bilgisi - Trafik"),
    "directions": ("sosyal", "Sosyal / Hayat Bilgisi - Yönler"),
}

# id, concept, drawing kind, label, question, answer, distractors, explanation
SCENES = {}


def scene(key, skill, concept, kind, label, question, answer, others, explanation):
    SCENES[key] = dict(skill=skill, concept=concept, kind=kind, label=label,
                       question=question, answer=answer, options=[answer, *others],
                       explanation=explanation)


scene("plant_water", "living_needs", "plant_needs", "plant", "Saksıdaki bitki",
      "Toprağı kuruyan bitkinin hangi ihtiyacını karşılamalıyız?", "Su",
      ["Oyuncak", "Defter", "Televizyon"], "Bitkiler yaşamak ve büyümek için suya ihtiyaç duyar.")
scene("plant_light", "living_needs", "plant_needs", "plant", "Pencere yanındaki bitki",
      "Bitkinin besin üretmesine hangisi yardım eder?", "Güneş ışığı",
      ["Oyuncak araba", "Kalem kutusu", "Televizyon"], "Yeşil bitkiler ışık yardımıyla besin üretir.")
scene("fish_water", "living_needs", "animal_needs", "fish", "Akvaryumdaki balık",
      "Bu hayvanın yaşadığı ortam hangisidir?", "Su",
      ["Kuru kum", "Kitaplık", "Okul çantası"], "Balıklar suda yaşar ve solungaçlarıyla sudaki oksijeni alır.")
scene("bird_food", "living_needs", "animal_needs", "bird", "Yemligin yanındaki kuş",
      "Kuşun enerji kazanması için hangisi gereklidir?", "Besin",
      ["Plastik oyuncak", "Defter", "Silgi"], "Hayvanlar enerji kazanmak için beslenir.")
for key, label, kind, answer in [
    ("ice", "Buz küpleri", "ice", "Katı"),
    ("stone", "Taş", "stone", "Katı"),
    ("water", "Bardaktaki su", "water", "Sıvı"),
    ("milk", "Bardaktaki süt", "milk", "Sıvı"),
    ("air", "Balonun içindeki hava", "balloon", "Gaz"),
    ("air_ball", "Topun içindeki hava", "ball", "Gaz"),
]:
    scene(key, "matter_states", {"Katı": "kati", "Sıvı": "sivi", "Gaz": "gaz"}[answer], kind, label,
          f"{label} maddenin hangi hâline örnektir?", answer,
          [x for x in ["Katı", "Sıvı", "Gaz"] if x != answer],
          {"Katı": "Katıların belirli bir şekli vardır.",
           "Sıvı": "Sıvılar akar ve bulundukları kabın şeklini alır.",
           "Gaz": "Hava gazdır; bulunduğu balonun veya topun içini doldurur."}[answer])
for color, label, answer in [("red", "Kırmızı", "Beklemeli"),
                             ("green", "Yeşil", "Kontrol ederek geçmeli")]:
    scene("traffic_" + color, "traffic", "pedestrian_signal", "traffic_" + color,
          f"Yaya ışığında {label.lower()} yanıyor",
          f"Yaya ışığı {label.lower()} yanıyor. Yaya ne yapmalı?", answer,
          ["Yola koşmalı", "Gözlerini kapatmali", "Yolda oynamalı"],
          "Yayalar kırmızıda bekler; yeşilde yolu kontrol ederek geçer.")
scene("crossing", "traffic", "safe_crossing", "crossing", "Yaya geçidi",
      "Karşı kaldirima geçmek için hangisini kullanmalıyız?", "Yaya geçidi",
      ["Araçların arası", "Yolun ortası", "Viraj"], "Yaya geçidi, güvenli geçiş için ayrılan yerdir; yine de yolu kontrol ederiz.")
scene("belt", "traffic", "vehicle_safety", "belt", "Araçta yolcu",
      "Araçtaki yolcu yolculuk boyunca ne takmalı?", "Emniyet kemeri",
      ["Okul çantası", "Oyuncak gözlük", "Yüzme simidi"], "Yolcuların emniyet kemeri takması güvenlik için gereklidir.")
for direction, label in [("north", "Kuzey"), ("south", "Güney"),
                         ("east", "Doğu"), ("west", "Batı")]:
    scene("map_" + direction, "directions", "map_directions", "map_" + direction,
          "Yön krokisi: okul ve park",
          "Krokide park, okulun hangi yönündedir?", label,
          [x for x in ["Kuzey", "Güney", "Doğu", "Batı"] if x != label],
          f"Krokide kuzey yukarı, güney aşağı, doğu sağ, batı soldur. Park okulun {label.lower()} yönündedir.")


def local_question(skill, used, concept=None):
    candidates = [(key, variant) for key, item in SCENES.items()
                  if item["skill"] == skill and (concept is None or item["concept"] == concept)
                  for variant in range(8)
                  if f"scene:{key}:{variant}" not in used]
    if not candidates and concept:
        return local_question(skill, used)
    if not candidates:
        raise ValueError("Bu konu için yeni soru kalmadi.")
    key, variant = random.choice(candidates)
    item = SCENES[key]
    intros = ["Resme bakalım. ", "Görseli incele. ", "Birlikte düşünelim. ",
              "Resimdeki durumu düşün. ", "Sence, ", "Dikkatle bak. ",
              "Küçük bir keşif yapalım. ", "Şimdi senin sıran. "]
    options = list(item["options"])
    random.shuffle(options)
    return dict(signature=f"scene:{key}:{variant}", prompt=intros[variant] + item["question"],
                options=options, correct_index=options.index(item["answer"]),
                hint="Resimdeki nesneyi ve sorunun ne istediğini düşün.",
                explanation=item["explanation"], example="Hatırlayalım: " + item["explanation"],
                visual={"scene_id": key}, concept=item["concept"], source="local")


def draw_scene(canvas, visual):
    """Render bounded, code-owned illustrations; model output is never executed."""
    if visual.get("math_kind"):
        draw_math(canvas, visual)
        return
    key = visual.get("scene_id", "")
    item = SCENES.get(key)
    if not item:
        return
    kind = item["kind"]
    canvas.create_rectangle(0, 0, 740, 170, fill="#edf7ff", outline="")
    canvas.create_text(530, 80, text=item["label"], width=260, font=("Arial", 16, "bold"), fill="#29445a")
    if kind == "plant":
        canvas.create_oval(40, 15, 85, 60, fill="#ffd45a", outline="")
        canvas.create_polygon(175, 100, 245, 100, 235, 150, 185, 150, fill="#cb7948")
        canvas.create_line(210, 105, 210, 45, fill="#3a8850", width=7)
        canvas.create_oval(165, 48, 211, 75, fill="#65b65d", outline="")
        canvas.create_oval(210, 30, 255, 60, fill="#65b65d", outline="")
    elif kind in ("fish", "bird"):
        canvas.create_oval(110, 45, 260, 125, fill="#ffb54e", outline="#986529", width=2)
        canvas.create_polygon(110, 85, 70, 50, 70, 120, fill="#ff984e")
        canvas.create_oval(228, 65, 237, 74, fill="#263847")
        if kind == "fish":
            canvas.create_rectangle(45, 15, 290, 150, outline="#4d9dd1", width=4)
            canvas.create_line(45, 35, 290, 35, fill="#4d9dd1", width=3)
        else:
            canvas.create_polygon(260, 75, 283, 85, 260, 93, fill="#e77c31")
            canvas.create_line(185, 125, 185, 148, fill="#986529", width=3)
    elif kind in ("water", "milk"):
        canvas.create_polygon(140, 25, 255, 25, 240, 145, 155, 145, fill="#d9f1fc", outline="#467993", width=3)
        canvas.create_polygon(148, 70, 247, 70, 238, 140, 157, 140, fill="#55bce8" if kind == "water" else "#fffdf0")
    elif kind in ("ice", "stone"):
        if kind == "ice":
            for x, y in [(115, 65), (185, 35), (210, 100)]:
                canvas.create_rectangle(x, y, x+52, y+45, fill="#95ddf5", outline="#489dbd", width=3)
        else:
            canvas.create_polygon(110, 110, 145, 45, 220, 30, 270, 100, 235, 145, fill="#a8a7ad", outline="#666878", width=3)
    elif kind in ("balloon", "ball"):
        canvas.create_oval(135, 20, 255, 135, fill="#f58f9f", outline="#c65e79", width=3)
        if kind == "balloon":
            canvas.create_line(195, 135, 200, 163, fill="#526a7a", width=2)
    elif kind.startswith("traffic_"):
        canvas.create_rectangle(170, 10, 235, 135, fill="#334553", outline="")
        for y, color in [(38, "red"), (105, "green")]:
            canvas.create_oval(185, y-18, 221, y+18, fill=color if kind.endswith(color) else "#63727c")
        canvas.create_line(203, 135, 203, 165, fill="#334553", width=8)
    elif kind == "crossing":
        canvas.create_rectangle(55, 25, 330, 145, fill="#626d78")
        for x in range(75, 320, 45):
            canvas.create_rectangle(x, 45, x+24, 125, fill="white", outline="")
    elif kind == "belt":
        canvas.create_rectangle(105, 20, 285, 155, fill="#7ca9d2", outline="")
        canvas.create_oval(180, 30, 215, 65, fill="#f1c49e")
        canvas.create_rectangle(173, 68, 223, 140, fill="#facd65", outline="")
        canvas.create_line(160, 25, 230, 140, fill="#334553", width=9)
    elif kind.startswith("map_"):
        canvas.create_line(80, 85, 320, 85, fill="#a5bfd1", width=2)
        canvas.create_line(200, 10, 200, 160, fill="#a5bfd1", width=2)
        for x,y,t in [(200, 12, "Kuzey"), (200, 158, "Güney"), (65, 85, "Batı"), (337,85,"Doğu")]:
            canvas.create_text(x, y, text=t, font=("Arial", 10, "bold"))
        canvas.create_rectangle(180, 65, 220, 105, fill="#facd65")
        canvas.create_text(200, 85, text="Okul")
        x,y = {"north": (200,40), "south": (200,130), "east": (280,85), "west": (120,85)}[kind[4:]]
        canvas.create_oval(x-22, y-15, x+22, y+15, fill="#87ce83", outline="")
        canvas.create_text(x, y, text="Park")


def draw_math(canvas, visual):
    canvas.create_rectangle(0, 0, 740, 170, fill="#fff8e8", outline="")
    values = visual.get("values", [])
    if len(values) != 2 or any(type(n) is not int or not 1 <= n <= 100 for n in values):
        return
    if visual["math_kind"] == "fraction":
        for x, n in zip((220, 520), values):
            box = (x-58, 15, x+58, 131)
            canvas.create_oval(*box, fill="#ffdc82", outline="#ba7b36", width=3)
            canvas.create_arc(*box, start=90, extent=-360/n, fill="#f58a6e", outline="", style="pieslice")
            import math
            for i in range(n):
                angle = math.radians(90-i*360/n)
                canvas.create_line(x, 73, x+58*math.cos(angle), 73-58*math.sin(angle), fill="#ba7b36")
            canvas.create_text(x, 151, text=f"1/{n}", font=("Arial", 15, "bold"))
    else:
        for x, n in zip((95, 425), values):
            tens, units = divmod(n, 10)
            for i in range(tens):
                left = x + (i % 5)*38
                top = 12 + (i // 5)*40
                canvas.create_rectangle(left, top, left+30, top+30, fill="#6aa5d9", outline="")
                canvas.create_text(left+15, top+15, text="10", fill="white")
            for i in range(units):
                left = x + (i % 5)*30
                top = 96 + (i // 5)*22
                canvas.create_oval(left, top, left+15, top+15, fill="#ef9f4a", outline="")
            canvas.create_text(x+75, 153, text=str(n), font=("Arial", 15, "bold"))
        canvas.create_text(360, 75, text="+", font=("Arial", 30, "bold"))
        canvas.create_text(700, 83, text="Mavi\nkutu:\n10\n\nTuruncu:\n1", font=("Arial", 10))
