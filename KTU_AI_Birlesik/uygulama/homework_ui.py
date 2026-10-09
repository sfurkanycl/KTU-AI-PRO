# -*- coding: utf-8 -*-
"""
Ana Uygulama: Eğlenceli (gamified) eğitim uygulaması
Hedef Kitle: 6-10 yaş arası öğrenciler, veliler ve öğretmenler
Tüm arayüz metinleri Türkçedir ve Türkçe karakterleri (ç, ğ, ı, ö, ş, ü, İ, Ç, Ğ, Ö, Ş, Ü)
düzgün görüntülemek için UTF-8 ve sistem Türkçe fontları kullanılır.

Bağımlılıklar: PyQt6
    pip install PyQt6
"""

import os
import sys
import random

from PyQt6.QtCore import (
    Qt,
    QSize,
    QRect,
    QEasingCurve,
    QVariantAnimation,
    QAbstractAnimation,
    QPropertyAnimation,
    QTimer,
    QPoint,
    QPointF,
    pyqtProperty,
    pyqtSignal,
    QObject,
    QThread,
    QCoreApplication,
    QEvent,
)
from PyQt6.QtGui import (
    QFont,
    QFontDatabase,
    QIcon,
    QPainter,
    QBrush,
    QColor,
    QPen,
    QPixmap,
    QPainterPath,
    QBitmap,
    QImage,
    QLinearGradient,
    QRadialGradient,
    QRegion,
)
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QStackedWidget,
    QFrame,
    QSizePolicy,
    QMessageBox,
    QDialog,
    QComboBox,
    QSpinBox,
    QCheckBox,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QGraphicsEffect,
    QToolButton,
)


# ---------------------------------------------------------------------------
# Yardımcı: Türkçe karakterlerin sorunsuz görünmesi için uygun font seçimi
# ---------------------------------------------------------------------------
def turkce_font(boyut: int = 14, kalin: bool = False) -> QFont:
    """Sistemde yüklü olan Türkçe dostu fontlardan birini seçer."""
    aday_fontlar = [
        "Noto Sans",
        "Noto Sans Turkish",
        "Arial Unicode MS",
        "Segoe UI",
        "Calibri",
        "DejaVu Sans",
        "Ubuntu",
        "FreeSans",
        "Helvetica",
    ]
    aileler = QFontDatabase.families()
    secilen = None
    for ad in aday_fontlar:
        if ad in aileler:
            secilen = ad
            break
    if secilen is None:
        font = QFont()
    else:
        font = QFont(secilen)
    font.setPointSize(boyut)
    font.setBold(kalin)
    return font


# ---------------------------------------------------------------------------
# Global QSS: Yumuşak pastel renkler, yuvarlak köşeler, modern görünüm
# ---------------------------------------------------------------------------
GLOBAL_QSS = """
/* Uygulama genel arka plan */
QWidget {
    font-family: "Noto Sans", "Segoe UI", "Calibri", "DejaVu Sans", sans-serif;
    color: #2d3748;
}

#AnaPencere {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                 stop:0 #f7fbe9, stop:0.5 #e9f7fb, stop:1 #e8f9f1);
    border-radius: 24px;
}

/* Ortak başlık etiketleri */
QLabel#Baslik {
    background-color: #ffffff;
    border: 2px solid #bde0fe;
    border-radius: 18px;
    padding: 14px 20px;
    font-size: 20px;
    font-weight: bold;
    color: #1d3557;
}

QLabel#AltBaslik {
    font-size: 14px;
    color: #4a5568;
    padding: 4px;
}

QLabel#MascotAlani {
    background-color: #fff8d7;
    border: 3px dashed #f3c969;
    border-radius: 24px;
    min-height: 140px;
    qproperty-alignment: AlignCenter;
    font-size: 64px;
}

QLabel#SoruAlani {
    background-color: #ffffff;
    border: 2px solid #a8dadc;
    border-radius: 20px;
    padding: 18px;
    font-size: 22px;
    font-weight: bold;
    color: #1d3557;
    min-height: 90px;
    qproperty-alignment: AlignCenter;
}

/* Rol seçim kartları (giriş ekranı) */
QFrame#RolKarti {
    background-color: #ffffff;
    border-radius: 24px;
    border: 2px solid #e2e8f0;
}
QFrame#RolKarti:hover {
    border: 2px solid #90cdf4;
}

QPushButton#RolButon {
    background-color: #a8dadc;
    border: none;
    border-radius: 16px;
    padding: 12px 18px;
    font-size: 16px;
    font-weight: bold;
    color: #0f3d3e;
    min-height: 42px;
}
QPushButton#RolButon:hover  { background-color: #7fc7c9; }
QPushButton#RolButon:pressed{ background-color: #62b4b7; }

QPushButton#RolButonVeli     { background-color: #ffd6a5; color: #6b3e02; }
QPushButton#RolButonVeli:hover  { background-color: #ffbf78; }
QPushButton#RolButonOgretmen{ background-color: #bdb2ff; color: #2d1b69; }
QPushButton#RolButonOgretmen:hover { background-color: #a495ff; }
QPushButton#RolButonOgrenci { background-color: #caffbf; color: #1b4332; }
QPushButton#RolButonOgrenci:hover  { background-color: #9ef594; }

/* Cevap butonları */
QPushButton#CevapButon {
    background-color: #ffffff;
    border: 2px solid #bde0fe;
    border-radius: 18px;
    padding: 14px;
    font-size: 15px;
    color: #1d3557;
    min-height: 64px;
    text-align: left;
    padding-left: 20px;
}
QPushButton#CevapButon:hover {
    background-color: #e0f2fe;
    border: 2px solid #7dd3fc;
}
QPushButton#CevapButon:pressed {
    background-color: #bae6fd;
}
QPushButton#CevapButon[dogru="true"] {
    background-color: #b7efc5;
    border: 2px solid #52b788;
    color: #1b4332;
}
QPushButton#CevapButon[yanlis="true"] {
    background-color: #ffccd5;
    border: 2px solid #ef476f;
    color: #590d22;
}

/* Alt bar butonları */
QPushButton#AltButon {
    background-color: #ffffff;
    border: 2px solid #cbd5e0;
    border-radius: 14px;
    padding: 8px 16px;
    font-size: 13px;
    color: #2d3748;
    min-height: 36px;
}
QPushButton#AltButon:hover {
    background-color: #edf2f7;
    border: 2px solid #90cdf4;
}

QFrame#AltCubuk {
    background-color: rgba(255, 255, 255, 180);
    border-top: 1px solid #e2e8f0;
    border-bottom-left-radius: 24px;
    border-bottom-right-radius: 24px;
}

/* Ayarlardaki spinbox / combobox */
QComboBox, QSpinBox {
    padding: 6px 10px;
    border: 1px solid #cbd5e0;
    border-radius: 8px;
    background-color: #ffffff;
    min-height: 24px;
}

QCheckBox { spacing: 8px; }
"""


# ---------------------------------------------------------------------------
# Görsel yollarını çözümle + yardımcı widget'lar
# ---------------------------------------------------------------------------
def _klasor() -> str:
    """Bu dosyanın bulunduğu klasörü döndürür (görsellerle aynı yer)."""
    return os.path.dirname(os.path.abspath(__file__))


def gorsel_yol(ad: str) -> str:
    """Klasördeki görselin tam yolunu döndürür.
    Aşağıdaki durumlarla başa çıkmak için dosya listesi üzerinden arama yapar:
      - macOS HFS+/APFS Türkçe karakterleri NFD biçiminde saklayabilir
      - Bazı görseller 'ğ' yerine 'g' gibi alternatif yazımlarla kaydedilmiş olabilir
    Arama NFC normalize edilmiş isimler üzerinden yapılır ve bulunamazsa
    'ğ' ↔ 'g', 'ı' ↔ 'i' gibi Türkçe karakter varyasyonları da denenir.
    """
    import unicodedata
    klasor = _klasor()

    def varyasyonlar(isim: str):
        """Bir ismin olası yazım varyasyonlarını verir (NFC olarak)."""
        isim = unicodedata.normalize("NFC", isim)
        sonuclar = {isim}
        # Türkçe karakterlerin ASCII benzerleri
        ikameler = [
            ("ğ", "g"), ("Ğ", "G"),
            ("ı", "i"), ("İ", "I"),
            ("ö", "o"), ("Ö", "O"),
            ("ü", "u"), ("Ü", "U"),
            ("ş", "s"), ("Ş", "S"),
            ("ç", "c"), ("Ç", "C"),
        ]
        # Basit tek-ikame varyasyonları (yeterli)
        for eski, yeni in ikameler:
            if eski in isim:
                sonuclar.add(isim.replace(eski, yeni))
            if yeni in isim:
                # Tersini de dene: ASCII g -> ğ gibi
                for ters_eski, ters_yeni in ikameler:
                    if ters_yeni == yeni:
                        continue
                sonuclar.add(isim.replace(yeni, eski))
        return sonuclar

    hedef_varyasyonlar = varyasyonlar(ad)
    try:
        for dosya in os.listdir(klasor):
            ndosya = unicodedata.normalize("NFC", dosya)
            if ndosya in hedef_varyasyonlar or ad == dosya:
                return os.path.join(klasor, dosya)
    except OSError:
        pass
    # Yedek: doğrudan birleştir (bazı sistemler NFC kullanır)
    return os.path.join(klasor, ad)


