# Reddit: r/opensource

**Title:**
AGPL-3.0 autonomous humanitarian AI system — values-gated, self-archiving, forkable in one afternoon

**Body:**
Sharing this here because the licensing approach might be interesting to this community.

The system uses AGPL-3.0 + a custom Ethical Use Rider that prohibits:
- Surveillance or tracking of individuals without consent
- Weapons development
- Labor exploitation
- Use by authoritarian governments
- Closing the source

The interesting part: AGPL means any fork that's networked must also be open source. The Ethical Use Rider propagates through forks — you can't take this, close it, and deploy it as a surveillance tool. The license prevents that legally.

The system itself:
- 21 GitHub repos, all public
- 10 automated daily workflows
- Full documentation including START_HERE.md for strangers
- FORK_REGISTRY.md to track forks in the wild
- Brain file that gates every automated action against stated values

Monthly cost to run: $0 (GitHub free tier)
Hardware: standard desktop, no GPU

Full source: https://github.com/meekotharaccoon-cell/meeko-nerve-center

The question I'm genuinely curious about for this community: does the Ethical Use Rider make this no longer "open source" by OSI definition? (It does — OSI requires no restrictions on use.) Does that matter? The code is public, forkable, modifiable. The restriction is on harm.
