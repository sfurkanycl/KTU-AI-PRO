"""Preserved Windows implementation; see legacy_runtime/README.md."""
from legacy_loader import load_into
load_into(globals(), 'student_panel')

from integrated_ui import enhance_break_window
PackagedBreakWindow = BreakWindow
BreakWindow = enhance_break_window(PackagedBreakWindow, FractionBars)