def yuvarlak_pixmap(yol: str, cap: int, arka_renk: str | None = None,
                    padding: int = 0, arka_renk_2: str | None = None) -> QPixmap:
    """Verilen görseli en-boy oranını koruyarak CAP x CAP boyutunda yuvarlak (daire) bir
    pixmap haline getirir. Eğer ARKA_RENK belirtilmişse dairenin içi o renkle doldurulur
    (isteğe bağlı ikinci renk belirtilirse dairesel gradyan). Görsel bu arka planın
    üstüne CENTER-CENTER sığdırılır (tamamen doldurmak yerine padding bırakılır).

    macOS güvenliği: QBitmap maskesi yerine QPainterPath kırpma kullanılır.
    """
    # 0'dan küçük veya negatif boyutlarla QImage/QPixmap oluşturmak
    # macOS CoreGraphics patlar — parametreleri korumalı al
    cap = max(8, int(cap))
    padding = max(0, int(padding))

    kaynak = QPixmap(yol)
    cikis = QPixmap(cap, cap)
    cikis.fill(Qt.GlobalColor.transparent)

    p = QPainter(cikis)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
    p.setRenderHint(QPainter.RenderHint.LosslessImageRendering, True)

    # 1) Arka plan (dolgu / gradyan) — QPainterPath kırpma ile
    yol_path = QPainterPath()
    yol_path.addEllipse(0, 0, cap, cap)
    p.setClipPath(yol_path)
    if arka_renk:
        if arka_renk_2:
            gradient = QRadialGradient(
                float(cap) / 2.0, float(cap) / 2.0, float(cap) / 2.0,
                float(cap) / 2.0, float(cap) / 3.0,
            )
            gradient.setColorAt(0.0, QColor(arka_renk).lighter(112))
            gradient.setColorAt(1.0, QColor(arka_renk_2).darker(105))
            p.fillRect(0, 0, cap, cap, QBrush(gradient))
        else:
            p.fillRect(0, 0, cap, cap, QBrush(QColor(arka_renk)))

    # 2) Kaynak null ise sadece arka plan döner
    if not kaynak.isNull():
        # Kaynağı merkeze al, karesel kırp + küçült
        kaynak_boyut = max(1, min(kaynak.width(), kaynak.height()))
        kx = max(0, (kaynak.width() - kaynak_boyut) // 2)
        ky = max(0, (kaynak.height() - kaynak_boyut) // 2)
        hedef_boyut = max(1, cap - 2 * padding)
        kare = kaynak.copy(kx, ky, kaynak_boyut, kaynak_boyut).scaled(
            hedef_boyut, hedef_boyut,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        # Ortala
        cx = (cap - kare.width()) // 2
        cy = (cap - kare.height()) // 2 + max(0, padding // 8)
        p.drawPixmap(cx, cy, kare)

    # Painter'ı düzgün kapat (macOS bu sırayı zorlar — leak olursa crash olur)
    p.end()
    return cikis


def olcekli_pixmap(yol: str, maks_genislik: int, maks_yukseklik: int) -> QPixmap:
    """Görseli oran koruyarak verilen sınırlar içinde ölçekler."""
    kaynak = QPixmap(yol)
    if kaynak.isNull():
        return QPixmap()
    return kaynak.scaled(
        maks_genislik, maks_yukseklik,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )


# ---------------------------------------------------------------------------
# Hover animasyonlu kart (fare üstüne gelince hafif yukarı kalkar + gölge büyür)
# ---------------------------------------------------------------------------
class AnimasyonluKart(QFrame):
    """
    QFrame tabanlı, hover olunca minik yukarı kalkma + gölge büyütme efekti.
    macOS'ta QGraphicsDropShadowEffect + transparan pencere birleşimi
    EXC_BAD_ACCESS (SIGSEGV) yapabildiği için gölgeyi QPainter ile
    paintEvent içinde ELLE çiziyoruz. Hiç QGraphicsEffect kullanmıyoruz.
    """

    def __init__(self, parent=None, lift_miktari: int = 8, anim_ms: int = 160):
        super().__init__(parent)
        self._lift = max(0, int(lift_miktari))
        # Frame süresi: ~16 ms -> 60 FPS
        self._frame_ms = 16
        # Toplam frame sayısı (tam sayıya yuvarla)
        self._total_frames = max(1, int(round(anim_ms / self._frame_ms)))
        self._dur = 0  # 0..100
        self._hedef = 0  # 0 veya 100
        self._frame = 0  # 0.._total_frames — mevcut animasyon pozisyonu
        self._tween_timer = None  # QTimer (None ise animasyon çalışmıyor)
        # macOS emniyeti: QGraphicsDropShadowEffect KULLANILMIYOR
        self.setAttribute(Qt.WidgetAttribute.WA_Hover)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    # Qt animasyonu için pyqtProperty (geriye dönük uyumluluk — kullanılmıyor
    # ama herhangi bir kod yuzde'yi okursa çalışır)
    def _get_yuzde(self) -> int:
        return self._dur

    def _set_yuzde(self, v: int):
        # Doğrudan yüzde atamak dışarıdan çağrılırsa yumuşatmasın (frame tween)
        v = max(0, min(100, int(v)))
        try:
            ml, mt, mr, mb = self.getContentsMargins()
            if not hasattr(self, "_base_mt"):
                self._base_mt = mt
                self._base_ml = ml
                self._base_mr = mr
                self._base_mb = mb
            kalkis = int(self._base_mt - int(self._lift * (v / 100.0)))
            if self.layout() is not None or self.parentWidget() is not None:
                self.setContentsMargins(
                    self._base_ml, kalkis, self._base_mr, self._base_mb
                )
            self.update()
        except Exception:
            pass

    yuzde = pyqtProperty(int, _get_yuzde, _set_yuzde)

    # QTimer tween — OutCubic eğrisi ile her karede yuzde'yi ilerlet
    def _tick(self):
        """Her 16ms'de bir çalışır, bir kare ilerler."""
        if self._tween_timer is None:
            return
        try:
            if self._hedef == 100:
                self._frame = min(self._total_frames, self._frame + 1)
            else:
                self._frame = max(0, self._frame - 1)
            # OutCubic: 1 - (1 - t)^3
            t = self._frame / float(self._total_frames)
            eased = 1.0 - pow(1.0 - t, 3.0)
            self._dur = int(round(eased * 100.0))
            # Margin/shadow güncelle
            ml, mt, mr, mb = self.getContentsMargins()
            if not hasattr(self, "_base_mt"):
                self._base_mt = mt
                self._base_ml = ml
                self._base_mr = mr
                self._base_mb = mb
            kalkis = int(self._base_mt - int(self._lift * eased))
            if self.layout() is not None or self.parentWidget() is not None:
                self.setContentsMargins(
                    self._base_ml, kalkis, self._base_mr, self._base_mb
                )
            self.update()
            # Animasyon bitti mi?
            if (self._hedef == 100 and self._frame >= self._total_frames) or \
               (self._hedef == 0 and self._frame <= 0):
                self._tween_timer.stop()
                self._tween_timer.setParent(None)
                self._tween_timer = None
        except Exception:
            # Hata olursa timer'ı durdur (uygulama çökmesin)
            try:
                if self._tween_timer is not None:
                    self._tween_timer.stop()
                    self._tween_timer.setParent(None)
            except Exception:
                pass
            self._tween_timer = None

    # --- QSS dynamic property refresh
    def _qss_ozellik_ata(self, ad: str, deger):
        try:
            self.setProperty(ad, deger)
            st = self.style()
            if st is None:
                return
            st.unpolish(self)
            st.polish(self)
            self.update()
        except Exception:
            pass

    def enterEvent(self, event):
        super().enterEvent(event)
        QTimer.singleShot(0, lambda: self._animate(100))
        QTimer.singleShot(0, lambda: self._qss_ozellik_ata("hovered", "true"))

    def leaveEvent(self, event):
        super().leaveEvent(event)
        QTimer.singleShot(0, lambda: self._animate(0))
        QTimer.singleShot(0, lambda: self._qss_ozellik_ata("hovered", "false"))

    def _animate(self, hedef: int):
        """Hedef 0 (indir) veya 100 (kaldır)."""
        if hedef == self._hedef and self._tween_timer is None:
            # Zaten hedef durumda, animasyon yok
            return
        self._hedef = 100 if hedef >= 50 else 0
        # Timer zaten çalışıyorsa tekrar başlatma (karelerine devam eder)
        if self._tween_timer is not None:
            return
        try:
            t = QTimer(self)
            t.setInterval(self._frame_ms)
            t.timeout.connect(self._tick)
            t.start()
            self._tween_timer = t
        except Exception:
            self._tween_timer = None

    # ------------------------------------------------------------------
    # macOS emniyetli gölge + kart çizimi (paintEvent QSS'ten önce)
    # ------------------------------------------------------------------
    def paintEvent(self, event):
        # Eğer sadece yuvarlak görsel gösterilecekse (kare çerçeve / gölge
        # istenmiyorsa), KART GÖVDESİNİ çizme; alt widget'lar normal
        # çizilsin (hover lift animasyonu MARGIN üzerinden yine çalışır).
        if getattr(self, "_sadece_yuvark_goster", False):
            super().paintEvent(event)
            return

        rct = self.rect()
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        yuzde = max(0.0, min(1.0, float(self._dur) / 100.0))
        dy = 3.0 + 7.0 * yuzde  # gölge dikey öteleme
        radi = 22.0

        # Kart iç çerçevesi: dış padding 10px gölgeye ayrılsın
        inset = 10
        card_rct = rct.adjusted(inset, inset, -inset, -inset)

        # 3 katmanlı yumuşak gölge (alpha + shrink artırarak dışarı yayma)
        for (shrink, alpha) in [(16, 20), (8, 30), (3, 46)]:
            sr = card_rct.adjusted(-shrink, -shrink, shrink, shrink)
            sr.translate(0, int(dy))
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor(0, 0, 0, alpha)))
            rr = max(6.0, radi - shrink / 2.0)
            # QRectF üzerinden çiz — tüm PyQt6 sürümlerinde uyumlu
            p.drawRoundedRect(
                QRect(
                    int(sr.x()), int(sr.y()),
                    int(sr.width()), int(sr.height()),
                ),
                rr, rr,
            )

        # Kartın beyaz gövdesi + border (hover/selected renk değişimi)
        p.setBrush(QBrush(QColor("#ffffff")))
        border_col = QColor("#e2e8f0")
        if self.property("secili") is True or self.property("secili") == "true":
            secili_renk = self.property("secili_renk")
            if secili_renk:
                border_col = QColor(secili_renk)
            else:
                border_col = QColor("#4299e1")
        elif self.property("hovered") == "true":
            border_col = QColor("#90cdf4")
        p.setPen(QPen(border_col, 2))
        p.drawRoundedRect(card_rct, radi, radi)
        p.end()

        # Alt widget'lar ve layout çizimi devam etsin
        super().paintEvent(event)


# ---------------------------------------------------------------------------
# Rol kartlarında kullanılacak, resim gösteren label (yuvarlak, role özgü arka plan rengi)
# ---------------------------------------------------------------------------
class RolResmiLabel(QLabel):
    """
    Bir görseli oran koruyarak, yuvarlak arka plan üzerinde gösterir.
    ARKA_RENK rolle yuvarlağın iç rengidir.
    """

    def __init__(self, gorsel_adi: str, arka_renk: str, arka_renk_2: str | None = None,
                 boy: int = 110, padding: int = 10, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.gorsel_adi = gorsel_adi
        self.arka_renk = arka_renk
        self.arka_renk_2 = arka_renk_2 or arka_renk
        self.boy = boy
        self.padding = padding
        outer = boy + 34
        self.setFixedSize(outer, outer)
        # Görsel çemberi yuvarlak çerçeve (arka plan renginden biraz daha koyu bir çember çevre
        self.setStyleSheet(
            f"background-color: transparent;"
        )
        self._yeniden_ciz()

    def _yeniden_ciz(self):
        cap = self.boy + 34
        pm = QPixmap(cap, cap)
        pm.fill(Qt.GlobalColor.transparent)
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        # Dış çember (beyaz ince halka — ince gölge hissi)
        path_dis = QPainterPath()
        path_dis.addEllipse(1, 1, cap - 2, cap - 2)
        p.setPen(QPen(QColor(255, 255, 255, 230), 3))
        p.setBrush(QBrush(QColor("white")))
        p.drawPath(path_dis)
        p.end()
        # İç kısma gerçek yuvarlak görsel (arka_renk dolgulu)
        ics = cap - 12
        ic_pix = yuvarlak_pixmap(
            gorsel_yol(self.gorsel_adi), ics,
            arka_renk=self.arka_renk,
            arka_renk_2=self.arka_renk_2,
            padding=self.padding,
        )
        birlesik = QPixmap(pm.size())
        birlesik.fill(Qt.GlobalColor.transparent)
        p2 = QPainter(birlesik)
        p2.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p2.drawPixmap(0, 0, pm)
        p2.drawPixmap(
            (birlesik.width() - ic_pix.width()) // 2,
            (birlesik.height() - ic_pix.height()) // 2,
            ic_pix,
        )
        p2.end()
        self.setPixmap(birlesik)

    def gorsel_degistir(self, yeni_ad: str, arka_renk: str | None = None,
                        arka_renk_2: str | None = None):
        self.gorsel_adi = yeni_ad
        if arka_renk:
            self.arka_renk = arka_renk
        if arka_renk_2:
            self.arka_renk_2 = arka_renk_2
        self._yeniden_ciz()


# ---------------------------------------------------------------------------
# _SecilebilirYuvarlakLabel
# RolResmiLabel gibidir ama ekstra olarak:
#   * set_secili(bool) çağrılınca seçili durumda KALIN bir dış çember çizer
#     (seçim rengi ile) ve ölçeğini %5 büyütür -> hafif "daha belirgin" hissi.
#   * Tıklandığında setAttribute WA_TransparentForMouseEvents=False,
#     mousePressEvent yakalar ve kullanıcı verilen tiklama_cb()'i çağırır.
#   * Kare çerçeve DEĞİL — her zaman sadece yuvarlak bir görsel,
#     gerekirse seçim çemberi.
# ---------------------------------------------------------------------------
class _SecilebilirYuvarlakLabel(QLabel):
    def __init__(self, gorsel_adi: str, arka_renk: str,
                 arka_renk_2: str | None = None, secim_renk: str = "#90cdf4",
                 boy: int = 140, padding: int = 16, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        # Boyutlar
        self._boy_ic = boy                   # Görsel + iç dolgu çapı
        self._padding = padding
        self._dis_pad = 10                   # Dışarıda çember çizmek için pay
        self._hovered = False
        self._secili = False
        # Veri
        self.gorsel_adi = gorsel_adi
        self.arka_renk = arka_renk
        self.arka_renk_2 = arka_renk_2 or arka_renk
        self.secim_renk = secim_renk
        # Callback
        self.tiklama_cb = None
        # Sabit boyut (seçili olduğunda resize etmiyoruz, scale yapıyoruz)
        outer = self._boy_ic + 2 * self._dis_pad
        self.setFixedSize(outer + 18, outer + 18)  # +18 scale büyümesi için
        self.setStyleSheet("background-color: transparent;")
        self._yeniden_ciz()

    # -------- Dış API --------
    def set_secili(self, s: bool):
        if self._secili == bool(s):
            return
        self._secili = bool(s)
        self.update()

    def secili(self) -> bool:
        return self._secili

    # -------- Olaylar --------
    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.tiklama_cb:
            try:
                self.tiklama_cb(event)
            except Exception:
                pass
        event.accept()

    # -------- Çizim --------
    def _yeniden_ciz(self):
        """Gerçek görseli (iç daire) önceden hazırlar, cache'ler."""
        ic_cap = self._boy_ic
        self._ic_pix = yuvarlak_pixmap(
            gorsel_yol(self.gorsel_adi), ic_cap,
            arka_renk=self.arka_renk,
            arka_renk_2=self.arka_renk_2,
            padding=self._padding,
        )

    def paintEvent(self, event):
        p = QPainter(self)
        try:
            p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

            w, h = self.width(), self.height()
            cx, cy = w / 2.0, h / 2.0

            # --- Ölçekleme: Seçili ise %6 büyüt, sadece hover ise %2 büyüt ---
            if self._secili:
                skala = 1.06
            elif self._hovered:
                skala = 1.02
            else:
                skala = 1.0
            p.translate(cx, cy)
            p.scale(skala, skala)
            p.translate(-cx, -cy)

            ic = self._ic_pix
            if ic.isNull():
                p.setPen(QPen(QColor("#e2e8f0"), 2))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawEllipse(int(cx - self._boy_ic / 2), int(cy - self._boy_ic / 2),
                              self._boy_ic, self._boy_ic)
                return

            # İç görseli ortala
            x = int(cx - ic.width() / 2)
            y = int(cy - ic.height() / 2)
            p.drawPixmap(x, y, ic)

            # Seçili ise dışarıda belirgin bir çember (secim_rengi)
            if self._secili:
                kalem = QPen(QColor(self.secim_renk), 5)
                kalem.setCosmetic(False)
                p.setPen(kalem)
                p.setBrush(Qt.BrushStyle.NoBrush)
                yaricap = ic.width() / 2.0 + 6
                p.drawEllipse(int(cx - yaricap), int(cy - yaricap),
                              int(2 * yaricap), int(2 * yaricap))
            # Hover ve seçili DEĞİLSE hafif bir beyaz halka (daha temiz)
            elif self._hovered:
                kalem = QPen(QColor(255, 255, 255, 210), 2.5)
                kalem.setCosmetic(False)
                p.setPen(kalem)
                p.setBrush(Qt.BrushStyle.NoBrush)
                yaricap = ic.width() / 2.0 + 3
                p.drawEllipse(int(cx - yaricap), int(cy - yaricap),
                              int(2 * yaricap), int(2 * yaricap))
        finally:
            p.end()



# ---------------------------------------------------------------------------
# Mascot / karakter gösterimi: resimli (öğrenci görseli) + emoji yüz
# ---------------------------------------------------------------------------
class MascotWidget(QWidget):
    """
    Öğrenci görselini + üzerinde tepki emojisini gösteren bir widget.
    Eğer görsel yoksa emoji+emoji gösterimine geri döner.
    """

    def __init__(self, parent=None, cinsiyet: str = "kiz", yukseklik: int = 180):
        super().__init__(parent)
        self.setMinimumHeight(max(140, yukseklik))
        self.cinsiyet = cinsiyet   # "kiz" veya "erkek"
        self.durum = "mutlu"
        self._yukseklik = yukseklik
        self.setStyleSheet(
            "background-color: #fff8d7;"
            "border: 3px dashed #f3c969;"
            "border-radius: 24px;"
        )

    # ---------------- Görsel yollarını ve arka plan renklerini çözümle ----------------
    def _ogrenci_gorseli(self) -> str:
        if self.cinsiyet == "erkek":
            return gorsel_yol("erkeköğrenci.png")
        return gorsel_yol("kızöğrenci.png")

    def _arka_renkler(self):
        # Kız: pembe tonlu, erkek: mavi tonlu — çember içi dolgu renkleri
        if self.cinsiyet == "erkek":
            return "#a2d2ff", "#bde0fe"
        return "#ffc8dd", "#ffafcc"

    def _yuz_emoji(self) -> str:
        return {
            "mutlu": "😊",
            "sasirma": "🤔",
            "dogru": "🥳",
            "yanlis": "😅",
        }.get(self.durum, "🙂")

    # ---------------- Dışarıdan çağrılan API ----------------
    def cinsiyet_degistir(self, cinsiyet: str):
        self.cinsiyet = cinsiyet
        self.update()

    def mutlu_ol(self):     self.durum = "mutlu";     self.update()
    def sasir(self):        self.durum = "sasirma";   self.update()
    def dogru_cevap(self):  self.durum = "dogru";     self.update()
    def yanlis_cevap(self): self.durum = "yanlis";    self.update()

    # ---------------- Özel çizim ----------------
    def paintEvent(self, event):
        # Önce QSS arka planını çiz
        super().paintEvent(event)

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        alan = self.rect().adjusted(12, 10, -12, -10)

        # Görsel yükseklik: alan yüksekliğinin %85'i
        gorsel_cap = int(min(alan.height(), alan.width() * 0.55))
        if gorsel_cap < 60:
            gorsel_cap = 60

        renk1, renk2 = self._arka_renkler()
        pix = yuvarlak_pixmap(
            self._ogrenci_gorseli(), gorsel_cap,
            arka_renk=renk1, arka_renk_2=renk2, padding=14,
        )
        if not pix.isNull():
            # Görseli ortala, biraz sola kaydır (sağ tarafa emoji yüzü gelsin diye)
            x = alan.center().x() - pix.width() // 2 - 20
            y = alan.center().y() - pix.height() // 2
            p.drawPixmap(x, y, pix)

            # Emoji yüze sağ-üst köşede
            emoji = self._yuz_emoji()
            emoji_font = turkce_font(max(18, gorsel_cap // 4))
            p.setFont(emoji_font)
            emoji_alan = QRect(
                x + pix.width() - gorsel_cap // 4,
                y - 6,
                gorsel_cap // 2,
                gorsel_cap // 2,
            )
            p.drawText(emoji_alan, Qt.AlignmentFlag.AlignCenter, emoji)
        else:
            # Görsel bulunamazsa emoji temsili
            emoji_font = turkce_font(gorsel_cap // 2)
            p.setFont(emoji_font)
            if self.cinsiyet == "erkek":
                metin = f"👦 {self._yuz_emoji()}"
            else:
                metin = f"👧 {self._yuz_emoji()}"
            p.drawText(alan, Qt.AlignmentFlag.AlignCenter, metin)
        p.end()


# ---------------------------------------------------------------------------
# AppBridge: 3 parçalı (projeyi 3'e böldüğünüz) tümleşik çalışma için ortak
#            sinyal kordonu. TÜM emit'ler ANA THREAD'de çalışır (pyqtSignal kuralı).
#
# Kullanım (arkadaşının gönderdiği sözleşme):
#   bridge = AppBridge()
#   bridge.finished.emit("tamamlandi")   # çocuk ekranı tamamlanınca
#   bridge.finished.emit("veli_cikisi")  # Veli PIN ile çıkışta
# ---------------------------------------------------------------------------
class AppBridge(QObject):
    """
    Uygulama (ana parça) ile diğer iki dış parça arasında güvenli haberleşme.
    Geliştirme / tek parça test modunda bu sinyallere slot bağlayabilirsiniz;
    3 parçayı birleştiren bütünleştirici modül de aynı sinyalleri dinler.
    """

    # str tipinde: "tamamlandi" | "veli_cikisi"  (ileride genişletilebilir)
    finished = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        # Debug / yerel kayıt için: sinyal emitionlarını hafızada tut (opsiyonel)
        self._son_10_emit = []

    # Yardımcı: ana thread'de olduğumuzu garanti ederek emit eder
    def guvenli_emit(self, etiket: str):
        try:
            if QThread.currentThread() is not QCoreApplication.instance().thread():
                # Farklı thread'den gelme ihtimaline karşı (çok nadir) QTimer
                # ile ana event döngüsüne bırakarak emit ederiz.
                QTimer.singleShot(0, lambda et=etiket: self.finished.emit(et))
            else:
                self.finished.emit(etiket)
            # Kayıt
            self._son_10_emit.append(etiket)
            if len(self._son_10_emit) > 10:
                self._son_10_emit.pop(0)
        except Exception:
            pass

    def son_emitler(self) -> list[str]:
        return list(self._son_10_emit)


# ---------------------------------------------------------------------------
# ActivityGuard: Mola + çocuk kilidi / dışarı çıkma engelleyici.
#
# Kullanım (arkadaşının sözleşmesi):
#   guard = ActivityGuard(ana_pencere)
#   guard.start(max_seconds=mola_suresi + 120)   # kilit + süre başlar
#   guard.stop()                                 # kilit + süre durur
#   guard.blocked_count()                        # kaç girişim engellendi? (rapor)
#
# Davranış:
#   - start() çağrılınca: Ana pencere etrafında şeffaf "süre" etiketi belirir.
#     Süre dolana kadar:
#       * pencereyi kapatma (✕, Cmd+W, Alt+F4, close()) ENGEL
#       * pencereyi küçültme (WindowMinimize yakalanır) ENGEL
#       * pencereyi arka plana gönderme (Deactivate / başka pencereye geçiş)
#         1 sn sonra otomatik olarak raise_() + activateWindow()
#   - Her engellenen eylem _blocked_count +=1 (rapor)
#   - Süre dolunca otomatik stop() + bridge.finished.emit("mola_bitti") (ops.)
# ---------------------------------------------------------------------------
class ActivityGuard(QObject):
    def __init__(self, ana_pencere, parent=None):
        super().__init__(parent or ana_pencere)
        self._pencere = ana_pencere   # AnaPencere (QWidget) referansı
        self._aktif = False
        self._blocked_count = 0
        self._kalan_saniye = 0
        self._toplam_saniye = 0
        # Süre sayacı: her saniye tick
        self._sayac = QTimer(self)
        self._sayac.setInterval(1000)
        self._sayac.timeout.connect(self._tick)

        # Kilit sırasında UI üstünde (ya da pencere kenarında) kalan
        # süreyi göstermek için küçük bir "badge" QLabel. Ana pencere ic_cerceve
        # üstüne bir child olarak bağlarız — ama layout ile değil doğrudan
        # top-right'a fixed-size yerleştirmek daha güvenli.
        self._badge = None   # type: QLabel | None

        # EventFilter: ana pencere ve çocukları üstünde Close / Minimize gibi
        # olayları aradan geçirebilmek için (qApp seviyesinde kuracağız)
        try:
            app = QApplication.instance()
            if app is not None:
                app.installEventFilter(self)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # PUBLIC API (arkadaşının sözleşmesi — istediği komutlar)
    # ------------------------------------------------------------------
    def start(self, max_seconds: int):
        """Mola (veya sonrası +2dk ek süre) boyunca pencereyi kilitler."""
        try:
            max_seconds = max(1, int(max_seconds))
        except Exception:
            max_seconds = 60
        self._aktif = True
        self._kalan_saniye = max_seconds
        self._toplam_saniye = max_seconds
        if not self._sayac.isActive():
            self._sayac.start()
        # UI: badge göster
        self._badge_goster()
        # Eğer pencere "StaysOnTop" değilse aktif kilitlemek için üstte tut
        try:
            self._pencere.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
            self._pencere.show()
            self._pencere.raise_()
            self._pencere.activateWindow()
        except Exception:
            pass

    def stop(self):
        """Kilit açılır, sayaç durur, badge gizlenir."""
        self._aktif = False
        try:
            self._sayac.stop()
        except Exception:
            pass
        self._badge_gizle()

    def blocked_count(self) -> int:
        return int(self._blocked_count)

    def blocked_count_sifirla(self):
        """Raporu aldıktan sonra sıfırlamak için (opsiyonel)."""
        self._blocked_count = 0

    def aktif_mi(self) -> bool:
        return bool(self._aktif)

    def kalan_saniye(self) -> int:
        return self._kalan_saniye if self._aktif else 0

    # ------------------------------------------------------------------
    # İÇ — sayaç / UI
    # ------------------------------------------------------------------
    def _tick(self):
        if not self._aktif:
            try:
                self._sayac.stop()
            except Exception:
                pass
            return
        self._kalan_saniye -= 1
        # Badge güncelle
        if self._badge is not None:
            self._badge.setText(self._badge_metin())
        # Süre bitti?
        if self._kalan_saniye <= 0:
            # Otomatik kilidi aç
            self.stop()
            # Bütünleştirici için sinyal yay (opsiyonel, API tanımı değil ama
            # arkadaşlarının 3. parçayla haberleşmesi için kullanışlı)
            try:
                br = getattr(self._pencere, "bridge", None)
                if br is not None:
                    br.guvenli_emit("mola_bitti")
            except Exception:
                pass

    def _badge_metin(self) -> str:
        dk = self._kalan_saniye // 60
        sn = self._kalan_saniye % 60
        return f"⏸  Mola / Kilit  {dk:02d}:{sn:02d}  🛡 ({self._blocked_count})"

    def _badge_goster(self):
        if self._badge is None:
            bdg = QLabel("", getattr(self._pencere, "ic_cerceve", self._pencere))
            bdg.setAlignment(Qt.AlignmentFlag.AlignCenter)
            bdg.setFont(turkce_font(10, True))
            bdg.setStyleSheet(
                "QLabel { background-color: #1d3557; color: #f1faee;"
                " padding: 6px 12px; border-radius: 12px;"
                " border: 2px solid #457b9d; }"
            )
            bdg.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            self._badge = bdg
        self._badge.setText(self._badge_metin())
        self._badge.adjustSize()
        # Yerleşim: ana pencerenin iç çerçevesi (varsa) sağ-üst köşesine
        hedef = getattr(self._pencere, "ic_cerceve", self._pencere)
        pw = hedef.width() if hasattr(hedef, "width") else self._pencere.width()
        x = max(8, pw - self._badge.width() - 16)
        self._badge.move(x, 8)
        self._badge.show()
        self._badge.raise_()

    def _badge_gizle(self):
        try:
            if self._badge is not None:
                self._badge.hide()
                # Metni sıfırla — sayacı 0 göstermesin
                self._badge.setText("")
        except Exception:
            pass

    # Ana pencere resize olursa badge'i tekrar yerleştir
    def pencere_resize_hook(self):
        if self._aktif and self._badge is not None:
            self._badge.adjustSize()
            hedef = getattr(self._pencere, "ic_cerceve", self._pencere)
            pw = hedef.width()
            x = max(8, pw - self._badge.width() - 16)
            self._badge.move(x, 8)

    # ------------------------------------------------------------------
    # EVENT FILTER — kilit açıksa pencere kapatma / küçültme / arka plana düşme
    # ------------------------------------------------------------------
    def eventFilter(self, izlenen, olay):
        try:
            if not self._aktif:
                return False   # Kilit açık değilse dokunma
            if izlenen is self._pencere or (
                hasattr(izlenen, "window") and izlenen.window() is self._pencere
            ):
                # 1) Pencereyi kapatmaya çalışıyorlar mı?
                if olay.type() == QEvent.Type.Close:
                    self._blocked_count += 1
                    # Geri bildirim: badge'i kırmızıya döndür
                    self._flash_kirmizi()
                    olay.ignore()
                    return True   # Olay tüketildi, kapatma ENGEL
                # 2) Pencereyi simge durumuna küçültüyorlar mı?
                if olay.type() == QEvent.Type.WindowStateChange:
                    try:
                        w = izlenen.windowHandle()
                        if w is not None and bool(w.windowState() & Qt.WindowState.WindowMinimized):
                            self._blocked_count += 1
                            self._flash_kirmizi()
                            # Simge durumunu geri al: showNormal
                            QTimer.singleShot(0, lambda p=self._pencere: (
                                p.showNormal(), p.raise_(), p.activateWindow()
                            ))
                            return False  # State değişikliği kendi içinde
                    except Exception:
                        pass
                # 3) Pencere odak / aktifliğini kaybederse (arka plana düşerse)
                #    Hemen geri getir (200ms gecikmeli)
                if olay.type() == QEvent.Type.WindowDeactivate:
                    self._blocked_count += 1
                    self._flash_kirmizi()
                    QTimer.singleShot(200, lambda p=self._pencere: (
                        p.raise_(), p.activateWindow()
                    ))
        except Exception:
            pass
        return False   # Diğer durumlar: normal yayıl

    def _flash_kirmizi(self):
        """Engellenen girişimde badge'i 500 ms kırmızı yap, sonra geri al."""
        try:
            if self._badge is None:
                return
            self._badge.setStyleSheet(
                "QLabel { background-color: #ef233c; color: white;"
                " padding: 6px 12px; border-radius: 12px;"
                " border: 2px solid #d90429; font-weight:bold; }"
            )

            def _geri():
                try:
                    if self._badge is not None:
                        self._badge.setStyleSheet(
                            "QLabel { background-color: #1d3557; color: #f1faee;"
                            " padding: 6px 12px; border-radius: 12px;"
                            " border: 2px solid #457b9d; }"
                        )
                except Exception:
                    pass
            QTimer.singleShot(500, _geri)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Profil Seçim Ekranı (Uygulama ilk açıldığında karşımıza çıkar)
# ---------------------------------------------------------------------------
class ProfilEkrani(QWidget):
    """
    Kız/Erkek seçimi + isim girdisi. Kullanıcı kaydedince ana_pencere'ye iletilir.
    Kartlar AnimasyonluKart sınıfındadır (hover yukarı kalkma efekti).
    """

    def __init__(self, ana_pencere):
        super().__init__()
        self.ana = ana_pencere
        self.secili_cinsiyet = None   # "kiz" veya "erkek"
        self._kiz_seg = None
        self._erkek_seg = None
        self._isim_input = None
        self._hata_lbl = None
        self._onay_btn = None
        self._secilen_konteyner = None  # Kartların seçim göstergesi için
        self._arayuz_olustur()

    def _arayuz_olustur(self):
        dis = QVBoxLayout(self)
        dis.setContentsMargins(28, 24, 28, 18)
        dis.setSpacing(16)

        baslik = QLabel("Profilini Oluştur 🎈")
        baslik.setAlignment(Qt.AlignmentFlag.AlignCenter)
        baslik.setFont(turkce_font(20, True))
        baslik.setStyleSheet(
            "background-color:#ffffff; border:2px solid #bde0fe;"
            "border-radius: 18px; padding: 12px; color:#1d3557;"
        )
        dis.addWidget(baslik)

        alt = QLabel("Öğrenci rolünde adın ve seçtiğin karakter kullanılır.")
        alt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        alt.setFont(turkce_font(11))
        alt.setStyleSheet("color:#4a5568;")
        dis.addWidget(alt)

        # İsim satırı
        form_satir = QHBoxLayout()
        form_satir.setSpacing(10)
        lbl = QLabel("Adın:")
        lbl.setFont(turkce_font(13, True))
        lbl.setStyleSheet("color:#1d3557;")
        form_satir.addWidget(lbl)

        self._isim_input = QLineEdit()
        self._isim_input.setPlaceholderText("Lütfen adını yaz...")
        self._isim_input.setFont(turkce_font(13))
        self._isim_input.setStyleSheet(
            "QLineEdit { padding: 10px 14px; border-radius: 14px;"
            "border: 2px solid #bde0fe; background: #ffffff; min-height: 26px; }"
            "QLineEdit:focus { border: 2px solid #7dd3fc; }"
        )
        form_satir.addWidget(self._isim_input, 1)
        dis.addLayout(form_satir)

        # Profil kartları (Kız / Erkek)
        kartlar = QHBoxLayout()
        kartlar.setSpacing(24)
        self._kiz_kart = self._profil_karti("kiz")
        self._erkek_kart = self._profil_karti("erkek")
        kartlar.addStretch(1)
        kartlar.addWidget(self._kiz_kart)
        kartlar.addWidget(self._erkek_kart)
        kartlar.addStretch(1)
        dis.addLayout(kartlar, 1)

        # Hata mesajı
        self._hata_lbl = QLabel("")
        self._hata_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._hata_lbl.setFont(turkce_font(10, True))
        self._hata_lbl.setStyleSheet("color:#c9184a; min-height: 14px;")
        dis.addWidget(self._hata_lbl)

        # Onay butonu — profil seçilmeden önce devre dışı
        onay = QPushButton("Devam Et ➡")
        onay.setCursor(Qt.CursorShape.PointingHandCursor)
        onay.setFont(turkce_font(14, True))
        onay.setEnabled(False)
        onay.setStyleSheet(
            "QPushButton:disabled { background-color:#cbd5e1;"
            " color:#94a3b8; border:none; border-radius:16px;"
            " padding: 12px 18px; min-height:44px; }"
            "QPushButton:enabled { background-color:#74c69d; color:#081c15;"
            "border:none; border-radius:16px; padding: 12px 18px;"
            "min-height:44px; }"
            "QPushButton:hover:enabled { background-color:#52b788; }"
            "QPushButton:pressed:enabled { background-color:#40916c; }"
        )
        onay.clicked.connect(self._onayla)
        self._onay_btn = onay
        dis.addWidget(onay)

    # ---------------- Profil "kartı" — sadece YUVARLAK FOTOĞRAF + BAŞLIK
    #  (İSTEK: Seç butonu ve kare çerçeve KALDIRILSIN, yalnızca yuvarlak profil
    #   fotoğrafları kalsın; fotoğrafa tıklayınca seçilsin)
    def _profil_karti(self, cinsiyet: str) -> QWidget:
        # Dış kapsayıcı: AnimasyonluKart Hala hover yukarı kalkma efektini
        # korusun diye kullanıyoruz ama paintEvent'te KARE çerçeve VE GÖLGE
        # ÇİZİLMESİN — bunun için Kartın kendisini "invisible" frame yapıyoruz.
        kart = AnimasyonluKart(lift_miktari=10, anim_ms=170)
        # Minimum boyut: sadece yuvarlak fotoğraf + başlığın sığacağı kadar
        kart.setMinimumHeight(200)
        kart.setMinimumWidth(200)
        # ÇERÇEVESİZ (border + background çizilmesin) diye paintEvent'teki
        # kart çizimini atlatmak için özel property:
        kart._sadece_yuvark_goster = True

        if cinsiyet == "kiz":
            resim_adi = "kızöğrenci.png"
            ad = "Kız Öğrenci"
            arka_renk = "#ffc8dd"
            arka_renk2 = "#ffafcc"
            secim_renk = "#ff8fab"
        else:
            resim_adi = "erkeköğrenci.png"
            ad = "Erkek Öğrenci"
            arka_renk = "#a2d2ff"
            arka_renk2 = "#bde0fe"
            secim_renk = "#3a86ff"

        katman = QVBoxLayout(kart)
        katman.setContentsMargins(0, 0, 0, 0)
        katman.setSpacing(8)

        # Yuvarlak görsel + SEÇİLİ OLDUĞUNDA dışarıda belirgin çember
        self._yeni_seg = _SecilebilirYuvarlakLabel(
            resim_adi,
            arka_renk=arka_renk,
            arka_renk_2=arka_renk2,
            secim_renk=secim_renk,
            boy=140,
            padding=16,
        )
        if cinsiyet == "kiz":
            self._kiz_seg = self._yeni_seg
        else:
            self._erkek_seg = self._yeni_seg

        gorsel_holder = QHBoxLayout()
        gorsel_holder.addStretch(1)
        gorsel_holder.addWidget(self._yeni_seg)
        gorsel_holder.addStretch(1)
        katman.addLayout(gorsel_holder, 1)

        ad_lbl = QLabel(ad)
        ad_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ad_lbl.setFont(turkce_font(14, True))
        ad_lbl.setStyleSheet("color:#1d3557;")
        katman.addWidget(ad_lbl)

        # Tıklama: fotoğrafa ya da label alanına tıklanınca seç
        def _sec(_e=None, c=cinsiyet, s=self._yeni_seg):
            self._cinsiyet_sec(c, s)
        self._yeni_seg.tiklama_cb = _sec
        kart._tikla = _sec
        # Kart üstüne fare tıklanınca da seç (kart içindeki herhangi bir boş alana)
        orig_mp = kart.mousePressEvent
        def _karta_tik(e, _orig=orig_mp, _cb=_sec):
            try:
                _orig(e)
            except Exception:
                pass
            if e.button() == Qt.MouseButton.LeftButton:
                _cb()
            e.accept()
        kart.mousePressEvent = _karta_tik

        kart._secili_renk = secim_renk
        return kart

    # ---------------- Seçim mantığı ----------------
    def _cinsiyet_sec(self, cinsiyet, seg):
        self.secili_cinsiyet = cinsiyet
        self._hata_lbl.setText("")
        # İki seg'i güncelle: biri seçili, diğeri değil
        for s in (getattr(self, "_kiz_seg", None),
                  getattr(self, "_erkek_seg", None)):
            if s is None: continue
            s.set_secili(s is seg)
        # Onay butonunu bir şey seçilince aktifleştir
        try:
            self._onay_btn.setEnabled(True)
        except Exception:
            pass

    def _onayla(self):
        isim = self._isim_input.text().strip()
        if len(isim) < 2:
            self._hata_lbl.setText("Lütfen en az 2 harfli bir isim yaz.")
            return
        if self.secili_cinsiyet is None:
            self._hata_lbl.setText("Lütfen bir profil (kız ya da erkek) seç.")
            return
        # Ana pencereye kaydet ve role seçim ekranına geç
        self.ana.profil_kaydet(isim, self.secili_cinsiyet)
        self.ana.goruntu_degistir("giris")


# ---------------------------------------------------------------------------
# Giriş Ekranı (Rol Seçimi) — Veli / Öğretmen / Öğrenci
# Açıklama metinleri kaldırıldı. Her kart AnimasyonluKart (hover yukarı kalkma).
# Yuvarlak görsellerin arka planı role özgü pastel renklerle doldurulur.
# ---------------------------------------------------------------------------
class GirisEkrani(QWidget):
    """
    Veli, Öğretmen ve Öğrenci için ayrı kartlar.
    ARKA PLAN (kullanıcı isteği):
      * Sol (Veli)       : Turuncu  #ffd6a5 / #ffbf78
      * Orta (Öğretmen)  : Mor       #bdb2ff / #a495ff
      * Sağ (Öğrenci)    : Yeşil     #caffbf / #9ef594
    Sıvımsı (keskin hatasız) geçiş için QRadialGradient (3 merkez) +
    iki adet açılı QLinearGradient üst üste karıştırılır.
    """

    def __init__(self, ana_pencere):
        super().__init__()
        self.ana = ana_pencere
        self.ogr_ad_lbl = None   # öğrenci kartındaki adını göstermek için
        self._ogrenci_resim = None
        self._ogrenci_resim_holder = None
        # Butonlar KALDIRILDI (kullanıcı isteği: sadece foto + etiket, kart tıkla)
        #
        # ARKA PLAN PAINT: widget kendisi için özel renkli arka plan çizer.
        # Background role + autoFillEnabled etki etmiyor, paintEvent override.
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        self._arayuz_olustur()

    # ------------------------------------------------------------------
    # 3 renkli sıvı gradient (keskin hatasız içiçe)
    # ------------------------------------------------------------------
    def paintEvent(self, event):
        # Önce varsayılan (QSS varsa) çizilir
        super().paintEvent(event)
        p = QPainter(self)
        try:
            p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            w, h = self.width(), self.height()

            # Gradient toplamı yapmak için 3 katman çizeceğiz: katman opacity ile
            # QPainter CompositionMode_SourceOver karışımı.

            # ----- KATMAN 1: Veli (SOL TURUNCU) -----
            sol_merkez = QPointF(w * 0.02, h * 0.55)
            yaricap = max(w, h) * 0.85
            g1 = QRadialGradient(sol_merkez, yaricap)
            g1.setColorAt(0.0, QColor(255, 191, 120, 230))   # koyu turuncu (alpha 0.9)
            g1.setColorAt(0.40, QColor(255, 214, 165, 170)) # açık turuncu
            g1.setColorAt(0.85, QColor(255, 214, 165, 0))   # saydam
            g1.setColorAt(1.0, QColor(255, 214, 165, 0))
            p.fillRect(self.rect(), QBrush(g1))

            # ----- KATMAN 2: Öğretmen (ORTA MOR) -----
            orta_merkez = QPointF(w * 0.50, h * 0.48)
            g2 = QRadialGradient(orta_merkez, yaricap * 0.88)
            g2.setColorAt(0.0, QColor(164, 149, 255, 220))  # koyu mor (alpha 0.86)
            g2.setColorAt(0.42, QColor(189, 178, 255, 140))  # açık mor
            g2.setColorAt(0.88, QColor(189, 178, 255, 0))
            g2.setColorAt(1.0, QColor(189, 178, 255, 0))
            p.fillRect(self.rect(), QBrush(g2))

            # ----- KATMAN 3: Öğrenci (SAĞ YEŞİL) -----
            sag_merkez = QPointF(w * 0.98, h * 0.55)
            g3 = QRadialGradient(sag_merkez, yaricap)
            g3.setColorAt(0.0, QColor(158, 245, 148, 220))  # koyu nane yeşil (alpha 0.86)
            g3.setColorAt(0.40, QColor(202, 255, 191, 150)) # açık nane yeşil
            g3.setColorAt(0.85, QColor(202, 255, 191, 0))
            g3.setColorAt(1.0, QColor(202, 255, 191, 0))
            p.fillRect(self.rect(), QBrush(g3))

            # ----- KATMAN 4: Yumuşatıcı 45 derece doğrusal sıyırma -----
            # (sol turuncu -> orta mor -> sağ yeşil akıcılığı artırır)
            g4 = QLinearGradient(0.0, 0.0, float(w), float(h))
            g4.setColorAt(0.00, QColor(255, 214, 165, 60))   # turuncu ışıltı
            g4.setColorAt(0.50, QColor(189, 178, 255, 30))   # mor ışıltı
            g4.setColorAt(1.00, QColor(202, 255, 191, 60))   # yeşil ışıltı
            p.fillRect(self.rect(), QBrush(g4))

            # ----- KATMAN 5: Genel yumuşak yapay aydınlatma (tepe) -----
            # Üst kısım hafif açık (ışık efekti), alt kısım hafif koyu.
            g5 = QLinearGradient(0.0, 0.0, 0.0, float(h))
            g5.setColorAt(0.0, QColor(255, 255, 255, 70))   # tepede beyaz yıkama
            g5.setColorAt(0.45, QColor(255, 255, 255, 0))
            g5.setColorAt(1.0, QColor(15, 23, 42, 20))       # dipte hafif gölge
            p.fillRect(self.rect(), QBrush(g5))
        finally:
            p.end()

    # İsim değiştiğinde çağrılır
    def ogrenci_adi_guncelle(self, ad: str):
        if self.ogr_ad_lbl is not None and ad:
            self.ogr_ad_lbl.setText(ad)
        # Butonlar KALDIRILDI — metin güncellemesine gerek yok

    def _arayuz_olustur(self):
        dis = QVBoxLayout(self)
        # (KULLANICI İSTEĞİ)
        # Üstteki "Rolünü Seç ve Başla 🌈" dörtgen + alt açıklama KALDIRILDI.
        # Sadece kartlar (3 tane YUVARLAK görsel + ad) + biraz boşluk.
        dis.setContentsMargins(24, 24, 24, 18)
        dis.setSpacing(12)

        # Üstten biraz boşluk (üst başlığı kaldırdığımız için)
        dis.addSpacing(44)

        # Üç kartlık satır
        kartlar = QHBoxLayout()
        kartlar.setSpacing(24)

        kartlar.addWidget(self._kart_olustur(
            gorsel="veli.png",
            ad="Veli",
            arka_renk="#ffd6a5",
            arka_renk2="#ffbf78",
            buton_stil="veli",
            tiklama=lambda: self.ana.goruntu_degistir("veli"),
        ))
        kartlar.addWidget(self._kart_olustur(
            gorsel="ogretmen.png",
            ad="Öğretmen",
            arka_renk="#bdb2ff",
            arka_renk2="#a495ff",
            buton_stil="ogretmen",
            tiklama=lambda: self.ana.goruntu_degistir("ogretmen"),
        ))
        ogrenci_karti = self._kart_olustur(
            gorsel=None,        # öğrenci cinsiyete göre değişir
            ad="Öğrenci",
            arka_renk="#caffbf",
            arka_renk2="#9ef594",
            buton_stil="ogrenci",
            tiklama=lambda: self.ana.goruntu_degistir("ogrenci"),
            ogrenci_ozel=True,
        )
        kartlar.addWidget(ogrenci_karti)

        # Boş alan büyümesini sınırlama
        sarici = QHBoxLayout()
        sarici.addStretch(1)
        sarici.addLayout(kartlar, 5)
        sarici.addStretch(1)

        dis.addStretch(1)
        dis.addLayout(sarici)
        dis.addStretch(2)

    def _buton_stili(self, stil_adi: str) -> str:
        if stil_adi == "veli":
            arka = "#ffd6a5"
            hover = "#ffbf78"
            press = "#ffaa55"
            yazi_renk = "#6b3e02"
        elif stil_adi == "ogretmen":
            arka = "#bdb2ff"
            hover = "#a495ff"
            press = "#8b7bff"
            yazi_renk = "#2d1b69"
        else:  # ogrenci
            arka = "#caffbf"
            hover = "#9ef594"
            press = "#7ce070"
            yazi_renk = "#1b4332"
        return f"""
            QPushButton {{
                background-color: {arka}; color: {yazi_renk};
                border: none; border-radius: 14px;
                padding: 8px 14px; font-size: 13px; font-weight: bold;
                min-height: 40px;
            }}
            QPushButton:hover   {{ background-color: {hover}; }}
            QPushButton:pressed {{ background-color: {press}; }}
        """

    def _kart_olustur(self, gorsel, ad, arka_renk, arka_renk2, buton_stil, tiklama, ogrenci_ozel=False) -> AnimasyonluKart:
        kart = AnimasyonluKart(lift_miktari=7, anim_ms=150)
        # Kullanıcı istediği için KARE ÇERÇEVE VE ARKA PLAN GÖSTERİLMESİN
        kart._sadece_yuvark_goster = True
        kart.setMinimumHeight(220)
        kart.setMaximumWidth(240)
        kart.setCursor(Qt.CursorShape.PointingHandCursor)
        # Kart tıkla = geçiş
        orig_mp = kart.mousePressEvent
        def _kart_tik(e, _orig=orig_mp, _tiklama=tiklama):
            try:
                _orig(e)
            except Exception:
                pass
            if e.button() == Qt.MouseButton.LeftButton:
                try:
                    _tiklama()
                except Exception:
                    pass
            e.accept()
        kart.mousePressEvent = _kart_tik

        katman = QVBoxLayout(kart)
        katman.setContentsMargins(0, 0, 0, 0)
        katman.setSpacing(8)

        # Görsel: öğrenci ise seçilen görsel, diğerleri için sabit PNG
        if ogrenci_ozel:
            self._ogrenci_resim_holder = QHBoxLayout()
            self._ogrenci_resim_holder.addStretch(1)
            # Başlangıç: kız görseli (profil seçimi gelince güncellenir)
            self._ogrenci_resim = _SecilebilirYuvarlakLabel(
                "kızöğrenci.png", arka_renk=arka_renk, arka_renk_2=arka_renk2,
                secim_renk="#90cdf4",
                boy=130, padding=16,
            )
            self._ogrenci_resim.tiklama_cb = lambda e=None, _t=tiklama: _t()
            self._ogrenci_resim_holder.addWidget(self._ogrenci_resim)
            self._ogrenci_resim_holder.addStretch(1)
            katman.addLayout(self._ogrenci_resim_holder, 1)
        else:
            holder = QHBoxLayout()
            holder.addStretch(1)
            seg = _SecilebilirYuvarlakLabel(
                gorsel, arka_renk=arka_renk, arka_renk_2=arka_renk2,
                secim_renk="#90cdf4",
                boy=130, padding=16,
            )
            seg.tiklama_cb = lambda e=None, _t=tiklama: _t()
            holder.addWidget(seg)
            holder.addStretch(1)
            katman.addLayout(holder, 1)

        if ogrenci_ozel:
            ad_lbl = QLabel("Öğrenci")
            self.ogr_ad_lbl = ad_lbl
        else:
            ad_lbl = QLabel(ad)
        ad_lbl.setFont(turkce_font(15, True))
        ad_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ad_lbl.setStyleSheet("color:#1d3557;")
        katman.addWidget(ad_lbl)

        # Açıklama + BUTONLAR KALDIRILDI (kullanıcı isteği üzerine)
        return kart

    # Ana pencere tarafından çağrılır
    def ogrenci_gorsel_guncelle(self, cinsiyet: str):
        if not hasattr(self, "_ogrenci_resim"):
            return
        if self._ogrenci_resim is None:
            return
        # Eski görsel nesnesini tutuyoruz; sadece pixmap cache + arka plan rengini
        # güncelleyip update() çağırmak yeterli — _SecilebilirYuvarlakLabel
        # boyut/yerleşimini sabit tutar.
        if cinsiyet == "erkek":
            gorsel_adi = "erkeköğrenci.png"
        else:
            gorsel_adi = "kızöğrenci.png"
        # Öğrenci kartında ARKA_PLAN rengi daima nane yeşili (#caffbf/#9ef594)
        # — bu, Profil Ekrani'ndaki cinsiyet renginden FARKLIDIR (rol kartı rengi)
        arka = "#caffbf"
        arka2 = "#9ef594"
        seg = self._ogrenci_resim
        seg.gorsel_adi = gorsel_adi
        seg.arka_renk = arka
        seg.arka_renk_2 = arka2
        seg._yeniden_ciz()
        seg.update()


# ---------------------------------------------------------------------------
# Veli Paneli (veli görselli + yer tutucu)
# ---------------------------------------------------------------------------
class VeliPaneli(QWidget):
    def __init__(self, ana_pencere):
        super().__init__()
        self.ana = ana_pencere
        self._arayuz_olustur()

    def _arayuz_olustur(self):
        katman = QVBoxLayout(self)
        katman.setContentsMargins(28, 22, 28, 14)
        katman.setSpacing(14)

        baslik = QLabel("👨‍👩‍👧   Veli Paneli")
        baslik.setObjectName("Baslik")
        baslik.setAlignment(Qt.AlignmentFlag.AlignCenter)
        baslik.setFont(turkce_font(18, True))
        katman.addWidget(baslik)

        # Veli görseli + bilgi satırı
        govde = QHBoxLayout()
        govde.setSpacing(20)

        gorsel_kutusu = QFrame()
        gorsel_kutusu.setStyleSheet(
            "QFrame { background-color: #fff1e6;"
            "border-radius: 24px; border: 2px solid #ffd6a5; }"
        )
        gorsel_katman = QVBoxLayout(gorsel_kutusu)
        gorsel_katman.setContentsMargins(14, 14, 14, 14)
        gorsel_katman.addStretch(1)
        # Veli kartının yuvarlak görselindeki dolgu rengi: pastel turuncu (veli rengi)
        gorsel_katman.addWidget(
            RolResmiLabel(
                "veli.png",
                arka_renk="#ffd6a5",
                arka_renk_2="#fff1e6",
                boy=150,
                padding=18,
            ),
            0,
            Qt.AlignmentFlag.AlignCenter,
        )
        gorsel_katman.addStretch(1)
        govde.addWidget(gorsel_kutusu, 1)

        bilgi_kutusu = QFrame()
        bilgi_kutusu.setStyleSheet(
            "QFrame { background-color: #ffffff;"
            "border-radius: 20px; border: 2px solid #a8dadc; }"
        )
        bilgi_katman = QVBoxLayout(bilgi_kutusu)
        bilgi_katman.setContentsMargins(18, 16, 18, 16)
        bilgi_katman.setSpacing(10)

        bilgi_baslik = QLabel("Hoş geldiniz!")
        bilgi_baslik.setFont(turkce_font(16, True))
        bilgi_baslik.setStyleSheet("color:#1d3557;")
        bilgi_katman.addWidget(bilgi_baslik)

        bilgi = QLabel(
            "Burada çocuğunun ilerlemesini, kazandığı yıldızları ve "
            "çözdüğü soruları görebilirsin.\n\n"
            "Bu bölüm yer tutucudur. Sonraki sürümlerde detaylı raporlar eklenecektir."
        )
        bilgi.setWordWrap(True)
        bilgi.setFont(turkce_font(12))
        bilgi.setStyleSheet("color:#2d3748;")
        bilgi_katman.addWidget(bilgi, 1)
        govde.addWidget(bilgi_kutusu, 2)

        katman.addLayout(govde, 1)

        # --- Veli PIN ile ÇIKIŞ butonu (arkadaşının API: finished.emit("veli_cikisi")) ---
        cikis_row = QHBoxLayout()
        cikis_row.addStretch(1)

        # Varsayılan 4 haneli geliştirici PIN (1234)
        self._pin_satiri = QLineEdit()
        self._pin_satiri.setPlaceholderText("Veli PIN (örn. 1234)")
        self._pin_satiri.setEchoMode(QLineEdit.EchoMode.Password)
        self._pin_satiri.setMaxLength(8)
        self._pin_satiri.setFont(turkce_font(12))
        self._pin_satiri.setFixedWidth(220)
        self._pin_satiri.setStyleSheet(
            "QLineEdit { padding: 8px 12px; border-radius: 14px;"
            " border: 2px solid #ffd6a5; background: white; }"
            " QLineEdit:focus { border: 2px solid #ff9f1c; }"
        )
        cikis_row.addWidget(self._pin_satiri)

        self._pin_sonuc = QLabel("")
        self._pin_sonuc.setFont(turkce_font(11, True))
        cikis_row.addWidget(self._pin_sonuc)

        pin_cikis_btn = QPushButton("🚪  Veli PIN ile Çık")
        pin_cikis_btn.setFont(turkce_font(12, True))
        pin_cikis_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        pin_cikis_btn.setStyleSheet(
            "QPushButton { background-color: #e76f51; color: white;"
            " border: none; border-radius: 14px; padding: 10px 16px;"
            " min-height: 38px; }"
            " QPushButton:hover { background-color: #ef633b; }"
            " QPushButton:pressed { background-color: #d05a3b; }"
        )
        pin_cikis_btn.clicked.connect(self._veli_pin_cikis)
        cikis_row.addWidget(pin_cikis_btn)
        cikis_row.addStretch(1)
        katman.addLayout(cikis_row)

    # Veli PIN doğrulaması + bridge sinyali (veli_cikisi)
    def _veli_pin_cikis(self):
        try:
            girilen = (self._pin_satiri.text() or "").strip()
            # ************************
            # *  GERÇEK PIN KAYNAĞINI buraya bağlayabilirsin (veritabanı vb.)
            # *  Şimdilik geliştirme amaçlı: 1234
            # ************************
            dogru_pin = "1234"
            if len(girilen) < 4 or girilen != dogru_pin:
                self._pin_sonuc.setStyleSheet("color:#c9184a;")
                self._pin_sonuc.setText("❌  PIN yanlış! (ipucu: 1234)")
                return
            # PIN DOĞRU → arkadaşının beklediği API:
            #     finished.emit("veli_cikisi")
            self._pin_sonuc.setStyleSheet("color:#2d6a4f;")
            self._pin_sonuc.setText("✅  Doğru! Çıkış sinyali yayınlandı...")
            self._pin_satiri.clear()
            try:
                self.ana.bridge.guvenli_emit("veli_cikisi")
            except Exception:
                try:
                    self.ana.bridge.finished.emit("veli_cikisi")
                except Exception:
                    pass

            # Görsel dönüş: kısa bir süre sonra Giriş ekranına geri dön
            def _geridon():
                try:
                    self.ana.goruntu_degistir("giris")
                    self._pin_sonuc.setText("")
                except Exception:
                    pass
            QTimer.singleShot(450, _geridon)
        except Exception as e:
            print(f"veli_pin_cikis hatasi: {e}", file=sys.stderr)
# ---------------------------------------------------------------------------
class OgretmenPaneli(QWidget):
    def __init__(self, ana_pencere):
        super().__init__()
        self.ana = ana_pencere
        self._arayuz_olustur()

    def _arayuz_olustur(self):
        katman = QVBoxLayout(self)
        katman.setContentsMargins(28, 22, 28, 14)
        katman.setSpacing(14)

        baslik = QLabel("👩‍🏫   Öğretmen Paneli")
        baslik.setObjectName("Baslik")
        baslik.setAlignment(Qt.AlignmentFlag.AlignCenter)
        baslik.setFont(turkce_font(18, True))
        katman.addWidget(baslik)

        # Görsel + bilgi satırı
        govde = QHBoxLayout()
        govde.setSpacing(20)

        gorsel_kutusu = QFrame()
        gorsel_kutusu.setStyleSheet(
            "QFrame { background-color: #f3efff;"
            "border-radius: 24px; border: 2px solid #bdb2ff; }"
        )
        gorsel_katman = QVBoxLayout(gorsel_kutusu)
        gorsel_katman.setContentsMargins(14, 14, 14, 14)
        gorsel_katman.addStretch(1)
        # Öğretmen kartının yuvarlak görselindeki dolgu rengi: pastel mor (öğretmen rengi)
        gorsel_katman.addWidget(
            RolResmiLabel(
                "ogretmen.png",
                arka_renk="#bdb2ff",
                arka_renk_2="#f3efff",
                boy=150,
                padding=18,
            ),
            0,
            Qt.AlignmentFlag.AlignCenter,
        )
        gorsel_katman.addStretch(1)
        govde.addWidget(gorsel_kutusu, 1)

        bilgi_kutusu = QFrame()
        bilgi_kutusu.setStyleSheet(
            "QFrame { background-color: #ffffff;"
            "border-radius: 20px; border: 2px solid #a8dadc; }"
        )
        bilgi_katman = QVBoxLayout(bilgi_kutusu)
        bilgi_katman.setContentsMargins(18, 16, 18, 16)
        bilgi_katman.setSpacing(10)

        bilgi_baslik = QLabel("Merhaba Öğretmenim!")
        bilgi_baslik.setFont(turkce_font(16, True))
        bilgi_baslik.setStyleSheet("color:#1d3557;")
        bilgi_katman.addWidget(bilgi_baslik)

        bilgi = QLabel(
            "Sınıfın için özel soru havuzları hazırlayabilir, ödevler oluşturabilir "
            "ve her öğrencinin başarı grafiğini inceleyebilirsin.\n\n"
            "Bu bölüm yer tutucudur. Sonraki sürümlerde soru editörü eklenecektir."
        )
        bilgi.setWordWrap(True)
        bilgi.setFont(turkce_font(12))
        bilgi.setStyleSheet("color:#2d3748;")
        bilgi_katman.addWidget(bilgi, 1)
        govde.addWidget(bilgi_kutusu, 2)

        katman.addLayout(govde, 1)


# ---------------------------------------------------------------------------
# Öğrenci / Quiz Görünümü
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ARKADAŞIN SORU EKLEMEK İÇİN DÜZENLEYEBİLECEĞİ HARİCİ SORU HAVUZU
# ---------------------------------------------------------------------------
# Arkadaşın ya da sen bu listeye istediğin kadar soru ekleyebilirsin.
# Her soru sözlük (dict) formatında:
#   {
#       "soru"       : str   -> sorunun metni
#       "secenekler" : list  -> tam olarak 4 adet seçenek (str)
#       "dogru"      : int   -> doğru seçeneğin INDEX'i (0, 1, 2, veya 3)
#       "kategori"   : str   -> (opsiyonel) "matematik", "türkçe", "genel" vb.
#       "zorluk"     : int   -> (opsiyonel) 1, 2, 3... raporlama için
#   }
#
# İstersen Dışarıdan JSON dosyası da yükleyebilirsin:
#   Eğer klasörde `sorular.json` dosyası varsa OTOMATİK olarak onun içindeki
#   soru listesi kullanılır (YOKSA aşağıdaki gömülü havuz kullanılır).
#   `sorular.json` şöyle olmalı:
#       [
#         { "soru": "...", "secenekler": ["A","B","C","D"], "dogru": 1 },
#         { ... }
#       ]
# ---------------------------------------------------------------------------
_GOMULU_SORULAR: list[dict] = [
    # --- MATEMATİK ---
    {
        "soru": "7 + 5 işleminin sonucu kaçtır?",
        "secenekler": ["10", "11", "12", "13"],
        "dogru": 2,
        "kategori": "matematik",
        "zorluk": 1,
    },
    {
        "soru": "15 - 8 işleminin sonucu kaçtır?",
        "secenekler": ["5", "6", "7", "8"],
        "dogru": 2,
        "kategori": "matematik",
        "zorluk": 1,
    },
    {
        "soru": "3 × 4 işleminin sonucu kaçtır?",
        "secenekler": ["7", "9", "12", "15"],
        "dogru": 2,
        "kategori": "matematik",
        "zorluk": 1,
    },
    {
        "soru": "Elinde 9 çikolata var, 4 tanesini arkadaşına verdi. Kaç çikolatan kaldı?",
        "secenekler": ["3", "4", "5", "6"],
        "dogru": 2,
        "kategori": "matematik",
        "zorluk": 2,
    },
    {
        "soru": "20 + 35 işleminin sonucu kaçtır?",
        "secenekler": ["45", "50", "55", "60"],
        "dogru": 2,
        "kategori": "matematik",
        "zorluk": 2,
    },
    {
        "soru": "100 - 43 işleminin sonucu kaçtır?",
        "secenekler": ["53", "57", "63", "67"],
        "dogru": 1,
        "kategori": "matematik",
        "zorluk": 2,
    },
    {
        "soru": "Bir sayıyı 5 ile çarptığında 30 buluyorsun. O sayı kaçtır?",
        "secenekler": ["4", "5", "6", "7"],
        "dogru": 2,
        "kategori": "matematik",
        "zorluk": 3,
    },
    {
        "soru": "12 ÷ 3 işleminin sonucu kaçtır?",
        "secenekler": ["2", "3", "4", "6"],
        "dogru": 2,
        "kategori": "matematik",
        "zorluk": 2,
    },
    # --- TÜRKÇE ---
    {
        "soru": "Şu harflerden SESLİ harf hangisidir?",
        "secenekler": ["Ç", "Ş", "Ü", "T"],
        "dogru": 2,
        "kategori": "türkçe",
        "zorluk": 1,
    },
    {
        "soru": "Aşağıdaki kelimelerden hangisi EYLEM (fiil)dir?",
        "secenekler": ["Kalem", "Koşmak", "Okul", "Mavi"],
        "dogru": 1,
        "kategori": "türkçe",
        "zorluk": 2,
    },
    {
        "soru": "\"Ev\" kelimesinin çoğulu hangisidir?",
        "secenekler": ["Evler", "Evim", "Evde", "Evin"],
        "dogru": 0,
        "kategori": "türkçe",
        "zorluk": 1,
    },
    {
        "soru": "Aşağıdakilerden hangisi birleşik yazılır?",
        "secenekler": ["bilgisayar", "pazartesi", "her gün", "elma"],
        "dogru": 0,
        "kategori": "türkçe",
        "zorluk": 3,
    },
    # --- GENEL KÜLTÜR ---
    {
        "soru": "Aşağıdakilerden hangisi bir MEVSİMdir?",
        "secenekler": ["Pazartesi", "İlkbahar", "Sabah", "Ocak"],
        "dogru": 1,
        "kategori": "genel",
        "zorluk": 1,
    },
    {
        "soru": "Aşağıdakilerden hangisi bir HAYVANDIR?",
        "secenekler": ["Gül", "Köpek", "Masa", "Öğretmen"],
        "dogru": 1,
        "kategori": "genel",
        "zorluk": 1,
    },
    {
        "soru": "İstanbul hangi ülkede bulunur?",
        "secenekler": ["Almanya", "Fransa", "Türkiye", "İtalya"],
        "dogru": 2,
        "kategori": "genel",
        "zorluk": 2,
    },
    {
        "soru": "Aşağıdakilerden hangisi bir TAŞITtır?",
        "secenekler": ["Uçak", "Kedi", "Portakal", "Güneş"],
        "dogru": 0,
        "kategori": "genel",
        "zorluk": 1,
    },
    {
        "soru": "Ankara Türkiye'nin hangisidir?",
        "secenekler": ["En büyük şehri", "Başkenti", "En eski şehri", "Sahil şehri"],
        "dogru": 1,
        "kategori": "genel",
        "zorluk": 2,
    },
    {
        "soru": "Güneş doğudan batıya doğru hareket ediyormuş gibi görünür. Bunun nedeni nedir?",
        "secenekler": [
            "Dünyanın kendi ekseni etrafında dönmesi",
            "Güneşin dünyanın etrafında dönmesi",
            "Ayın dünya etrafında dönmesi",
            "Yıldızların hareketi",
        ],
        "dogru": 0,
        "kategori": "fen",
        "zorluk": 3,
    },
    {
        "soru": "Su sıfır derecede ne olur?",
        "secenekler": ["Kaynar", "Donar", "Buharlaşır", "Rengini değiştirir"],
        "dogru": 1,
        "kategori": "fen",
        "zorluk": 2,
    },
    {
        "soru": "Vücudumuzdaki en büyük organ hangisidir?",
        "secenekler": ["Kalp", "Akciğer", "Cilt", "Beyin"],
        "dogru": 2,
        "kategori": "fen",
        "zorluk": 3,
    },
]


def _sorulari_yukle() -> list[dict]:
    """
    Arkadaşının düzenleyebileceği gibi:
      1) Önce `sorular.json` adında bir dosya var mı diye bakar (klasörde).
         Eğer varsa ve JSON olarak okunabiliyorsa ONUNKINI kullanır.
      2) JSON yoksa ya da bozuksa `_GOMULU_SORULAR` listesini kullanır.
      3) Sonuçta en az 4 geçerli soru olduğundan emin olur.
    """
    try:
        import json as _json
        import os as _os
        p = _os.path.join(_os.path.dirname(__file__) or ".", "sorular.json")
        if _os.path.isfile(p):
            with open(p, "r", encoding="utf-8") as f:
                veri = _json.load(f)
            # Geçerli mi kontrol et
            if isinstance(veri, list) and len(veri) >= 4 and all(
                isinstance(s, dict)
                and "soru" in s
                and isinstance(s.get("secenekler"), list)
                and len(s["secenekler"]) == 4
                and isinstance(s.get("dogru"), int)
                and 0 <= s["dogru"] <= 3
                for s in veri
            ):
                return [dict(s) for s in veri]   # kopya dön
            print(
                "[uyarı] sorular.json okundu ama formatı hatalı; "
                "gömülü sorular kullanılacak.", file=sys.stderr,
            )
    except Exception as e:
        print(f"[uyarı] sorular.json okunamadı: {e}", file=sys.stderr)
    # Gömülü havuz (yukarıda) — en az 4 garanti
    havuz = [dict(s) for s in _GOMULU_SORULAR]
    return havuz if len(havuz) >= 4 else list(_GOMULU_SORULAR)


class OgrenciQuizEkrani(QWidget):
    """
    BÜYÜK PROFİL RESMİ KALDIRILDI (kullanıcı isteği üzerine).
    Artık sadece:
      - Üstte: Başlık + Yıldız sayısı
      - Ortada: Büyük soru metni
      - Altında: 4 adet şık butonu (2x2 ızgara)
      - En altta: (isteğe bağlı) Quiz bitirme butonu
    """

    # Havuzu doldur (harici JSON'a bağlayan fonksiyon)
    SORULAR: list[dict] = _sorulari_yukle()

    def __init__(self, ana_pencere):
        super().__init__()
        self.ana = ana_pencere
        self.yildiz_sayisi = 0
        self.soru_index = -1
        self.butonlar = []
        self._ogr_ad = "Öğrenci"
        self._ogr_cinsiyet = "kiz"
        # QGraphicsOpacityEffect — GEÇİŞ ANİMASYONU için opacity kontrolü
        try:
            self._eff_opak = QGraphicsOpacityEffect(self)
            self._eff_opak.setOpacity(1.0)
            self.setGraphicsEffect(self._eff_opak)
        except Exception:
            self._eff_opak = None
        self._anim_gecis = None   # QPropertyAnimation tutarız
        self._arayuz_olustur()
        self.yeni_soru()

    # ------------------------------------------------------------------
    # Animasyon: öğrenci sayfasına ilk girildiğinde / her seferinde
    # 1) Opacity: 0 → 1  (fade-in)
    # 2) Pos     : +60 px sağdan → normal (sağdan kayma)
    # ------------------------------------------------------------------
    def giris_animasyonu_baslat(self, sure_ms: int = 360):
        # Eğer zaten çalışıyorsa önce eski animasyonu temizle
        try:
            if self._anim_gecis is not None:
                try:
                    self._anim_gecis.stop()
                except Exception:
                    pass
                try:
                    self._anim_gecis.setParent(None)
                except Exception:
                    pass
                self._anim_gecis = None
        except Exception:
            self._anim_gecis = None
        # 1) Opacity efektini sıfırla
        if self._eff_opak is not None:
            self._eff_opak.setOpacity(0.0)
        # 2) Pos: parent'a göre şu anki pos'unu al, +60 px sağa taşı
        parent = self.parentWidget()
        hedef_pos = self.pos()
        baslangic_pos = None
        if parent is not None:
            try:
                baslangic_pos = self.pos()
                # Sağdan kayma = +60 px ek X ötelemesi
                baslangic_pos = baslangic_pos + QPoint(60, 0)
                hedef_pos = self.pos()
            except Exception:
                baslangic_pos = None
        try:
            anim = QPropertyAnimation(self, b"pos", self)
            anim.setDuration(sure_ms)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            if baslangic_pos is not None:
                anim.setStartValue(baslangic_pos)
            anim.setEndValue(hedef_pos)
            anim.start()
            self._anim_gecis = anim
        except Exception:
            self._anim_gecis = None
        # Opacity animasyonu ayrı bir QPropertyAnimation
        if self._eff_opak is not None:
            try:
                anim2 = QPropertyAnimation(self._eff_opak, b"opacity", self)
                anim2.setDuration(int(sure_ms * 0.95))
                anim2.setStartValue(0.0)
                anim2.setEndValue(1.0)
                anim2.setEasingCurve(QEasingCurve.Type.OutCubic)
                anim2.start()
                # anim2 saklanmasına gerek yok; eff parent bizim old için gc'den korunur
            except Exception:
                pass
        # Eğer opacity effect yoksa fallback: kendimiz QTimer ile görünürlük
        if self._eff_opak is None:
            try:
                self.hide()
                QTimer.singleShot(0, lambda w=self: w.show())
            except Exception:
                pass

    # Ana pencere tarafından dışarıdan güncellenir
    def profil_guncelle(self, ad: str, cinsiyet: str):
        self._ogr_ad = ad if ad else "Öğrenci"
        self._ogr_cinsiyet = cinsiyet if cinsiyet in ("kiz", "erkek") else "kiz"
        self.baslik.setText(f"🎒   {self._ogr_ad}, Quiz Macerası!")
        # Mascot KALDIRILDI — o satır yok

    def _arayuz_olustur(self):
        dis = QVBoxLayout(self)
        dis.setContentsMargins(34, 26, 34, 18)
        dis.setSpacing(20)

        # ------------------------------------------------------------------
        # Üst bilgi (yıldız + başlık) — Mascot KALDIRILDI
        # ------------------------------------------------------------------
        ust_satir = QHBoxLayout()
        ust_satir.setSpacing(12)

        self.baslik = QLabel(f"🎒   {self._ogr_ad}, Quiz Macerası!")
        self.baslik.setObjectName("Baslik")
        self.baslik.setFont(turkce_font(17, True))
        ust_satir.addWidget(self.baslik, 1)

        self.yildiz_lbl = QLabel("⭐ 0")
        self.yildiz_lbl.setFont(turkce_font(16, True))
        self.yildiz_lbl.setStyleSheet(
            "background-color:#fff3b0; border-radius:14px;"
            "padding: 10px 16px; border:2px solid #f5c518;"
        )
        ust_satir.addWidget(self.yildiz_lbl)

        dis.addLayout(ust_satir)

        # (Masco KALDIRILDI)

        # ------------------------------------------------------------------
        # Soru metin alanı — daha büyük font, daha fazla padding
        # ------------------------------------------------------------------
        self.soru_lbl = QLabel("Soru hazırlanıyor...")
        self.soru_lbl.setObjectName("SoruAlani")
        self.soru_lbl.setWordWrap(True)
        self.soru_lbl.setFont(turkce_font(22, True))
        self.soru_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.soru_lbl.setMinimumHeight(140)
        self.soru_lbl.setStyleSheet(
            "QLabel#SoruAlani { background-color: #ffffff;"
            " border: 2px solid #bde0fe;"
            " border-radius: 22px; padding: 26px 28px; color: #1d3557; }"
        )
        dis.addWidget(self.soru_lbl, 1)

        # ------------------------------------------------------------------
        # 4 adet cevap butonu (2x2 ızgara) — butonlar biraz daha büyütüldü
        # ------------------------------------------------------------------
        ızgara = QGridLayout()
        ızgara.setHorizontalSpacing(16)
        ızgara.setVerticalSpacing(16)

        for i in range(4):
            btn = QPushButton(f"Seçenek {i+1}")
            btn.setObjectName("CevapButon")
            btn.setFont(turkce_font(14, False))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setProperty("index", i)
            btn.setMinimumHeight(80)
            btn.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
            )
            btn.clicked.connect(lambda _, ix=i: self.cevap_secildi(ix))
            satir, sutun = divmod(i, 2)
            ızgara.addWidget(btn, satir, sutun)
            self.butonlar.append(btn)
        dis.addLayout(ızgara, 2)

        # -------------------- Çocuk Ekranı Çıkış Butonu --------------------
        # (arkadaşının API: finished.emit("tamamlandi") — çocuk ekranı tamamlanınca)
        bitir_satir = QHBoxLayout()
        bitir_satir.addStretch(1)

        # Toplam soru / doğru sayısı özeti
        self._ozet_lbl = QLabel("")
        self._ozet_lbl.setFont(turkce_font(11, True))
        self._ozet_lbl.setStyleSheet("color:#457b9d;")
        bitir_satir.addWidget(self._ozet_lbl)

        self._bitir_sonuc = QLabel("")
        self._bitir_sonuc.setFont(turkce_font(11, True))
        bitir_satir.addWidget(self._bitir_sonuc)

        bitir_btn = QPushButton("🏁  Quiz'i Bitir / Ana Menü")
        bitir_btn.setFont(turkce_font(13, True))
        bitir_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        bitir_btn.setStyleSheet(
            "QPushButton { background-color: #4361ee; color: white;"
            " border: none; border-radius: 16px; padding: 12px 20px;"
            " min-height: 44px; }"
            " QPushButton:hover { background-color: #3a56d4; }"
            " QPushButton:pressed { background-color: #2d46b9; }"
        )
        bitir_btn.clicked.connect(self._quiz_bitir)
        bitir_satir.addWidget(bitir_btn)
        bitir_satir.addStretch(1)
        dis.addLayout(bitir_satir)

    # --- Quiz çıkışını bildiren bridge sinyali (çocuk ekranı bitti) ---
    def _quiz_bitir(self):
        try:
            self._bitir_sonuc.setStyleSheet("color:#2d6a4f;")
            self._bitir_sonuc.setText(
                f"✅  Sinyal yayınlandı ({self.yildiz_sayisi} ⭐)"
            )
            # Arkadaşının istediği API:
            #     finished.emit("tamamlandi")
            try:
                self.ana.bridge.guvenli_emit("tamamlandi")
            except Exception:
                try:
                    self.ana.bridge.finished.emit("tamamlandi")
                except Exception:
                    pass
            # Görsel dönüş: kısa süre sonra giriş ekranına geri dön
            def _geridon():
                try:
                    self.ana.goruntu_degistir("giris")
                    self._bitir_sonuc.setText("")
                except Exception:
                    pass
            QTimer.singleShot(450, _geridon)
        except Exception as e:
            print(f"quiz_bitir hatasi: {e}", file=sys.stderr)

    # -------------------- Soru / cevap mantığı --------------------
    def yeni_soru(self):
        """Rastgele bir soru seçip arayüze yansıtır."""
        try:
            havuz = _sorulari_yukle()   # her seferinde JSON'u tazele (arkadaşın sonradan eklediğini görür)
            if len(havuz) > 0:
                # Sınıfın kendi SORULAR listesini de güncelle (kararlılık için)
                OgrenciQuizEkrani.SORULAR = havuz
        except Exception:
            pass
        toplam = len(OgrenciQuizEkrani.SORULAR)
        if toplam <= 0:
            return
        self.soru_index = (self.soru_index + 1) % toplam
        soru_kelime = OgrenciQuizEkrani.SORULAR[self.soru_index]
        # Seçenekleri karıştır ama doğru seçeneği yeni indekse göre takip et
        dogru_metin = soru_kelime["secenekler"][soru_kelime["dogru"]]
        secenekler = list(soru_kelime["secenekler"])
        random.shuffle(secenekler)
        yeni_dogru = secenekler.index(dogru_metin)

        self._aktif_dogru = yeni_dogru
        self.soru_lbl.setText(soru_kelime["soru"])

        for btn, metin in zip(self.butonlar, secenekler):
            btn.setText(metin)
            btn.setEnabled(True)
            # Sıfırlama: dinamik özellikleri kaldırmak için
            btn.setProperty("dogru", False)
            btn.setProperty("yanlis", False)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        # Özet etiketini güncelle
        try:
            self._ozet_lbl.setText(
                f"Soru {self.soru_index + 1} / {len(OgrenciQuizEkrani.SORULAR)}"
            )
        except Exception:
            pass

        # Mascot artık yok — self.mascot.sasir() KALDIRILDI

    def cevap_secildi(self, index: int):
        dogru_mu = index == self._aktif_dogru
        # Görsel geri bildirim
        for i, btn in enumerate(self.butonlar):
            btn.setEnabled(False)
            if i == self._aktif_dogru:
                btn.setProperty("dogru", True)
            elif i == index and not dogru_mu:
                btn.setProperty("yanlis", True)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        if dogru_mu:
            self.yildiz_sayisi += 1
            self.yildiz_lbl.setText(f"⭐ {self.yildiz_sayisi}")
            # Mascot KALDIRILDI — yerine soru alanı yeşil flash
            self._alan_flash("dogru")
        else:
            # Mascot KALDIRILDI — yerine soru alanı kırmızı flash
            self._alan_flash("yanlis")

        # Kısa bir geri bildirim sonrası sonraki soruya geç
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(1400, self.yeni_soru)

    # --- Soru alanına renkli flash efekti (mascot kaldırıldı yerine) ---
    def _alan_flash(self, tip: str):
        if tip == "dogru":
            arka = "#d8f3dc"   # açık yeşil
            kenar = "#40916c"
        else:
            arka = "#ffd6d6"   # açık kırmızı
            kenar = "#e63946"
        eski_stil = (
            "QLabel#SoruAlani { background-color: %s;"
            " border: 2px solid %s; border-radius: 22px;"
            " padding: 26px 28px; color: #1d3557; }"
        ) % (arka, kenar)
        self.soru_lbl.setStyleSheet(eski_stil)
        # 600 ms sonra geri normal
        def _geri():
            try:
                self.soru_lbl.setStyleSheet(
                    "QLabel#SoruAlani { background-color: #ffffff;"
                    " border: 2px solid #bde0fe; border-radius: 22px;"
                    " padding: 26px 28px; color: #1d3557; }"
                )
            except Exception:
                pass
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(600, _geri)


# ---------------------------------------------------------------------------
# Ayarlar Diyaloğu
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Ayarlar Ekrani (ARTIK BİR QDialog DEĞİL, stacked widget'ta bir sayfa)
# Kullanıcı isteği: Ayarlar sekmesini uygulama İÇİNDE bir pencere olarak göster.
# Eski AyarlarDialog kaldırıldı; yerine bu sınıf.
# ---------------------------------------------------------------------------
class AyarlarEkrani(QWidget):
    """
    İçerik aynıdır (zorluk, soru sayısı, ses, herzaman üstte); ama:
     * Ana içerikle aynı pencerede (stacked widget içinde) gösterilir.
     * Üstte bir başlık çubuğu, altta Kaydet / Geri Dön butonları.
     * Kaydedilince AnaPencere.ayarlara uygular (eski Dialog.Accepted akışı gibi).
    """
    def __init__(self, ana_pencere):
        super().__init__()
        self.ana = ana_pencere
        self._kayit_sonuc_lbl = None
        self._arayuz_olustur()

    # ------ UI ------
    def _arayuz_olustur(self):
        dis = QVBoxLayout(self)
        dis.setContentsMargins(34, 24, 34, 24)
        dis.setSpacing(18)

        # --- Üst başlık ---
        baslik_satir = QHBoxLayout()
        baslik = QLabel("⚙   Uygulama Ayarları")
        baslik.setFont(turkce_font(18, True))
        baslik.setStyleSheet("color:#1d3557;")
        baslik_satir.addWidget(baslik)
        baslik_satir.addStretch(1)
        # Anında geri (vazgeç) butonu
        vazgec = QPushButton("↩  Geri Dön")
        vazgec.setFont(turkce_font(12, True))
        vazgec.setCursor(Qt.CursorShape.PointingHandCursor)
        vazgec.setStyleSheet(
            "QPushButton { background-color:#f8edeb; color:#6d6875;"
            " border:none; border-radius:14px; padding: 10px 16px;"
            " min-height:40px; }"
            " QPushButton:hover { background-color:#f4dcd6; color:#3d3a3a; }"
        )
        vazgec.clicked.connect(lambda: self.ana.goruntu_degistir("giris"))
        baslik_satir.addWidget(vazgec)
        dis.addLayout(baslik_satir)

        # --- Form kutusu (kart görünümü) ---
        kutu = QFrame()
        kutu.setStyleSheet(
            "QFrame { background-color: #ffffff; border-radius: 22px;"
            " border: 2px solid #bde0fe; }"
        )
        form_kat = QVBoxLayout(kutu)
        form_kat.setContentsMargins(26, 22, 26, 22)
        form_kat.setSpacing(16)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        form.setHorizontalSpacing(20)
        form.setVerticalSpacing(18)

        # Mevcut ayarları AnaPencere'den oku (yoksa varsayılan)
        varsayilan = getattr(self.ana, "ayarlar", {}) or {}

        # --- Zorluk ---
        self.cmb_zorluk = QComboBox()
        self.cmb_zorluk.addItems(["Kolay 🌱", "Orta 🌿", "Zor 🌳"])
        self.cmb_zorluk.setCurrentIndex(int(varsayilan.get("zorluk", 1)))
        self.cmb_zorluk.setStyleSheet(self._combo_stil())
        zorluk_lbl = QLabel("Zorluk Seviyesi:")
        zorluk_lbl.setFont(turkce_font(12, True))
        form.addRow(zorluk_lbl, self.cmb_zorluk)

        # --- Soru sayısı ---
        self.spn_soru_sayisi = QSpinBox()
        self.spn_soru_sayisi.setRange(5, 50)
        self.spn_soru_sayisi.setValue(int(varsayilan.get("soru_sayisi", 10)))
        self.spn_soru_sayisi.setFont(turkce_font(12))
        self.spn_soru_sayisi.setStyleSheet(self._spin_stil())
        soru_lbl = QLabel("Oturum Başına Soru:")
        soru_lbl.setFont(turkce_font(12, True))
        form.addRow(soru_lbl, self.spn_soru_sayisi)

        # --- Ses ---
        self.chk_ses = QCheckBox("Sesli geri bildirim açık kalsın 🔊")
        self.chk_ses.setChecked(bool(varsayilan.get("ses", True)))
        self.chk_ses.setFont(turkce_font(12, True))
        self.chk_ses.setStyleSheet(self._chk_stil("#ffd166"))
        form.addRow("", self.chk_ses)

        # --- Her zaman üstte ---
        self.chk_herzaman_ustte = QCheckBox("Pencere her zaman üstte kalsın 📌")
        ustte = varsayilan.get("herzaman_ustte", None)
        if ustte is None:   # ilk defa açılıyorsa pencere bayrağına bak
            from PyQt6.QtCore import Qt as _Qt
            ustte = bool(self.ana.windowFlags() & _Qt.WindowType.WindowStaysOnTopHint)
        self.chk_herzaman_ustte.setChecked(bool(ustte))
        self.chk_herzaman_ustte.setFont(turkce_font(12, True))
        self.chk_herzaman_ustte.setStyleSheet(self._chk_stil("#a2d2ff"))
        form.addRow("", self.chk_herzaman_ustte)

        form_kat.addLayout(form)
        dis.addWidget(kutu, 1)

        # --- Kayıt butonu + sonuç etiketi ---
        alt_satir = QHBoxLayout()
        alt_satir.addStretch(1)

        self._kayit_sonuc_lbl = QLabel("")
        self._kayit_sonuc_lbl.setFont(turkce_font(12, True))
        alt_satir.addWidget(self._kayit_sonuc_lbl)

        kaydet = QPushButton("💾  Ayarları Kaydet ve Uygula")
        kaydet.setFont(turkce_font(13, True))
        kaydet.setCursor(Qt.CursorShape.PointingHandCursor)
        kaydet.setStyleSheet(
            "QPushButton { background-color:#40916c; color:white;"
            " border:none; border-radius:16px; padding: 12px 22px;"
            " min-height:44px; }"
            " QPushButton:hover { background-color:#2d6a4f; }"
            " QPushButton:pressed { background-color:#1b4332; }"
        )
        kaydet.clicked.connect(self._kaydet_ve_uygula)
        alt_satir.addWidget(kaydet)
        alt_satir.addStretch(1)
        dis.addLayout(alt_satir)

    # ------ Buton / form stilleri (pastel temaya uyumlu) ------
    def _combo_stil(self) -> str:
        return (
            "QComboBox { background-color:#f1faee; color:#1d3557;"
            " border:2px solid #bde0fe; border-radius:12px;"
            " padding: 8px 12px; min-height:36px; }"
            " QComboBox:hover { border:2px solid #90cdf4; }"
            " QComboBox QAbstractItemView { background-color:#f1faee;"
            " border:1px solid #bde0fe; selection-background-color:#bde0fe;"
            " selection-color:#1d3557; padding:4px; }"
        )

    def _spin_stil(self) -> str:
        return (
            "QSpinBox { background-color:#f1faee; color:#1d3557;"
            " border:2px solid #bdb2ff; border-radius:12px;"
            " padding: 6px 10px; min-height:36px; }"
            " QSpinBox:hover { border:2px solid #a495ff; }"
        )

    def _chk_stil(self, hover_renk: str) -> str:
        return (
            "QCheckBox { spacing: 10px; padding: 4px; }"
            " QCheckBox::indicator { width:20px; height:20px; border-radius:6px;"
            " border:2px solid #c0c0c0; background:#ffffff; }"
            " QCheckBox::indicator:checked { background:" + hover_renk + ";"
            " border:2px solid " + hover_renk + "; }"
            " QCheckBox:hover { color:#1d3557; }"
        )

    # ------ Kaydet ve uygula ------
    def _kaydet_ve_uygula(self):
        ayarlar = {
            "zorluk": int(self.cmb_zorluk.currentIndex()),
            "soru_sayisi": int(self.spn_soru_sayisi.value()),
            "ses": bool(self.chk_ses.isChecked()),
            "herzaman_ustte": bool(self.chk_herzaman_ustte.isChecked()),
        }
        # Ana pencereye kaydet
        try:
            self.ana.ayarlar = dict(ayarlar)
        except Exception:
            setattr(self.ana, "ayarlar", dict(ayarlar))

        # --- Her zaman üstte bayrağını hemen uygula ---
        def _uygula_herzaman_ustte():
            try:
                self.ana.setWindowFlag(
                    Qt.WindowType.WindowStaysOnTopHint,
                    ayarlar["herzaman_ustte"],
                )
                self.ana.show()
                self.ana.raise_()
                self.ana.activateWindow()
            except Exception:
                pass
        QTimer.singleShot(0, _uygula_herzaman_ustte)

        # Kullanıcıya geri bildirim
        try:
            if self._kayit_sonuc_lbl is not None:
                self._kayit_sonuc_lbl.setStyleSheet("color:#2d6a4f;")
                self._kayit_sonuc_lbl.setText("✅  Ayarlar kaydedildi!")
                # 1.8 sn sonra label temizle
                def _temizle():
                    try:
                        if self._kayit_sonuc_lbl:
                            self._kayit_sonuc_lbl.setText("")
                    except Exception:
                        pass
                from PyQt6.QtCore import QTimer as _QT
                _QT.singleShot(1800, _temizle)
        except Exception:
            pass

        # 700ms sonra giriş ekranına geri dön (kullanıcı dostu)
        def _geridon():
            try:
                self.ana.goruntu_degistir("giris")
            except Exception:
                pass
        QTimer.singleShot(700, _geridon)

    # Eski API uyumluluğu (istediğin zaman çağrılabilir)
    def ayarlari_aktar(self):
        return {
            "zorluk": int(self.cmb_zorluk.currentIndex()),
            "soru_sayisi": int(self.spn_soru_sayisi.value()),
            "ses": bool(self.chk_ses.isChecked()),
            "herzaman_ustte": bool(self.chk_herzaman_ustte.isChecked()),
        }


# ---------------------------------------------------------------------------
# YARDIMCI: yuvarlak köşeli QRegion maskesi üretir (macOS setMask için güvenli)
# ---------------------------------------------------------------------------
def _yuvarlak_maske(boyut: QSize, yaricap: int) -> QRegion:
    """Verilen boyut için yuvarlak köşeli maske üretir.
    macOS QBitmap ile mask'de hizalama çakışması olmasın diye QImage +
    QPainterPath ile çizip Region'a çevirir."""
    w = max(1, int(boyut.width()))
    h = max(1, int(boyut.height()))
    yaricap = max(0, min(yaricap, min(w, h) // 2))
    # 1-bit mask image benzeri — ARGB32_Premultiplied üzerine siyah-dolu
    # dikdörtgen çizip createAlphaMask() ile dönüştürmek QBitmap + hizalama
    # sorunundan kaçınır.
    img = QImage(w, h, QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(QColor(0, 0, 0, 0))  # tamamen saydam
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing, False)
    path = QPainterPath()
    path.addRoundedRect(0.0, 0.0, float(w), float(h), float(yaricap), float(yaricap))
    # Tamamen opak siyah ile doldur (alpha 255)
    p.fillPath(path, QBrush(QColor(0, 0, 0, 255)))
    p.end()
    # Alpha kanalı üzerinden maske üret — 1-bit QBitmap benzeri
    alpha_bmp = QBitmap.fromImage(img.createAlphaMask())
    return QRegion(alpha_bmp)


# ---------------------------------------------------------------------------
# Ana Pencere
# ---------------------------------------------------------------------------
class AnaPencere(QWidget):
    def __init__(self):
        # macOS güvenliği: QApplication ana thread'de oluşturulmamışsa
        # raise yerine (kullanıcı yanlış thread'de çağırırsa) uyarı ver
        app = QApplication.instance()
        if app is None:
            raise RuntimeError(
                "AnaPencere oluşturulmadan önce QApplication(sys.argv) "
                "ana iş parçacığında (main thread) oluşturulmalıdır."
            )
        super().__init__()
        self.setObjectName("AnaPencere")

        # Profil bilgileri (başlangıçta boş)
        self.profil_ad = ""
        self.profil_cinsiyet = "kiz"

        # Pencere özellikleri: başlıksız çerçeve + her zaman üstte
        # macOS'ta WA_TranslucentBackground + FramelessWindowHint birlikte
        # kullanıldığında CALayer çakışması nedeniyle Python crash raporu
        # oluşuyordu. Yerine setMask ile yuvarlak köşe + QGraphicsEffect gölge.
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Window
        )

        # macOS ve Linux ortak: çerçeve artıkları olmasın diye
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, False)
        # Double-buffered render, flicker olmasın
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, False)

        self.setWindowTitle("Eğlenceli Öğrenme")
        # Boyutlandırmadan önce minimum boyut ver (macOS pencere yeniden
        # yaratma sırasında 0x0 pencere oluşturmasını önler)
        self.setMinimumSize(QSize(640, 480))
        self.resize(860, 640)

        self._arayuz_olustur()
        # ------------------------------------------------------------------
        # 3 PARÇALI BÜTÜNLEŞTİRME KÖPRÜSÜ (arkadaşının istediği API)
        #   * self.bridge.finished  -> pyqtSignal(str)
        #       - "tamamlandi" : çocuk ekranı bitti (emit)
        #       - "veli_cikisi": Veli PIN çıkışı (emit)
        #   * self.guard         -> ActivityGuard
        #       - guard.start(max_seconds) / .stop() / .blocked_count()
        # ------------------------------------------------------------------
        self.bridge = AppBridge(self)
        self.guard = ActivityGuard(self, parent=self)

        # Varsayılan font:
        try:
            if QApplication.instance() is not None:
                QApplication.instance().setFont(turkce_font(11))
        except Exception:
            pass

        # Başlangıçta profil seçim ekranını aç — 0ms gecikme ile
        # (layout ilk pass tamamlandıktan sonra stack değişsin)
        QTimer.singleShot(0, lambda: self.goruntu_degistir("profil"))

    # ------------------------------------------------------------------
    def _arayuz_olustur(self):
        # Dış kapsayıcı layout (macOS emniyeti: çerçevenin gölgeye alan bırakması için
        # 16px boşluk — QGraphicsEffect kullanmıyoruz)
        dis = QVBoxLayout(self)
        dis.setContentsMargins(14, 14, 14, 14)
        dis.setSpacing(0)

        # İçerik çerçevesi (yuvarlak köşeleri olan ana beyaz/alacalı alan)
        self.ic_cerceve = QFrame()
        self.ic_cerceve.setObjectName("AnaPencere")
        # macOS PyQt6 crash kaynakları: QGraphicsEffect kullanmıyoruz
        # (AnimasyonluKart da kendi paintEvent'inde elle gölge çiziyor).
        ic_katman = QVBoxLayout(self.ic_cerceve)
        ic_katman.setContentsMargins(0, 0, 0, 0)
        ic_katman.setSpacing(0)

        # Özel başlık çubuğu (çerçevesiz pencere için)
        ic_katman.addLayout(self._ozel_baslik_cubugu())

        # İçerik alanı: stacked widget
        self.stack = QStackedWidget()
        ic_katman.addWidget(self.stack, 1)

        # Sayfaları oluştur
        self.sayfa_profil = ProfilEkrani(self)
        self.sayfa_giris = GirisEkrani(self)
        self.sayfa_veli = VeliPaneli(self)
        self.sayfa_ogretmen = OgretmenPaneli(self)
        self.sayfa_ogrenci = OgrenciQuizEkrani(self)
        # (Kullanıcı isteği) Ayarlar şimdi bir sayfa (stacked widget içinde)
        self.sayfa_ayarlar = AyarlarEkrani(self)

        self.stack.addWidget(self.sayfa_profil)      # index 0
        self.stack.addWidget(self.sayfa_giris)       # index 1
        self.stack.addWidget(self.sayfa_veli)        # index 2
        self.stack.addWidget(self.sayfa_ogretmen)    # index 3
        self.stack.addWidget(self.sayfa_ogrenci)     # index 4
        self.stack.addWidget(self.sayfa_ayarlar)     # index 5  ← YENİ

        # Alt çubuk (ayarlar butonu vb.)
        ic_katman.addWidget(self._alt_cubuk_olustur())

        dis.addWidget(self.ic_cerceve)

    # ------------------------------------------------------------------
    def profil_kaydet(self, ad: str, cinsiyet: str):
        """Profil ekranından çağrılır; bilgileri kaydedip ilgili yerlere iletir."""
        self.profil_ad = ad.strip() or "Öğrenci"
        self.profil_cinsiyet = cinsiyet if cinsiyet in ("kiz", "erkek") else "kiz"

        # macOS: widget güncellemeleri, henüz layout geçmemiş stacked widget sayfalarında
        # paint tetiklemek yerine 0ms sonra yap ki event döngüsüne bırakalım
        def _guncelle():
            try:
                # Giriş sayfasındaki öğrenci kartını güncelle
                if hasattr(self, "sayfa_giris"):
                    self.sayfa_giris.ogrenci_adi_guncelle(self.profil_ad)
                    self.sayfa_giris.ogrenci_gorsel_guncelle(self.profil_cinsiyet)
            except Exception:
                pass
            try:
                # Quiz sayfasını güncelle
                if hasattr(self, "sayfa_ogrenci"):
                    self.sayfa_ogrenci.profil_guncelle(self.profil_ad, self.profil_cinsiyet)
            except Exception:
                pass
        QTimer.singleShot(0, _guncelle)

    # ------------------------------------------------------------------
    def _ozel_baslik_cubugu(self) -> QHBoxLayout:
        """FramelessWindowHint olduğu için basit bir başlık + kapat butonu."""
        satir = QHBoxLayout()
        satir.setContentsMargins(20, 12, 16, 0)
        satir.setSpacing(8)

        logo = QLabel("🌈")
        logo.setFont(turkce_font(18))
        satir.addWidget(logo)

        lbl = QLabel("Eğlenceli Öğrenme Uygulaması")
        lbl.setFont(turkce_font(13, True))
        lbl.setStyleSheet("color:#1d3557;")
        satir.addWidget(lbl)

        satir.addStretch(1)

        kapat = QPushButton("✕")
        kapat.setFixedSize(32, 32)
        kapat.setCursor(Qt.CursorShape.PointingHandCursor)
        kapat.setToolTip("Uygulamayı kapat")
        kapat.setStyleSheet("""
            QPushButton {
                background-color:#ff6b6b; color:white; border:none;
                border-radius:16px; font-weight:bold; font-size:14px;
            }
            QPushButton:hover { background-color:#ef4444; }
        """)
        kapat.clicked.connect(self.close)
        satir.addWidget(kapat)

        # Sürükleme için değişkenler
        self._surukle_baslangic = None
        return satir

    # ------------------------------------------------------------------
    def _alt_cubuk_olustur(self) -> QFrame:
        cubuk = QFrame()
        cubuk.setObjectName("AltCubuk")
        # (KULLANICI İSTEĞİ) Alt çubuğun arka plan rengi pastel beyaz + ince üst
        # ayraç çizgisi ile uygulamaya daha uyumlu (daha temiz) görünsün.
        cubuk.setStyleSheet(
            "QFrame#AltCubuk {"
            " background-color: #f8fbff;"
            " border-top: 1px solid #cfe2ff;"
            "}"
        )
        satir = QHBoxLayout(cubuk)
        satir.setContentsMargins(18, 10, 18, 12)
        satir.setSpacing(12)

        # --- Ortak pastel buton üretici (uygulamaya uyumlu) ---
        def _buton_olustur(
            metin: str,
            arka: str,
            hover: str,
            yazi: str = "#1d3557",
            kenar: str = "#d6e4ff",
            ikon_sol: str = "",
        ) -> QPushButton:
            b = QPushButton((ikon_sol + "  " + metin).strip() if ikon_sol else metin)
            b.setObjectName("AltButon")
            b.setFont(turkce_font(12, True))
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setMinimumHeight(46)
            b.setStyleSheet(
                "QPushButton#AltButon {"
                f" background-color: {arka};"
                f" color: {yazi};"
                f" border: 2px solid {kenar};"
                " border-radius: 18px;"
                " padding: 10px 18px;"
                "}"
                " QPushButton#AltButon:hover {"
                f" background-color: {hover};"
                " border: 2px solid #90cdf4;"
                "}"
                " QPushButton#AltButon:pressed {"
                " background-color: #d8e7ff;"
                " border: 2px solid #5a9eff;"
                "}"
            )
            return b

        # 1) Geri (Giriş Ekranı) — pastel mavi
        self.geri_btn = _buton_olustur(
            "Giriş Ekranı",
            arka="#e8f1ff", hover="#d5e6ff",
            yazi="#1d3557", kenar="#cfe2ff",
            ikon_sol="⬅",
        )
        self.geri_btn.clicked.connect(lambda: self.goruntu_degistir("giris"))
        satir.addWidget(self.geri_btn)

        # 2) Mola / Kilit — pastel turuncu (veli renk)
        self.mola_btn = _buton_olustur(
            "Mola / Kilit",
            arka="#fff1dd", hover="#ffe3c2",
            yazi="#6b3e02", kenar="#ffd8a8",
            ikon_sol="⏸",
        )
        self.mola_btn.clicked.connect(self._mola_toggle)
        satir.addWidget(self.mola_btn)

        # 3) Rapor (Bloke Sayısı) — pastel mor (öğretmen rengi)
        self.rapor_btn = _buton_olustur(
            "Bloke Sayısı",
            arka="#efecff", hover="#dfd9ff",
            yazi="#2d1b69", kenar="#cdc1ff",
            ikon_sol="📊",
        )
        self.rapor_btn.clicked.connect(self._rapor_goster)
        satir.addWidget(self.rapor_btn)

        satir.addStretch(1)

        # 4) Ayarlar — pastel nane yeşili (öğrenci rengi)
        ayarlar_btn = _buton_olustur(
            "Ayarlar",
            arka="#e8ffe3", hover="#d4ffc9",
            yazi="#1b4332", kenar="#b7e4c7",
            ikon_sol="⚙",
        )
        # (KULLANICI İSTEĞİ) Artık QDialog değil — stacked widget içinde
        # "ayarlar" sayfasına yönlendir (AyarlarEkrani).
        ayarlar_btn.clicked.connect(lambda: self.goruntu_degistir("ayarlar"))
        satir.addWidget(ayarlar_btn)

        return cubuk

    # ---- Mola butonu (guard API) ----
    def _mola_toggle(self):
        try:
            if self.guard.aktif_mi():
                # İkinci basış: Kilit / Mola DURDUR (guard.stop())
                self.guard.stop()
                try:
                    QMessageBox.information(
                        self,
                        "Kilit Açıldı",
                        "🔓  Mola / Kilit sonlandırıldı.\n"
                        f"Bu oturumda toplam {self.guard.blocked_count()} adet"
                        " dışarı çıkma girişimi engellendi.",
                    )
                except Exception:
                    pass
            else:
                # İlk basış: 5 dk mola + 2 dk ek = 420 sn KİLİT başla
                #   (arkadaşının komutu: guard.start(max_seconds=mola_suresi + 120))
                mola_suresi = 5 * 60       # 5 dakika (istediğin gibi değiştir)
                self.guard.start(max_seconds=mola_suresi + 120)
        except Exception as e:
            print(f"mola_toggle hatası: {e}", file=sys.stderr)

    # ---- Rapor butonu (guard.blocked_count() kullanılır) ----
    def _rapor_goster(self):
        try:
            blk = self.guard.blocked_count()
            kln = self.guard.kalan_saniye()
            aktif = self.guard.aktif_mi()
            # Son emit kayıtları (AppBridge)
            emitler = list(self.bridge.son_emitler()) if hasattr(self, "bridge") else []
            if aktif:
                durum = f"🟢  Aktif (Kalan: {kln // 60:02d}:{kln % 60:02d})"
            else:
                durum = "⚪  Aktif değil"
            msj = (
                "📊   Oturum Raporu (Önizleme)\n\n"
                f"Kilit / Mola durumu : {durum}\n"
                f"Bloke edilen girişim: {blk}\n"
                f"Son bridge sinyalleri: {emitler if emitler else '(henüz yayın yok)'}\n\n"
                "Bu veriler projeyi 3 parçaya böldüğünüzde arkadaşlarınızın"
                " rapor modülüne aktarılabilir.\n"
                "Kullanılan API:\n"
                "   guard.start(max_seconds=...)\n"
                "   guard.stop()\n"
                "   guard.blocked_count()  ←  şu anki değer ↑\n"
                "   bridge.finished.emit('tamamlandi' | 'veli_cikisi')"
            )
            try:
                QMessageBox.information(self, "Rapor", msj)
            except Exception:
                pass
        except Exception as e:
            print(f"rapor_goster hatası: {e}", file=sys.stderr)

    # ------------------------------------------------------------------
    def goruntu_degistir(self, anahtar: str):
        """Stacked widget içinde ilgili sayfaya geçiş yapar.
        Eğer hedef "ogrenci" (Quiz ekrani) ise ÖĞRENCİYE ÖZEL geçiş animasyonu
        (sağdan kayma + fade-in) çalıştırılır."""
        harita = {
            "profil": 0,
            "giris": 1,
            "veli": 2,
            "ogretmen": 3,
            "ogrenci": 4,
            "ayarlar": 5,
        }
        if anahtar in harita:
            hedef_idx = harita[anahtar]
            self.stack.setCurrentIndex(hedef_idx)
            # Öğrenci ekranıysa -> özel GEÇİŞ ANİMASYONU
            if anahtar == "ogrenci":
                try:
                    ekran = self.sayfa_ogrenci
                    # Layout henüz yerleşim yapmamış olabilir (sadece
                    # setCurrentIndex'ten sonra). 12 ms sonra animasyonu
                    # başlatmak daha güvenilir (hiç frame düşmeden çalışır).
                    def _calistir():
                        try:
                            if hasattr(ekran, "giris_animasyonu_baslat"):
                                ekran.giris_animasyonu_baslat(sure_ms=380)
                        except Exception as e:
                            print(f"ogrenci anim hatası: {e}", file=sys.stderr)
                    QTimer.singleShot(12, _calistir)
                except Exception as e:
                    print(f"goruntu_degistir ogrenci anim hatası: {e}", file=sys.stderr)

    # (eski) def ayarlar_ac KALDIRILDI — Ayarlar artık AyarlarEkrani (stacked 5.index)
    # Alt çubuk "⚙ Ayarlar" butonu doğrudan goruntu_degistir("ayarlar") çağırır.

    # ------------------------------------------------------------------
    # macOS emniyeti: WA_TranslucentBackground KULLANILMIYOR.
    # setMask() / QBitmap kombinasyonu PyQt6 6.6+ macOS sürümlerinde
    # SIGSEGV (139) yapabiliyor. Yerine QSS border-radius kullanılır.
    # resizeEvent içinde pencere yeniden boyutlanınca QSS otomatik uygulanır,
    # biz ayrıca bir şey yapmayız (çerçeve maskesi yok, opak pencere).
    # ------------------------------------------------------------------
    def resizeEvent(self, event):
        super().resizeEvent(event)
        # ActivityGuard badge'ini yeniden yerleştir
        try:
            g = getattr(self, "guard", None)
            if g is not None:
                g.pencere_resize_hook()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Yuvarlak köşe dışı artık çizmemesi için paintEvent sadeleştirdik;
    # gölge çerçeve üzerinden QGraphicsEffect ile çizilir.
    # ------------------------------------------------------------------
    def paintEvent(self, event):
        # Arka planı QSS'teki #AnaPencere gradyanı ile çizer
        super().paintEvent(event)

    # ------------------------------------------------------------------
    # Başlık çubuğu sürükleme desteği (macOS window recreate sonrası
    # geometry kullanımına karşı iki kez kontrol)
    # ------------------------------------------------------------------
    def mousePressEvent(self, event):
        try:
            if event.button() == Qt.MouseButton.LeftButton and event.position().y() < 60:
                fg = self.frameGeometry()
                self._surukle_baslangic = (
                    event.globalPosition().toPoint() - fg.topLeft()
                )
                event.accept()
                return
        except Exception:
            self._surukle_baslangic = None
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._surukle_baslangic is not None and (
            event.buttons() & Qt.MouseButton.LeftButton
        ):
            try:
                self.move(
                    event.globalPosition().toPoint() - self._surukle_baslangic
                )
                event.accept()
                return
            except Exception:
                pass
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._surukle_baslangic = None
        super().mouseReleaseEvent(event)


# ---------------------------------------------------------------------------
# 3 PARÇALI BİRLEŞTİRME İÇİN DIŞA AÇIK MODÜLER SINIF
# ---------------------------------------------------------------------------
# Arkadaşlarının bu modülü (main.py) import ederek kendi kodlarına gömebilmesi
# için tasarlandı. EMBED (iç içe yerleştirme) kullanım senaryosu:
#
#   from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout
#   import sys, main
#
#   app = QApplication(sys.argv)
#   pencere = QWidget()                # arkadaşının kendi ana penceresi
#   kat = QVBoxLayout(pencere)
#   egitim = main.EgitimUygulamasi(parent=pencere)   # EMBED
#   kat.addWidget(egitim, 1)
#
#   # API örnekleri:
#   egitim.profil_kaydet("Ayşe", "kiz")
#   egitim.soru_ekle(
#       soru="5 + 8 = ?",
#       secenekler=["11","12","13","14"],
#       dogru=2,
#       kategori="matematik",
#       zorluk=1,
#   )
#   egitim.ekran_degistir("ogrenci")   # direkt Quiz ekrani aç
#   egitim.bridge.finished.connect(lambda mesaj: print("Sinyal:", mesaj))
#
# ---------------------------------------------------------------------------
class EgitimUygulamasi(QWidget):
    """
    Eğitici oyun modülünün (3 parçalı birleşimden 1. parça) DIŞA AÇIK (public)
    sarmalayıcı widget'ı. Herhangi bir QWidget içine (ya da tek başına pencere
    olarak) yerleştirilebilir.

    --- TEK SEVİYE SINIF NESNESİ (bir örnek) ---
    * İçinde AnaPencere'nin stack yapısı + bütün sayfalar + alt çubuk
      (üstteki kırmızı kapat butonu yoktur; embedder kapatma işini yapar).

    --- Dış API (arkadaşlarının çağıracağı metotlar) ---
      * profil_kaydet(ad, cinsiyet)         : Profil ismi + cinsiyet
      * profil_oku()                        : {"ad":..,"cinsiyet":..} döner
      * ekran_degistir(anahtar)             : "profil"|"giris"|"veli"|
                                                "ogretmen"|"ogrenci"|"ayarlar"
      * ayarlari_uygula(dict)               : zorluk/soru_sayisi/ses/herzaman_ustte
      * ayarlari_oku()                      : mevcut ayarlar sözlüğü
      * soru_ekle(soru, secenekler, dogru, kategori=None, zorluk=None)
                                            : Havuz YENİ SORU ekle (JSON'u güncelle)
      * soru_havuzunu_degistir(list[dict])  : Havuzu TAMAMEN DEĞİŞTİR (JSON kayıt)
      * soru_havuzunu_oku()                 : Mevcut havuzu liste olarak dön
      * get_bridge() / .bridge özniteliği   : pyqtSignal(str) → finished
      * get_guard()  / .guard  özniteliği   : ActivityGuard (start/stop/blocked_count)
      * start_quiz(istenen_soru_sayisi=None): Direkt Quiz ekranına geç + animasyon
      * stop_quiz()                         : Quiz'den çıkış + "tamamlandi" emit
    """

    # Arkadaşlarının kolay referans olması için SINIF SEVİYESİ sabitler
    EKRANLAR = ("profil", "giris", "veli", "ogretmen", "ogrenci", "ayarlar")

    def __init__(self, parent=None, include_title_bar: bool = False):
        """
        Parametreler:
          parent            : İsteğe bağlı üst widget (embed için kullanılır).
                              None ise widget bağımsızdır.
          include_title_bar : True ise üstte Uygulama Başlığı + ✕ kapat butonu
                              gösterilir. Standalone kullanım için önerilir.
                              False ise sadece içerik (arkadaşı kendisi pencere
                              yönetimini yapıyor demektir).
        """
        super().__init__(parent)
        # ------------------------------------------------------------------
        # High-Dpi ayarı QApplication yaratım ÖNCESİ olmalı. Eğer QApplication
        # HALİHAZIRDA varsa (arkadaşı embed etmiş) atla; yoksa önce high-dpi
        # ayarla, sonra QApplication yarat.
        # ------------------------------------------------------------------
        app_mevcut = QApplication.instance()
        if app_mevcut is None:
            try:
                from PyQt6.QtGui import QGuiApplication as _QG
                try:
                    _QG.setHighDpiScaleFactorRoundingPolicy(
                        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
                    )
                except Exception:
                    pass
            except Exception:
                pass
        app = QApplication.instance()
        if app is None:
            import sys as _sys
            app = QApplication(_sys.argv)
        try:
            app.setStyleSheet(GLOBAL_QSS)
        except Exception:
            pass
        try:
            app.setFont(turkce_font(11))
        except Exception:
            pass

        # İç yapıda doğrudan AnaPencere'yi kullanmak yerine onun stack yapısını
        # ve bütün sayfalarını BU widget içinde oluşturuyoruz. Üst başlık
        # çubuğunu istersek ekliyoruz (arkaşının penceresine embed için atlıyoruz).
        self._kurulum = False
        self._sayfa_ayarlar = None
        self._sayfa_profil = None
        self._sayfa_giris = None
        self._sayfa_veli = None
        self._sayfa_ogretmen = None
        self._sayfa_ogrenci = None
        self.stack = None
        self.bridge: AppBridge | None = None
        self.guard: ActivityGuard | None = None
        self.ayarlar: dict = {}
        # üst başlık cubugu
        self._include_title_bar = include_title_bar
        self._kapat_butonu = None
        self._kaynak_ana_pencere_sinif = AnaPencere

        self._kurulum_yap()
        self._kurulum = True

    # ==================================================================
    # Dahili: stack / sayfalar / bridge / guard / alt cubuk kurulumu
    # ==================================================================
    def _kurulum_yap(self):
        dis = QVBoxLayout(self)
        # Eğer parent verildiyse (embed) kenar boşlukları 0; değilse 14
        if self.parentWidget() is None:
            dis.setContentsMargins(14, 14, 14, 14)
            self.setObjectName("EgitimUygulamasiRoot")
            self.setStyleSheet(
                "QWidget#EgitimUygulamasiRoot { background: transparent; }"
            )
        else:
            dis.setContentsMargins(0, 0, 0, 0)
        dis.setSpacing(0)

        # İç çerçeve (yuvarlak ana alan — eskiden AnaPencere.ic_cerceve)
        cerceve = QFrame()
        cerceve.setObjectName("AnaPencere")
        cerceve.setStyleSheet(
            "QFrame#AnaPencere { background-color: #f6faff;"
            " border-radius: 24px; border: none; }"
        )
        cer_kat = QVBoxLayout(cerceve)
        cer_kat.setContentsMargins(0, 0, 0, 0)
        cer_kat.setSpacing(0)

        if self._include_title_bar:
            cer_kat.addLayout(self._baslik_cubugu_olustur())

        self.stack = QStackedWidget(cerceve)
        cer_kat.addWidget(self.stack, 1)

        # --- Sayfaları oluştur (self referansıyla, yani EgitimUygulamasi)
        # Bu sayfalar "self.ana" üzerinden ayarlara / guard / bridge erişecek.
        # Bu yüzden self nesnesine AnaPencere gibi görünen öznitelikler eklenir.
        def _ana_pencere_api_sunum(self_=self):
            # Sayfaların çağırdığı "ana.goruntu_degistir()" diye bir metot var;
            # onu biz sağlıyoruz (self.ekran_degistir ile aynı).
            def goruntu_degistir(anahtar: str):
                self_.ekran_degistir(anahtar)
            self_.goruntu_degistir = goruntu_degistir
            # Profil bilgileri (ProfilEkrani tarafından beklenir)
            self_.profil_ad = ""
            self_.profil_cinsiyet = "kiz"
        _ana_pencere_api_sunum()

        self._sayfa_profil = ProfilEkrani(self)       # self.ana = bu nesne
        self._sayfa_giris = GirisEkrani(self)
        self._sayfa_veli = VeliPaneli(self)
        self._sayfa_ogretmen = OgretmenPaneli(self)
        self._sayfa_ogrenci = OgrenciQuizEkrani(self)
        self._sayfa_ayarlar = AyarlarEkrani(self)

        self.stack.addWidget(self._sayfa_profil)    # 0
        self.stack.addWidget(self._sayfa_giris)     # 1
        self.stack.addWidget(self._sayfa_veli)      # 2
        self.stack.addWidget(self._sayfa_ogretmen)  # 3
        self.stack.addWidget(self._sayfa_ogrenci)   # 4
        self.stack.addWidget(self._sayfa_ayarlar)   # 5

        # Alt çubuk (aynı _alt_cubuk_olustur — AnaPencere sınıfından uyarlanmış)
        cubuk = self._alt_cubuk_olustur_embed()
        cer_kat.addWidget(cubuk)

        dis.addWidget(cerceve)

        # Bridge + Guard
        self.bridge = AppBridge(self)
        self.guard = ActivityGuard(self, parent=self)

        # Varsayılan ayarlar
        self.ayarlar = {
            "zorluk": 1,
            "soru_sayisi": 10,
            "ses": True,
            "herzaman_ustte": False,   # embed'de parent window karar verir
        }
        # Ayarlar sayfasındaki form alanlarını güncelle
        try:
            self._sayfa_ayarlar.cmb_zorluk.setCurrentIndex(int(self.ayarlar["zorluk"]))
            self._sayfa_ayarlar.spn_soru_sayisi.setValue(int(self.ayarlar["soru_sayisi"]))
            self._sayfa_ayarlar.chk_ses.setChecked(bool(self.ayarlar["ses"]))
            self._sayfa_ayarlar.chk_herzaman_ustte.setChecked(bool(self.ayarlar["herzaman_ustte"]))
        except Exception:
            pass

        # Başlangıçta profil ekranına geç (0 ms sonra yerleşim tamamlandıktan)
        from PyQt6.QtCore import QTimer as _QT
        _QT.singleShot(0, lambda: self.ekran_degistir("profil"))

        if self.parentWidget() is None:
            self.resize(860, 640)
            self.setMinimumSize(640, 480)

    # ---------- Başlık çubuğu (ancak include_title_bar=True ise) ----------
    def _baslik_cubugu_olustur(self) -> QHBoxLayout:
        satir = QHBoxLayout()
        satir.setContentsMargins(20, 12, 16, 0)
        satir.setSpacing(8)
        logo = QLabel("🌈")
        logo.setFont(turkce_font(18))
        satir.addWidget(logo)
        lbl = QLabel("Eğlenceli Öğrenme Uygulaması")
        lbl.setFont(turkce_font(13, True))
        lbl.setStyleSheet("color:#1d3557;")
        satir.addWidget(lbl)
        satir.addStretch(1)
        kapat = QPushButton("✕")
        kapat.setFixedSize(32, 32)
        kapat.setCursor(Qt.CursorShape.PointingHandCursor)
        kapat.setStyleSheet(
            "QPushButton { background-color:#ff6b6b; color:white; border:none;"
            " border-radius:16px; font-weight:bold; font-size:14px; }"
            " QPushButton:hover { background-color:#ef4444; }"
        )
        kapat.clicked.connect(self.close)
        self._kapat_butonu = kapat
        satir.addWidget(kapat)
        return satir

    # ---------- Alt çubuk (embed versiyonu — AnaPencere._alt_cubuk_olustur) ----------
    def _alt_cubuk_olustur_embed(self) -> QFrame:
        cubuk = QFrame()
        cubuk.setObjectName("AltCubuk")
        cubuk.setStyleSheet(
            "QFrame#AltCubuk {"
            " background-color: #f8fbff;"
            " border-top: 1px solid #cfe2ff;"
            "}"
        )
        satir = QHBoxLayout(cubuk)
        satir.setContentsMargins(18, 10, 18, 12)
        satir.setSpacing(12)

        def _buton_olustur(metin, arka, hover, yazi="#1d3557", kenar="#d6e4ff", ikon_sol=""):
            b = QPushButton((ikon_sol + "  " + metin).strip() if ikon_sol else metin)
            b.setObjectName("AltButon")
            b.setFont(turkce_font(12, True))
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setMinimumHeight(46)
            # Önemli: QSS'te süslü parantez { } kullanıldığı için .format()
            # KeyError yapıyordu. Yerine f-string + {{ }} kaçış kullanıyoruz.
            b.setStyleSheet(
                f"""
                QPushButton#AltButon {{
                    background-color: {arka};
                    color: {yazi};
                    border: 2px solid {kenar};
                    border-radius: 18px;
                    padding: 10px 18px;
                }}
                QPushButton#AltButon:hover {{
                    background-color: {hover};
                    border: 2px solid #90cdf4;
                }}
                QPushButton#AltButon:pressed {{
                    background-color: #d8e7ff;
                    border: 2px solid #5a9eff;
                }}
                """
            )
            return b

        # 1. Giriş ekranı
        b1 = _buton_olustur("Giriş Ekranı", "#e8f1ff","#d5e6ff","#1d3557","#cfe2ff","⬅")
        b1.clicked.connect(lambda: self.ekran_degistir("giris"))
        satir.addWidget(b1)

        # 2. Mola / Kilit
        b2 = _buton_olustur("Mola / Kilit", "#fff1dd","#ffe3c2","#6b3e02","#ffd8a8","⏸")
        b2.clicked.connect(self._mola_toggle_embed)
        satir.addWidget(b2)

        # 3. Rapor
        b3 = _buton_olustur("Bloke Sayısı", "#efecff","#dfd9ff","#2d1b69","#cdc1ff","📊")
        b3.clicked.connect(self._rapor_goster_embed)
        satir.addWidget(b3)
        satir.addStretch(1)

        # 4. Ayarlar
        b4 = _buton_olustur("Ayarlar", "#e8ffe3","#d4ffc9","#1b4332","#b7e4c7","⚙")
        b4.clicked.connect(lambda: self.ekran_degistir("ayarlar"))
        satir.addWidget(b4)
        return cubuk

    # --------- (embed) mola + rapor yardımcıları ---------
    def _mola_toggle_embed(self):
        try:
            if self.guard.aktif_mi():
                self.guard.stop()
                try:
                    QMessageBox.information(
                        self, "Kilit Açıldı",
                        "🔓  Mola / Kilit sonlandırıldı.\n"
                        f"Bloke sayısı: {self.guard.blocked_count()}",
                    )
                except Exception:
                    pass
            else:
                self.guard.start(max_seconds=(5 * 60) + 120)
        except Exception:
            pass

    def _rapor_goster_embed(self):
        try:
            msj = (
                f"Bloke: {self.guard.blocked_count()}\n"
                f"Kalan sn: {self.guard.kalan_saniye()}\n"
                f"Aktif: {self.guard.aktif_mi()}\n"
                f"Son emitler: {list(self.bridge.son_emitler()) if self.bridge else []}"
            )
            QMessageBox.information(self, "Rapor", msj)
        except Exception:
            pass

    # ==================================================================
    # DIŞA AÇIK METOTLAR (PUBLIC API — arkadaşlarının kullanacağı)
    # ==================================================================

    # -------- Profil yönetimi --------
    def profil_kaydet(self, ad: str, cinsiyet: str):
        """
        Ekrandaki bütün "Öğrenci" metinlerini ad ile değiştir,
        öğrenci fotoğrafını (kız/erkek) seç.
        """
        ad = (ad or "").strip() or "Öğrenci"
        cinsiyet = cinsiyet if cinsiyet in ("kiz", "erkek") else "kiz"
        self.profil_ad = ad
        self.profil_cinsiyet = cinsiyet
        from PyQt6.QtCore import QTimer as _QT
        def _guncel():
            try:
                if self._sayfa_giris is not None:
                    self._sayfa_giris.ogrenci_adi_guncelle(ad)
                    self._sayfa_giris.ogrenci_gorsel_guncelle(cinsiyet)
            except Exception:
                pass
            try:
                if self._sayfa_ogrenci is not None:
                    self._sayfa_ogrenci.profil_guncelle(ad, cinsiyet)
            except Exception:
                pass
        _QT.singleShot(0, _guncel)

    def profil_oku(self) -> dict:
        """Mevcut profil sözlüğünü döner."""
        return {"ad": getattr(self, "profil_ad", "Öğrenci"),
                "cinsiyet": getattr(self, "profil_cinsiyet", "kiz")}

    # -------- Ekran geçişleri --------
    def ekran_degistir(self, anahtar: str):
        if anahtar not in self.EKRANLAR:
            raise ValueError(
                f"Bilinmeyen ekran: {anahtar}. Seçenekler: {self.EKRANLAR}"
            )
        harita = {"profil": 0, "giris": 1, "veli": 2, "ogretmen": 3, "ogrenci": 4, "ayarlar": 5}
        hedef = harita[anahtar]
        self.stack.setCurrentIndex(hedef)
        # Öğrenci ekranıysa fade + slide animasyonunu tetikle
        if anahtar == "ogrenci" and self._sayfa_ogrenci is not None:
            def _calistir():
                try:
                    if hasattr(self._sayfa_ogrenci, "giris_animasyonu_baslat"):
                        self._sayfa_ogrenci.giris_animasyonu_baslat(sure_ms=380)
                except Exception:
                    pass
            from PyQt6.QtCore import QTimer as _QT
            _QT.singleShot(12, _calistir)

    # -------- Ayarlar --------
    def ayarlari_uygula(self, ayarlar: dict):
        """Formdan bağımsız, sözlük üzerinden ayar ataması yapar."""
        gecerli = {}
        if "zorluk" in ayarlar and 0 <= int(ayarlar["zorluk"]) <= 2:
            gecerli["zorluk"] = int(ayarlar["zorluk"])
        if "soru_sayisi" in ayarlar and 5 <= int(ayarlar["soru_sayisi"]) <= 50:
            gecerli["soru_sayisi"] = int(ayarlar["soru_sayisi"])
        if "ses" in ayarlar:
            gecerli["ses"] = bool(ayarlar["ses"])
        if "herzaman_ustte" in ayarlar:
            gecerli["herzaman_ustte"] = bool(ayarlar["herzaman_ustte"])
        self.ayarlar = dict(self.ayarlar or {}, **gecerli)
        # Ayarlar sayfasındaki form alanlarını senkronize et (açık tekrar açanlar için)
        try:
            if self._sayfa_ayarlar is not None:
                if "zorluk" in gecerli:
                    self._sayfa_ayarlar.cmb_zorluk.setCurrentIndex(gecerli["zorluk"])
                if "soru_sayisi" in gecerli:
                    self._sayfa_ayarlar.spn_soru_sayisi.setValue(gecerli["soru_sayisi"])
                if "ses" in gecerli:
                    self._sayfa_ayarlar.chk_ses.setChecked(gecerli["ses"])
                if "herzaman_ustte" in gecerli:
                    self._sayfa_ayarlar.chk_herzaman_ustte.setChecked(gecerli["herzaman_ustte"])
        except Exception:
            pass
        # "Her zaman üstte" ayarını uygula (en üst pencereyi bulmaya çalışır)
        if "herzaman_ustte" in gecerli:
            def _uygula():
                try:
                    # Parent hiyerarşisinde en üst pencere
                    win = self.window()
                    if win is not None and win is not self:
                        win.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint,
                                          gecerli["herzaman_ustte"])
                        win.show()
                except Exception:
                    pass
            from PyQt6.QtCore import QTimer as _QT
            _QT.singleShot(0, _uygula)

    def ayarlari_oku(self) -> dict:
        return dict(self.ayarlar)

    # -------- Soru havuzu (JSON + programatik ekleme) --------
    def _json_yolu(self) -> str:
        import os as _os
        base = None
        try:
            base = _os.path.dirname(__file__)
        except Exception:
            base = None
        if not base:
            base = _os.getcwd()
        return _os.path.join(base, "sorular.json")

    def soru_havuzunu_oku(self) -> list[dict]:
        try:
            return _sorulari_yukle()
        except Exception:
            return [dict(s) for s in _GOMULU_SORULAR]

    def soru_ekle(self, soru: str, secenekler: list[str], dogru: int,
                  kategori: str | None = None, zorluk: int | None = None):
        """
        Yeni soruyu çalışma anında HAVUZA ekler. Kalıcı olması için de
        `sorular.json`'a yazar (varsa üzerine ekler).
        """
        if not isinstance(secenekler, (list, tuple)) or len(secenekler) != 4:
            raise ValueError("secenekler listesi 4 elemanlı olmalı")
        if not isinstance(dogru, int) or not (0 <= dogru <= 3):
            raise ValueError("dogru indeksi 0..3 aralığında tam sayı olmalı")
        yeni = {
            "soru": str(soru).strip(),
            "secenekler": [str(x) for x in secenekler],
            "dogru": int(dogru),
        }
        if kategori:
            yeni["kategori"] = str(kategori)
        if zorluk is not None:
            try:
                yeni["zorluk"] = int(zorluk)
            except Exception:
                pass
        # Mevcut havuzu oku, ekle
        havuz = self.soru_havuzunu_oku()
        havuz.append(yeni)
        self.soru_havuzunu_degistir(havuz)

    def soru_havuzunu_degistir(self, yeni_havuz: list[dict], kaydedilsin: bool = True):
        """
        Bütün havuzu baştan belirle. `kaydedilsin=True` ise JSON'a da yazar
        (uygulama kapanıp açılınca korunur).
        """
        # Doğrulama
        if not isinstance(yeni_havuz, list) or len(yeni_havuz) < 4:
            raise ValueError("Yeni havuz en az 4 sözlük elemanlı liste olmalı")
        for s in yeni_havuz:
            if (not isinstance(s, dict) or "soru" not in s
                    or not isinstance(s.get("secenekler"), list)
                    or len(s["secenekler"]) != 4
                    or not isinstance(s.get("dogru"), int)
                    or not (0 <= s["dogru"] <= 3)):
                raise ValueError(
                    "Her soru soru/secenekler(4)/dogru(0..3) anahtarlarına sahip olmalı"
                )
        # OgrenciQuizEkrani.SORULAR sınıf özniteliğini güncelle (hedef ekran havuzunu)
        OgrenciQuizEkrani.SORULAR = [dict(s) for s in yeni_havuz]
        # Eğer Ogrenci ekranı daha önce oluşturulduysa cache'i de tazele
        if self._sayfa_ogrenci is not None:
            try:
                self._sayfa_ogrenci.__class__.SORULAR = [dict(s) for s in yeni_havuz]
            except Exception:
                pass
        # Kalıcı yaz
        if kaydedilsin:
            try:
                import json as _json, os as _os
                yol = self._json_yolu()
                with open(yol, "w", encoding="utf-8") as f:
                    _json.dump([dict(s) for s in yeni_havuz], f, ensure_ascii=False, indent=2)
            except Exception:
                pass

    # -------- Bridge / Guard erişim (kolaylık) --------
    def get_bridge(self) -> AppBridge:
        return self.bridge

    def get_guard(self) -> ActivityGuard:
        return self.guard

    # -------- Quiz yaşam döngüsü --------
    def start_quiz(self, istenen_soru_sayisi: int | None = None):
        """Direkt Quiz ekranına geç + giris animasyonu. Eğer sayı verilirse
        ayarlardaki oturum soru sayısını da o değere zorlar."""
        if istenen_soru_sayisi is not None:
            try:
                self.ayarlari_uygula({"soru_sayisi": int(istenen_soru_sayisi)})
            except Exception:
                pass
        self.ekran_degistir("ogrenci")

    def stop_quiz(self, donulecek_ekran: str = "giris", emit_et: bool = True):
        """Quiz ekrandan çık, sinyal yayınla (emit), sonra verilen ekrana dön."""
        if emit_et and self.bridge is not None:
            try:
                self.bridge.guvenli_emit("tamamlandi")
            except Exception:
                self.bridge.finished.emit("tamamlandi")
        from PyQt6.QtCore import QTimer as _QT
        _QT.singleShot(0, lambda: self.ekran_degistir(donulecek_ekran))

    # -------- Ekstra özellik (örnek export) --------
    def mevcut_skoru_oku(self) -> dict:
        """Quiz ekranındaki yıldız sayısı, aktif soru indeksi vb. özet döner."""
        s = self._sayfa_ogrenci
        if s is None:
            return {"yildiz": 0, "soru_indeksi": -1, "toplam_soru": len(self.soru_havuzunu_oku())}
        return {
            "yildiz": int(getattr(s, "yildiz_sayisi", 0)),
            "soru_indeksi": int(getattr(s, "soru_index", -1)) + 1,
            "toplam_soru": len(self.soru_havuzunu_oku()),
            "oturum_hedef_soru": int(self.ayarlari_oku().get("soru_sayisi", 10)),
        }


# ---------------------------------------------------------------------------
# Ana Giriş (STANDALONE: python3 main.py)
# ---------------------------------------------------------------------------
def main() -> int:
    # macOS'ta QApplication'ın yalnızca ANA (main) thread üzerinde
    # oluşturulması gerekir. Aksi halde ThreadingViolation + Python crash.
    import threading
    if threading.current_thread() is not threading.main_thread():
        raise RuntimeError(
            "Uygulama yalnızca ana iş parçacığında (main thread) "
            "çalıştırılmalıdır. İş parçacığı: " + threading.current_thread().name
        )

    # HighDpi politika AYARLARI QApplication OLUŞTURULMADAN ÖNCE yapılmalı
    # — aksi halde Qt6 macOS AppKit üzerinde uyarı verir.
    try:
        from PyQt6.QtGui import QGuiApplication
        QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
    except Exception:
        pass

    # Önce mevcut bir örnek var mı diye bak (bazı IDE testleri tekrar yaratır)
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    else:
        if len(app.arguments()) <= 1 and len(sys.argv) > 1:
            pass  # dokunma

    try:
        app.setStyleSheet(GLOBAL_QSS)
    except Exception:
        pass

    try:
        app.setFont(turkce_font(11))
    except Exception:
        pass

    try:
        pencere = AnaPencere()
    except Exception as e:
        print(f"Pencere oluşturulamadı: {e}", file=sys.stderr)
        return 1

    pencere.show()

    # app.exec sonrası temizlik — macOS CoreGraphics çıkışta crash'ini engelle
    cikis_kodu = 1
    try:
        cikis_kodu = app.exec()
    except (SystemExit, KeyboardInterrupt):
        raise
    except Exception as e:
        print(f"Uygulama hatası: {e}", file=sys.stderr)
        cikis_kodu = 2
    finally:
        try:
            app.sendPostedEvents(None)
            app.processEvents()
        except Exception:
            pass
    return cikis_kodu


if __name__ == "__main__":
    sys.exit(main())
