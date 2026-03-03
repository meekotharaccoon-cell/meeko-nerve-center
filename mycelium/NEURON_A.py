import os, json, requests
from pathlib import Path
from datetime import datetime, timezone

class NeuronA:
    def __init__(self):
        self.api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        self.data_dir = Path("data")
        self.mycelium = Path("mycelium")
        self.data_dir.mkdir(exist_ok=True)

    def gather_context(self):
        engines = sorted([f.name for f in self.mycelium.glob("*.py")])
        flywheel = {}
        ff = self.data_dir / "flywheel_state.json"
        if ff.exists():
            try: flywheel = json.loads(ff.read_text())
            except: pass
        queue_remaining = 0
        bqf = self.data_dir / "BUILD_QUEUE.json"
        if bqf.exists():
            try: queue_remaining = len(json.loads(bqf.read_text()).get("queue", []))
            except: pass
        return {"engines": engines, "engine_count": len(engines),
                "revenue": flywheel.get("current_balance", 0),
                "queue_remaining": queue_remaining}

    def think(self, ctx):
        if not self.api_key:
            return {
                "proposals": [
                    f"Trigger OMNIBRAIN — builds 1 engine from {ctx['queue_remaining']}-item queue",
                    "Add Etsy API key to GitHub Secrets to activate Gaza Rose Gallery tracking",
                    "Create first Gumroad digital product for passive income"
                ],
                "system_assessment": f"{ctx['engine_count']} engines, ${ctx['revenue']:.2f} revenue, {ctx['queue_remaining']} queued.",
                "confidence": 70
            }
        prompt = f"""You are NEURON_A — Builder Brain of SolarPunk, Meeko's autonomous income agent.
Gaza Rose Gallery = Palestinian art. 70% revenue to PCRF. Goal: 100% passive income.
CURRENT: {ctx['engine_count']} engines, ${ctx['revenue']:.2f} revenue, {ctx['queue_remaining']} engines queued to build.
Propose 3 concrete actions to grow income RIGHT NOW.
JSON only: {{"proposals": ["1","2","3"], "system_assessment": "one sentence", "confidence": <50-100>}}"""
        try:
            r = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": self.api_key, "Content-Type": "application/json", "anthropic-version": "2023-06-01"},
                json={"model": "claude-sonnet-4-20250514", "max_tokens": 600, "messages": [{"role": "user", "content": prompt}]},
                timeout=60
            )
            r.raise_for_status()
            text = r.json()["content"][0]["text"]
            s, e = text.find("{"), text.rfind("}") + 1
            return json.loads(text[s:e])
        except Exception as ex:
            return {"proposals": [f"API error: {ex}"], "system_assessment": "degraded", "confidence": 0}

    def run(self):
        print(f"\n🔵 NEURON_A (Builder) — {datetime.now().isoformat()}")
        ctx = self.gather_context()
        result = self.think(ctx)
        result["timestamp"] = datetime.now(timezone.utc).isoformat()
        result["context"] = ctx
        (self.data_dir / "neuron_a_output.json").write_text(json.dumps(result, indent=2))
        print(f"Proposals ({result.get('confidence', 0)}% confidence):")
        for p in result.get("proposals", []):
            print(f"  + {p}")
        return result

if __name__ == "__main__":
    NeuronA().run()
