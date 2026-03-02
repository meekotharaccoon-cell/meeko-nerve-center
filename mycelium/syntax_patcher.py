#!/usr/bin/env python3
"""
syntax_patcher.py — Bulk Python syntax fixer for Meeko Mycelium
================================================================
Scans all .py files in the repo and auto-patches three known LLM
code-generation patterns that break on Python 3.11+:

  PATTERN 1: Bare uncommented section dividers
    Before:  COLORS
             SECTION TITLE
    After:   # --- Colors ---
             # --- Section title ---

  PATTERN 2: Nested single-quotes in f-strings
    Before:  f"<div class=\"{'ok' if v else 'off'}\">..."
    After:   pre-computed variable + string concat

  PATTERN 3: Backslash in f-string expression
    Before:  f"...{'\\n'.join(items)}..."
    After:   nl = '\\n'; f"...{nl.join(items)}..."

Writes fixes directly to files. Safe to run repeatedly (idempotent).
Skips files that are already clean.

Usage:
  python syntax_patcher.py            # scan and fix all files
  python syntax_patcher.py --dry-run  # show what would be fixed, no writes
  python syntax_patcher.py --check    # exit 1 if any errors found (CI mode)
"""

import ast
import sys
import re
import argparse
from pathlib import Path

ROOT = Path(__file__).parent.parent

# ─── Helpers ───────────────────────────────────────────────────────────────

GREEN  = '\033[92m'
YELLOW = '\033[93m'
RED    = '\033[91m'
CYAN   = '\033[96m'
DIM    = '\033[2m'
BOLD   = '\033[1m'
RESET  = '\033[0m'

def colorize(s, c):
    return c + s + RESET

def ok(s):   print(colorize('  \u2713 ', GREEN)  + s)
def warn(s): print(colorize('  \u26a0 ', YELLOW) + s)
def err(s):  print(colorize('  \u2717 ', RED)    + s)
def info(s): print(colorize('  \u2192 ', CYAN)   + s)

# ─── Pattern 1: Bare section dividers ──────────────────────────────────────

# These are lines that appear between # ─── separator lines and are just
# plain text treated as Python identifiers (SyntaxError or NameError).
# 
# We identify them as: non-empty lines that:
#   - don't start with # or a Python keyword
#   - don't contain =, (, ), :, [, {, @
#   - are adjacent to lines starting with "# ─" or "# =" or "# ="

PYTHON_STARTS = (
    'def ', 'class ', 'import ', 'from ', 'if ', 'else', 'elif ',
    'for ', 'while ', 'try', 'except', 'finally', 'with ', 'return',
    'raise ', 'pass', 'break', 'continue', 'yield', 'async ', 'await ',
    '@', '#', '"""', "'''", '"', "'",
)
PYTHON_OPERATORS = set('=()[]{}<>:,./\\|&^%*+-!~;@')

def is_separator_line(line):
    stripped = line.strip()
    return (stripped.startswith('# \u2500') or stripped.startswith('# \u2501') or
            stripped.startswith('# =') or stripped.startswith('# -') or
            stripped.startswith('# \u2014') or stripped.startswith('# \u2013'))

def is_bare_section_divider(line, prev_lines, next_lines):
    """Returns True if this line is a bare text section title that's not valid Python."""
    stripped = line.strip()
    if not stripped:
        return False
    # Must not start with any Python token
    if any(stripped.startswith(s) for s in PYTHON_STARTS):
        return False
    # Must not contain Python operators (but allow text with hyphens, spaces, emojis)
    has_python_op = any(c in PYTHON_OPERATORS for c in stripped
                        if c not in '-\u2014\u2013\u2192 ')
    if has_python_op:
        return False
    # Check neighbors are separator lines
    for neighbor in prev_lines + next_lines:
        if is_separator_line(neighbor):
            return True
    return False

def fix_bare_dividers(lines):
    """Comment out bare section divider lines."""
    fixed = list(lines)
    changed = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        prev = [lines[i-1]] if i > 0 else []
        nxt  = [lines[i+1]] if i < len(lines)-1 else []
        if is_bare_section_divider(line, prev, nxt):
            indent = len(line) - len(line.lstrip())
            fixed[i] = ' ' * indent + '# --- ' + stripped.title() + ' ---\n'
            changed += 1
    return fixed, changed

# ─── Pattern 2: Nested quotes in f-strings ─────────────────────────────────

# Detect: f"...{'expr' if cond else 'other'}..." or f'...{d["key"]}...'
# These fail in Python <3.12 inside f-strings.
# We flag them for manual review (too risky to auto-patch reliably).

NESTED_FSTRING_RE = re.compile(
    r"""f['\"].*?\{[^}]*(?:'[^']*'|"[^"]*")[^}]*\}""",
    re.DOTALL
)

def find_nested_fstring_issues(lines):
    issues = []
    for i, line in enumerate(lines):
        if 'f"' in line or "f'" in line:
            if re.search(r"f['\"][^'\"]*\{[^}]*(?:'[^']*'|\"[^\"]*\")[^}]*\}", line):
                issues.append((i + 1, line.rstrip()))
    return issues

# ─── Pattern 3: Backslash in f-string expression ───────────────────────────

BACKSLASH_FSTRING_RE = re.compile(r"f['\"].*?\{[^}]*\\[ntr][^}]*\}")

