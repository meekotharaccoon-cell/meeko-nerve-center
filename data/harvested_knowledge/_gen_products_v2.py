import sys, os, json, urllib.request, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, PageBreak
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

OUT = Path(r'C:\Users\meeko\Desktop\PRODUCTS')
OUT.mkdir(exist_ok=True)

def ask(prompt, model='mistral', max_tokens=600):
    """Short, fast Ollama calls that don't timeout."""
    payload = json.dumps({
        'model': model, 'prompt': prompt, 'stream': False,
        'options': {'temperature': 0.4, 'num_predict': max_tokens}
    }).encode()
    req = urllib.request.Request('http://localhost:11434/api/generate',
        data=payload, headers={'Content-Type':'application/json'})
    resp = urllib.request.urlopen(req, timeout=90)
    return json.loads(resp.read()).get('response','').strip()

def make_pdf(path, title, subtitle, content_blocks, accent='#ff3366'):
    doc = SimpleDocTemplate(str(path), pagesize=letter,
        leftMargin=0.8*inch, rightMargin=0.8*inch,
        topMargin=0.8*inch, bottomMargin=0.8*inch)
    ac = HexColor(accent)
    s_title = ParagraphStyle('t', fontName='Helvetica-Bold', fontSize=26,
        textColor=ac, spaceAfter=6, alignment=TA_CENTER, leading=32)
    s_sub   = ParagraphStyle('s', fontName='Helvetica', fontSize=12,
        textColor=HexColor('#666666'), spaceAfter=18, alignment=TA_CENTER)
    s_h1    = ParagraphStyle('h1', fontName='Helvetica-Bold', fontSize=15,
        textColor=ac, spaceAfter=8, spaceBefore=18)
    s_body  = ParagraphStyle('b', fontName='Helvetica', fontSize=11,
        textColor=HexColor('#1a1a1a'), leading=17, spaceAfter=8, alignment=TA_JUSTIFY)
    s_bull  = ParagraphStyle('bl', fontName='Helvetica', fontSize=11,
        textColor=HexColor('#222222'), leading=15, spaceAfter=5, leftIndent=20)
    s_foot  = ParagraphStyle('f', fontName='Helvetica-Oblique', fontSize=9,
        textColor=HexColor('#999999'), alignment=TA_CENTER)
    story = []
    story += [Spacer(1,0.3*inch), Paragraph(title, s_title),
              Paragraph(subtitle, s_sub), HRFlowable(width='100%',thickness=2,color=ac),
              Spacer(1,0.2*inch)]
    for block in content_blocks:
        t = block.get('type','body')
        if   t=='h1':    story.append(Paragraph(block['text'], s_h1))
        elif t=='body':
            for para in block['text'].split('\n\n'):
                p = para.strip()
                if p: story.append(Paragraph(p.replace('\n',' '), s_body))
        elif t=='bullets':
            for b in block['items']:
                story.append(Paragraph('• ' + b, s_bull))
        elif t=='hr':
            story += [HRFlowable(width='100%',thickness=1,color=HexColor('#dddddd')),
                      Spacer(1,0.1*inch)]
        elif t=='space':  story.append(Spacer(1, block.get('h',0.15)*inch))
        elif t=='break':  story.append(PageBreak())
    story += [Spacer(1,0.3*inch),
              HRFlowable(width='100%',thickness=1,color=HexColor('#dddddd')),
              Paragraph('Gaza Rose Collection · meekotharaccoon@gmail.com · 70% of profits to PCRF', s_foot)]
    doc.build(story)
    kb = path.stat().st_size // 1024
    print(f'  DONE: {path.name} ({kb}KB)')
    return path

# ═══════════════════════════════════════════════════════════
print('Generating PDF 1: AI System Guide...')

sections = []

prompts_and_headings = [
    ('How I Built a Fully Autonomous AI Agent System',
     'Explain in 2 paragraphs: what an autonomous AI agent system is and why anyone should build one for passive income. Be conversational and practical.'),
    ('The Philosophy: Local, Free, Forever',
     'Write 2 paragraphs about why running AI locally with Ollama (free, private, no API costs) is better than paying for cloud AI APIs. Mention mistral, llama3.2, SQLite, Python.'),
    ('Step 1: Install the Brain (Ollama)',
     'Write step-by-step instructions (2 paragraphs) for installing Ollama and downloading mistral on Windows. Include the exact commands.'),
    ('Step 2: Build the Agent Loop',
     'Write 2 paragraphs explaining the core agent loop: diagnose -> fix -> report -> sleep 5 min -> repeat. Explain why this makes a system self-healing.'),
    ('Step 3: Connect Your Revenue Streams',
     'Write 2 paragraphs on connecting PayPal, Gumroad, and GitHub Pages as revenue channels for an AI-powered art store. Be specific.'),
    ('Step 4: The Conductor Pattern',
     'Write 2 paragraphs explaining how one GitHub repo (conductor) can dispatch commands to multiple other repos via GitHub Actions, making the whole system orchestrated.'),
    ('Step 5: Making It Passive',
     'Write 2 paragraphs on how GitHub Actions scheduled workflows (cron jobs) and the local agent loop make this system generate income without daily human input.'),
    ('The Revenue Blueprint',
     'Write 2 paragraphs describing 4 specific passive income streams: digital art sales, PDF guides, prompt packs, and GitHub Sponsors. Give rough income estimates.'),
]

