#!/usr/bin/env python3
"""
AI_CLIENT.py — SolarPunk AI brain
===================================
Priority: ANTHROPIC_API_KEY (Claude) → HF_TOKEN (HuggingFace fallback)
All engines import this. Zero config needed beyond secrets.

ask()           — returns text string
ask_json()      — returns parsed dict
ask_json_list() — returns parsed list
"""
import os, json, requests

ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
HF_TOKEN      = os.environ.get("HF_TOKEN", "")

ANTHROPIC_MODEL = "claude-sonnet-4-6"  # fixed: was claude-sonnet-4-20250514 (invalid)
HF_MODELS = [
    "Qwen/Qwen2.5-72B-Instruct",
    "meta-llama/Llama-3.1-8B-Instruct",
    "microsoft/Phi-3.5-mini-instruct",
]


def _ask_anthropic(messages, max_tokens=2000, system=None):
    """Call Anthropic API directly."""
    body = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": max_tokens,
        "messages": messages,
    }
    if system:
        body["system"] = system
    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_KEY,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        json=body,
        timeout=120,
    )
    r.raise_for_status()
    data = r.json()
    text = data["content"][0]["text"]
    print(f"  [AI] Claude ({len(text)}c)")
    return text


def _ask_hf(messages, max_tokens=2000, system=None):
    """Call HuggingFace as fallback."""
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
                timeout=120,
            )
            r.raise_for_status()
            text = r.json()["choices"][0]["message"]["content"]
            print(f"  [AI] HF/{model.split('/')[-1]} ({len(text)}c)")
            return text
        except Exception as e:
            print(f"  [AI] HF/{model.split('/')[-1]} failed: {e}")
            last_err = e
    raise RuntimeError(f"All HF models failed. Last: {last_err}")


def ask(messages, max_tokens=2000, system=None):
    """
    Ask the AI. Returns text string.
    Uses ANTHROPIC_API_KEY if available, falls back to HF_TOKEN.
    messages: list of {"role": "user"|"assistant", "content": "..."}
    """
    if ANTHROPIC_KEY:
        try:
            return _ask_anthropic(messages, max_tokens=max_tokens, system=system)
        except Exception as e:
            print(f"  [AI] Anthropic failed ({e}), trying HF fallback...")
    if HF_TOKEN:
        return _ask_hf(messages, max_tokens=max_tokens, system=system)
    raise RuntimeError("No AI credentials — set ANTHROPIC_API_KEY or HF_TOKEN in GitHub Secrets")


def ask_json(prompt, max_tokens=2000, system=None):
    """Ask for a JSON object response. Returns parsed dict or None."""
    sys_suffix = "\nRespond ONLY with a valid JSON object. No markdown fences, no preamble."
    full_system = ((system or "") + sys_suffix).strip()
    try:
        text = ask([{"role": "user", "content": prompt}], max_tokens=max_tokens, system=full_system)
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
    """Ask for a JSON array response. Returns parsed list or []."""
    sys_suffix = "\nRespond ONLY with a valid JSON array. No markdown fences, no preamble."
    full_system = ((system or "") + sys_suffix).strip()
    try:
        text = ask([{"role": "user", "content": prompt}], max_tokens=max_tokens, system=full_system)
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
    """Returns True if any AI backend is configured."""
    return bool(ANTHROPIC_KEY or HF_TOKEN)


def ai_backend():
    """Returns which backend will be used."""
    if ANTHROPIC_KEY: return "anthropic"
    if HF_TOKEN: return "huggingface"
    return "none"


if __name__ == "__main__":
    print(f"AI_CLIENT — backend: {ai_backend()}")
    result = ask([{"role": "user", "content": "Say exactly: SolarPunk AI online."}], max_tokens=20)
    print(f"Test: {result}")
