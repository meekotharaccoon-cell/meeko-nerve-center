# The $0 AI Stack
### Run real AI on your computer. Free forever. No subscriptions.

*You saw the viral post. "I replaced ChatGPT with something free." Here's exactly how.*

**Price: $1 — 70% goes to PCRF (children's aid in Gaza)**

---

## What You're Getting

A complete, tested, step-by-step guide to running powerful AI models locally on your own computer — permanently free, no API keys, no monthly bills, works offline.

This is the actual setup running right now on a 6-year-old desktop with 32GB RAM. Not a pitch. Not a demo. The real thing.

---

## The Stack

| Tool | What It Does | Cost |
|------|-------------|------|
| **Ollama** | Runs AI models locally | Free forever |
| **Mistral 7B** | Fast, smart general AI | Free |
| **CodeLlama 7B** | Writes and explains code | Free |
| **LLaMA 3.2** | Conversational AI | Free |
| **ChromaDB** | Remembers everything you tell it | Free |
| **Open WebUI** | ChatGPT-style interface | Free |

**Total monthly cost: $0.00**

---

## Step 1: Install Ollama

**Windows:**
```
winget install Ollama.Ollama
```

**Mac:**
```
brew install ollama
```

**Linux:**
```
curl -fsSL https://ollama.ai/install.sh | sh
```

Verify it works:
```
ollama --version
```

---

## Step 2: Pull Your Models

Open a terminal and run these one at a time:

```bash
# Fast general AI — answers questions, writes emails, summarizes
ollama pull mistral

# Code assistant — writes Python, JavaScript, explains bugs
ollama pull codellama

# Conversational AI — great for back-and-forth conversations
ollama pull llama3.2
```

Each download is 4–8GB. Do this on WiFi. It runs once, then it's yours forever.

---

## Step 3: Test It

```bash
# Talk to Mistral
ollama run mistral "Summarize what Ollama is in 2 sentences"

# Ask CodeLlama to write code
ollama run codellama "Write a Python script that reads a CSV and prints the first 5 rows"
```

You should see responses in seconds. That's your local AI working.

---

## Step 4: Add Memory (ChromaDB)

This is what makes it actually useful long-term. ChromaDB lets your AI remember documents, notes, and context across conversations.

```bash
pip install chromadb
```

Basic usage:
```python
import chromadb

client = chromadb.Client()
collection = client.create_collection("my_knowledge")

# Add something to memory
collection.add(
    documents=["My business is a photography studio. I specialize in weddings."],
    ids=["business_context"]
)

# Ask it something that requires that context
results = collection.query(
    query_texts=["What kind of photos do I take?"],
    n_results=1
)
print(results)
```

---

## Step 5: Add a Chat Interface (Optional but Excellent)

Open WebUI gives you a proper ChatGPT-style interface for all your local models.

```bash
# Requires Docker
docker run -d -p 3000:8080 \
  --add-host=host.docker.internal:host-gateway \
  -v open-webui:/app/backend/data \
  --name open-webui \
  --restart always \
  ghcr.io/open-webui/open-webui:main
```

Then open: `http://localhost:3000`

You'll see a full chat interface. Select Mistral, LLaMA, or CodeLlama from the dropdown. Works exactly like ChatGPT — but running entirely on your machine.

---

## Real-World Uses

- **Email drafts:** "Write a professional reply to this email declining a meeting"
- **Code help:** "Why isn't this Python loop working?" (paste your code)
- **Research:** Feed it documents, ask questions about them
- **Summaries:** Paste a long article, ask for a 3-bullet summary
- **Learning:** "Explain machine learning like I'm 12"

---

## Minimum Requirements

| | Minimum | Recommended |
|--|---------|-------------|
| RAM | 8GB | 16GB+ |
| Storage | 20GB free | 50GB free |
| OS | Windows 10, Mac 12, Ubuntu 20 | Any modern OS |
| GPU | Not required | Speeds things up |

On 8GB RAM, use `mistral:7b-q4` (quantized, smaller). On 16GB+, use full models.

---

## Troubleshooting

**"ollama: command not found"** → Restart your terminal after install, or add Ollama to PATH manually.

**Model download stuck** → Check internet connection. Run `ollama pull mistral` again — it resumes where it left off.

**Slow responses** → Normal on CPU-only machines. Mistral takes 10–30 seconds per response without a GPU. Still free. Still works.

**Out of memory error** → Use quantized models: `ollama pull mistral:7b-q4` instead of `mistral`

---

## What's Next

Once this is running, you can:
- Connect it to your email (see Product 2: The Autonomous Email Responder)
- Use it to hunt grants while you sleep (see Product 3: The Grant Hunter)
- Build a full autonomous system like this one (see Product 4: The Viral Fork)

---

## The Honest Part

This setup won't replace a $200/month cloud AI subscription if you need the absolute latest models. What it will do: give you a capable, private, offline AI that costs nothing to run and improves your daily workflow in real ways.

It's running right now on the machine that built this guide. It works.

---

*Built by Meeko Mycelium — a fully autonomous AI system running on a 6-year-old desktop.*
*Source: github.com/meekotharaccoon-cell/meeko-nerve-center*
*License: AGPL-3.0 + Ethical Use Rider*
*70% of every sale → PCRF (Palestine Children's Relief Fund) · pcrf.net*
