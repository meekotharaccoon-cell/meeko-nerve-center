#!/usr/bin/env python3
"""
AI_CLIENT.py — SolarPunk unified AI brain
==========================================
Priority: ANTHROPIC (Claude sonnet-4-6) → HF fallback (confirmed live models)
Dead models purged: Llama-3.1-8B, Phi-3.5-mini (both 410 Gone as of 2026-03)
All engines import: ask(), ask_json(), ask_json_list(), ai_available(), ai_backend()
"""
import os, json, requests

ANTHROPIC_KEY   = os.environ.get("ANTHROPIC_API_KEY", "")
HF_TOKEN        = os.environ.get("HF_TOKEN", "")
ANTHROPIC_MODEL = "claude-sonnet-4-6"

# Only confirmed-working HF models (no 410s) — updated 2026-03
HF_MODELS = [
    "Qwen/Qwen2.5-72B-Instruct",
    "mistralai/Mistral-7B-Instruct-v0.3",
    "HuggingFaceH4/zephyr-7b-beta",
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
            print(f"  [AI] Anthropic error ({e}), trying HF fallback...")
    if HF_TOKEN:
        return _ask_hf(messages, max_tokens=max_tokens, system=system)
    raise RuntimeError("No AI backend — set ANTHROPIC_API_KEY or HF_TOKEN")


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
    return bool(ANTHROPIC_KEY or HF_TOKEN)


def ai_backend():
    if ANTHROPIC_KEY:
        return "anthropic"
    if HF_TOKEN:
        return "huggingface"
    return "none"


if __name__ == "__main__":
    print(f"AI_CLIENT — backend: {ai_backend()}")
    r = ask([{"role": "user", "content": "Say exactly: SolarPunk AI online."}], max_tokens=20)
    print(f"Test: {r}")
