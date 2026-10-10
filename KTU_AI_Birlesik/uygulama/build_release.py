"""Build a clean Windows release, excluding all user databases, keys and caches."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parent


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--without-local-voice',action='store_true');args=parser.parse_args()
    build=ROOT/'_build_artifacts';dist=ROOT/'dist'
    build.mkdir(exist_ok=True);dist.mkdir(exist_ok=True)
    command=[sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onedir','--windowed',
        '--name','OgrenmeMolasi','--distpath',str(dist),'--workpath',str(build/'app'),
        '--specpath',str(build),'--paths',str(ROOT),
        '--add-binary',str(ROOT/'keyboard_guard.dll')+';.',
        '--add-data',str(ROOT/'assets')+';assets',
        '--add-data',str(ROOT/'legacy_runtime')+';legacy_runtime',
        '--add-data',str(ROOT/'sorular.json')+';.',
        '--add-data',str(ROOT/'meb_curriculum.json')+';.',
        '--add-data',str(ROOT/'active_curriculum.json')+';.',
        '--add-data',str(ROOT/'learning_engine'/'question_bank.json')+';learning_engine',
        '--add-data',str(ROOT/'recognize_ink.ps1')+';.',
        '--hidden-import','main','--hidden-import','learning','--hidden-import','session_runner',
        '--hidden-import','question_api','--hidden-import','resources','--hidden-import','eleven_audio',
        '--hidden-import','pin_security','--hidden-import','school_content','--hidden-import','winsound',
        str(ROOT/'packaged_main.py')]
    subprocess.run(command,cwd=ROOT,check=True)
    release=dist/'OgrenmeMolasi'
    if not args.without_local_voice:
        voice_python=ROOT/'learning_engine'/'.venv-tts'/'Scripts'/'python.exe'
        model=ROOT/'learning_engine'/'local_models'/'tr_TR-dfki-medium.onnx'
        if not voice_python.exists() or not model.exists(): raise SystemExit('Yerel ses ortamı/modeli yok. Önce öğrenme motorunun yerel ses kurulumunu tamamlayın.')
        subprocess.run([str(voice_python),'-m','PyInstaller','--noconfirm','--clean','--onedir','--console',
            '--name','LocalSpeech','--distpath',str(build/'speech_dist'),'--workpath',str(build/'speech'),
            '--specpath',str(build),'--paths',str(ROOT),'--collect-all','piper','--collect-all','onnxruntime',
            str(ROOT/'packaged_speech.py')],cwd=ROOT,check=True)
        shutil.copytree(build/'speech_dist'/'LocalSpeech',release/'speech',dirs_exist_ok=True)
        models=release/'speech'/'models';models.mkdir(exist_ok=True)
        for p in (model,Path(str(model)+'.json')):shutil.copy2(p,models/p.name)
    shutil.copy2(ROOT/'ROL_KULLANIMI.md',release/'KULLANIM.md')
    shutil.copy2(ROOT/'.env.example',release/'.env.example')
    (release/'BASLAMADAN_ONCE.txt').write_text('OgrenmeMolasi.exe dosyasini calistirin. ZIP tamamen cikarilmalidir.\nKisisel veriler ve .env ayarlari %LOCALAPPDATA%/OgrenmeMolasi altinda tutulur.\nKaynak projenin hesaplari ve API anahtarlari bu pakete eklenmemistir.\n',encoding='utf-8')
    archive=dist/'OgrenmeMolasi-Windows.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for p in release.rglob('*'):
            if p.is_file(): z.write(p,p.relative_to(dist))
    print('RELEASE:',archive)


if __name__=='__main__':main()
