# The Prompt That Changed Everything
### The prompting techniques that actually work. Tested on 18 months of real projects.

*Not "10 ChatGPT prompts for productivity." The actual mechanics of how prompting works.*

**Price: $1 — 70% goes to PCRF (children's aid in Gaza)**

---

## What You're Getting

A practical guide to prompt engineering that actually changes results — not a list of tricks, but an understanding of how language models process instructions, and how to use that to get dramatically better outputs.

---

## The Thing Most Guides Get Wrong

Most prompt guides treat prompting like keyword stuffing. "Add 'think step by step' and it gets smarter." That works sometimes, but it's not why it works, so you can't generalize it.

Here's the actual mechanic: **language models predict the most likely next token given everything that came before it**. Your prompt is evidence about what kind of document this is. The model completes it.

This means:
- Vague prompts → vague completions (what does a vague document look like?)
- Expert-sounding prompts → expert-sounding completions (the model completes like an expert would)
- Specific format requests → specific formats (you told it what the document looks like)

---

## The Five Moves That Actually Work

### Move 1: Prime the context

Instead of asking a question, start the document you want.

❌ Bad: *"Write a cover letter for a software engineer job."*
✅ Good: *"Cover Letter — Software Engineering Position at [Company]\n\nDear Hiring Manager,\n\nI am writing to express my strong interest in..."* then let it continue.

You've told it: this is a professional letter, already started, follow the pattern.

### Move 2: Specify the anti-pattern

Tell it what NOT to do. Language models default to the average of everything they've seen — which is often mediocre.

✅ Good addition: *"Do not use filler phrases like 'In conclusion', 'It's important to note', or 'As an AI'. Do not hedge every statement. Be direct."*

### Move 3: Give it a role with stakes

Not just "you are an expert" — give it a reason to be rigorous.

❌ Bad: *"You are a helpful assistant."*
✅ Good: *"You are a senior engineer doing a code review. If this code ships with bugs, users are affected. Be thorough and honest, not polite."*

### Move 4: Constrain the output format

If you want a specific format, show it.

✅ Good: *"Respond only in this format:\n**Finding:** [one sentence]\n**Evidence:** [specific example]\n**Recommendation:** [specific action]"*

### Move 5: The verification prompt

After getting an answer, ask: *"What are the top 3 ways this answer could be wrong or incomplete?"*

This forces the model to surface its own uncertainty. It's more reliable than asking it to check its work in the same response.

---

## The System Prompt Is Everything

If you're using the API or building with Ollama, the system prompt shapes every response. Use it to encode:

```
You are [ROLE].
Your task is [SPECIFIC TASK].
The person you're helping is [CONTEXT ABOUT USER].
Always [STANDING INSTRUCTION 1].
Never [STANDING RULE 1].
Format every response as [FORMAT].
```

Time spent on system prompts pays off 100x over individual prompts.

---

## The Prompts That Changed Real Projects

**For writing that sounds like you:**
*"Here are three examples of how I write: [paste 3 emails or posts]. Now write [new thing] in the same voice. Match my sentence length, my level of directness, and my tendency to [specific habit from examples]."*

**For code debugging:**
*"This code should [intended behavior] but instead it [actual behavior]. Here is the code: [paste]. Before suggesting fixes, explain in one sentence what you think is happening and why."*

**For hard decisions:**
*"I'm deciding between [Option A] and [Option B]. I care most about [Value 1] and [Value 2]. Argue for Option A as strongly as possible. Then argue for Option B as strongly as possible. Then give your actual recommendation and why."*

**For research synthesis:**
*"I'm going to paste several documents. After reading them all, identify: (1) what they agree on, (2) what they contradict, (3) what question they all leave unanswered. Documents: [paste]"*

---

## When Prompting Doesn't Help

Prompting cannot fix:
- A model that doesn't have relevant knowledge (use a better model or provide the information)
- Fundamentally incorrect beliefs baked into training
- Tasks requiring real-time or personal information the model doesn't have
- Long documents that exceed the context window

Knowing the limits is as useful as knowing the techniques.

---

*Built by Meeko Mycelium · github.com/meekotharaccoon-cell*
*70% of every sale → PCRF · pcrf.net*
