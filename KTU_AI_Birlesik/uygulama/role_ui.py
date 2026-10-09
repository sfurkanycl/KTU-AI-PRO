"""Separate student, parent and teacher experiences backed by real records."""
from datetime import date, timedelta
import sqlite3
from PyQt6.QtCore import Qt, QRectF, QDate, QSize, QTimer, QTime
from PyQt6.QtGui import QColor, QPainter, QPen, QFont, QIcon, QPixmap
from pathlib import Path
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QLineEdit, QComboBox, QDialog, QFormLayout, QSpinBox, QDateEdit,
    QFrame, QScrollArea, QStackedWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMessageBox, QInputDialog, QCheckBox, QTimeEdit, QPlainTextEdit, QSizePolicy)
import role_store as store


STYLE = '''
QWidget { font-family: 'Segoe UI'; font-size: 15px; color: #1b304a; background: #f3f6fb; }
QLabel { background: transparent; }
QFrame#Sidebar { background: #142b49; border: none; }
QLabel#Brand { color: white; font-size: 23px; font-weight: 700; }
QLabel#SidebarCaption { color: #acc1dc; }
QPushButton#Nav { color: #d5e2f5; background: transparent; text-align: left; padding: 14px; border: none; }
QPushButton#Nav:checked, QPushButton#Nav:hover { background: #294b75; color: white; border-radius: 10px; }
QFrame#Card { background: white; border: 1px solid #e1e8f2; border-radius: 16px; }
QLabel#Title { font-size: 28px; font-weight: 700; color: #142b49; }
QLabel#Section { font-size: 19px; font-weight: 650; }
QLabel#Muted { color: #65788f; font-size: 14px; }
QLabel#Metric { font-size: 32px; font-weight: 700; color: #245fbd; }
QLabel#Error { color: #b53c48; }
QPushButton { background: #2864c7; color: white; border: none; border-radius: 9px; padding: 11px 17px; font-weight: 600; }
QPushButton:hover { background: #1e50a4; }
QPushButton:disabled { background: #dce5f0; color: #75869a; }
QPushButton#Secondary { background: #eaf0fa; color: #285794; }
QPushButton#RoleChoice { background: white; color: #244b76; border: 1px solid #ccdaed; padding: 16px; }
QPushButton#RoleChoice:checked { background: #e5efff; border: 2px solid #2864c7; }
QLineEdit, QComboBox, QSpinBox, QDateEdit, QTimeEdit, QPlainTextEdit { background: white; color: #1b304a; border: 1px solid #bccde2; border-radius: 8px; padding: 9px; min-height: 20px; }
QComboBox QAbstractItemView { background: white; color: #1b304a; selection-background-color: #e5efff; selection-color: #142b49; }
QScrollArea { border: none; background: transparent; }
QTableWidget { background: white; alternate-background-color: #f6f9fe; color: #1b304a; border: none; gridline-color: #e9eef5; selection-background-color: #e5efff; selection-color: #142b49; }
QHeaderView::section { background: #edf3fc; color: #45617f; border: none; padding: 12px; font-weight: 600; }
QDialog { background: #f3f6fb; }
'''


def label(text, kind=None):
    item = QLabel(text)
    item.setTextFormat(Qt.TextFormat.PlainText)
    item.setWordWrap(True)
    if kind:
        item.setObjectName(kind)
    return item


def button(text, callback, secondary=False):
    item = QPushButton(text)
    item.setCursor(Qt.CursorShape.PointingHandCursor)
    item.clicked.connect(callback)
    if secondary:
        item.setObjectName('Secondary')
    return item


def card(title=None):
    frame = QFrame()
    frame.setObjectName('Card')
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(20, 18, 20, 18)
    layout.setSpacing(12)
    if title:
        layout.addWidget(label(title, 'Section'))
    return frame, layout


class Chart(QWidget):
    def __init__(self, kind, data, parent=None):
        super().__init__(parent)
        self.kind, self.data = kind, data
        self.setMinimumHeight(230)
        self.setMinimumWidth(260)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setFont(QFont('Segoe UI', 10))
        if self.kind == 'donut':
            correct, wrong = self.data
            total = correct + wrong
            size = min(160, self.height()-65, self.width()-35)
            rect = QRectF((self.width()-size)/2, 12, size, size)
            p.setPen(QPen(QColor('#e7eef8'), 17))
            p.drawEllipse(rect)
            if total:
                p.setPen(QPen(QColor('#2eaa88'), 17))
                p.drawArc(rect, 90*16, -round(360*16*correct/total))
                p.setPen(QPen(QColor('#ef8291'), 17))
                p.drawArc(rect, 90*16-round(360*16*correct/total), -round(360*16*wrong/total))
            p.setPen(QColor('#183153'))
            p.setFont(QFont('Segoe UI', 25, QFont.Weight.Bold))
            p.drawText(rect, Qt.AlignmentFlag.AlignCenter, f'%{round(100*correct/total)}' if total else '—')
            p.setFont(QFont('Segoe UI', 11))
            p.drawText(QRectF(0, size+38, self.width(), 30), Qt.AlignmentFlag.AlignCenter,
                       f'{correct} doğru   ·   {wrong} yanlış' if total else 'Henüz cevap kaydı yok')
        else:
            values = self.data
            if not values:
                p.setPen(QColor('#65788f'))
                p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, 'Henüz çalışma verisi yok')
                return
            maximum = max([v for _,v in values] + [1])
            gap = self.width()/len(values)
            height = self.height()-55
            for i,(name,value) in enumerate(values):
                x, width = i*gap+gap*.2, gap*.6
                h = max(2, height*.85*value/maximum)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QColor('#4282d9' if value else '#e5edf8'))
                p.drawRoundedRect(QRectF(x, height-h, width, h), 6, 6)
                p.setPen(QColor('#45617f'))
                p.drawText(QRectF(i*gap, height+10, gap, 25), Qt.AlignmentFlag.AlignCenter, name)
                p.drawText(QRectF(i*gap, height-h-25, gap, 22), Qt.AlignmentFlag.AlignCenter, str(value))
        p.end()


