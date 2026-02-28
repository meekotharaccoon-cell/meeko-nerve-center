#!/usr/bin/env python3
"""
Diagnostic Emailer
===================
Wrapper that calls unified_briefing.py.
Exists so MASTER_CONTROLLER.yml Phase 0 and Final steps don't fail
with 'No such file' errors.

The actual logic lives in unified_briefing.py which has full
delta tracking (only emails when content is genuinely new).
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

try:
    import unified_briefing
    unified_briefing.run()
except Exception as e:
    print(f'[diagnostic_emailer] Error: {e}')
    print('[diagnostic_emailer] unified_briefing.py unavailable — skipping')
