#!/usr/bin/env python3
"""GRANT_HUNTER - Finds grants SolarPunk can apply for
Scores 20 grant sources by match. Claude researches top 5.
Outputs grants_found.json -> GRANT_APPLICANT actions them.
"""
import os,json,requests
from pathlib import Path
from datetime import datetime,timezone

DATA=Path("data"); DATA.mkdir(exist_ok=True)
API=os.environ.get("ANTHROPIC_API_KEY","")

GRANTS=[
    {"name":"Mozilla Foundation","url":"https://foundation.mozilla.org/en/what-we-fund/","tags":["open source","internet health","AI"]},
    {"name":"Open Technology Fund","url":"https://www.opentech.fund/funds/","tags":["internet freedom","open source","human rights"]},
    {"name":"Knight Foundation","url":"https://knightfoundation.org/grants/","tags":["journalism","information","community"]},
    {"name":"Shuttleworth Foundation","url":"https://www.shuttleworthfoundation.org/fellows/","tags":["open source","social change","tech"]},
    {"name":"Ford Foundation","url":"https://www.fordfoundation.org/work/our-grants/","tags":["social justice","technology","equity"]},
    {"name":"NLnet Foundation","url":"https://nlnet.nl/propose/","tags":["open source","internet","privacy"]},
    {"name":"Prototype Fund","url":"https://prototypefund.de/en/","tags":["open source","civic tech","social good"]},
    {"name":"Gitcoin Grants","url":"https://grants.gitcoin.co","tags":["web3","open source","public goods"]},
    {"name":"Awesome Foundation","url":"https://www.awesomefoundation.org","tags":["community","art","$1000","monthly"]},
    {"name":"Arab Fund for Arts","url":"https://www.afac.com.lb","tags":["Arab","arts","culture","Palestine"]},
    {"name":"Art for Justice Fund","url":"https://artforjusticefund.org","tags":["social justice","art","advocacy"]},
    {"name":"Rhizome","url":"https://rhizome.org","tags":["digital art","net art","AI art"]},
    {"name":"Tech for Good","url":"https://www.techforgood.global/","tags":["humanitarian tech","social good","AI"]},
    {"name":"GitHub Fund","url":"https://resources.github.com/github-fund/","tags":["open source","developer","GitHub"]},
    {"name":"Wikimedia Foundation","url":"https://meta.wikimedia.org/wiki/Grants","tags":["open knowledge","free culture"]},
    {"name":"Creative Commons","url":"https://creativecommons.org/about/program-areas/arts-culture/","tags":["creative commons","art","open culture"]},
    {"name":"Experiment.com","url":"https://experiment.com","tags":["crowdfunded research","community"]},
    {"name":"Open Collective","url":"https://opencollective.com/grants","tags":["open source","community","tools"]},
    {"name":"Palestine Festival of Literature","url":"https://www.palfest.org/","tags":["Palestine","culture","arts","Arabic"]},
    {"name":"Sundance Institute","url":"https://www.sundance.org/programs/","tags":["storytelling","social impact","documentary"]},
]

PROFILE_TAGS={"open source","AI","humanitarian","Gaza","Palestine","art","community","social good","tech","generative art"}

def score(g):
    s=len(PROFILE_TAGS & set(g.get("tags",[])))*15
    text=(g.get("name","")+" ".join(g.get("tags",[]))).lower()
    for w in ["open source","humanitarian","gaza","palestine","art","ai","social good","community","$1000"]:
        if w in text: s+=8
    return min(s,100)

def research(g):
    if not API: return g
    prompt=f"""Research this grant for SolarPunk - open-source AI system funding Palestinian artists ($1 art, 70% to Gaza Rose).
GRANT: {g['name']} | URL: {g['url']} | TAGS: {g['tags']}
Respond ONLY JSON: {{"eligibility":"likely/unlikely/maybe","amount_range":"$X-Y","deadline":"date or rolling","application_type":"email/form/online","application_email":"email or null","application_url":"apply URL or null","pitch":"2-sentence pitch","priority":"high/medium/low","key_requirements":["req1","req2"]}}"""
    try:
        r=requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key":API,"Content-Type":"application/json","anthropic-version":"2023-06-01"},
            json={"model":"claude-sonnet-4-20250514","max_tokens":400,"messages":[{"role":"user","content":prompt}]},timeout=25)
        t=r.json()["content"][0]["text"]; s2,e=t.find("{"),t.rfind("}")+1
        g.update(json.loads(t[s2:e]))
    except Exception as ex: g["research_error"]=str(ex)
    return g

def run():
    sf=DATA/"grant_hunter_state.json"
    state=json.loads(sf.read_text()) if sf.exists() else {"cycles":0}
    state["cycles"]=state.get("cycles",0)+1; state["last_run"]=datetime.now(timezone.utc).isoformat()
    print(f"GRANT_HUNTER cycle {state['cycles']}")
    grants=[dict(g,match_score=score(g)) for g in GRANTS]
    grants.sort(key=lambda x:x["match_score"],reverse=True)
    print(f"  Top matches: {', '.join(g['name'] for g in grants[:5])}")
    if API:
        for g in grants[:5]:
            if not g.get("researched"):
                research(g); g["researched"]=True
                print(f"  Researched: {g['name']} -> priority:{g.get('priority','?')}")
    (DATA/"grants_found.json").write_text(json.dumps(grants,indent=2))
    state["grants_scored"]=len(grants)
    state["high_priority"]=[g["name"] for g in grants if g.get("priority")=="high"]
    sf.write_text(json.dumps(state,indent=2))
    print(f"  {len(grants)} grants scored | {len(state['high_priority'])} high priority")
    return state

if __name__=="__main__": run()
