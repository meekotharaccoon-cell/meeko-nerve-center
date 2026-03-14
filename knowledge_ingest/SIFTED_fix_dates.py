#!/usr/bin/env python3
"""
DATE FIXER - Ensures all generated content uses 2026 dates
Run this before any content generation
"""

import os
import re
from datetime import datetime
import json

CURRENT_YEAR = "2026"

def fix_dates_in_file(filepath):
    """Replace all 2026/2026 dates with 2026"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix years
    new_content = re.sub(r'20(2[4-5])', f'20{CURRENT_YEAR[-2:]}', content)
    
    # Fix copyright statements
    new_content = re.sub(r' 20\d{2}(-20\d{2})?', f' 2026', new_content)
    
    # Fix "Updated" statements
    new_content = re.sub(r'(Updated|Last updated|As of) (January|February|March|April|May|June|July|August|September|October|November|December) 20(2[4-5])', 
                        f'\\1 \\2 {CURRENT_YEAR}', new_content)
    
    if content != new_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

# Fix all Python and JSON files
fixed = 0
for root, dirs, files in os.walk('.'):
    for file in files:
        if file.endswith(('.py', '.json', '.html', '.md', '.txt', '.ps1', '.bat')):
            path = os.path.join(root, file)
            if fix_dates_in_file(path):
                print(f' Fixed: {path}')
                fixed += 1

print(f'\n TOTAL: {fixed} files updated to {CURRENT_YEAR}')
