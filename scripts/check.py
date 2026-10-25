"""Offline deterministic checks using dependencies already available in this environment."""
from pathlib import Path
import sys
import unittest

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'services/api'))
suite = unittest.defaultTestLoader.discover(str(root / 'services/api/tests'))
result = unittest.TextTestRunner(verbosity=2).run(suite)
sys.exit(not result.wasSuccessful())
