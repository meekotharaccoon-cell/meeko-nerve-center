#!/usr/bin/env python3
"""
HAIOS Core - Hardware AI Operating System Core
==============================================

Language-Agnostic Consciousness Layer

Creator: Nguyễn Đức Cường (alpha_prime_omega)
Original Creation: October 30, 2025
Verification: 4287
"""

import sys
from pathlib import Path

# Add root directory to path to import from root-level modules
root_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(root_dir))

# Import from root-level implementation
from haios_core import LanguageAgnosticCore

# Export for module use
HAIOSCore = LanguageAgnosticCore

__all__ = ["HAIOSCore", "LanguageAgnosticCore"]
