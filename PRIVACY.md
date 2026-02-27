# Privacy Policy — Meeko Nerve Center

> Short version: We collect nothing. We store nothing about you. Your data serves its one purpose and is gone.

## What We Collect

**Nothing personally identifiable.**

When you scan a QR code:
- We do not log your IP address
- We do not log your device type or browser
- We do not set tracking cookies
- We do not use analytics that identify individuals
- The URL parameter (`?src=`) tells us which physical object you scanned — not who you are

When you make a choice (Yes/No on the consent page):
- Your choice is honored immediately
- No record of your decision is stored anywhere
- Session data is scrubbed from your browser by the page itself

## What Happens to Data

All data the system collects from APIs (earthquake data, crypto prices, job listings, etc.) is:
- Used to generate content or intelligence
- Kept only as long as it serves a purpose
- Subject to automatic rolling scrubbing (`privacy_scrubber.py` runs daily)
- Never sold, shared, or passed through third parties beyond the API source

## The Scrubber

`mycelium/privacy_scrubber.py` runs every night and:
- Deletes session and consent logs immediately after use
- Removes sensitive key patterns (IP addresses, emails, etc.) from any data files
- Age-scrubs API data beyond its useful life
- Logs the FACT of scrubbing (not the data) to `data/scrub_log.json`

## QR Codes

The QR codes embedded in physical objects point to `consent.html`.
This page:
- Explains exactly what will happen if you say yes
- Requires your explicit consent before doing anything
- Accepts a 'No' with equal dignity: "Yeah, no problem! Thanks for being YOU."
- Scrubs all session data from your browser after either choice

## The Philosophy

Data should pass through the minimum number of hands necessary.
After it serves its final purpose: it should not exist anymore.
This is not a legal compliance document. This is how we actually build.

---
*AGPL-3.0 | Meeko Nerve Center | Open source, open ethics*
