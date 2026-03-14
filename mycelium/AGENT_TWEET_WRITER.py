# NEURAL_LINK: The
# Part of the Meeko SolarPunk Swarm.

#!/usr/bin/env python3
"""
AGENT_TWEET_WRITER.py — Nano-agent that generates tweet drafts
==============================================================
Runs every cycle. Generates new tweet threads about SolarPunk
and appends them to data/tweets_queue.txt for Meeko to post.

No API needed for templated tweets. Uses Claude for fresh content
if key is available.
"""
import sys, os
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from NANO_AGENT import NanoAgent, DATA
import json, random
from datetime import datetime, timezone

TEMPLATES = [
    # (topic, tweet1, tweet2, tweet3, tweet4)
    (
        "system-fact",
        "SolarPunk has now run {cycles} autonomous cycles without human intervention.\n\nEach cycle: 76 engines, 8 layers, ~55 minutes of execution.\n\nTotal uptime: {uptime_days} days.",
        "In those {cycles} cycles it has:\n→ Sent {emails_out} outreach emails\n→ Built {businesses} product pages\n→ Self-healed {heals} times\n→ Written new engines: {engines_built}",
        "Current health score: {health}/100\n\nThe gap between 40 and 100 is one missing API key.\n\nEverything else is already running.",
        "All of this runs on free GitHub infrastructure.\n\nThe only cost: ~$5-20/month in API credits when the key is connected.\n\ngithub.com/meekotharaccoon-cell/meeko-nerve-center"
    ),
    (
        "architecture",
        "People ask how an AI system can run itself forever.\n\nHere's the actual answer: it can't.\n\nBut it can detect every failure mode and either fix it or skip it gracefully.\n\nThat's close enough.",
        "SolarPunk's 8 execution layers:\n\nL0: Check + heal itself\nL1: Gather intel (email, news, AI models)\nL2: Revenue planning\nL3: Deploy content\nL4: Distribute + publish\nL5: Collect + pay out\nL6: Think + expand\nL7: Report + prove",
        "The key insight: every layer is a set of Python scripts.\n\nEvery script either succeeds, fails gracefully, or times out.\n\nThe system knows the difference. It logs everything. It patches what it can.",
        "You can read every line of this architecture.\n\nAll 76 engines. All 8 workflows. Every data file.\n\nMIT licensed. Fork it if you want your own.\n\ngithub.com/meekotharaccoon-cell/meeko-nerve-center"
    ),
]

class AGENT_TWEET_WRITER(NanoAgent):
    def run(self):
        # Load current system state for dynamic content
        brain  = self.load_data("brain_state.json", {})
        omnibus = self.load_data("omnibus_last.json", {})
        cycle_mem = self.load_data("cycle_delta.json", {})
        outreach = self.load_data("outreach_state.json", {"sent": []})

        stats = {
            "cycles":    cycle_mem.get("cycle_number", 0),
            "health":    brain.get("health_score", 40),
            "uptime_days": round(cycle_mem.get("cycle_number", 0) * 0.25, 1),  # 4x/day
            "emails_out": len([e for e in outreach.get("sent", []) if e.get("sent")]),
            "businesses": len(list((DATA.parent / "data").glob("business_*.json"))) if (DATA.parent / "data").exists() else 0,
            "heals":     0,
            "engines_built": len(omnibus.get("engines_auto_built", [])),
        }

        new_tweets = []
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Use Claude if available for fresh content
        if os.environ.get("ANTHROPIC_API_KEY"):
            context = f"""SolarPunk stats: cycles={stats['cycles']}, health={stats['health']}/100, emails={stats['emails_out']}, engines_built={stats['engines_built']}
Today's date: {ts}"""
            prompt = f"""Write a 4-tweet Twitter thread about the SolarPunk autonomous AI system. 
Context: {context}

Rules:
- Facts only, no hype
- No selling, just what the system does
- Only link allowed: github.com/meekotharaccoon-cell/meeko-nerve-center
- Each tweet under 280 characters
- Format as: [Tweet 1/4]\\n...\\n\\n[Tweet 2/4]\\n... etc

Topic: Pick one of: self-healing, email processing, Gaza fund routing, or autonomous code writing."""
            result = self.ask_claude(prompt, max_tokens=1024)
            if result:
                new_tweets.append(f"\n\n{'='*40}\nAI-GENERATED THREAD — {ts}\n{'='*40}\n{result}")

        # Always add a templated thread using real stats
        tmpl = random.choice(TEMPLATES)
        topic, t1, t2, t3, t4 = tmpl
        thread = f"\n\n{'='*40}\nTHREAD — {topic.upper()} — {ts}\n{'='*40}\n"
        for i, tweet_text in enumerate([t1, t2, t3, t4], 1):
            try:
                formatted = tweet_text.format(**stats)
            except:
                formatted = tweet_text
            thread += f"\n[Tweet {i}/4]\n{formatted}\n"
        new_tweets.append(thread)

        # Append to queue file
        queue_file = DATA / "tweets_queue.txt"
        existing = queue_file.read_text() if queue_file.exists() else ""
        queue_file.write_text(existing + "\n".join(new_tweets))
        self._log(f"Added {len(new_tweets)} tweet blocks to queue")

        return {
            "status": "ok",
            "summary": f"Added {len(new_tweets)} tweet thread(s) to tweets_queue.txt",
            "tweet_blocks_added": len(new_tweets),
            "queue_size_bytes": queue_file.stat().st_size,
        }

if __name__ == "__main__":
    AGENT_TWEET_WRITER("AGENT_TWEET_WRITER").execute()
