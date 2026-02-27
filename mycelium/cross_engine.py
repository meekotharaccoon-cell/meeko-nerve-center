#!/usr/bin/env python3
"""
Cross Engine
=============
Where the system stops being a collection of tools
and starts thinking in connections.

Each function combines two or more existing data streams
into something new that none of them could make alone.

Connections built:
  1. Congressional trade -> Gaza Rose art
  2. Donation -> personal FLUX artwork for donor
  3. Earthquake near conflict zone -> solidarity content
  4. Crypto spike -> donation context post
  5. Idea passes -> auto grant scan + draft
  6. Book + music + word + visual -> full culture post
  7. Live world data -> video script
  8. Fork detected -> welcome + QR + announcement

Runs after all individual engines have populated their data.
"""

import json, datetime, os, time
from pathlib import Path
from urllib import request as urllib_request

ROOT    = Path(__file__).parent.parent
DATA    = ROOT / 'data'
KB      = ROOT / 'knowledge'
CONTENT = ROOT / 'content' / 'queue'
PUBLIC  = ROOT / 'public'

CONTENT.mkdir(parents=True, exist_ok=True)

TODAY = datetime.date.today().isoformat()
NOW   = datetime.datetime.utcnow().isoformat()

HF_TOKEN        = os.environ.get('HF_TOKEN', '')
GMAIL_ADDRESS   = os.environ.get('GMAIL_ADDRESS', '')
GMAIL_APP_PASSWORD = os.environ.get('GMAIL_APP_PASSWORD', '')
GITHUB_TOKEN    = os.environ.get('GITHUB_TOKEN', '')

# ── Shared utilities ──────────────────────────────────────────────────────────────

def fetch_json(url, headers=None, timeout=15):
    try:
        h = {'User-Agent': 'meeko-cross-engine/1.0'}
        if headers: h.update(headers)
        req = urllib_request.Request(url, headers=h)
        with urllib_request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read())
    except Exception as e:
        return None

