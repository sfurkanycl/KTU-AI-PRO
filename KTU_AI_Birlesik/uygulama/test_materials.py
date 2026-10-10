"""Scoped authoring, document handling, adaptive support and reporting regressions."""
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import test_roles as fixtures
import role_store as store
import teaching_materials as materials
from role_quiz import AccountSession,concept_of,semantic_key
from curriculum import catalogue
from data import education_database as school


class MaterialTests(unittest.TestCase):
    setUp=fixtures.RoleTests.setUp
    close_windows=fixtures.RoleTests.close_windows
    @classmethod
    def setUpClass(cls): fixtures.RoleTests.setUpClass.__func__(cls)
    def bank(self):
        return [dict(text=f'Okuduğun metne göre {n} numaralı soruyu yanıtla.',choices=['A','B','C','D'],answer=0,
            hint='Metindeki bilgiyi bul.',explanation='Metinde A bilgisi veriliyor.',concept='okudugunu_anlama',
            example='Başka bir metinde bilgiyi bulup karşılaştırabiliriz.') for n in range(3)]
    def metadata(self):
        course=next(r for r in catalogue(3) if r['subject']=='Türkçe');unit=course['units'][0]
        return dict(grade=3,subject='Türkçe',title=unit['title'],source=unit['url'])
    def test_read_text_docx_pdf_and_reject_empty_scan(self):
        folder=Path(self.temp.name)
        text='Çocuklar kitap okur. '*10
        (folder/'ders.txt').write_text(text,encoding='utf-8-sig')
        self.assertEqual(materials.extract_text(folder/'ders.txt'),text.strip())
        with zipfile.ZipFile(folder/'ders.docx','w') as z:
            z.writestr('word/document.xml','<w:document xmlns:w="urn:word"><w:p><w:r><w:t>Çocuklar kitap okur.</w:t></w:r></w:p></w:document>')
        self.assertEqual(materials.extract_text(folder/'ders.docx'),'Çocuklar kitap okur.')
        from pypdf import PdfWriter
        writer=PdfWriter();writer.add_blank_page(width=200,height=200)
        with (folder/'scan.pdf').open('wb') as f: writer.write(f)
        with self.assertRaisesRegex(ValueError,'OCR'): materials.extract_text(folder/'scan.pdf')
        (folder/'huge.txt').write_text('a'*45001)
        with self.assertRaisesRegex(ValueError,'45.000'): materials.extract_text(folder/'huge.txt')
    def test_approval_owned_packs_and_curriculum_task(self):
        metadata=self.metadata()
        pid=materials.save_pack(self.teacher,'Okuma paketi',3,'Türkçe',metadata['title'],metadata['source'],'ders.docx',self.bank())
        pack=materials.owned_packs(self.teacher)[0]
        self.assertEqual(pack['id'],pid)
        self.assertEqual(materials.owned_packs(self.other_teacher),[])
        self.assertEqual(materials.owned_packs(self.parent),[])
        with self.assertRaises(ValueError): materials.owned_packs(self.student)
        aid=store.create_task(self.teacher,'Okuma görevi','m3_toplama',3,class_id=self.class_id,
            curriculum=metadata,custom_questions=pack['questions'])
        qs=store.task_questions(self.student,aid)
        self.assertTrue(all(q['verified'] and q['source']=='teacher-reviewed' for q in qs))
        self.assertEqual(store.tasks(self.student)[0]['subject'],'Türkçe')
    def test_validation_does_not_publish_bad_questions(self):
        for changes in (dict(choices=['A','A','B','C']),dict(answer=4),dict(explanation='')):
            q=dict(self.bank()[0],**changes)
            with self.assertRaises(ValueError): materials.validate_questions([q])
        with self.assertRaises(ValueError): materials.validate_questions([self.bank()[0]]*2)
        with self.assertRaises(ValueError): store.create_task(self.parent,'Eksik paket','traffic',3,student_id=self.child,custom_questions=self.bank()[:2])
    def test_wrong_answer_prefers_same_concept_without_duplicate_task_results(self):
        bank=self.bank();bank[1]['concept']='başka_kazanım'
        aid=store.create_task(self.teacher,'Kazanım sırası','m3_toplama',3,class_id=self.class_id,curriculum=self.metadata(),custom_questions=bank)
        qs=store.task_questions(self.student,aid)
        session=AccountSession(self.student,qs,aid,enable_support=True)
        first=session.next_question();feedback=session.answer(1,5)
        self.assertEqual(feedback['kind'],'hint')
        second=session.next_question()
        self.assertEqual(second['id'],qs[2]['id'])
        self.assertNotEqual(semantic_key(first),semantic_key(second))
        self.assertEqual(session.answer(1,5)['kind'],'explanation')
        self.assertEqual(store.tasks(self.student)[0]['completed'],2)
        self.assertEqual(session.support_attempts,0)
    def test_additional_support_is_bounded_and_separate_from_task_completion(self):
        from learning_engine.school_content import SCENES
        scene=SCENES['traffic_red']
        q=dict(id=1,skill='traffic',text=scene['question'],choices=scene['options'],answer=0,
            hint='Işığın rengine bak.',explanation=scene['explanation'],visual={'scene_id':'traffic_red'})
        session=AccountSession(self.student,[q],enable_support=True)
        session.next_question();session.answer(1,5)
        self.assertFalse(session.goal_reached())
        support=session.next_question()
        self.assertTrue(support['_support_question'])
        self.assertEqual(concept_of(support),concept_of(q))
        self.assertNotEqual(semantic_key(support),semantic_key(q))
        session.answer(support['answer'],5,True)
        self.assertTrue(session.goal_reached())
        report=store.analytics(self.parent,self.child)
        self.assertEqual(sum(r['support'] for r in report['concepts']),1)
        self.assertEqual(sum(r['hints'] for r in report['concepts']),1)
        self.assertEqual(session.progress_value(),(1,1))
        self.assertLessEqual(session._support_added,2)
    def test_ai_drafts_require_explicit_save_and_do_not_call_real_api(self):
        response=SimpleNamespace(output_text=json.dumps({'questions':self.bank()[:2]},ensure_ascii=False))
        fake=SimpleNamespace(interactions=SimpleNamespace(create=lambda **kw:response),close=lambda:None)
        with patch.dict('os.environ',{'GEMINI_GENERATOR_KEY':'test-only'}),patch('google.genai.Client',return_value=fake):
            generated=materials.generate_questions('Örnek ders içeriği. '*15,3,'Türkçe','Okuma',2)
        self.assertFalse(any(q['verified'] for q in generated))
        self.assertEqual(materials.owned_packs(self.teacher),[])
    def test_material_ui_renders_without_affecting_existing_roles(self):
        from material_ui import MaterialDialog
        d=MaterialDialog(self.teacher,3);self.windows.append(d)
        d.title.setText('Doğayı tanıyoruz')
        d.composer.set_questions(self.bank());d.show();self.app.processEvents()
        Path('test_artifacts').mkdir(exist_ok=True)
        d.grab().save('test_artifacts/material_workshop.png')
        self.assertEqual(d.grade.currentData(),3)
        self.assertEqual(d.composer.list.count(),3)
        d.reject()

    def test_approved_pack_can_be_assigned_through_task_form(self):
        from role_ui import RoleWindow
        from PyQt6.QtCore import QTimer
        from PyQt6.QtWidgets import QDialog,QPushButton
        metadata=self.metadata()
        pid=materials.save_pack(self.teacher,'Okuma ataması',3,'Türkçe',metadata['title'],metadata['source'],'ders.txt',self.bank())
        window=RoleWindow();self.windows.append(window);window.enter(self.teacher)
        def submit():
            d=next(w for w in self.app.topLevelWidgets() if isinstance(w,QDialog) and w.isVisible())
            next(b for b in d.findChildren(QPushButton) if b.text()=='Görevi oluştur').click()
            if d.isVisible(): d.reject()
        QTimer.singleShot(100,submit);window.task_dialog(pid)
        tasks=store.tasks(self.student)
        self.assertEqual(len(tasks),1)
        self.assertEqual(tasks[0]['actual_count'],3)
        self.assertEqual(tasks[0]['subject'],'Türkçe')

    def test_csv_report_contains_only_selected_child_and_help_metrics(self):
        from role_ui import RoleWindow
        from PyQt6.QtWidgets import QFileDialog,QMessageBox
        metadata=self.metadata()
        aid=store.create_task(self.parent,'Okuma','m3_toplama',3,student_id=self.child,curriculum=metadata,custom_questions=self.bank())
        session=AccountSession(self.student,store.task_questions(self.student,aid),aid)
        q=session.next_question();session.answer(q['answer'],5,True)
        data=store.analytics(self.parent,self.child)
        self.assertEqual(data['concepts'][0]['hints'],1)
        self.assertEqual(data['concepts'][0]['clean'],0)
        self.assertEqual(data['concepts'][0]['status'],'Veri birikiyor')
        window=RoleWindow();self.windows.append(window)
        path=Path(self.temp.name)/'report.csv'
        with patch.object(QFileDialog,'getSaveFileName',return_value=(str(path),'CSV')),patch.object(QMessageBox,'information'):
            window.export_report(data)
        self.assertIn('okudugunu_anlama',path.read_text(encoding='utf-8-sig'))
        self.assertEqual(store.analytics(self.other)['total'],0)


    def test_workshop_without_key_loads_ready_unit_questions(self):
        import os
        from material_ui import MaterialDialog
        dialog=MaterialDialog(self.teacher,3);self.windows.append(dialog)
        dialog.text.setPlainText('Belgedeki bu cümle soru üretiminde kullanılmadı.')
        with patch.dict(os.environ,{'GEMINI_GENERATOR_KEY':''}),patch.object(dialog,'run_worker') as worker:
            dialog.generate()
        worker.assert_not_called()
        self.assertTrue(dialog.composer.questions)
        self.assertIn('belgeden üretilmedi',dialog.status.text())
        self.assertTrue(all(q['curriculum']['title']==dialog.unit.currentData()['title'] for q in dialog.composer.questions))
        self.assertTrue(dialog.title.text())
        dialog.save();self.assertIsNotNone(dialog.saved_pack_id)
    def test_workshop_settings_uses_adult_settings_dialog(self):
        from material_ui import MaterialDialog
        from role_ui import RoleWindow
        window=RoleWindow();self.windows.append(window);window.enter(self.teacher)
        dialog=MaterialDialog(self.teacher,3,window)
        with patch.object(window,'ai_settings') as settings:dialog.open_settings()
        settings.assert_called_once();dialog.reject();window.schedule_timer.stop()

if __name__=='__main__':unittest.main()
