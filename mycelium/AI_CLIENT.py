#!/usr/bin/env python3
"""
AI_CLIENT.py — SolarPunk AI brain, free tier
=============================================
Drop-in replacement for Anthropic API.
Uses HuggingFace Inference API (free, uses HF_TOKEN already in secrets).
All engines import this instead of calling Anthropic directly.

ask()        — returns text string
ask_json()   — returns parsed dict (handles {...} objects)
ask_json_list() — returns parsed list (handles [...] arrays)
"""
import os, json, requests

HF_TOKEN = os.environ.get("HF_TOKEN", "")

# Free serverless models, tried in order
MODELS = [
    "Qwen/Qwen2.5-72B-Instruct",
    "mistralai/Mixtral-8x7B-Instruct-v0.1",
    "mistralai/Mistral-7B-Instruct-v0.3",
]


def ask(messages, max_tokens=2000, system=None):
    """
    Ask the AI. Returns text string.
    messages: list of {"role": "user"|"assistant", "content": "..."}
    system: optional system prompt string
    """
    if not HF_TOKEN:
        raise ValueError("HF_TOKEN not set in GitHub Secrets")

    full_messages = []
    if system:
        full_messages.append({"role": "system", "content": system})
    full_messages.extend(messages)

    last_error = None
    for model in MODELS:
        try:
            url = f"https://api-inference.huggingface.co/models/{model}/v1/chat/completions"
            r = requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {HF_TOKEN}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": full_messages,
                    "max_tokens": max_tokens,
                    "temperature": 0.7,
                },
                timeout=120
            )
            r.raise_for_status()
            text = r.json()["choices"][0]["message"]["content"]
            print(f"  [AI] {model.split('/')[-1]} ({len(text)}c)")
            return text
        except Exception as e:
            print(f"  [AI] {model.split('/')[-1]} failed: {e}")
            last_error = e
            continue

    raise RuntimeError(f"All AI models failed. Last: {last_error}")


def ask_json(prompt, max_tokens=2000, system=None):
    """
    Ask for a JSON object response. Returns parsed dict or None.
    Handles both raw JSON and markdown-fenced JSON.
    """
    sys_suffix = "\nRespond ONLY with a valid JSON object. No markdown fences, no preamble, no explanation."
    full_system = ((system or "") + sys_suffix).strip()
    try:
        text = ask([{"role": "user", "content": prompt}], max_tokens=max_tokens, system=full_system)
        # Strip markdown fences
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```", 2)[-1] if text.count("```") >= 2 else text
            text = text.lstrip("json").strip()
        s, e = text.find("{"), text.rfind("}") + 1
        if s >= 0:
            return json.loads(text[s:e])
    except Exception as ex:
        print(f"  [AI] ask_json parse failed: {ex}")
    return None


def ask_json_list(prompt, max_tokens=2000, system=None):
    """
    Ask for a JSON array response. Returns parsed list or [].
    Use this when you expect [...] not {...}.
    """
    sys_suffix = "\nRespond ONLY with a valid JSON array. No markdown fences, no preamble, no explanation."
    full_system = ((system or "") + sys_suffix).strip()
    try:
        text = ask([{"role": "user", "content": prompt}], max_tokens=max_tokens, system=full_system)
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]) if len(lines) > 2 else text
        s, e = text.find("["), text.rfind("]") + 1
        if s >= 0:
            return json.loads(text[s:e])
    except Exception as ex:
        print(f"  [AI] ask_json_list parse failed: {ex}")
    return []


if __name__ == "__main__":
    print("Testing AI_CLIENT...")
    result = ask([{"role": "user", "content": "Say 'SolarPunk is alive' in exactly 5 words."}], max_tokens=20)
    print(f"Result: {result}")