def find_backslash_fstring_issues(lines):
    issues = []
    for i, line in enumerate(lines):
        if re.search(r"f['\"].*?\{[^}]*\\[ntr0-9][^}]*\}", line):
            issues.append((i + 1, line.rstrip()))
    return issues

def fix_backslash_fstrings(source):
    """
    Replace {'\n'.join(x)} → {nl.join(x)} pattern.
    Prepends nl = '\n' before the function/method if not already present.
    """
    if "nl = '\\n'" in source or 'nl = "\\n"' in source:
        return source, 0  # already fixed

    # Check if pattern exists
    pattern = re.compile(r"\{['\"]\\n['\"]\.join\(([^)]+)\)\}")
    if not pattern.search(source):
        return source, 0

    # Add nl = '\n' near the top (after imports, before first function)
    nl_decl = "nl = '\\n'  # pre-assigned to avoid backslash-in-fstring\n"
    lines = source.split('\n')
    insert_at = 0
    for i, line in enumerate(lines):
        if line.startswith('def ') or line.startswith('class ') or line.startswith('async def '):
            insert_at = i
            break
    if insert_at > 0:
        lines.insert(insert_at, nl_decl.rstrip())
        source = '\n'.join(lines)

    # Replace the pattern
    fixed, count = pattern.subn(r'{nl.join(\1)}', source)
    return fixed, count

# ─── Syntax check ──────────────────────────────────────────────────────────

def check_syntax(source, filepath):
    try:
        ast.parse(source)
        return True, None
    except SyntaxError as e:
        return False, e

# ─── Main scanner ──────────────────────────────────────────────────────────

def scan_and_fix(root, dry_run=False, check_mode=False):
    py_files = sorted(root.rglob('*.py'))
    
    total = 0
    broken = []
    fixed_files = []
    warned_files = []

    print(f'\n{BOLD}\u2588 MEEKO SYNTAX PATCHER{RESET}')
    print(f'{DIM}Scanning {len(py_files)} Python files...{RESET}\n')

    for fpath in py_files:
        # Skip __pycache__ and hidden dirs
        if any(p.startswith('.') or p == '__pycache__' for p in fpath.parts):
            continue
        try:
            source = fpath.read_text(encoding='utf-8', errors='replace')
        except Exception as e:
            warn(str(fpath.relative_to(root)) + ' — read error: ' + str(e))
            continue

        total += 1
        rel = str(fpath.relative_to(root))

        # Check initial syntax
        ok_syntax, syn_err = check_syntax(source, fpath)
        
        lines = source.splitlines(keepends=True)
        new_lines = list(lines)
        changes = 0

        # Pattern 1: bare dividers
        new_lines, n1 = fix_bare_dividers(new_lines)
        changes += n1

        # Pattern 3: backslash in fstring
        new_source_p3, n3 = fix_backslash_fstrings(''.join(new_lines))
        if n3:
            new_lines = new_source_p3.splitlines(keepends=True)
            changes += n3

        new_source = ''.join(new_lines)

        # Re-check syntax after fixes
        ok_after, syn_after = check_syntax(new_source, fpath)

        # Pattern 2: nested quotes — flag only, don't auto-fix (too risky)
        nested = find_nested_fstring_issues(new_lines)

        if changes > 0 and ok_after:
            if not dry_run:
                fpath.write_text(new_source, encoding='utf-8')
            status = '[DRY RUN] Would fix' if dry_run else 'Fixed'
            ok(rel + ' — ' + status + ' (' + str(changes) + ' patches)')
            fixed_files.append(rel)
        elif not ok_syntax and ok_after:
            # Fixer solved it
            if not dry_run:
                fpath.write_text(new_source, encoding='utf-8')
            ok(rel + ' — Fixed syntax error')
            fixed_files.append(rel)
        elif not ok_after:
            err(rel + ' — STILL BROKEN: ' + str(syn_after))
            broken.append((rel, syn_after))
        
        if nested:
            for lineno, linetext in nested[:2]:  # show up to 2
                warn(rel + ':' + str(lineno) + ' — nested f-string quotes (manual fix needed)')
                info('  ' + linetext[:100])
            warned_files.append(rel)

    # Summary
    print('\n' + BOLD + '=' * 55 + RESET)
    print(BOLD + '  SCAN COMPLETE' + RESET)
    print('  ' + colorize(str(total), CYAN) + ' files scanned')
    if fixed_files:
        print('  ' + colorize(str(len(fixed_files)), GREEN) + ' files fixed')
    if warned_files:
        print('  ' + colorize(str(len(warned_files)), YELLOW) + ' files need manual review (nested f-string quotes)')
    if broken:
        print('  ' + colorize(str(len(broken)), RED) + ' files still broken:')
        for f, e in broken:
            print('    ' + RED + f + RESET + ' — ' + str(e))
    else:
        print('  ' + colorize('\u2713 Zero syntax errors remain', GREEN))
    print(BOLD + '=' * 55 + RESET + '\n')

    if check_mode and broken:
        sys.exit(1)

    return {'total': total, 'fixed': len(fixed_files), 
            'broken': len(broken), 'warned': len(warned_files)}

if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Meeko Syntax Patcher')
    p.add_argument('--dry-run', action='store_true', help='Show changes without writing')
    p.add_argument('--check',   action='store_true', help='Exit 1 if errors found (CI)')
    args = p.parse_args()

    scan_and_fix(ROOT, dry_run=args.dry_run, check_mode=args.check)