for heading, prompt in prompts_and_headings:
    print(f'  Writing: {heading}...')
    content = ask(prompt, max_tokens=400)
    sections.append({'type':'h1', 'text': heading})
    sections.append({'type':'body', 'text': content})

sections += [
    {'type':'hr'},
    {'type':'h1','text':'Quick Start (5 Commands)'},
    {'type':'bullets','items':[
        '1. Download Ollama: ollama.com/download',
        '2. Install model: ollama pull mistral',
        '3. Install Python packages: pip install requests yfinance sqlite3 reportlab',
        '4. Run your agent: python AUTONOMOUS_AGENT.py',
        '5. Open status page: http://localhost:7780',
        'Thats it. Your autonomous AI system is running.',
    ]},
]

make_pdf(OUT/'Gaza_Rose_AI_System_Guide.pdf',
    'How I Built a Fully Autonomous\nAI Agent System',
    'Zero Cloud Cost · Runs 24/7 · Multiple Passive Income Streams',
    sections, accent='#00cc66')

# ═══════════════════════════════════════════════════════════
print('\nGenerating PDF 2: Prompt Pack...')

psections = []
flower_prompts = [
    'A single red rose, hyper-detailed macro, 8k, water droplets, studio lighting, white background, print quality, 300dpi',
    'Neon lily, bioluminescent glow, dark background, vibrant purple and teal, ultra-sharp, digital art print',
    'Sunflower field at golden hour, cinematic bokeh, warm tones, photorealistic, editorial photography quality',
    'Cherry blossom branch, soft pink petals, misty background, Japanese minimalism, fine art print',
    'Dahlias close-up, electric colors, black background, geometric patterns in petals, museum quality',
    'Lavender field, purple gradient sky, dreamy blur, soft focus, romantic, gallery wall art',
    'Venus flytrap, emerald green, morning dew, macro photography, white background, botanical illustration style',
    'Chrysanthemum, fractal geometry, golden ratio composition, white petals, dark background, sacred geometry',
    'Hibiscus, tropical neon colors, abstract background, high contrast, Pantone color accuracy',
    'Wildflowers meadow, watercolor wash, loose brushstrokes, impressionist, pastel palette, art print',
    'Magnolia bloom, alabaster petals, green leaves, soft natural light, minimalist, Scandinavian interior art',
    'Fuchsia, electric pink and purple, crystalline background, surreal, fantasy flower, album art quality',
    'Jasmine cluster, moonlight, blue-silver tones, ethereal, fragrance visualized, dreamy art print',
    'Larkspur, cobalt blue, geometric shadows, architectural composition, fine art photography style',
    'Peony, blush pink, gold details, luxury aesthetic, editorial fashion magazine quality, 300dpi',
    'Ginkgo leaves, autumn gold, falling motion blur, Japanese zen, minimalist art print',
    'Crocus emerging from snow, hope symbolism, vivid purple, white negative space, emotional art',
    'Orchid, exotic patterns, tropical green background, botanical accuracy + surreal color, museum print',
    'Cosmos flowers, galaxy background, stars visible through petals, space-floral fusion, poster art',
    'Abstract rose, geometric deconstruction, Mondrian-inspired, primary colors, bold lines, modern art print',
]

prompts_intro = ask('Write 2 paragraphs explaining why AI art prompts are the most valuable skill in the AI art economy. How do prompts determine 90% of the output quality?', max_tokens=300)
quality_tips = ask('Write 3 specific technical tips for getting 300 DPI print-quality results from AI image generators. Mention resolution, upscaling, and color profile settings.', max_tokens=300)
selling_tips = ask('Write 2 paragraphs on the legal and ethical way to sell AI-generated art. Cover copyright, disclosure, and the best platforms (Gumroad, Etsy, Redbubble).', max_tokens=300)

psections += [
    {'type':'body','text': prompts_intro},
    {'type':'h1','text':'The Gaza Rose Prompt Formula'},
    {'type':'body','text':'Every piece in the Gaza Rose Collection was generated using this core structure:\n\n[SUBJECT], [STYLE], [LIGHTING], [BACKGROUND], [QUALITY MODIFIER], [RESOLUTION]\n\nExample: "A single red rose, hyper-detailed macro photography, studio lighting, pure white background, print-ready, 300 DPI"'},
    {'type':'h1','text':'20 Production-Ready Prompts'},
]
for i, p in enumerate(flower_prompts, 1):
    psections.append({'type':'bullets','items':[f'{i}. {p}']})

