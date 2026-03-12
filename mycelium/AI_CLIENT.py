#!/usr/bin/env python3
"""
AI_CLIENT.py — SolarPunk unified AI brain
==========================================
Priority chain (first key that works wins):
  1. ANTHROPIC  (Claude claude-sonnet-4-6)    — best quality
  2. GROQ       (llama-3.3-70b-versatile)     — free tier, fast, ~14k req/day
  3. GEMINI     (gemini-2.0-flash)             — free tier, ~1500 req/day
  4. HF         (Qwen2.5-7B, Phi-4, gemma-2)  — fallback, HF_TOKEN required

Add GROQ_API_KEY or GEMINI_API_KEY to GitHub Secrets to unlock free AI.
All engines import: ask(), ask_json(), ask_json_list(), ai_available(), ai_backend()
"""
import os, json, requests

ANTHROPIC_KEY   = os.environ.get("ANTHROPIC_API_KEY", "")
GROQ_KEY        = os.environ.get("GROQ_API_KEY", "")
GEMINI_KEY      = os.environ.get("GEMINI_API_KEY", "")
HF_TOKEN        = os.environ.get("HF_TOKEN", "")
ANTHROPIC_MODEL = "claude-sonnet-4-6"

# HF fallback — smaller models that are actually free-tier accessible
HF_MODELS = [
    "Qwen/Qwen2.5-7B-Instruct",
    "microsoft/Phi-4",
    "google/gemma-2-9b-it",
]


def _ask_anthropic(messages, max_tokens=2000, system=None):
    body = {"model": ANTHROPIC_MODEL, "max_tokens": max_tokens, "messages": messages}
    if system:
        body["system"] = system
    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_KEY,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        json=body, timeout=120,
    )
    r.raise_for_status()
    text = r.json()["content"][0]["text"]
    print(f"  [AI] Claude ✓ ({len(text)}c)")
    return text


def _ask_groq(messages, max_tokens=2000, system=None):
    full = []
    if system:
        full.append({"role": "system", "content": system})
    full.extend(messages)
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json"},
        json={"model": "llama-3.3-70b-versatile", "messages": full, "max_tokens": max_tokens},
        timeout=60,
    )
    r.raise_for_status()
    text = r.json()["choices"][0]["message"]["content"]
    print(f"  [AI] Groq ✓ ({len(text)}c)")
    return text


def _ask_gemini(messages, max_tokens=2000, system=None):
    parts = []
    if system:
        parts.append({"text": system + "\n\n"})
    for m in messages:
        parts.append({"text": m["content"]})
    body = {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {"maxOutputTokens": max_tokens},
    }
    r = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}",
        headers={"Content-Type": "application/json"},
        json=body, timeout=60,
    )
    r.raise_for_status()
    text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
    print(f"  [AI] Gemini ✓ ({len(text)}c)")
    return text


def _ask_hf(messages, max_tokens=2000, system=None):
    full = []
    if system:
        full.append({"role": "system", "content": system})
    full.extend(messages)
    last_err = None
    for model in HF_MODELS:
        try:
            url = f"https://api-inference.huggingface.co/models/{model}/v1/chat/completions"
            r = requests.post(
                url,
                headers={"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"},
                json={"model": model, "messages": full, "max_tokens": max_tokens, "temperature": 0.7},
                timeout=60,
            )
            if r.status_code == 410:
                print(f"  [AI] HF {model.split('/')[-1]} — 410 Gone, skip")
                continue
            r.raise_for_status()
            text = r.json()["choices"][0]["message"]["content"]
            print(f"  [AI] HF {model.split('/')[-1]} ✓ ({len(text)}c)")
            return text
        except Exception as e:
            print(f"  [AI] HF {model.split('/')[-1]} failed: {e}")
            last_err = e
    raise RuntimeError(f"All HF models failed. Last: {last_err}")


def ask(messages, max_tokens=2000, system=None):
    if ANTHROPIC_KEY:
        try:
            return _ask_anthropic(messages, max_tokens=max_tokens, system=system)
        except Exception as e:
            print(f"  [AI] Anthropic error ({e}), trying next...")
    if GROQ_KEY:
        try:
            return _ask_groq(messages, max_tokens=max_tokens, system=system)
        except Exception as e:
            print(f"  [AI] Groq error ({e}), trying next...")
    if GEMINI_KEY:
        try:
            return _ask_gemini(messages, max_tokens=max_tokens, system=system)
        except Exception as e:
            print(f"  [AI] Gemini error ({e}), trying HF fallback...")
    if HF_TOKEN:
        return _ask_hf(messages, max_tokens=max_tokens, system=system)
    raise RuntimeError("No AI backend — add GROQ_API_KEY or GEMINI_API_KEY to GitHub Secrets (both free)")


def ask_json(prompt, max_tokens=2000, system=None):
    sys_suffix = "\nRespond ONLY with a valid JSON object. No markdown, no preamble."
    full_sys = ((system or "") + sys_suffix).strip()
    try:
        text = ask([{"role": "user", "content": prompt}], max_tokens=max_tokens, system=full_sys)
        text = text.strip()
        for fence in ["```json", "```"]:
            if text.startswith(fence):
                text = text[len(fence):]
                if text.endswith("```"):
                    text = text[:-3]
                break
        s, e = text.find("{"), text.rfind("}") + 1
        if s >= 0:
            return json.loads(text[s:e])
    except Exception as ex:
        print(f"  [AI] ask_json parse failed: {ex}")
    return None


def ask_json_list(prompt, max_tokens=2000, system=None):
    sys_suffix = "\nRespond ONLY with a valid JSON array. No markdown, no preamble."
    full_sys = ((system or "") + sys_suffix).strip()
    try:
        text = ask([{"role": "user", "content": prompt}], max_tokens=max_tokens, system=full_sys)
        text = text.strip()
        for fence in ["```json", "```"]:
            if text.startswith(fence):
                text = text[len(fence):]
                if text.endswith("```"):
                    text = text[:-3]
                break
        s, e = text.find("["), text.rfind("]") + 1
        if s >= 0:
            return json.loads(text[s:e])
    except Exception as ex:
        print(f"  [AI] ask_json_list parse failed: {ex}")
    return []


def ai_available():
    return bool(ANTHROPIC_KEY or GROQ_KEY or GEMINI_KEY or HF_TOKEN)


def ai_backend():
    if ANTHROPIC_KEY:
        return "anthropic"
    if GROQ_KEY:
        return "groq"
    if GEMINI_KEY:
        return "gemini"
    if HF_TOKEN:
        return "huggingface"
    return "none"


if __name__ == "__main__":
    print(f"AI_CLIENT — backend: {ai_backend()}")
    r = ask([{"role": "user", "content": "Say exactly: SolarPunk AI online."}], max_tokens=20)
    print(f"Test: {r}")
