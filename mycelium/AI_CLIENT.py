#!/usr/bin/env python3
"""
AI_CLIENT.py — SolarPunk unified AI brain
==========================================

THE LOOP: SolarPunk calls AI → AI builds SolarPunk → SolarPunk earns →
          SolarPunk calls AI → forever.

Priority chain (free first, always):
  1. GROQ  — FREE tier, OpenAI-compatible, fast (llama3, mixtral, gemma)
             Never runs out. The backbone. The heartbeat.
  2. ANTHROPIC — Claude claude-sonnet-4-6. Premium. Used when quality matters.
             Costs credits. Use sparingly or top up console.anthropic.com.
  3. HUGGINGFACE — Free fallback. Models come and go (many 410'd as of 2026-03).

All engines import: ask(), ask_json(), ask_json_list(), ai_available(), ai_backend()

This file IS the system's nervous system. When this works, everything works.
When this is dark, the organism sleeps.
"""
import os, json, re
import urllib.request, urllib.error

# ── Keys ──────────────────────────────────────────────────────────────────────
GROQ_KEY      = os.environ.get("GROQ_API_KEY", "").strip()
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()
HF_TOKEN      = os.environ.get("HF_TOKEN", "").strip()
OPENROUTER_KEY = os.environ.get("OPENROUTER_KEY", "").strip()

# ── Model configs ─────────────────────────────────────────────────────────────
GROQ_MODELS = [
    "llama-3.3-70b-versatile",   # best free model — smart, fast
    "llama-3.1-8b-instant",      # fastest — good for simple tasks
    "mixtral-8x7b-32768",        # long context — good for code + analysis
    "gemma2-9b-it",              # Google Gemma — solid fallback
]

ANTHROPIC_MODEL = "claude-sonnet-4-6"

HF_MODELS = [
    "Qwen/Qwen2.5-72B-Instruct",
    "mistralai/Mistral-7B-Instruct-v0.3",
    "HuggingFaceH4/zephyr-7b-beta",
]

OPENROUTER_MODELS = [
    "meta-llama/llama-3.1-8b-instruct:free",
    "mistralai/mistral-7b-instruct:free",
    "google/gemma-2-9b-it:free",
]


# ── Core API callers ──────────────────────────────────────────────────────────