class TopicChart(QWidget):
    def __init__(self, topics):
        super().__init__()
        self.topics = topics[:8]
        self.setMinimumHeight(max(105, 60*len(self.topics)))

    def paintEvent(self,event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setFont(QFont('Segoe UI',10))
        if not self.topics:
            p.setPen(QColor('#65788f'))
            p.drawText(self.rect(),Qt.AlignmentFlag.AlignCenter,'İlk cevaplarla konu grafiğin oluşacak')
        for i,row in enumerate(self.topics):
            y = i*60
            p.setPen(QColor('#45617f'))
            p.drawText(QRectF(0,y,self.width()-100,25),Qt.AlignmentFlag.AlignLeft,row['topic'])
            p.drawText(QRectF(self.width()-100,y,100,25),Qt.AlignmentFlag.AlignRight,f"{row['correct']} / {row['total']}")
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor('#f0b2bb'))
            p.drawRoundedRect(QRectF(0,y+30,self.width(),12),6,6)
            p.setBrush(QColor('#2eaa88'))
            width = self.width()*row['correct']/max(1,row['total'])
            if width:
                p.drawRoundedRect(QRectF(0,y+30,width,12),6,6)
        p.end()


class RoleWindow(QWidget):
    def __init__(self):
        super().__init__()
        store.init()
        self.identity = None
        self.quiz = None
        self.selected_role = 'student'
        self.setWindowTitle('Öğrenme Molası')
        self.resize(1240, 850)
        self.setMinimumSize(960, 680)
        self.setStyleSheet(STYLE)
        self.root = QVBoxLayout(self)
        self.root.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget()
        self.root.addWidget(self.stack)
        self.show_login()
        self.schedule_timer = QTimer(self)
        self.schedule_timer.timeout.connect(self.check_schedules)
        self.schedule_timer.start(10000)

    def check_schedules(self):
        if self.quiz and not self.quiz._allow_close:
            return
        from role_schedule import due_schedule, claim_schedule
        item = due_schedule()
        if item and claim_schedule(item['id']):
            self.identity = store.student_identity(item['student_id'])
            self.start_quiz(item['assignment_id'])

    def _replace(self, page):
        while self.stack.count():
            old = self.stack.widget(0)
            self.stack.removeWidget(old)
            old.deleteLater()
        self.stack.addWidget(page)

    def show_login(self):
        self.identity = None
        page = QWidget()
        row = QHBoxLayout(page)
        row.setContentsMargins(65, 45, 65, 45)
        intro = QVBoxLayout()
        intro.addStretch()
        intro.addWidget(label('ÖĞRENME MOLASI', 'Muted'))
        intro.addWidget(label('Her öğrenciye\nbir öğrenme yolculuğu.', 'Title'))
        intro.addWidget(label('Öğrenci için keşif.\nVeli için gelişim.\nÖğretmen için sınıfın tamamı.', 'Section'))
        intro.addWidget(label('Görevler, anlaşılır raporlar ve birlikte öğrenme araçları tek yerde.', 'Muted'))
        illustrations = QHBoxLayout()
        for asset in ('parent.png','student_boy.png','student_girl.png','teacher.png'):
            illustration = QLabel()
            illustration.setPixmap(QPixmap(str(Path(__file__).parent/'assets'/asset)).scaled(110,150,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
            illustrations.addWidget(illustration)
        intro.addLayout(illustrations)
        intro.addStretch()
        row.addLayout(intro, 1)
        panel, content = card('Hesabına giriş yap')
        panel.setMaximumWidth(510)
        content.addWidget(label('Kendi hesabınla sana özel ekranı aç.', 'Muted'))
        roles = QHBoxLayout()
        choices = {}
        for key, text in [('student','Öğrenci'),('parent','Veli'),('teacher','Öğretmen')]:
            b = QPushButton(text)
            b.setIcon(QIcon(str(Path(__file__).parent/'assets'/({'student':'student_boy.png','parent':'parent.png','teacher':'teacher.png'}[key]))))
            b.setIconSize(QSize(52,70))
            b.setObjectName('RoleChoice')
            b.setCheckable(True)
            b.clicked.connect(lambda _, r=key: select(r))
            choices[key] = b
            roles.addWidget(b)
        content.addLayout(roles)
        self.username, self.password = QLineEdit(), QLineEdit()
        self.username.setPlaceholderText('Kullanıcı adı')
        self.password.setPlaceholderText('Şifre')
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        content.addWidget(self.username)
        content.addWidget(self.password)
        self.login_error = label('', 'Error')
        content.addWidget(self.login_error)
        self.login_button = button('Giriş yap', self.login)
        content.addWidget(self.login_button)
        self.child_chooser = QWidget()
        child_grid = QGridLayout(self.child_chooser)
        for index, child in enumerate(store.child_profiles()):
            display_name=child['alias'].replace(' · Örnek','')
            b = button(f"{display_name}\n{child['grade']}. sınıf",lambda _,sid=child['id']:self.enter(store.student_identity(sid)))
            b.setToolTip(child['alias'])
            b.setSizePolicy(QSizePolicy.Policy.Ignored,QSizePolicy.Policy.Fixed)
            b.setIcon(QIcon(str(Path(__file__).parent/'assets'/store.avatar_for(child['id']))))
            b.setIconSize(QSize(48,70))
            b.setMinimumHeight(110)
            b.setStyleSheet('QPushButton { background: #fff0b8; color: #663b81; border: 2px solid #f7bf55; border-radius: 20px; font-size: 17px; padding: 10px; } QPushButton:hover { background: #ffe28b; }')
            child_grid.addWidget(b,index//2,index%2)
        if not store.child_profiles():
            child_grid.addWidget(label('Velin senin için bir profil oluştursun. Sonra resmine dokunarak başlayabilirsin!'))
        chooser_scroll = QScrollArea()
        chooser_scroll.setWidgetResizable(True)
        chooser_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        chooser_scroll.setWidget(self.child_chooser)
        content.addWidget(chooser_scroll)
        self.register_button = button('Yeni veli / öğretmen hesabı oluştur', self.registration, True)
        content.addWidget(self.register_button)
        self.login_hint = label('', 'Muted')
        content.addWidget(self.login_hint)
        content.addStretch()

        def select(role):
            self.selected_role = role
            for key,b in choices.items():
                b.setChecked(key == role)
            self.register_button.setVisible(role != 'student')
            for w in (self.username,self.password,self.login_button):
                w.setVisible(role != 'student')
            chooser_scroll.setVisible(role == 'student')
            self.login_hint.setText('Resmine dokun, keşfe başla! Şifreye ihtiyacın yok.' if role == 'student'
                                    else 'İlk kullanımda hesap oluştur. Her hesabın kayıtları ayrı tutulur.')
            self.login_error.clear()
            content.itemAt(0).widget().setText('Resmini seç, maceranı başlat!' if role=='student' else 'Hesabına giriş yap')
            page.setStyleSheet('QWidget { background: #fff7df; } QLabel { background: transparent; } QFrame#Card { background: white; }' if role=='student' else '')

        select(self.selected_role)
        self.password.returnPressed.connect(self.login)
        row.addWidget(panel, 1)
        self._replace(page)

    def login(self):
        try:
            identity = store.authenticate(self.username.text(), self.password.text())
            if identity.role != self.selected_role:
                raise ValueError('Bu hesap için doğru giriş türünü seçin.')
            self.enter(identity)
        except ValueError as error:
            self.login_error.setText(str(error))

    def registration(self):
        dialog, form, error = self.form_dialog('Yeni hesap')
        name, username, password, confirm = QLineEdit(), QLineEdit(), QLineEdit(), QLineEdit()
        password.setEchoMode(QLineEdit.EchoMode.Password)
        confirm.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow('Ad soyad', name)
        form.addRow('Kullanıcı adı', username)
        form.addRow('Şifre (en az 6 karakter)', password)
        form.addRow('Şifre tekrarı', confirm)

        def submit():
            try:
                if password.text() != confirm.text():
                    raise ValueError('Şifreler uyuşmuyor.')
                identity = store.register(username.text(), password.text(), name.text(), self.selected_role)
                dialog.accept()
                self.enter(identity)
            except sqlite3.IntegrityError:
                error.setText('Bu kullanıcı adı zaten kullanılıyor.')
            except ValueError as exc:
                error.setText(str(exc))
        form.addRow(button('Hesabı oluştur', submit))
        dialog.exec()

    def form_dialog(self, title):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setMinimumWidth(480)
        outer = QVBoxLayout(dialog)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        body = QWidget()
        form = QFormLayout(body)
        scroll.setWidget(body)
        outer.addWidget(scroll)
        dialog.resize(710,720)
        if self.screen():
            dialog.setMaximumHeight(self.screen().availableGeometry().height()-60)
        form.setContentsMargins(24, 24, 24, 24)
        form.setSpacing(14)
        error = label('', 'Error')
        form.addRow(label(title, 'Section'))
        form.addRow(error)
        return dialog, form, error

    def enter(self, identity):
        self.identity = identity
        if identity.role == 'student':
            self.student_home()
        else:
            self.dashboard()
            notices = store.notifications(identity)
            if notices:
                QMessageBox.information(self,'Yeni sınıf davetlerin', '\n\n'.join(n['message'] for n in notices)+'\n\nÇocuklarım → Yönetim bölümünden kodla sınıfa katılabilirsin.')
                store.notifications(identity,acknowledge=True)

    def dashboard(self):
        page = QWidget()
        shell = QHBoxLayout(page)
        shell.setContentsMargins(0,0,0,0)
        shell.setSpacing(0)
        sidebar = QFrame()
        sidebar.setObjectName('Sidebar')
        sidebar.setFixedWidth(225)
        nav = QVBoxLayout(sidebar)
        nav.setContentsMargins(20,28,20,24)
        nav.addWidget(label('Öğrenme\nMolası', 'Brand'))
        nav.addWidget(label('VELİ ALANI' if self.identity.role == 'parent' else 'ÖĞRETMEN ALANI', 'SidebarCaption'))
        nav.addSpacing(28)
        self.nav_buttons = {}
        entries = [('overview','Genel bakış'), ('tasks','Görevler'),
                   ('people','Çocuklarım' if self.identity.role == 'parent' else 'Öğrencilerim'),
                   ('manage','Hesap ve sınıflar')]
        for key,text in entries:
            b = QPushButton(text)
            b.setObjectName('Nav')
            b.setCheckable(True)
            b.clicked.connect(lambda _, k=key: self.show_section(k))
            nav.addWidget(b)
            self.nav_buttons[key] = b
        nav.addStretch()
        nav.addWidget(label(self.identity.name, 'SidebarCaption'))
        nav.addWidget(button('Çıkış yap', self.show_login, True))
        shell.addWidget(sidebar)
        main = QVBoxLayout()
        main.setContentsMargins(28,24,28,24)
        header = QHBoxLayout()
        header.addWidget(label('Çocuğunun gelişim yolculuğu' if self.identity.role == 'parent' else 'Sınıfının öğrenme haritası', 'Title'), 1)
        header.addWidget(button('Yenile', lambda: self.show_section(self.section), True))
        main.addLayout(header)
        filters = QHBoxLayout()
        self.class_picker = QComboBox()
        self.student_picker = QComboBox()
        if self.identity.role == 'teacher':
            for cl in store.classes(self.identity):
                self.class_picker.addItem(f"{cl['name']} · {cl['grade']}. sınıf", cl['id'])
            filters.addWidget(label('Sınıf', 'Muted'))
            filters.addWidget(self.class_picker, 1)
        filters.addWidget(label('Çocuk' if self.identity.role == 'parent' else 'Görünüm', 'Muted'))
        filters.addWidget(self.student_picker, 2)
        main.addLayout(filters)
        self.content = QStackedWidget()
        main.addWidget(self.content, 1)
        shell.addLayout(main, 1)
        self.section = 'overview'
        self.fill_students()
        self.class_picker.currentIndexChanged.connect(lambda: (self.fill_students(), self.show_section(self.section)))
        self.student_picker.currentIndexChanged.connect(lambda: self.show_section(self.section))
        self._replace(page)
        self.show_section('overview')

    def fill_students(self):
        self.student_picker.blockSignals(True)
        self.student_picker.clear()
        if self.identity.role == 'teacher':
            self.student_picker.addItem('Sınıfın tamamı', None)
        for child in store.students(self.identity, self.class_picker.currentData()):
            self.student_picker.addItem(f"{child['alias']} · {child['grade']}. sınıf", child['id'])
        self.student_picker.blockSignals(False)

    def show_section(self, section):
        self.section = section
        for key,b in self.nav_buttons.items():
            b.setChecked(key == section)
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0,8,0,0)
        layout.setSpacing(18)
        if section == 'overview':
            self.overview(layout)
        elif section == 'tasks':
            self.tasks_page(layout)
        elif section == 'people':
            self.people_page(layout)
        else:
            self.manage_page(layout)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)
        while self.content.count():
            old = self.content.widget(0)
            self.content.removeWidget(old)
            old.deleteLater()
        self.content.addWidget(scroll)

    def overview(self, layout):
        sid, cid = self.student_picker.currentData(), self.class_picker.currentData()
        data = store.analytics(self.identity, sid, cid)
        if not store.students(self.identity, cid):
            welcome, contents = card('İlk adımı birlikte atalım')
            if self.identity.role == 'parent':
                contents.addWidget(label('Çocuk hesabını oluştur, ardından bir öğrenme görevi ver. Çözümler başladığında grafikler burada oluşacak.', 'Muted'))
                contents.addWidget(button('Çocuk hesabı oluştur',self.child_dialog))
            elif not store.classes(self.identity):
                contents.addWidget(label('Sınıfını oluştur ve katılım kodunu velilerle paylaş. Öğrenciler bağlandıkça sınıf raporun oluşacak.', 'Muted'))
                contents.addWidget(button('İlk sınıfımı oluştur',self.class_dialog))
            else:
                classroom = next((c for c in store.classes(self.identity) if c['id']==cid),None)
                contents.addWidget(label('Veliler bu kodu kendi ekranından kullanarak çocuklarını sınıfına bağlayabilir.', 'Muted'))
                contents.addWidget(label(classroom['code'] if classroom else '', 'Metric'))
            layout.addWidget(welcome)
        title = self.student_picker.currentText() or 'İlk kaydını oluştur'
        layout.addWidget(label(title, 'Section'))
        if self.identity.role == 'teacher' and sid is None:
            layout.addWidget(label(f"{len(data['students'])} öğrenci · Sınıfın tüm görev ve alıştırma sonuçları", 'Muted'))
        layout.addWidget(label('Görev ve alıştırma cevapları birlikte gösterilir. Başarı oranı, doğru cevap / toplam cevap olarak hesaplanır.', 'Muted'))
        metrics = QHBoxLayout()
        for title,value in [('Çözülen soru',data['total']), ('Doğru',data['correct']), ('Yanlış',data['wrong']), ('Başarı',f"%{data['rate']}")]:
            tile, contents = card()
            contents.addWidget(label(title, 'Muted'))
            contents.addWidget(label(str(value), 'Metric'))
            metrics.addWidget(tile)
        layout.addLayout(metrics)
        charts = QHBoxLayout()
        success, l = card('Cevap dağılımı')
        l.addWidget(Chart('donut', (data['correct'], data['wrong'])))
        activity, l = card('Son 7 gün · Çözülen sorular')
        l.addWidget(Chart('bars', data['trend']))
        charts.addWidget(success, 1)
        charts.addWidget(activity, 2)
        layout.addLayout(charts)
        chart, contents = card('Konulara göre doğru / yanlış dağılımı')
        contents.addWidget(label('Yeşil: doğru cevaplar   ·   Pembe: yanlış cevaplar', 'Muted'))
        contents.addWidget(TopicChart(data['topics']))
        layout.addWidget(chart)
        topics, contents = card('Konu bazında gelişim')
        contents.addWidget(self.table(['Konu','Çözülen','Doğru','Yanlış','Başarı'],
            [[r['topic'],r['total'],r['correct'],r['wrong'],f"%{round(100*r['correct']/r['total'])}"] for r in data['topics']]))
        if not data['topics']:
            contents.addWidget(label('Henüz çözüm yok. Bir görev verdiğinde sonuçlar burada görünür.', 'Muted'))
        layout.addWidget(topics)
        layout.addStretch()

    def table(self, columns, rows):
        table = QTableWidget(len(rows), len(columns))
        table.setHorizontalHeaderLabels(columns)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setAlternatingRowColors(True)
        table.verticalHeader().hide()
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for c in range(1,len(columns)):
            table.horizontalHeader().setSectionResizeMode(c, QHeaderView.ResizeMode.ResizeToContents)
        for i,row in enumerate(rows):
            table.setRowHeight(i, 44)
            for j,value in enumerate(row):
                table.setItem(i,j,QTableWidgetItem(str(value)))
        table.setMinimumHeight(min(350,max(100,50+44*len(rows))))
        return table

    def tasks_page(self, layout):
        row = QHBoxLayout()
        row.addWidget(label('Planla, takip et, birlikte tamamla', 'Section'), 1)
        row.addWidget(button('Yeni görev ver', self.task_dialog))
        layout.addLayout(row)
        tasks = store.tasks(self.identity, self.student_picker.currentData())
        if self.identity.role == 'teacher':
            tasks = [t for t in tasks if t['class_id'] == self.class_picker.currentData()]
        if not tasks:
            layout.addWidget(label('Henüz görev yok. Seçtiğin ders ve konudan yeni bir çalışma oluştur.', 'Muted'))
        for task in tasks:
            frame, l = card(task['title'])
            l.addWidget(label(f"{task['subject']} · {task['topic']} · {task['actual_count']} soru", 'Muted'))
            due = task.get('due_date') or 'Belirtilmedi'
            status = f"{task['completed']}/{task['actual_count']} soru tamamlandı" if 'completed' in task else f"{task['completed_students']}/{task['recipient_count']} öğrenci tamamladı"
            l.addWidget(label(f'Son tarih: {due}   ·   {status}'))
            if task.get('scheduled_at'):
                from datetime import datetime
                when=datetime.fromisoformat(task['scheduled_at']).strftime('%d.%m.%Y · %H:%M')
                l.addWidget(label(f'Otomatik açılış: {when}', 'Section'))
                if task.get('schedule_error'):
                    l.addWidget(label('Windows zamanlaması kurulamadı. Bu saatte uygulamayı açık tutun.','Error'))
            layout.addWidget(frame)
        layout.addStretch()

    def people_page(self, layout):
        layout.addWidget(label('Her öğrencinin gelişimini ayrı izle', 'Section'))
        data = store.analytics(self.identity, class_id=self.class_picker.currentData())
        rows = data['students']
        table = self.table(['Öğrenci','Sınıf','Soru','Doğru','Yanlış','Başarı'],
            [[r['alias'],r['grade'],r['total'],r['correct'],r['wrong'],f"%{round(100*r['correct']/r['total']) if r['total'] else 0}"] for r in rows])
        def detail(row, _):
            if row < len(rows):
                self.student_picker.setCurrentIndex(self.student_picker.findData(rows[row]['id']))
                self.show_section('overview')
        table.cellDoubleClicked.connect(detail)
        layout.addWidget(table)
        layout.addWidget(label('Bir öğrencinin satırına çift tıklayarak kişisel grafiklerini aç.', 'Muted'))
        if not rows:
            layout.addWidget(label('Henüz öğrenci yok. Hesap ve sınıflar bölümünden başlayabilirsin.', 'Muted'))
        layout.addStretch()

    def manage_page(self, layout):
        if self.identity.role == 'parent':
            frame,l = card('Çocuk hesapları')
            l.addWidget(label('Çocuğun resmine dokunarak şifresiz giriş yapar. Veli ve öğretmen alanları şifreyle korunur.', 'Muted'))
            l.addWidget(button('Çocuk hesabı oluştur', self.child_dialog))
            l.addWidget(button('Seçili çocuğu sınıfa bağla', self.join_dialog, True))
            l.addWidget(button('Serbest çalışma derslerini seç',self.practice_preferences,True))
            l.addWidget(button('Önceki tek öğrenci raporlarını bağla',self.import_history,True))
            l.addWidget(label('Eski uygulamanın raporlarını seçili çocuğa bağlamak için eski ebeveyn PIN’i gerekir. Aktarım eski kayıtları silmez.', 'Muted'))
            layout.addWidget(frame)
        else:
            layout.addWidget(button('Yeni sınıf oluştur', self.class_dialog))
            for classroom in store.classes(self.identity):
                frame,l = card(f"{classroom['name']} · {classroom['grade']}. sınıf")
                l.addWidget(label('Sınıf katılım kodu', 'Muted'))
                code = label(classroom['code'] or 'Bu eski sınıf için kod henüz oluşturulmadı.', 'Metric')
                code.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                l.addWidget(code)
                l.addWidget(button('Kodu velilerle paylaş · Bildirim gönder',lambda _,cid=classroom['id']:self.share_code(cid)))
                l.addWidget(label('Bu kodu velilerle paylaş. Veli, çocuğunu kendi hesabından bu sınıfa bağlayabilir.', 'Muted'))
                layout.addWidget(frame)
        layout.addStretch()

    def child_dialog(self):
        d,f,error = self.form_dialog('Çocuk hesabı oluştur')
        name = QLineEdit()
        grade = QSpinBox()
        grade.setRange(1,4)
        avatar = QComboBox()
        for text,asset in [('Erkek öğrenci','student_boy.png'),('Kız öğrenci','student_girl.png')]:
            avatar.addItem(QIcon(str(Path(__file__).parent/'assets'/asset)),text,asset)
        for title,w in [('Çocuğun adı',name),('Sınıf düzeyi',grade)]:
            f.addRow(title,w)
        f.addRow('Öğrenci görseli',avatar)
        def save():
            try:
                child_id=store.add_child(self.identity,name.text(),grade.value())
                store.set_avatar(self.identity,child_id,avatar.currentData())
                d.accept()
                self.dashboard()
                self.show_section('people')
            except sqlite3.IntegrityError:
                error.setText('Kullanıcı adı zaten kullanılıyor.')
            except ValueError as exc:
                error.setText(str(exc))
        f.addRow(button('Hesabı oluştur',save))
        d.exec()

    def class_dialog(self):
        d,f,error = self.form_dialog('Yeni sınıf')
        name,grade = QLineEdit(),QSpinBox()
        name.setPlaceholderText('Örneğin 3-A')
        grade.setRange(1,4)
        f.addRow('Sınıf adı',name)
        f.addRow('Sınıf düzeyi',grade)
        def save():
            try:
                store.add_class(self.identity,name.text(),grade.value())
                d.accept()
                self.dashboard()
                self.show_section('manage')
            except (ValueError,sqlite3.IntegrityError):
                error.setText('Sınıf adı boş veya bu sınıf zaten mevcut.')
        f.addRow(button('Sınıfı oluştur',save))
        d.exec()

    def share_code(self,cid):
        count = store.share_class(self.identity,cid)
        QMessageBox.information(self,'Davetler gönderildi',f'{count} veliye uygulama içi bildirim gönderildi. Giriş yaptıklarında daveti görecekler.')

    def join_dialog(self):
        sid = self.student_picker.currentData()
        if not sid:
            QMessageBox.information(self,'Çocuk seçimi','Önce çocuk hesabı oluştur ve bir çocuk seç.')
            return
        code,ok = QInputDialog.getText(self,'Sınıfa katıl','Öğretmenin paylaştığı sınıf kodu:')
        if ok:
            try:
                store.join_class(self.identity,sid,code)
                QMessageBox.information(self,'Sınıfa katıldı','Çocuğun sınıfa bağlandı. Öğretmenin görevleri öğrenci girişinde görünür.')
            except ValueError as error:
                QMessageBox.warning(self,'Katılım yapılamadı',str(error))

    def reset_child_password(self):
        sid = self.student_picker.currentData()
        if not sid:
            return
        password,ok = QInputDialog.getText(self,'Öğrenci şifresi','Yeni şifre (en az 6 karakter):',QLineEdit.EchoMode.Password)
        if ok:
            try:
                store.reset_child_password(self.identity,sid,password)
                QMessageBox.information(self,'Tamamlandı','Öğrenci şifresi yenilendi.')
            except ValueError as error:
                QMessageBox.warning(self,'Şifre yenilenemedi',str(error))

    def task_dialog(self):
        import questions as qb
        sid, cid = self.student_picker.currentData(), self.class_picker.currentData()
        if self.identity.role == 'parent':
            if not sid:
                QMessageBox.information(self,'Çocuk hesabı','Önce çocuk hesabı oluştur.')
                return
            grade = store.require_student(self.identity,sid)['grade']
        else:
            classroom = next((c for c in store.classes(self.identity) if c['id']==cid),None)
            if not classroom:
                QMessageBox.information(self,'Sınıf seçimi','Önce bir sınıf oluştur.')
                return
            grade = classroom['grade']
        d,f,error = self.form_dialog('Yeni öğrenme görevi')
        title,topic,count,due = QLineEdit(),QComboBox(),QSpinBox(),QDateEdit()
        title.setPlaceholderText('Örneğin: Bu haftaki fen keşfim')
        from curriculum import catalogue, subject_for_skill, ready_skills
        courses = catalogue(grade)
        subject,unit = QComboBox(),QComboBox()
        subject.addItem('Hazır alıştırmalar',None)
        for course in courses:
            subject.addItem(course['subject'],course)
        custom = QCheckBox('Seçtiğim MEB temasına kendi sorumu ekle')
        custom_text = QPlainTextEdit()
        custom_text.setPlaceholderText('Her satır: Soru | A seçeneği | B seçeneği | C seçeneği | D seçeneği | Doğru seçenek (1–4) | Açıklama')
        custom_text.setMaximumHeight(115)
        custom_text.hide()
        custom.toggled.connect(custom_text.setVisible)
        source = label('MEB kaynakları çevrimdışı önbellekten gösterilir. Hazır sorular uygulamaya aittir.','Muted')
        source.setTextFormat(Qt.TextFormat.RichText)
        source.setOpenExternalLinks(True)
        f.addRow('Ders / MEB programı',subject)
        f.addRow('MEB tema / öğrenme alanı',unit)
        f.addRow(source)
        f.addRow(custom)
        f.addRow(custom_text)
        for key,_ in qb.skills_for_grade(grade):
            topic.addItem(qb.skill_name(key),key)
        def filter_subject():
            course=subject.currentData()
            unit.clear();topic.clear()
            for key,_ in qb.skills_for_grade(grade):
                if not course or subject_for_skill(key,grade)==course['subject']:
                    topic.addItem(qb.skill_name(key),key)
            if course:
                for row in course['units']: unit.addItem(row['title'],row)
                source.setText(f'<a href="{course["url"]}">MEB resmi programını aç</a> · {course["active_model"]}')
                custom.setChecked(True)
            else:
                source.setText('Hazır alıştırmalar uygulamanın soru bankasından gelir.')
                custom.setChecked(False)
            unit.setEnabled(bool(course))
            if course:
                filter_unit()
            else:
                custom.setEnabled(True)
        def filter_unit():
            course,chosen=subject.currentData(),unit.currentData()
            if not course or not chosen: return
            ready=ready_skills(course['subject'],chosen['title'],grade)
            topic.clear()
            for key in ready: topic.addItem(qb.skill_name(key),key)
            custom.setChecked(not bool(ready))
            custom.setEnabled(bool(ready))
        unit.currentIndexChanged.connect(filter_unit)
        subject.currentIndexChanged.connect(filter_subject)
        filter_subject()
        count.setRange(1,30)
        count.setValue(5)
        due.setCalendarPopup(True)
        due.setDate(QDate.currentDate().addDays(7))
        due.setDisplayFormat('dd.MM.yyyy')
        timed = QCheckBox('Bu tarihte otomatik soru ekranını aç')
        clock = QTimeEdit(QTime(18,0))
        clock.setDisplayFormat('HH:mm')
        if self.identity.role == 'parent':
            f.addRow(timed)
            f.addRow('Başlangıç saati',clock)
        target = QComboBox()
        if self.identity.role == 'teacher':
            target.addItem('Sınıfın tamamı',None)
            for child in store.students(self.identity,cid):
                target.addItem(child['alias'],child['id'])
            if sid:
                target.setCurrentIndex(target.findData(sid))
            f.addRow('Görev kime verilsin?',target)
        for text,w in [('Görev adı',title),('Ders / konu',topic),('Soru sayısı',count),('Son tarih',due)]:
            f.addRow(text,w)
        f.addRow(label('Sorular mevcut soru bankasından ve yerel üreticilerden hazırlanır.', 'Muted'))
        def save():
            try:
                curriculum_data=None;custom_bank=None
                selected_skill=topic.currentData()
                question_count=count.value()
                if subject.currentData():
                    course=subject.currentData(); chosen_unit=unit.currentData()
                    if not chosen_unit: raise ValueError('Bu dersin tema bilgisi bulunamadı.')
                    curriculum_data=dict(grade=grade,subject=course['subject'],title=chosen_unit['title'],source=chosen_unit['url'])
                    custom_bank=[] if custom.isChecked() else None
                    for line in (custom_text.toPlainText().splitlines() if custom.isChecked() else []):
                        if not line.strip(): continue
                        fields=[part.strip() for part in line.split('|')]
                        if len(fields)!=7 or not all(fields[:6]) or fields[5] not in ('1','2','3','4'):
                            raise ValueError('Soru biçimi: Soru | A | B | C | D | 1–4 | Açıklama')
                        custom_bank.append(dict(text=fields[0],choices=fields[1:5],answer=int(fields[5])-1,explanation=fields[6],hint=fields[6],visual=None))
                    if custom_bank is not None:
                        if not 1<=len(custom_bank)<=30: raise ValueError('Bu temada hazır banka yok. 1–30 kendi sorunuzu ekleyin veya hazır alıştırmaları seçin.')
                        question_count=len(custom_bank)
                    selected_skill=selected_skill or next(iter(dict(qb.skills_for_grade(grade))))
                if timed.isChecked():
                    from datetime import datetime
                    if datetime.fromisoformat(due.date().toString('yyyy-MM-dd')+'T'+clock.time().toString('HH:mm:ss')) <= datetime.now():
                        raise ValueError('Başlangıç zamanı gelecekte olmalı.')
                aid = store.create_task(self.identity,title.text(),selected_skill,question_count,
                    student_id=sid if self.identity.role=='parent' else target.currentData(),class_id=cid,
                    due_date=due.date().toString('yyyy-MM-dd'),curriculum=curriculum_data,custom_questions=custom_bank)
                if timed.isChecked():
                    from role_schedule import schedule
                    message = schedule(self.identity,aid,sid,due.date().toString('yyyy-MM-dd')+'T'+clock.time().toString('HH:mm:ss'))
                    QMessageBox.information(self,'Saatli görev',message)
                d.accept()
                self.show_section('tasks')
            except (ValueError,sqlite3.IntegrityError) as exc:
                error.setText(str(exc))
        f.addRow(button('Görevi oluştur',save))
        d.exec()

    def practice_preferences(self):
        import questions as qb
        sid = self.student_picker.currentData()
        if not sid:
            QMessageBox.information(self,'Çocuk seçimi','Önce çocuk hesabı oluştur.')
            return
        child = store.require_student(self.identity,sid)
        d,f,error = self.form_dialog('Serbest çalışma dersleri')
        selected = store.practice_skills(self.identity,sid)
        checks = {}
        for skill,_ in qb.skills_for_grade(child['grade']):
            check = QCheckBox(qb.skill_name(skill))
            check.setChecked(skill in selected)
            checks[skill] = check
            f.addRow(check)
        def save():
            try:
                store.set_practice_skills(self.identity,sid,[s for s,c in checks.items() if c.isChecked()])
                d.accept()
            except ValueError as exc:
                error.setText(str(exc))
        f.addRow(label('Alıştırmalarda yalnızca seçtiğin konular sırayla gelir. Atanmış görevlerin konuları değişmez.', 'Muted'))
        f.addRow(button('Dersleri kaydet',save))
        d.exec()

    def import_history(self):
        sid = self.student_picker.currentData()
        if not sid:
            QMessageBox.information(self,'Çocuk seçimi','Önce çocuk hesabı oluştur.')
            return
        confirmed = QMessageBox.question(self,'Eski raporları bağla',
            f'Önceki tek öğrenci uygulamasındaki TÜM cevaplar {self.student_picker.currentText()} hesabına bağlanacak. Doğru çocuğu seçtin mi?')
        if confirmed != QMessageBox.StandardButton.Yes:
            return
        pin,ok = QInputDialog.getText(self,'Eski ebeveyn doğrulaması','Eski uygulamanın ebeveyn PIN’i:',QLineEdit.EchoMode.Password)
        if ok:
            try:
                count = store.import_legacy_history(self.identity,sid,pin)
                QMessageBox.information(self,'Aktarım tamamlandı',f'{count} cevap raporlara eklendi.')
                self.show_section('overview')
            except ValueError as error:
                QMessageBox.warning(self,'Aktarım yapılamadı',str(error))

    def student_home(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(55,35,55,35)
        top = QHBoxLayout()
        top.addWidget(label(f'Merhaba, {self.identity.name}!', 'Title'),1)
        avatar = QLabel()
        avatar.setPixmap(QPixmap(str(Path(__file__).parent/'assets'/store.avatar_for(self.identity.student_id))).scaled(90,115,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
        top.insertWidget(0,avatar)
        page.setStyleSheet('QWidget { background: #fff7df; } QLabel { background: transparent; } QComboBox { background: white; } QFrame#Card { background: #ffffff; border: 2px solid #cbb5f5; border-radius: 22px; } QLabel#Title { color: #713fc0; font-size: 32px; } QPushButton { background: #8652d6; border-radius: 16px; padding: 15px; font-size: 17px; } QPushButton#Secondary { background: #efe3ff; color: #6734a8; } QPushButton:hover { background: #6c3eb5; }')
        top.addWidget(button('Çıkış yap',self.show_login,True))
        layout.addLayout(top)
        layout.addWidget(label('Bugün birlikte neler keşfedeceğiz?', 'Muted'))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        tasks_widget = QWidget()
        tasks_layout = QVBoxLayout(tasks_widget)
        tasks = store.tasks(self.identity)
        remaining = [t for t in tasks if t.get('completed',0)<t['actual_count']]
        if not tasks:
            tasks_layout.addWidget(label('Henüz atanmış görevin yok. İstersen alıştırma yapabilirsin.', 'Section'))
        for task in tasks:
            frame,l = card(task['title'])
            l.addWidget(label(f"{task['subject']} · {task['actual_count']} soru · Son tarih: {task['due_date'] or 'Yok'}", 'Muted'))
            completed = task.get('completed',0)
            l.addWidget(label(f"{completed}/{task['actual_count']} tamamlandı"))
            if completed < task['actual_count']:
                l.addWidget(button('Göreve devam et' if completed else 'Göreve başla',lambda _, aid=task['id']: self.start_quiz(aid)))
            else:
                l.addWidget(label('Tamamlandı. Harika iş!', 'Section'))
            tasks_layout.addWidget(frame)
        practice,l = card('Serbest keşif')
        l.addWidget(label('Bugünün keşfini sen seç! Yıldızlarını toplamak için hazır mısın?', 'Section'))
        import questions as qb
        topics = QComboBox()
        topics.addItem('Sürpriz keşif · Karışık dersler',None)
        for skill,_ in qb.skills_for_grade(store.require_student(self.identity,self.identity.student_id)['grade']):
            topics.addItem(qb.skill_name(skill),skill)
        l.addWidget(topics)
        l.addWidget(button('Keşfe başla!',lambda: self.start_quiz(skill=topics.currentData())))
        tasks_layout.addWidget(practice)
        tasks_layout.addStretch()
        scroll.setWidget(tasks_widget)
        layout.addWidget(scroll,1)
        self._replace(page)

    def start_quiz(self, assignment_id=None, skill=None):
        from role_quiz import StudentQuiz, practice_questions
        try:
            questions = store.task_questions(self.identity,assignment_id) if assignment_id else practice_questions(self.identity,skills=[skill] if skill else None)
            self.quiz = StudentQuiz(self.identity,questions,assignment_id)
            self.quiz.finished.connect(self.quiz_finished)
            self.quiz.showFullScreen()
            self.hide()
        except ValueError as error:
            QMessageBox.warning(self,'Çalışma açılamadı',str(error))

    def quiz_finished(self, status):
        parent = self.quiz.verified_parent if self.quiz else None
        if parent:
            self.enter(parent)
        elif status == 'ogrenci_cikisi':
            self.show_login()
        else:
            self.student_home()
        self.show()

    def closeEvent(self,event):
        if self.quiz and not self.quiz._allow_close:
            event.ignore()
            self.quiz.raise_()
            return
        super().closeEvent(event)
