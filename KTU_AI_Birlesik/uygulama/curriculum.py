"""Official MEB catalogue cache; quiz questions are authored locally, not by MEB."""
import json
from pathlib import Path
from html.parser import HTMLParser
from urllib.request import urlopen
from urllib.parse import urljoin

CACHE = Path(__file__).with_name('meb_curriculum.json')
BASE = 'https://tymm.meb.gov.tr'


class Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.items=[];self.href=None;self.parts=[]
    def handle_starttag(self,tag,attrs):
        if tag=='a': self.href=dict(attrs).get('href');self.parts=[]
    def handle_data(self,data):
        if self.href: self.parts.append(data)
    def handle_endtag(self,tag):
        if tag=='a' and self.href:
            self.items.append((' '.join(' '.join(self.parts).split()),urljoin(BASE,self.href)))
            self.href=None


def fetch(url):
    parser=Links()
    with urlopen(url,timeout=25) as response: parser.feed(response.read().decode('utf-8'))
    return parser.items


def refresh():
    courses=[('Matematik','ilkokul-matematik-dersi'),('Türkçe','ilkokul-turkce-dersi'),
        ('Hayat Bilgisi','hayat-bilgisi-dersi'),('Fen Bilimleri','fen-bilimleri-dersi'),
        ('Sosyal Bilgiler','sosyal-bilgiler-dersi'),('İngilizce','ingilizce-dersi-temel-egitim'),
        ('Görsel Sanatlar','gorsel-sanatlar-dersi-temel-egitim'),('Müzik','muzik-dersi-temel-egitim'),
        ('Beden Eğitimi ve Oyun','beden-egitimi-ve-oyun-dersi'),
        ('Din Kültürü ve Ahlak Bilgisi','din-kulturu-ve-ahlak-bilgisi-dersi-temel-egitim'),
        ('İnsan Hakları, Vatandaşlık ve Demokrasi','insan-haklari-vatandaslik-ve-demokrasi-dersi'),
        ('Trafik Güvenliği','trafik-guvenligi-dersi')]
    rows=[];errors=[]
    for subject,slug in courses:
        try:
            for title,url in fetch(f'{BASE}/ogretim-programlari/ders/{slug}'):
                grade=next((g for g in range(1,5) if title.replace(' ','')==f'{g}.Sınıf'),None)
                if grade is None: continue
                units=[{'title':t,'url':u} for t,u in fetch(url) if '/unite/' in u or '/tema/' in u]
                # All curriculum detail links share the grade URL as prefix on this site.
                if not units:
                    units=[{'title':t,'url':u} for t,u in fetch(url) if u.startswith(url+'/') and t]
                rows.append(dict(subject=subject,grade=grade,url=url,units=units,
                    active_model='TYMM 2026–2027' if grade<=3 else '4. sınıf: uygulanan yıllık planı ayrıca doğrulayın'))
        except Exception as error: errors.append(f'{subject}: {error}')
    if not rows: raise RuntimeError('MEB programları indirilemedi.')
    CACHE.write_text(json.dumps({'retrieved':'2026-10-09','school_year':'2026-2027','courses':rows,'errors':errors},ensure_ascii=False,indent=2),encoding='utf-8')
    return rows,errors


def catalogue(grade):
    active=Path(__file__).with_name('active_curriculum.json')
    cache=active if active.exists() else CACHE
    if not cache.exists(): return []
    return [r for r in json.loads(cache.read_text(encoding='utf-8'))['courses'] if r['grade']==grade]


def subject_for_skill(skill,grade):
    if skill.startswith('cur_'):
        from curriculum_practice import skill_details
        return skill_details(skill)['subject']
    if 'turkce' in skill: return 'Türkçe'
    if skill in ('living_needs','matter_states','homework_science'): return 'Fen Bilimleri' if grade>=3 else 'Hayat Bilgisi'
    if skill in ('traffic','directions','homework_general'): return 'Sosyal Bilgiler' if grade==4 else 'Hayat Bilgisi'
    return 'Matematik'


def legacy_ready_skills(subject,title,grade):
    """Only offer automatic banks whose concepts match a downloaded theme."""
    if subject=='İngilizce':
        from curriculum_practice import topics
        return [t['skill'] for t in topics(grade) if t['subject']==subject and t['title']==title]
    if grade==4: return []  # The 2026–27 fourth-grade programme has a separate rollout.
    text=title.casefold().replace('\u0307','')
    if subject=='Matematik' and 'işlemlerden' in text:
        return ['m3_toplama']+(['m3_carpma'] if grade>=3 else [])
    if subject=='Hayat Bilgisi' and 'güvenli' in text: return ['traffic']
    if subject=='Hayat Bilgisi' and 'doğa' in text: return ['living_needs']
    if subject=='Hayat Bilgisi' and 'yaşadığım' in text and grade>=3: return ['directions']
    if subject=='Fen Bilimleri' and ('madde' in text): return ['matter_states']
    if subject=='Fen Bilimleri' and ('canlı' in text or 'yaşam' in text): return ['living_needs']
    return []


def ready_skills(subject,title,grade):
    """Every active unit has an authored offline bank, plus matching legacy packs."""
    from curriculum_practice import topics
    current=[t['skill'] for t in topics(grade) if t['subject']==subject and t['title']==title]
    return list(dict.fromkeys(current+legacy_ready_skills(subject,title,grade)))


if __name__=='__main__':
    rows,errors=refresh()
    print(f'{len(rows)} sınıf/ders; {sum(len(r["units"]) for r in rows)} tema. Uyarılar: {errors}')
