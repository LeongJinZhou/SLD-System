"""cPanel/Passenger startup file; configure secrets through the hosting panel."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wsgi import application
