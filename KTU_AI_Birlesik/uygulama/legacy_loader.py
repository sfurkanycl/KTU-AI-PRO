"""Load exact Python 3.12 application code recovered from the supplied EXE."""
import importlib.util
import marshal
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent


def load_into(namespace, name):
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError("Windows sürümünün korunmuş modülleri Python 3.12 gerektiriyor.")
    data = (ROOT / 'legacy_runtime' / (name + '.pyc')).read_bytes()
    if data[:4] != importlib.util.MAGIC_NUMBER:
        raise RuntimeError("Python bytecode sürümü uyumsuz.")
    exec(marshal.loads(data[16:]), namespace)
