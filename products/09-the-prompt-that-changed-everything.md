# The Prompt That Changed Everything
### The prompting techniques that actually work. Tested across real projects.

**Price: $1 — 70% goes to PCRF (children's aid in Gaza)**

---

## The Actual Mechanic

Language models predict the most likely next token given everything before it. Your prompt is evidence about what kind of document this is. The model completes it.

- Vague prompts → vague completions
- Expert-sounding prompts → expert completions
- Specific format → specific output

---

## The Five Moves That Work

**1. Prime the context** — Start the document you want, don't ask for it.

❌ "Write a cover letter"
✅ "Cover Letter — Software Engineer at [Company]\n\nDear Hiring Manager,\n\nI am writing to..."

**2. Specify the anti-pattern** — Tell it what NOT to do.

✅ "Do not use 'In conclusion', 'It's important to note', or 'As an AI'. Be direct."

**3. Role with stakes** — Not just "you are an expert." Give it a reason to be rigorous.

✅ "You are a senior engineer doing code review. If this ships with bugs, users are affected. Be honest, not polite."

**4. Show the output format** — Don't describe it, show it.

✅ "Format every response as:\n**Finding:** [one sentence]\n**Evidence:** [specific example]\n**Action:** [specific next step]"

**5. Verification prompt** — After getting an answer: "What are the top 3 ways this could be wrong or incomplete?"

---

## The System Prompt Is Everything

```
You are [ROLE].
Your task is [SPECIFIC TASK].
The user is [CONTEXT].
Always [STANDING INSTRUCTION].
Never [STANDING RULE].
Format every response as [FORMAT].
```

Time spent on system prompts pays back 100x vs individual prompts.

---

## The Prompts That Changed Real Projects

**Write like me:** *"Here are 3 examples of how I write: [paste]. Now write [new thing] in the same voice. Match my sentence length, directness, and [specific habit]."*

**Debug code:** *"This should [behavior] but instead [actual behavior]. Code: [paste]. Before fixing, explain what you think is happening and why."*

**Hard decisions:** *"Argue for Option A as strongly as possible. Then argue for Option B as strongly as possible. Then give your actual recommendation."*

**Research synthesis:** *"After reading these documents, identify: what they agree on, what they contradict, what question they all leave unanswered."*

---

## When Prompting Doesn't Help

- Model doesn't have the knowledge → provide it or use a better model
- Real-time information needed → use search/tools
- Document too long → chunk it
- Fundamentally wrong training → can't prompt around it

Knowing the limits is as useful as knowing the techniques.

---

*Built by Meeko Mycelium · github.com/meekotharaccoon-cell*
*70% of every sale → PCRF · pcrf.net*