psections += [
    {'type':'h1','text':'Getting Print-Quality Output'},
    {'type':'body','text': quality_tips},
    {'type':'h1','text':'Selling AI Art: Legal and Ethical'},
    {'type':'body','text': selling_tips},
    {'type':'hr'},
    {'type':'h1','text':'Style Modifier Cheat Sheet'},
    {'type':'bullets','items':[
        'Realism: "photorealistic, DSLR, f/2.8, natural lighting, sharp focus"',
        'Fantasy: "bioluminescent, ethereal glow, magical, otherworldly, dreamy"',
        'Minimalist: "negative space, clean background, single subject, Scandinavian"',
        'Bold/Modern: "high contrast, vibrant, neon, editorial, magazine quality"',
        'Fine Art: "oil painting, impasto, textured canvas, gallery-worthy, masterpiece"',
        'Print Ready: "300 DPI, CMYK color space, print-ready, large format, museum quality"',
    ]},
]

make_pdf(OUT/'Gaza_Rose_Prompt_Pack.pdf',
    'Gaza Rose AI Art Prompt Pack',
    '20 Production Prompts · Print-Ready Formulas · Sell Anywhere Legally',
    psections, accent='#ff3366')

# ═══════════════════════════════════════════════════════════
print('\nGenerating PDF 3: Passive Income Blueprint...')

bsections = []

income_intro = ask('Write 2 paragraphs on why digital products are the best passive income for someone with AI tools and coding skills. Focus on zero marginal cost and 24/7 sales.', max_tokens=300)
stream1 = ask('Write specific setup steps for selling digital art on Gumroad and Etsy. Include pricing strategy ($1-3 for art), how to write descriptions that convert, and how to enable instant download. 2 paragraphs.', max_tokens=350)
stream2 = ask('Explain how print-on-demand works with Redbubble and Printify. How does an artist upload once and earn forever? What products sell best (posters, phone cases, tote bags)? 2 paragraphs.', max_tokens=350)
stream3 = ask('Write 2 paragraphs on monetizing technical knowledge: selling guides, prompt packs, and templates. Include pricing ($5-25) and the platforms that work best (Gumroad, Lemon Squeezy).', max_tokens=300)
stream4 = ask('Explain GitHub Sponsors and Ko-fi as passive income for open-source developers. How does having public repos with useful code attract supporters? Include setup steps. 2 paragraphs.', max_tokens=300)
automation = ask('Write 2 paragraphs on using Python + GitHub Actions to automate posting to Reddit, scheduling social media, and sending weekly email newsletters — all without daily effort.', max_tokens=300)
pcrf_angle = ask('Write 2 paragraphs on how donating 70% to charity (PCRF) actually INCREASES sales conversions. Why do buyers pay more when they know it helps children? Include statistics if possible.', max_tokens=280)
week1 = ask('Give a specific 7-day action plan to get the first passive income sale. Day-by-day, specific tasks, realistic goals. Format as numbered list.', max_tokens=350)

bsections += [
    {'type':'body','text':income_intro},
    {'type':'h1','text':'Stream 1: Digital Art Sales ($1-3/piece)'},
    {'type':'body','text':stream1},
    {'type':'h1','text':'Stream 2: Print-on-Demand (Upload Once, Earn Forever)'},
    {'type':'body','text':stream2},
    {'type':'h1','text':'Stream 3: Knowledge Products ($5-25/guide)'},
    {'type':'body','text':stream3},
    {'type':'h1','text':'Stream 4: GitHub Sponsors + Ko-fi (Tip Jar)'},
    {'type':'body','text':stream4},
    {'type':'h1','text':'Stream 5: Automated Promotion'},
    {'type':'body','text':automation},
    {'type':'h1','text':'The Charity Advantage: Why 70% to PCRF Increases Sales'},
    {'type':'body','text':pcrf_angle},
    {'type':'hr'},
    {'type':'h1','text':'Your 7-Day Launch Plan'},
    {'type':'body','text':week1},
    {'type':'space','h':0.2},
    {'type':'h1','text':'Revenue Targets (Realistic)'},
    {'type':'bullets','items':[
        'Week 1: First sale — $1 to $15',
        'Month 1: 50-100 sales across all streams — $50 to $200',
        'Month 3: Automated posting driving consistent traffic — $200 to $500/mo',
        'Month 6: Print-on-demand + digital + knowledge products — $500 to $1500/mo',
        'Year 1: Scaling with more art, more guides, more automation — $1500 to $5000/mo',
        'All of this: zero additional cost to you after setup',
    ]},
]

make_pdf(OUT/'Gaza_Rose_Passive_Income_Blueprint.pdf',
    'Passive Income Blueprint',
    'AI Art · Digital Products · Automation · 70% to PCRF',
    bsections, accent='#ffc800')

print(f"""
{'='*55}
3 PDFs READY IN: C:\\Users\\meeko\\Desktop\\PRODUCTS\\

  Gaza_Rose_AI_System_Guide.pdf      -> Sell for $9.99
  Gaza_Rose_Prompt_Pack.pdf          -> Sell for $4.99
  Gaza_Rose_Passive_Income_Blueprint -> Sell for $7.99

UPLOAD TO GUMROAD (2 minutes, manual):
  1. Go to gumroad.com
  2. Click + New Product
  3. Upload PDF, set price, publish
  Done. Gumroad handles PayPal checkout automatically.
{'='*55}
""")
