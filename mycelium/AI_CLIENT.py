#!/usr/bin/env python3
"""
AI_CLIENT.py — SolarPunk AI brain, free tier
=============================================
Drop-in replacement for Anthropic API.
Uses HuggingFace Inference API (free, uses HF_TOKEN already in secrets).
All engines import this instead of calling Anthropic directly.
"""
import os, requests

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
            print(f"  [AI_CLIENT] {model.split('/')[-1]} responded ({len(text)} chars)")
            return text
        except Exception as e:
            print(f"  [AI_CLIENT] {model.split('/')[-1]} failed: {e}")
            last_error = e
            continue

    raise RuntimeError(f"All AI models failed. Last error: {last_error}")


def ask_json(prompt, max_tokens=2000, system=None):
    """
    Ask for JSON response. Returns parsed dict or None.
    """
    import json
    json_system = (system or "") + "\nRespond ONLY with valid JSON. No markdown fences, no preamble."
    text = ask([{"role": "user", "content": prompt}], max_tokens=max_tokens, system=json_system.strip())
    try:
        s, e = text.find("{"), text.rfind("}") + 1
        if s >= 0:
            return json.loads(text[s:e])
    except Exception as ex:
        print(f"  [AI_CLIENT] JSON parse failed: {ex}")
    return None


if __name__ == "__main__":
    print("Testing AI_CLIENT...")
    result = ask([{"role": "user", "content": "Say 'SolarPunk is alive' in exactly 5 words."}], max_tokens=20)
    print(f"Result: {result}")
