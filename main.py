"""Launch the combined application from the project root."""
import os
from pathlib import Path
import runpy
import sys


def main():
    app_dir = Path(__file__).resolve().parent / 'KTU_AI_Birlesik' / 'uygulama'
    sys.path.insert(0, str(app_dir))
    os.chdir(app_dir)
    runpy.run_path(str(app_dir / 'main.py'), run_name='__main__')


if __name__ == '__main__':
    main()
