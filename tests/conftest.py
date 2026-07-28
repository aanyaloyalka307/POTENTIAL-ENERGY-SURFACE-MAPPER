"""Put the repository root on sys.path so tests can import the phase modules.

The modules deliberately live at the repository root rather than inside a
package directory, so that their filenames match the roadmap documents in
docs/ one-for-one.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