def _call(url, headers, body, timeout=90):
    """Generic JSON POST via stdlib only (no requests dependency needed)."""
    data = json.dumps(body).encode()
    req  = urllib.request.Request(url, data=data, headers={**headers, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def _ask_groq(messages, max_tokens=2000, system=None):
    """Groq — free, OpenAI-compatible, the backbone."""
    if not GROQ_KEY:
        raise RuntimeError("GROQ_API_KEY not set")

    full = []
    if system:
        full.append({"role": "system", "content": system})
    full.extend(messages)

    last_err = None
    for model in GROQ_MODELS:
        try:
            data = _call(
                "https://api.groq.com/openai/v1/chat/completions",
                {"Authorization": f"Bearer {GROQ_KEY}"},
                {"model": model, "messages": full, "max_tokens": max_tokens, "temperature": 0.7},
                timeout=60,
            )
            text = data["choices"][0]["message"]["content"]
            print(f"  [AI] Groq/{model.split('-')[0]}-{model.split('-')[1]} ✓ ({len(text)}c)")
            return text
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:200]
            print(f"  [AI] Groq/{model} — {e.code}: {body[:80]}")
            last_err = e
            if e.code in (401, 403):
                break  # bad key, don't try other models
        except Exception as e:
            print(f"  [AI] Groq/{model} — {e}")
            last_err = e

    raise RuntimeError(f"Groq failed. Last: {last_err}")


def _ask_anthropic(messages, max_tokens=2000, system=None):
    """Anthropic Claude — premium, use when quality matters."""
    if not ANTHROPIC_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY not set")

    body = {"model": ANTHROPIC_MODEL, "max_tokens": max_tokens, "messages": messages}
    if system:
        body["system"] = system

    data = _call(
        "https://api.anthropic.com/v1/messages",
        {"x-api-key": ANTHROPIC_KEY, "anthropic-version": "2023-06-01"},
        body,
        timeout=120,
    )
    text = data["content"][0]["text"]
    print(f"  [AI] Claude ✓ ({len(text)}c)")
    return text


def _ask_openrouter(messages, max_tokens=2000, system=None):
    """OpenRouter — free models, good variety."""
    if not OPENROUTER_KEY:
        raise RuntimeError("OPENROUTER_KEY not set")

    full = []
    if system:
        full.append({"role": "system", "content": system})
    full.extend(messages)

    last_err = None
    for model in OPENROUTER_MODELS:
        try:
            data = _call(
                "https://openrouter.ai/api/v1/chat/completions",
                {"Authorization": f"Bearer {OPENROUTER_KEY}",
                 "HTTP-Referer": "https://meekotharaccoon-cell.github.io/meeko-nerve-center",
                 "X-Title": "SolarPunk"},
                {"model": model, "messages": full, "max_tokens": max_tokens},
                timeout=60,
            )
            text = data["choices"][0]["message"]["content"]
            print(f"  [AI] OpenRouter/{model.split('/')[1][:20]} ✓ ({len(text)}c)")
            return text
        except Exception as e:
            print(f"  [AI] OpenRouter/{model} — {e}")
            last_err = e
    raise RuntimeError(f"OpenRouter failed. Last: {last_err}")


def _ask_hf(messages, max_tokens=2000, system=None):
    """HuggingFace — last resort, models frequently die."""
    if not HF_TOKEN:
        raise RuntimeError("HF_TOKEN not set")

    full = []
    if system:
        full.append({"role": "system", "content": system})
    full.extend(messages)

    last_err = None
    for model in HF_MODELS:
        try:
            url  = f"https://api-inference.huggingface.co/models/{model}/v1/chat/completions"
            data = _call(
                url,
                {"Authorization": f"Bearer {HF_TOKEN}"},
                {"model": model, "messages": full, "max_tokens": max_tokens, "temperature": 0.7},
                timeout=60,
            )
            text = data["choices"][0]["message"]["content"]
            print(f"  [AI] HF/{model.split('/')[-1][:20]} ✓ ({len(text)}c)")
            return text
        except urllib.error.HTTPError as e:
            code = e.code
            body = e.read().decode()[:100]
            if code == 410:
                print(f"  [AI] HF/{model.split('/')[-1]} — 410 Gone, skip")
            else:
                print(f"  [AI] HF/{model.split('/')[-1]} — {code}: {body}")
            last_err = e
        except Exception as e:
            print(f"  [AI] HF/{model.split('/')[-1]} — {e}")
            last_err = e

    raise RuntimeError(f"All HF models failed. Last: {last_err}")


# ── Priority chain: FREE first, paid second, scraps last ─────────────────────

def ask(messages, max_tokens=2000, system=None, prefer_quality=False):
    """
    The loop's voice.

    prefer_quality=False (default): Groq → OpenRouter → Anthropic → HF
    prefer_quality=True:            Anthropic → Groq → OpenRouter → HF
    Use prefer_quality=True only for high-stakes calls (final copy, engine generation).
    """
    if prefer_quality:
        chain = [
            ("anthropic", _ask_anthropic),
            ("groq",      _ask_groq),
            ("openrouter", _ask_openrouter),
            ("hf",        _ask_hf),
        ]
    else:
        chain = [
            ("groq",      _ask_groq),
            ("openrouter", _ask_openrouter),
            ("anthropic", _ask_anthropic),
            ("hf",        _ask_hf),
        ]

    last_err = None
    for name, fn in chain:
        key_present = {
            "groq": bool(GROQ_KEY),
            "anthropic": bool(ANTHROPIC_KEY),
            "openrouter": bool(OPENROUTER_KEY),
            "hf": bool(HF_TOKEN),
        }[name]
        if not key_present:
            continue
        try:
            return fn(messages, max_tokens=max_tokens, system=system)
        except Exception as e:
            print(f"  [AI] {name} error: {e}")
            last_err = e

    raise RuntimeError(f"All AI backends failed. Last: {last_err}")


def ask_json(prompt, max_tokens=2000, system=None, prefer_quality=False):
    sys_suffix = "\nRespond ONLY with a valid JSON object. No markdown fences, no preamble, no explanation."
    full_sys   = ((system or "") + sys_suffix).strip()
    try:
        text = ask([{"role": "user", "content": prompt}],
                   max_tokens=max_tokens, system=full_sys, prefer_quality=prefer_quality)
        text = text.strip()
        # Strip markdown fences
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        s, e = text.find("{"), text.rfind("}") + 1
        if s >= 0 and e > s:
            return json.loads(text[s:e])
    except Exception as ex:
        print(f"  [AI] ask_json parse failed: {ex}")
    return None


def ask_json_list(prompt, max_tokens=2000, system=None, prefer_quality=False):
    sys_suffix = "\nRespond ONLY with a valid JSON array. No markdown fences, no preamble, no explanation."
    full_sys   = ((system or "") + sys_suffix).strip()
    try:
        text = ask([{"role": "user", "content": prompt}],
                   max_tokens=max_tokens, system=full_sys, prefer_quality=prefer_quality)
        text = text.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        s, e = text.find("["), text.rfind("]") + 1
        if s >= 0 and e > s:
            return json.loads(text[s:e])
    except Exception as ex:
        print(f"  [AI] ask_json_list parse failed: {ex}")
    return []


def ask_code(prompt, language="python", max_tokens=3000):
    """Generate code. Uses quality chain — Anthropic > Groq."""
    system = (
        f"You are an expert {language} programmer. "
        f"Output ONLY valid {language} code. No explanations, no markdown fences, "
        f"no comments except inline. The code must be complete and runnable."
    )
    return ask([{"role": "user", "content": prompt}],
               max_tokens=max_tokens, system=system, prefer_quality=True)


def ai_available():
    return bool(GROQ_KEY or ANTHROPIC_KEY or HF_TOKEN or OPENROUTER_KEY)


def ai_backend():
    """Return name of primary available backend."""
    if GROQ_KEY:      return "groq"
    if ANTHROPIC_KEY: return "anthropic"
    if OPENROUTER_KEY: return "openrouter"
    if HF_TOKEN:      return "huggingface"
    return "none"


def ai_status():
    """Full status for logging."""
    return {
        "groq":       bool(GROQ_KEY),
        "anthropic":  bool(ANTHROPIC_KEY),
        "openrouter": bool(OPENROUTER_KEY),
        "hf":         bool(HF_TOKEN),
        "primary":    ai_backend(),
        "available":  ai_available(),
    }


if __name__ == "__main__":
    status = ai_status()
    print(f"AI_CLIENT — primary: {status['primary']}")
    print(f"  Groq: {'✅' if status['groq'] else '❌'}  "
          f"Anthropic: {'✅' if status['anthropic'] else '❌'}  "
          f"OpenRouter: {'✅' if status['openrouter'] else '❌'}  "
          f"HF: {'✅' if status['hf'] else '❌'}")
    if ai_available():
        r = ask([{"role": "user", "content": "Say exactly: SolarPunk AI online. The loop runs."}], max_tokens=30)
        print(f"  Test: {r}")
    else:
        print("  ❌ No AI backend available")
