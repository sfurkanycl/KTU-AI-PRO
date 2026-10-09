"""Persistent, current-user Windows appointment launches and in-app polling."""
from datetime import datetime
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import role_store as store
from data import education_database as school


def schedule(identity, assignment_id, student_id, starts_at):
    store.require_student(identity,student_id)
    if identity.role != 'parent' or assignment_id not in {t['id'] for t in store.tasks(identity,student_id)}:
        raise ValueError('Bu görev için zamanlama yapamazsınız.')
    when = datetime.fromisoformat(starts_at)
    if when <= datetime.now():
        raise ValueError('Başlangıç zamanı gelecekte olmalı.')
    store.init_extras()
    with school.get_connection() as c:
        c.execute("UPDATE task_schedules SET status='cancelled' WHERE assignment_id=? AND student_id=? AND status='pending'",(assignment_id,student_id))
        sid = c.execute('INSERT INTO task_schedules(assignment_id,student_id,starts_at) VALUES (?,?,?)',
                        (assignment_id,student_id,when.isoformat(timespec='seconds'))).lastrowid
    try:
        register_windows(sid,when)
    except (OSError,subprocess.SubprocessError) as error:
        with school.get_connection() as c:
            c.execute('UPDATE task_schedules SET system_error=? WHERE id=?',(str(error),sid))
        return 'Görev kaydedildi. Windows zamanlayıcısı kurulamadı; otomatik açılış için uygulamayı açık tutun.'
    return 'Saatli görev kaydedildi. Bilgisayar açık ve Windows oturumu açıkken uygulama bu saatte açılacak.'


def register_windows(schedule_id,when):
    if os.name != 'nt':
        raise OSError('Windows gerekli.')
    ns='http://schemas.microsoft.com/windows/2004/02/mit/task'
    ET.register_namespace('',ns)
    def node(parent,name,text=None,**attrs):
        element=ET.SubElement(parent,'{'+ns+'}'+name,attrs)
        if text is not None: element.text=text
        return element
    root=ET.Element('{'+ns+'}Task',version='1.2')
    triggers=node(root,'Triggers'); trigger=node(triggers,'TimeTrigger')
    node(trigger,'StartBoundary',when.isoformat(timespec='seconds'));node(trigger,'Enabled','true')
    principals=node(root,'Principals');principal=node(principals,'Principal',id='Author')
    user=subprocess.run(['whoami'],capture_output=True,text=True,check=True,creationflags=0x08000000).stdout.strip()
    node(principal,'UserId',user);node(principal,'LogonType','InteractiveToken');node(principal,'RunLevel','LeastPrivilege')
    settings=node(root,'Settings');node(settings,'MultipleInstancesPolicy','IgnoreNew')
    node(settings,'DisallowStartIfOnBatteries','false');node(settings,'StopIfGoingOnBatteries','false')
    node(settings,'StartWhenAvailable','true');node(settings,'ExecutionTimeLimit','PT0S')
    actions=node(root,'Actions',Context='Author'); action=node(actions,'Exec')
    pythonw=Path(sys.executable).with_name('pythonw.exe')
    frozen=bool(getattr(sys,'frozen',False))
    node(action,'Command',str(Path(sys.executable) if frozen else pythonw if pythonw.exists() else Path(sys.executable)))
    node(action,'Arguments',f'--schedule-id {schedule_id}' if frozen else f'"{Path(__file__).with_name("main.py")}" --schedule-id {schedule_id}')
    node(action,'WorkingDirectory',str(Path(sys.executable).parent if frozen else Path(__file__).parent))
    path=None
    try:
        with tempfile.NamedTemporaryFile(suffix='.xml',delete=False) as f:
            path=f.name;f.write(ET.tostring(root,encoding='utf-16',xml_declaration=True))
        subprocess.run(['schtasks','/Create','/TN',f'LearningBreak_{schedule_id}','/XML',path,'/F'],capture_output=True,text=True,check=True,creationflags=0x08000000)
    finally:
        if path: os.unlink(path)


def due_schedule(schedule_id=None):
    store.init_extras()
    with school.get_connection() as c:
        rows=c.execute("SELECT * FROM task_schedules WHERE status='pending' AND starts_at<=? ORDER BY starts_at",(datetime.now().isoformat(timespec='seconds'),)).fetchall()
        for row in rows:
            if schedule_id is None or row['id']==schedule_id:
                identity=store.student_identity(row['student_id'])
                if store.task_questions(identity,row['assignment_id']):
                    return dict(row)
                c.execute("UPDATE task_schedules SET status='completed' WHERE id=?",(row['id'],))


def claim_schedule(schedule_id):
    with school.get_connection() as c:
        return c.execute("UPDATE task_schedules SET status='started' WHERE id=? AND status='pending'",(schedule_id,)).rowcount==1
