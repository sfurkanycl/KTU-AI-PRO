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


from pastel_design import PASTEL_QSS as STYLE, STUDENT_QSS, WelcomeBackdrop, portrait, ROLE_COLORS



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
        self.schedule_timer.start(1000)
        QTimer.singleShot(0, self.check_schedules)

    def check_schedules(self):
        active = self.quiz and not self.quiz._allow_close
        # A scheduled assignment takes priority over voluntary practice.
        if active and self.quiz.learning.assignment_id is not None:
            return
        from role_schedule import due_schedule, claim_schedule
        item = due_schedule()
        if item and claim_schedule(item['id']):
            if active:
                self.quiz._finish('saatli_gorev')
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
        page = WelcomeBackdrop()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(36, 22, 36, 22)
        outer.setSpacing(12)
        title = label('Öğrenme Molası', 'Title')
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(title)
        caption = label('Birlikte keşfedelim, her gün biraz daha öğrenelim.', 'Muted')
        caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(caption)
        roles = QHBoxLayout(); roles.setSpacing(28);roles.addStretch()
        choices = {}
        for key,text,asset in [('parent','Veli','design_parent.png'),('teacher','Öğretmen','design_teacher.png'),('student','Öğrenci','design_girl.png')]:
            column=QVBoxLayout()
            b=QPushButton();b.setCheckable(True);b.setObjectName('RoleChoice')
            bg,hover,fg=ROLE_COLORS[key]
            b.setIcon(QIcon(portrait(asset,120,bg)));b.setIconSize(QSize(120,120))
            b.setFixedSize(156,140)
            b.setCursor(Qt.CursorShape.PointingHandCursor);b.setAccessibleName(text)
            b.setStyleSheet(f'QPushButton {{ background: transparent; border: 3px solid transparent; border-radius: 28px; padding: 4px; }} QPushButton:checked {{ background: rgba(255,255,255,150); border-color: {hover}; }} QPushButton:hover {{ background: rgba(255,255,255,100); }}')
            b.clicked.connect(lambda _,r=key:select(r));choices[key]=b
            column.addWidget(b,0,Qt.AlignmentFlag.AlignCenter)
            name=label(text,'Section');name.setAlignment(Qt.AlignmentFlag.AlignCenter)
            column.addWidget(name);roles.addLayout(column)
        roles.addStretch();outer.addLayout(roles)
        panel,content=card()
        panel.setMinimumWidth(760);panel.setMaximumWidth(860)
        panel_title=label('', 'Section');content.addWidget(panel_title)
        self.username,self.password=QLineEdit(),QLineEdit()
        self.username.setPlaceholderText('Kullanıcı adı');self.password.setPlaceholderText('Şifre')
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        content.addWidget(self.username);content.addWidget(self.password)
        self.login_error=label('', 'Error');content.addWidget(self.login_error)
        self.login_button=button('Giriş yap',self.login);content.addWidget(self.login_button)
        self.child_chooser=QWidget();child_grid=QGridLayout(self.child_chooser);child_grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        children=store.child_profiles()
        for index,child in enumerate(children):
            name=child['alias'].replace(' · Örnek','')
            asset='design_girl.png' if store.avatar_for(child['id'])=='student_girl.png' else 'design_boy.png'
            b=button(f"{name}\n{child['grade']}. sınıf",lambda _,sid=child['id']:self.enter(store.student_identity(sid)))
            b.setToolTip(child['alias']);b.setIcon(QIcon(portrait(asset,64)))
            b.setIconSize(QSize(64,64));b.setMinimumHeight(88)
            b.setSizePolicy(QSizePolicy.Policy.Ignored,QSizePolicy.Policy.Fixed)
            b.setStyleSheet('QPushButton { background: #edf9ef; color: #23664e; border: 2px solid #bee5c8; border-radius: 18px; padding: 8px; } QPushButton:hover { background: #d3f1db; }')
            child_grid.addWidget(b,index//3,index%3)
        if not children:child_grid.addWidget(label('Velin profilini oluştursun. Sonra resmine dokunarak başlayabilirsin!'))
        chooser_scroll=QScrollArea();chooser_scroll.setWidgetResizable(True)
        chooser_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        chooser_scroll.setMinimumHeight(160);chooser_scroll.setWidget(self.child_chooser)
        content.addWidget(chooser_scroll,1)
        if not children:
            content.addWidget(button('Örnek hesaplarla keşfet',self.load_demo,True))
            content.addWidget(label('Örnek veli: demo.veli · Öğretmen: demo.ogretmen · Şifre: Demo123!','Muted'))
        self.register_button=button('Yeni veli / öğretmen hesabı oluştur',self.registration,True)
        content.addWidget(self.register_button)
        self.login_hint=label('', 'Muted');content.addWidget(self.login_hint)
        def select(role):
            self.selected_role=role
            for key,b in choices.items():b.setChecked(key==role)
            for w in (self.username,self.password,self.login_button,self.register_button):w.setVisible(role!='student')
            chooser_scroll.setVisible(role=='student')
            panel_title.setText('Resmini seç, maceranı başlat!' if role=='student' else ('Veli girişi' if role=='parent' else 'Öğretmen girişi'))
            self.login_hint.setText('Resmine dokunman yeterli. Şifreye ihtiyacın yok.' if role=='student' else 'Kendi hesabınla sana özel gelişim ekranına gir.')
            self.login_error.clear()
        select(self.selected_role);self.password.returnPressed.connect(self.login)
        outer.addWidget(panel,1,Qt.AlignmentFlag.AlignHCenter)
        self._replace(page)

    def login(self):
        try:
            identity = store.authenticate(self.username.text(), self.password.text())
            if identity.role != self.selected_role:
                raise ValueError('Bu hesap için doğru giriş türünü seçin.')
            self.enter(identity)
        except ValueError as error:
            self.login_error.setText(str(error))

    def load_demo(self):
        from seed_demo import seed
        try:
            seed();self.show_login()
        except (ValueError,sqlite3.Error) as error:
            QMessageBox.warning(self,'Örnek veriler yüklenemedi',str(error))

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
        sidebar.setObjectName('ParentSidebar' if self.identity.role=='parent' else 'Sidebar')
        sidebar.setFixedWidth(225)
        nav = QVBoxLayout(sidebar)
        nav.setContentsMargins(20,28,20,24)
        avatar = QLabel()
        avatar.setPixmap(portrait('design_parent.png' if self.identity.role=='parent' else 'design_teacher.png',110,ROLE_COLORS[self.identity.role][0]))
        nav.addWidget(avatar,0,Qt.AlignmentFlag.AlignHCenter)
        nav.addWidget(label('Öğrenme\nMolası', 'Brand'))
        nav.addWidget(label('VELİ ALANI' if self.identity.role == 'parent' else 'ÖĞRETMEN ALANI', 'SidebarCaption'))
        nav.addSpacing(28)
        self.nav_buttons = {}
        entries = [('overview','Genel bakış'), ('tasks','Görevler'),
                   ('materials','Soru atölyesi'),
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
        elif section == 'materials':
            self.materials_page(layout)
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
        subjects,contents=card('Derslere göre gelişim')
        contents.addWidget(TopicChart([dict(topic=r['subject'],**{k:r[k] for k in ('correct','total')}) for r in data['subjects']]))
        layout.addWidget(subjects)
        details,contents=card('Kazanım ve yardım kullanımı')
        contents.addWidget(label('Az cevap olduğunda “Veri birikiyor” görünür. İpucuyla ve yardımsız verilen doğru cevaplar ayrı izlenir. Ek destek alıştırmaları rapora dahildir.','Muted'))
        rows=data['concepts']
        table=self.table(['Ders','Kazanım','Doğru','Yanlış','İpucu','Yardımsız doğru','Durum'],
            [[r['subject'],r['concept'],r['correct'],r['wrong'],r['hints'],r['clean'],r['status']] for r in rows])
        table.horizontalHeader().setSectionResizeMode(0,QHeaderView.ResizeMode.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1,QHeaderView.ResizeMode.Stretch)
        contents.addWidget(table)
        priorities=[r for r in rows if r['status']=='Tekrar önerilir']
        if priorities: contents.addWidget(label('Pekiştirme önerisi: '+' · '.join(r['subject']+': '+r['concept'] for r in priorities[:3]),'Section'))
        contents.addWidget(button('Gelişim raporunu CSV olarak indir',lambda:self.export_report(data),True))
        layout.addWidget(details)
        layout.addStretch()

    def export_report(self,data):
        from PyQt6.QtWidgets import QFileDialog
        import csv
        path,_=QFileDialog.getSaveFileName(self,'Gelişim raporu','gelisim_raporu.csv','CSV (*.csv)')
        if not path:return
        if not path.lower().endswith('.csv'):path+='.csv'
        def safe(value):
            value=str(value)
            return "'"+value if value.lstrip().startswith(('=','+','-','@')) else value
        try:
            with open(path,'w',encoding='utf-8-sig',newline='') as stream:
                writer=csv.writer(stream,delimiter=';')
                writer.writerow(['Ders','Konu','Kazanım','Toplam','Doğru','Yanlış','İpucu','Yardımsız doğru','Ek destek','Başarı %','Durum'])
                for r in data['concepts']:
                    writer.writerow([safe(r[k]) for k in ('subject','topic','concept','total','correct','wrong','hints','clean','support','rate','status')])
            QMessageBox.information(self,'Rapor hazır','Seçtiğin görünümün raporu kaydedildi.')
        except OSError as error: QMessageBox.warning(self,'Kaydedilemedi',str(error))

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
        row.addWidget(button('Belgeden soru hazırla',self.material_dialog,True))
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
            if self.identity.role=='parent' and self.student_picker.currentData() and task.get('completed',0)<task['actual_count']:
                l.addWidget(button('Başlangıç saatini ayarla',lambda _,aid=task['id']:self.schedule_task_dialog(aid),True))
            layout.addWidget(frame)
        layout.addStretch()

    def schedule_task_dialog(self,assignment_id):
        sid=self.student_picker.currentData()
        d,f,error=self.form_dialog('Otomatik çalışma saati')
        day=QDateEdit(QDate.currentDate());day.setCalendarPopup(True);day.setDisplayFormat('dd.MM.yyyy')
        clock=QTimeEdit(QTime.currentTime().addSecs(300));clock.setDisplayFormat('HH:mm')
        f.addRow(label('Seçtiğiniz saatte soru ekranı doğrudan açılır. Öğrencinin düğmeye basması gerekmez.','Muted'))
        f.addRow('Başlangıç tarihi',day);f.addRow('Başlangıç saati',clock)
        def save():
            from role_schedule import schedule
            try:
                message=schedule(self.identity,assignment_id,sid,day.date().toString('yyyy-MM-dd')+'T'+clock.time().toString('HH:mm:ss'))
                d.accept();self.show_section('tasks');QMessageBox.information(self,'Otomatik çalışma',message)
            except (ValueError,sqlite3.Error) as exc:error.setText(str(exc))
        f.addRow(button('Saati kaydet',save));d.exec()

    def materials_page(self,layout):
        import teaching_materials as materials
        top=QHBoxLayout();top.addWidget(label('Ders materyalleri ve soru paketlerim','Section'),1)
        top.addWidget(button('Yeni soru paketi hazırla',self.material_dialog));layout.addLayout(top)
        layout.addWidget(label('PDF / Word belgesinden taslak oluştur, soruları incele ve düzenle, sonra sınıfa veya çocuğuna görev ver. Paketler yalnızca kendi hesabında görünür.','Muted'))
        packs=materials.owned_packs(self.identity)
        if not packs: layout.addWidget(label('Henüz onaylanmış paketin yok. Belge seçebilir veya sorularını elle hazırlayabilirsin.','Section'))
        for pack in packs:
            frame,l=card(pack['title'])
            l.addWidget(label(f"{pack['grade']}. sınıf · {pack['subject']} · {len(pack['questions'])} onaylı soru",'Muted'))
            l.addWidget(label(pack['unit_title']))
            l.addWidget(label('Kaynak: '+(pack['document_name'] or 'Elle hazırlanmış sorular'),'Muted'))
            l.addWidget(button('Bu paketten görev ver',lambda _,pid=pack['id']:self.task_dialog(pid)))
            layout.addWidget(frame)
        layout.addStretch()

    def material_dialog(self):
        from material_ui import MaterialDialog
        grade=3
        if self.identity.role=='parent' and self.student_picker.currentData():
            grade=store.require_student(self.identity,self.student_picker.currentData())['grade']
        elif self.identity.role=='teacher':
            classroom=next((c for c in store.classes(self.identity) if c['id']==self.class_picker.currentData()),None)
            if classroom: grade=classroom['grade']
        dialog=MaterialDialog(self.identity,grade,self)
        if dialog.exec():
            self.show_section('materials')

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

    def task_dialog(self,selected_pack_id=None):
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
        import teaching_materials as materials
        from material_ui import QuestionComposer
        packs=materials.owned_packs(self.identity,grade)
        if selected_pack_id and selected_pack_id not in {p['id'] for p in packs}:
            QMessageBox.information(self,'Sınıf düzeyi','Bu paket için aynı sınıf düzeyindeki çocuğu veya sınıfı seçin.');return
        pack_picker=QComboBox();pack_picker.addItem('Hazır banka veya yeni sorular',None)
        for pack in packs: pack_picker.addItem(pack['title'],pack)
        f.addRow('Onaylı soru paketi',pack_picker)
        title,topic,count,due = QLineEdit(),QComboBox(),QSpinBox(),QDateEdit()
        title.setPlaceholderText('Örneğin: Bu haftaki fen keşfim')
        from curriculum import catalogue, subject_for_skill, ready_skills
        courses = catalogue(grade)
        subject,unit = QComboBox(),QComboBox()
        subject.addItem('Hazır alıştırmalar',None)
        for course in courses:
            subject.addItem(course['subject'],course)
        custom = QCheckBox('Seçtiğim MEB temasına kendi sorumu ekle')
        composer=QuestionComposer()
        composer.hide()
        custom.toggled.connect(composer.setVisible)
        source = label('MEB kaynakları çevrimdışı önbellekten gösterilir. Hazır sorular uygulamaya aittir.','Muted')
        source.setTextFormat(Qt.TextFormat.RichText)
        source.setOpenExternalLinks(True)
        f.addRow('Ders / MEB programı',subject)
        f.addRow('MEB tema / öğrenme alanı',unit)
        f.addRow(source)
        f.addRow(custom)
        f.addRow(composer)
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
            timed.setChecked(True);timed.setEnabled(False)
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
        for text,w in [('Görev adı',title),('Ders / konu',topic),('Soru sayısı',count),('Başlangıç tarihi' if self.identity.role=='parent' else 'Son tarih',due)]:
            f.addRow(text,w)
        def load_pack():
            pack=pack_picker.currentData()
            subject.setEnabled(True);unit.setEnabled(True);count.setEnabled(True)
            if pack:
                subject.setCurrentIndex(subject.findText(pack['subject']))
                unit.setCurrentIndex(unit.findText(pack['unit_title']))
                composer.set_questions(pack['questions'])
                custom.setEnabled(True);custom.setChecked(True);custom.setEnabled(False)
                subject.setEnabled(False);unit.setEnabled(False);count.setEnabled(False)
                title.setText(pack['title']);count.setValue(len(pack['questions']))
            else:
                composer.set_questions([]);filter_subject()
        pack_picker.currentIndexChanged.connect(load_pack)
        if selected_pack_id:
            pack_picker.setCurrentIndex(next(i for i in range(1,pack_picker.count()) if pack_picker.itemData(i)['id']==selected_pack_id))
        f.addRow(label('Sorular mevcut soru bankasından ve yerel üreticilerden hazırlanır.', 'Muted'))
        def save():
            try:
                curriculum_data=None;custom_bank=None
                selected_skill=topic.currentData()
                question_count=count.value()
                if custom.isChecked() and not subject.currentData():
                    custom_bank=materials.validate_questions(composer.questions)
                    question_count=len(custom_bank)
                if subject.currentData():
                    course=subject.currentData(); chosen_unit=unit.currentData()
                    if not chosen_unit: raise ValueError('Bu dersin tema bilgisi bulunamadı.')
                    curriculum_data=dict(grade=grade,subject=course['subject'],title=chosen_unit['title'],source=chosen_unit['url'])
                    custom_bank=materials.validate_questions(composer.questions) if custom.isChecked() else None
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
        page=QWidget();page.setStyleSheet(STUDENT_QSS)
        outer=QVBoxLayout(page);outer.setContentsMargins(30,24,30,24);outer.setSpacing(16)
        header=QHBoxLayout()
        asset='design_girl.png' if store.avatar_for(self.identity.student_id)=='student_girl.png' else 'design_boy.png'
        avatar=QLabel();avatar.setPixmap(portrait(asset,92));header.addWidget(avatar)
        greeting=QVBoxLayout();greeting.addWidget(label(f'Merhaba, {self.identity.name.replace(" · Örnek", "")}!', 'Title'))
        greeting.addWidget(label('Dersini seç, merak ettiğin konuyu keşfet.', 'Muted'));header.addLayout(greeting,1)
        header.addWidget(button('Çıkış yap',self.show_login,True));outer.addLayout(header)
        scroll=QScrollArea();scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        body=QWidget();columns=QHBoxLayout(body);columns.setContentsMargins(0,0,0,0);columns.setSpacing(18)
        practice,l=card('Bugün ne öğrenmek istersin?')
        l.addWidget(label('Kendi çalışmanı sen seç. İstediğin kadar alıştırma yapabilirsin.', 'Muted'))
        import questions as qb
        from curriculum import subject_for_skill
        grade=store.require_student(self.identity,self.identity.student_id)['grade']
        catalogue=list(qb.skills_for_grade(grade))
        subjects=list(dict.fromkeys(subject_for_skill(skill,grade) for skill,_ in catalogue))
        self.practice_subject=QComboBox();self.practice_subject.setObjectName('PracticeSubject')
        self.practice_subject.addItems(subjects)
        self.practice_topic=QComboBox();self.practice_topic.setObjectName('PracticeTopic')
        self.practice_count=QSpinBox();self.practice_count.setObjectName('PracticeCount')
        self.practice_count.setRange(1,1000);self.practice_count.setValue(12);self.practice_count.setSuffix(' soru')
        self.practice_continuous=QCheckBox('Soru sınırı olmadan devam et')
        self.practice_continuous.toggled.connect(lambda checked:self.practice_count.setEnabled(not checked))
        grid=QGridLayout();grid.setSpacing(10);subject_buttons={}
        colors={'Matematik':('#e0f2fe','#7dd3fc','#164d72'),'Türkçe':('#fff1e6','#ffadad','#82452d'),
                'Fen Bilimleri':('#d8f3dc','#95d5b2','#245d43'),'Hayat Bilgisi':('#fff3b0','#ead06a','#685315'),
                'Sosyal Bilgiler':('#f3efff','#bdb2ff','#4c3a91')}
        for index,subject in enumerate(subjects):
            bg,border,fg=colors.get(subject,('#f3efff','#bdb2ff','#4c3a91'))
            b=QPushButton(subject);b.setCheckable(True);b.setMinimumHeight(65)
            b.setStyleSheet(f'QPushButton {{ background: {bg}; color: {fg}; border: 2px solid {border}; border-radius: 18px; font-size: 18px; }} QPushButton:checked {{ border: 3px solid {fg}; }} QPushButton:hover {{ background: {border}; }}')
            b.clicked.connect(lambda _,value=subject:self.practice_subject.setCurrentText(value))
            grid.addWidget(b,index//2,index%2);subject_buttons[subject]=b
        l.addLayout(grid)
        form=QFormLayout();form.setSpacing(12)
        form.addRow('Ders',self.practice_subject);form.addRow('Konu',self.practice_topic)
        form.addRow('Kaç soru çözelim?',self.practice_count);l.addLayout(form)
        l.addWidget(self.practice_continuous)
        def topics_changed():
            subject=self.practice_subject.currentText();self.practice_topic.clear()
            self.practice_topic.addItem('Bu dersin tüm konuları',None)
            for skill,_ in catalogue:
                if subject_for_skill(skill,grade)==subject:self.practice_topic.addItem(qb.skill_name(skill),skill)
            for value,b in subject_buttons.items():b.setChecked(value==subject)
        self.practice_subject.currentIndexChanged.connect(topics_changed);topics_changed()
        def explore():
            skill=self.practice_topic.currentData()
            skills=[skill] if skill else [k for k,_ in catalogue if subject_for_skill(k,grade)==self.practice_subject.currentText()]
            self.start_quiz(skills=skills,count=self.practice_count.value(),continuous=self.practice_continuous.isChecked())
        l.addWidget(button('Alıştırmaya başla',explore));l.addStretch()
        columns.addWidget(practice,3)
        aside=QVBoxLayout();tasks=store.tasks(self.identity)
        buddy,bl=card('Öğrenme arkadaşın')
        owl=QLabel();owl.setPixmap(portrait('design_owl.png',100,'#fff3b0'));bl.addWidget(owl,0,Qt.AlignmentFlag.AlignHCenter)
        bl.addWidget(label('Her soru yeni bir keşif. Hazırsan sevdiğin dersle başlayalım!', 'Muted'))
        aside.addWidget(buddy)
        appointments,al=card('Planlı çalışmalarım')
        al.addWidget(label('Velinin seçtiği saat geldiğinde soru ekranın kendiliğinden açılır.', 'Muted'))
        for task in tasks:
            completed=task.get('completed',0)
            al.addWidget(label(task['title'],'Section'))
            if completed>=task['actual_count']:
                al.addWidget(label('Tamamlandı. Harika iş!'))
            elif task.get('scheduled_at'):
                from datetime import datetime
                when=datetime.fromisoformat(task['scheduled_at']).strftime('%d.%m.%Y · %H:%M')
                al.addWidget(label(f"{when} · Otomatik açılacak\n{completed}/{task['actual_count']} soru tamamlandı",'Muted'))
            else:
                al.addWidget(label('Başlama saatini velin belirleyecek.','Muted'))
        if not tasks:al.addWidget(label('Henüz planlı çalışman yok.','Muted'))
        aside.addWidget(appointments);aside.addStretch();columns.addLayout(aside,2)
        scroll.setWidget(body);outer.addWidget(scroll,1);self._replace(page)

    def start_quiz(self, assignment_id=None, skill=None, skills=None, count=12, continuous=False):
        from role_quiz import StudentQuiz, practice_questions
        try:
            questions = store.task_questions(self.identity,assignment_id) if assignment_id else practice_questions(self.identity,count=24 if continuous else count,skills=skills or ([skill] if skill else None))
            self.quiz = StudentQuiz(self.identity,questions,assignment_id,continuous=continuous,practice_skills=skills or ([skill] if skill else None))
            self.quiz.finished.connect(self.quiz_finished)
            self.quiz.showFullScreen()
            self.quiz.raise_()
            self.quiz.activateWindow()
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