def ask_llm(prompt, system='You are a humanitarian content writer. Be direct, human, powerful. Never preachy.', max_tokens=300):
    if not HF_TOKEN: return None
    try:
        payload = json.dumps({
            'model':      'meta-llama/Llama-3.3-70B-Instruct:fastest',
            'max_tokens': max_tokens,
            'messages':   [{'role': 'system', 'content': system}, {'role': 'user', 'content': prompt}]
        }).encode()
        req = urllib_request.Request(
            'https://router.huggingface.co/v1/chat/completions',
            data=payload,
            headers={'Authorization': f'Bearer {HF_TOKEN}', 'Content-Type': 'application/json'}
        )
        with urllib_request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read())
            return data['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f'[cross] LLM error: {e}')
        return None

def generate_flux_image(prompt, filename):
    if not HF_TOKEN: return None
    try:
        payload = json.dumps({'inputs': prompt}).encode()
        req = urllib_request.Request(
            'https://router.huggingface.co/v1/chat/completions',
            data=json.dumps({'model': 'black-forest-labs/FLUX.1-schnell', 'inputs': prompt}).encode(),
            headers={'Authorization': f'Bearer {HF_TOKEN}', 'Content-Type': 'application/json'}
        )
        # Use image generation endpoint directly
        img_req = urllib_request.Request(
            'https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell',
            data=payload,
            headers={'Authorization': f'Bearer {HF_TOKEN}', 'Content-Type': 'application/json'}
        )
        with urllib_request.urlopen(img_req, timeout=60) as r:
            img_bytes = r.read()
            if len(img_bytes) > 1000:
                out = PUBLIC / 'images' / filename
                out.parent.mkdir(exist_ok=True)
                out.write_bytes(img_bytes)
                print(f'[cross] Image saved: {filename}')
                return str(out)
    except Exception as e:
        print(f'[cross] FLUX error: {e}')
    return None

def queue_post(text, platform='all', post_type='cross', extra=None):
    post = {'platform': platform, 'type': post_type, 'text': text, 'date': TODAY}
    if extra: post.update(extra)
    ts = str(int(time.time()))
    out = CONTENT / f'cross_{post_type}_{ts}.json'
    out.write_text(json.dumps([post], indent=2))
    return out

def send_email(to, subject, body):
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD: return False
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From']    = f'Meeko <{GMAIL_ADDRESS}>'
        msg['To']      = to
        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.ehlo(); s.starttls()
            s.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
            s.sendmail(GMAIL_ADDRESS, to, msg.as_string())
        print(f'[cross] Email sent to {to}')
        return True
    except Exception as e:
        print(f'[cross] Email failed: {e}')
        return False

# ── CONNECTION 1: Congressional trade → Gaza Rose art ─────────────────────────────

def congress_to_art():
    """
    When a Congressional stock trade is flagged,
    generate a Gaza Rose image and post about that specific trade.
    Art as accountability. Accountability as art.
    """
    print('[cross] 1. Congressional trade -> Gaza Rose art')

    congress_path = DATA / 'congress.json'
    if not congress_path.exists():
        print('[cross] No congress.json yet')
        return

    try:
        congress = json.loads(congress_path.read_text())
        flagged  = congress.get('flagged', [])
        if not flagged:
            print('[cross] No flagged trades today')
            return

        trade = flagged[0]  # most recent flagged trade
        rep      = trade.get('representative', 'A representative')
        ticker   = trade.get('ticker', 'an unknown stock')
        amount   = trade.get('amount', 'an undisclosed amount')
        t_type   = trade.get('type', 'traded')
        industry = trade.get('industry', 'defense')

        # AI writes the post
        prompt = f"""{rep} {t_type} {ticker} ({industry}) worth {amount} while in office.

Write a short, powerful social post connecting this Congressional trade to Palestinian suffering.
Mention Gaza Rose art. End with something that gives people agency. Under 280 chars."""

        text = ask_llm(prompt) or f"{rep} {t_type} {ticker} ({amount}) while writing laws.\n\nMeanwhile Gaza Rose art funds Palestinian children.\n\n70% → PCRF. Accountability through art.\n#Congress #GazaRose #Palestine"

        # Generate image: a rose made of the trade data
        img_prompt = f"A red rose growing through a congressional document stamped '{ticker}', solarpunk style, warm defiant light, accountability aesthetic"
        img_path = generate_flux_image(img_prompt, f'congress_rose_{TODAY}.png')

        queue_post(text, post_type='congress_art', extra={'trade': trade, 'image': img_path})
        print(f'[cross] Congress art queued: {rep} / {ticker}')

    except Exception as e:
        print(f'[cross] Congress art error: {e}')

# ── CONNECTION 2: Donation → personal FLUX artwork for donor ─────────────────────

def donation_to_personal_art():
    """
    When someone donates via Ko-fi, generate a unique Gaza Rose
    image just for them and email it as their thank-you.
    Every donor gets a one-of-a-kind piece.
    """
    print('[cross] 2. Donation -> personal artwork')

    kofi_path = DATA / 'kofi_events.json'
    if not kofi_path.exists(): return

    try:
        events = json.loads(kofi_path.read_text()).get('events', [])
        new_donations = [
            e for e in events
            if e.get('date') == TODAY and not e.get('art_sent')
        ]

        for donation in new_donations:
            amount  = donation.get('amount', 0)
            message = donation.get('message', '')
            email   = donation.get('donor_email', '')

            # Personalize the rose based on their message or amount
            if message and message != '[private message]':
                flavor = f'inspired by the words: {message[:50]}'
            elif amount >= 25:
                flavor = 'bold and radiant, for a generous soul'
            elif amount >= 10:
                flavor = 'warm and blooming, full of hope'
            else:
                flavor = 'small but persistent, growing through concrete'

            img_prompt = f'Gaza Rose, {flavor}, solarpunk art, one of a kind, warm golden light, watercolor style'
            img_path = generate_flux_image(img_prompt, f'donor_rose_{TODAY}_{int(time.time())}.png')

            if img_path and email:
                pcrf = round(amount * 0.70, 2)
                body = f"""Your donation just became something permanent.

I made this Gaza Rose for you specifically. It exists because you chose to act.

${amount:.2f} donated → ${pcrf:.2f} to Palestinian children via PCRF.

The image is attached. It\'s yours.

Thanks for being YOU.

Meeko"""
                send_email(email, 'Your Gaza Rose — made for you', body)
                donation['art_sent'] = TODAY

        if new_donations:
            kofi_path.write_text(json.dumps({'events': events}, indent=2))
            print(f'[cross] Personal art sent to {len(new_donations)} donors')

    except Exception as e:
        print(f'[cross] Donation art error: {e}')

# ── CONNECTION 3: Earthquake near conflict zone → solidarity content ───────────────

def earthquake_to_solidarity():
    """
    When world intelligence detects a significant earthquake
    near Gaza, Palestine, Lebanon, or the wider MENA region,
    generate solidarity content immediately.
    """
    print('[cross] 3. Earthquake -> solidarity content')

    world_path = DATA / 'world_state.json'
    if not world_path.exists(): return

    try:
        world = json.loads(world_path.read_text())
        quakes = world.get('earthquakes', [])

        # MENA region bounding box
        MENA_LAT = (20, 42)
        MENA_LON = (25, 65)
        SOLIDARITY_REGIONS = ['gaza', 'palestine', 'west bank', 'lebanon', 'syria', 'jordan', 'egypt', 'iraq']

        significant = []
        for q in quakes:
            mag   = float(q.get('magnitude', 0))
            place = q.get('place', '').lower()
            lat   = float(q.get('lat', 0))
            lon   = float(q.get('lon', 0))

            in_mena    = MENA_LAT[0] <= lat <= MENA_LAT[1] and MENA_LON[0] <= lon <= MENA_LON[1]
            in_region  = any(r in place for r in SOLIDARITY_REGIONS)
            significant_mag = mag >= 4.0

            if significant_mag and (in_mena or in_region):
                significant.append(q)

        if not significant:
            print('[cross] No significant earthquakes in solidarity regions today')
            return

        q = significant[0]
        mag   = q.get('magnitude')
        place = q.get('place', 'the region')
        time_ = q.get('time', TODAY)

        prompt = f"""A magnitude {mag} earthquake just hit {place}.

Write a brief solidarity post. Acknowledge the human reality.
Mention that people in this region already face compounding crises.
End with something concrete people can do (donate to PCRF, share, bear witness).
Under 300 chars."""

        text = ask_llm(prompt) or f"Magnitude {mag} earthquake in {place}.\n\nPeople here already carry so much.\n\nBear witness. Share. If you can give: pcrf.net\n\n#Solidarity #Palestine #GazaRose"

        queue_post(text, post_type='earthquake_solidarity', extra={'earthquake': q})
        print(f'[cross] Solidarity post queued for M{mag} quake in {place}')

    except Exception as e:
        print(f'[cross] Earthquake solidarity error: {e}')

# ── CONNECTION 4: Crypto spike → donation context post ───────────────────────────

def crypto_spike_to_donation():
    """
    When BTC or SOL spikes significantly,
    post: 'If you rode that wave, here's what it could mean for kids in Gaza.'
    """
    print('[cross] 4. Crypto spike -> donation context')

    world_path = DATA / 'world_state.json'
    donate_path = DATA / 'donation_context.json'
    if not world_path.exists(): return

    try:
        world  = json.loads(world_path.read_text())
        crypto = world.get('crypto', [])

        spikes = [c for c in crypto if abs(float(c.get('change_24h', 0))) >= 5.0]
        if not spikes:
            print('[cross] No significant crypto spikes today')
            return

        coin  = spikes[0]
        sym   = coin.get('symbol', 'BTC')
        price = float(coin.get('price', 0))
        chg   = float(coin.get('change_24h', 0))
        direction = 'up' if chg > 0 else 'down'

        # Get ILS context if available
        rates = {}
        if donate_path.exists():
            rates = json.loads(donate_path.read_text()).get('rates', {})
        ils_context = ''
        if rates.get('ILS'):
            ils10 = round(10 * rates['ILS'])
            ils_context = f'$10 = {ils10} shekels today. '

        prompt = f"""{sym} is {direction} {abs(chg):.1f}% today. Price: ${price:,.0f}.

Write a post connecting today's crypto move to what that money could mean for Palestinian children.
{ils_context}
Not guilt. Just perspective. Give people agency at the end. Under 280 chars."""

        text = ask_llm(prompt) or f"{sym} moved {chg:+.1f}% today.\n\n{ils_context}\nIf today was good to you: pcrf.net\n\n70% of Gaza Rose art sales go directly to Palestinian children.\n#Crypto #GazaRose #PCRF"

        queue_post(text, post_type='crypto_context', extra={'coin': coin})
        print(f'[cross] Crypto context post queued: {sym} {chg:+.1f}%')

    except Exception as e:
        print(f'[cross] Crypto spike error: {e}')

# ── CONNECTION 5: Idea passes → auto grant scan + draft ─────────────────────────

def idea_to_grant():
    """
    When a new idea passes viability testing,
    check if it matches any open grant opportunities
    and draft a short application blurb automatically.
    """
    print('[cross] 5. Idea passes -> grant scan')

    ledger_path = DATA / 'idea_ledger.json'
    queue_path  = DATA / 'outreach_queue.json'
    if not ledger_path.exists(): return

    try:
        ledger = json.loads(ledger_path.read_text())
        ideas  = ledger.get('ideas', [])

        # Find ideas that passed today and haven't been grant-scanned
        new_passed = [
            i for i in ideas
            if i.get('status') == 'passed'
            and i.get('date', '') == TODAY
            and not i.get('grant_scanned')
        ]

        if not new_passed:
            print('[cross] No new passing ideas to scan today')
            return

        queue = json.loads(queue_path.read_text()) if queue_path.exists() else {'grants': [], 'press': []}

        for idea in new_passed[:3]:  # max 3 per run
            title = idea.get('title', idea.get('idea', 'New idea'))
            desc  = idea.get('description', title)

            prompt = f"""This idea just passed viability testing in an open-source humanitarian AI system:

"{title}: {desc}"

In 2 sentences, describe why this idea would qualify for a Mozilla Foundation, Tech for Palestine,
or open source humanitarian grant. Be specific about democratic or humanitarian impact."""

            blurb = ask_llm(prompt, max_tokens=150)
            if blurb:
                new_grant = {
                    'id':          f'auto_idea_{TODAY}_{ideas.index(idea)}',
                    'approved':    False,
                    'name':        f'Auto-scanned: {title}',
                    'amount':      'TBD',
                    'what_to_say': blurb,
                    'source_idea': title,
                    'date':        TODAY,
                    'note':        'Auto-generated from idea engine. Review and approve to send.'
                }
                queue['grants'].append(new_grant)
                idea['grant_scanned'] = TODAY
                print(f'[cross] Grant draft created for: {title}')

        ledger_path.write_text(json.dumps(ledger, indent=2))
        queue_path.write_text(json.dumps(queue, indent=2))

    except Exception as e:
        print(f'[cross] Idea grant error: {e}')

# ── CONNECTION 6: Book + music + word + visual → culture post ────────────────────

def culture_weave():
    """
    Pull today's Palestinian book, music find, word of the day,
    and a Picsum visual — weave them into one unified culture post.
    A whole moment from four separate APIs.
    """
    print('[cross] 6. Book + music + word + visual -> culture post')

    try:
        # Gather all four threads
        book = music = word_entry = None

        books_path = DATA / 'books.json'
        if books_path.exists():
            books_data = json.loads(books_path.read_text())
            books = books_data.get('books', books_data.get('results', []))
            if books: book = books[0]

        music_path = DATA / 'music.json'
        if music_path.exists():
            music_data = json.loads(music_path.read_text())
            tracks = music_data.get('tracks', music_data.get('results', []))
            if tracks: music = tracks[0]

        word_path = KB / 'language' / 'word_of_day.json'
        if word_path.exists():
            word_entry = json.loads(word_path.read_text()).get('word', {})

        # Need at least 2 of the 3 to make a culture post
        threads = [x for x in [book, music, word_entry] if x]
        if len(threads) < 2:
            print('[cross] Not enough culture threads today')
            return

        book_title  = book.get('title', '')  if book  else ''
        book_author = book.get('author', '') if book  else ''
        music_title = music.get('title', '') if music else ''
        music_artist = music.get('artist', '') if music else ''
        word        = word_entry.get('word', '') if word_entry else ''
        definition  = word_entry.get('definition', '') if word_entry else ''

        # Picsum visual seed based on today
        day_ord = datetime.date.today().toordinal()
        visual_url = f'https://picsum.photos/seed/culture-{day_ord}/800/600'

        prompt = f"""Weave these four things into one short, powerful social post about Palestinian culture and resistance:

Book: "{book_title}" by {book_author}
Music: "{music_title}" by {music_artist}
Word of the day: {word} — {definition}
Visual: a photograph of earth and nature

The post should feel like a moment, not a list. Under 300 chars. End with #FreePalestine or #GazaRose."""

        text = ask_llm(prompt)
        if not text:
            parts = [p for p in [book_title, music_title, word] if p]
            text = f"Today: {' • '.join(parts)}\n\nCulture as resistance.\n\n#Palestine #FreePalestine #GazaRose"

        queue_post(text, post_type='culture_weave', extra={
            'book':   book_title,
            'music':  music_title,
            'word':   word,
            'visual': visual_url
        })
        print(f'[cross] Culture post woven: {book_title} + {music_title} + {word}')

    except Exception as e:
        print(f'[cross] Culture weave error: {e}')

# ── CONNECTION 7: Live world data → video script ───────────────────────────────

def world_data_to_video_script():
    """
    Pull the most interesting data point from today's world state
    and write a punchy 30-second video script around it.
    News-speed accountability content, automated.
    """
    print('[cross] 7. Live world data -> video script')

    world_path = DATA / 'world_state.json'
    if not world_path.exists(): return

    try:
        world   = json.loads(world_path.read_text())
        crypto  = world.get('crypto', [])
        quakes  = world.get('earthquakes', [])
        carbon  = world.get('carbon_intensity', {})
        congress = json.loads((DATA / 'congress.json').read_text()) if (DATA / 'congress.json').exists() else {}
        flagged = congress.get('flagged', [])

        # Pick most interesting data point
        story = None
        if flagged:
            t = flagged[0]
            story = f"Congressional trade alert: {t.get('representative')} {t.get('type','traded')} {t.get('ticker')} worth {t.get('amount')} while in office."
        elif quakes:
            big = max(quakes, key=lambda q: float(q.get('magnitude', 0)))
            if float(big.get('magnitude', 0)) >= 5.0:
                story = f"Magnitude {big['magnitude']} earthquake in {big.get('place', 'the region')}."
        elif crypto:
            movers = sorted(crypto, key=lambda c: abs(float(c.get('change_24h', 0))), reverse=True)
            if movers and abs(float(movers[0].get('change_24h', 0))) >= 5:
                c = movers[0]
                story = f"{c['symbol']} moved {float(c['change_24h']):+.1f}% today. Price: ${float(c['price']):,.0f}."

        if not story:
            print('[cross] No compelling world data story today')
            return

        prompt = f"""Write a 30-second video script (about 75 words) for a YouTube Short.

Opening data point: {story}

Script should:
1. Open with the data fact (2 sentences)
2. Connect it to human impact or Palestinian cause (2 sentences)
3. End with what the viewer can do (1 sentence)
4. Include a call to action for Meeko Nerve Center

Format it as a script with [VISUAL] notes in brackets."""

        script = ask_llm(prompt, max_tokens=200)
        if script:
            script_path = DATA / f'video_script_{TODAY}.json'
            script_path.write_text(json.dumps({
                'date':  TODAY,
                'story': story,
                'script': script,
                'used':  False
            }, indent=2))
            print(f'[cross] Video script written: {story[:60]}...')

    except Exception as e:
        print(f'[cross] Video script error: {e}')

# ── CONNECTION 8: Fork detected → welcome + QR + announcement ────────────────────

def fork_to_welcome():
    """
    Check GitHub for new forks of the repo.
    When a new fork is detected:
    - Generate a QR code for their fork URL
    - Post a Mastodon/Bluesky announcement
    - Email yourself so you know
    - Log the fork in data/forks.json
    """
    print('[cross] 8. Fork detected -> welcome + announcement')

    forks_path = DATA / 'forks.json'
    known_forks = set()
    if forks_path.exists():
        try:
            known_forks = set(json.loads(forks_path.read_text()).get('fork_ids', []))
        except:
            pass

    # Fetch current forks from GitHub API
    headers = {'Accept': 'application/vnd.github+json'}
    if GITHUB_TOKEN:
        headers['Authorization'] = f'Bearer {GITHUB_TOKEN}'

    data = fetch_json(
        'https://api.github.com/repos/meekotharaccoon-cell/meeko-nerve-center/forks?per_page=30&sort=newest',
        headers=headers
    )

    if not data:
        print('[cross] Could not fetch forks from GitHub API')
        return

    new_forks = [f for f in data if str(f['id']) not in known_forks]

    if not new_forks:
        print(f'[cross] No new forks today (total: {len(data)})')
        return

    for fork in new_forks:
        fork_id      = str(fork['id'])
        forker       = fork.get('owner', {}).get('login', 'someone')
        fork_url     = fork.get('html_url', '')
        fork_api_url = fork.get('url', '')

        print(f'[cross] New fork: {forker} — {fork_url}')

        # Generate QR code for their fork
        qr_url = f'https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={fork_url}'
        qr_path = PUBLIC / 'qr' / f'fork_{forker}.png'
        qr_path.parent.mkdir(exist_ok=True)
        try:
            req = urllib_request.Request(qr_url)
            with urllib_request.urlopen(req, timeout=10) as r:
                qr_path.write_bytes(r.read())
        except:
            pass

        # Post announcement
        text = f'Another node just came online.\n\n{forker} forked the Meeko Nerve Center.\n\nThe network grows.\n\n{fork_url}\n\n#SolarPunk #OpenSource #ForkIt #GazaRose'
        queue_post(text, post_type='fork_announce', extra={'forker': forker, 'fork_url': fork_url})

        # Email yourself
        send_email(
            GMAIL_ADDRESS,
            f'🌿 New fork: {forker}',
            f'Someone forked your system.\n\nForker: {forker}\nFork URL: {fork_url}\n\nThe network is growing.'
        )

        known_forks.add(fork_id)

    # Save updated fork list
    forks_path.write_text(json.dumps({
        'last_checked': TODAY,
        'total':        len(data),
        'fork_ids':     list(known_forks)
    }, indent=2))
    print(f'[cross] {len(new_forks)} new fork(s) welcomed')

# ── Main ────────────────────────────────────────────────────────────────────────

def run():
    print(f'\n[cross] Cross Engine — {TODAY}')
    print('[cross] Building connections between data streams...\n')

    congress_to_art()        ; time.sleep(2)
    donation_to_personal_art(); time.sleep(2)
    earthquake_to_solidarity(); time.sleep(2)
    crypto_spike_to_donation(); time.sleep(2)
    idea_to_grant()          ; time.sleep(2)
    culture_weave()          ; time.sleep(2)
    world_data_to_video_script(); time.sleep(2)
    fork_to_welcome()

    print('\n[cross] All connections processed.')

if __name__ == '__main__':
    run()
