import sys, os, json, urllib.request, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, white, black
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, PageBreak
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

OUT = Path(r'C:\Users\meeko\Desktop\PRODUCTS')
OUT.mkdir(exist_ok=True)

OLLAMA = 'http://localhost:11434'

def ask(prompt, model='mistral', max_tokens=3000):
    payload = json.dumps({
        'model': model,
        'prompt': prompt,
        'stream': False,
        'options': {'temperature': 0.4, 'num_predict': max_tokens}
    }).encode()
    req = urllib.request.Request(f'{OLLAMA}/api/generate', data=payload,
        headers={'Content-Type':'application/json'})
    resp = urllib.request.urlopen(req, timeout=120)
    return json.loads(resp.read()).get('response','')

def build_pdf(filepath, title, subtitle, sections, accent='#ff3366'):
    doc = SimpleDocTemplate(str(filepath), pagesize=letter,
        leftMargin=0.75*inch, rightMargin=0.75*inch,
        topMargin=0.75*inch, bottomMargin=0.75*inch)
    
    styles = getSampleStyleSheet()
    ac = HexColor(accent)
    
    title_style = ParagraphStyle('Title', fontName='Helvetica-Bold',
        fontSize=28, textColor=ac, spaceAfter=6, alignment=TA_CENTER, leading=34)
    sub_style = ParagraphStyle('Sub', fontName='Helvetica',
        fontSize=13, textColor=HexColor('#666666'), spaceAfter=20, alignment=TA_CENTER)
    h1_style = ParagraphStyle('H1', fontName='Helvetica-Bold',
        fontSize=16, textColor=ac, spaceAfter=8, spaceBefore=20)
    h2_style = ParagraphStyle('H2', fontName='Helvetica-Bold',
        fontSize=13, textColor=HexColor('#333333'), spaceAfter=6, spaceBefore=12)
    body_style = ParagraphStyle('Body', fontName='Helvetica',
        fontSize=11, textColor=HexColor('#222222'), leading=16,
        spaceAfter=8, alignment=TA_JUSTIFY)
    bullet_style = ParagraphStyle('Bullet', fontName='Helvetica',
        fontSize=11, textColor=HexColor('#333333'), leading=15,
        spaceAfter=5, leftIndent=20)
    footer_style = ParagraphStyle('Footer', fontName='Helvetica-Oblique',
        fontSize=9, textColor=HexColor('#999999'), alignment=TA_CENTER, spaceAfter=4)
    
    story = []
    story.append(Spacer(1, 0.4*inch))
    story.append(Paragraph(title, title_style))
    story.append(Paragraph(subtitle, sub_style))
    story.append(HRFlowable(width='100%', thickness=2, color=ac))
    story.append(Spacer(1, 0.2*inch))
    
    for section in sections:
        if section.get('type') == 'h1':
            story.append(Paragraph(section['text'], h1_style))
        elif section.get('type') == 'h2':
            story.append(Paragraph(section['text'], h2_style))
        elif section.get('type') == 'body':
            for para in section['text'].split('\n\n'):
                para = para.strip()
                if para:
                    story.append(Paragraph(para.replace('\n',' '), body_style))
        elif section.get('type') == 'bullets':
            for b in section['items']:
                story.append(Paragraph('• ' + b, bullet_style))
        elif section.get('type') == 'hr':
            story.append(HRFlowable(width='100%', thickness=1, color=HexColor('#dddddd')))
            story.append(Spacer(1, 0.1*inch))
        elif section.get('type') == 'pagebreak':
            story.append(PageBreak())
        elif section.get('type') == 'spacer':
            story.append(Spacer(1, section.get('h', 0.2)*inch))
    
    story.append(Spacer(1, 0.3*inch))
    story.append(HRFlowable(width='100%', thickness=1, color=HexColor('#dddddd')))
    story.append(Paragraph('Gaza Rose Collection · meekotharaccoon@gmail.com · 70% to PCRF', footer_style))
    
    doc.build(story)
    print(f"  PDF written: {filepath.name} ({filepath.stat().st_size//1024}KB)")
    return filepath

# ═══════════════════════════════════════════════════════════
# PDF 1: HOW I BUILT MY AI AGENT SYSTEM
# ═══════════════════════════════════════════════════════════
print("Generating PDF 1: AI Agent System Guide...")
print("  Asking Ollama to write the content...")

guide_content = ask("""Write a detailed practical guide titled 'How I Built a Fully Autonomous AI Agent System on My Desktop (With Zero Cloud Costs)'.

Structure it with these exact sections. Write each section as flowing prose (2-4 paragraphs each), not bullet points:

1. Introduction: What this system does and why it matters for passive income
2. The Core Philosophy: Local AI, open-source tools, zero recurring cost
3. The Tech Stack: Python 3.12, Ollama, mistral/llama3.2, SQLite, GitHub Actions
4. Step 1: Setting Up Ollama and Local AI Models
5. Step 2: Building the Agent Brain (autonomous diagnosis, fix, report loop)  
6. Step 3: Connecting Revenue Streams (Gumroad, PayPal, GitHub Pages)
7. Step 4: The Conductor Pattern (one system orchestrating many repos)
8. Step 5: Making It Truly Passive (GitHub Actions, scheduled tasks, self-healing)
9. The Revenue Blueprint: How the system generates income while you sleep
10. Conclusion: What's next and how to scale it

Write in a conversational, practical tone. Be specific about commands and code where it helps. Approximately 1500 words total.""")

print(f"  Ollama wrote {len(guide_content.split())} words")

# Parse into sections
guide_sections = [
    {'type':'body', 'text': 'This guide shows you exactly how I built a fully autonomous AI agent system that runs on my local machine, costs nothing per month to operate, and generates passive income while I sleep. No cloud bills. No subscriptions. Just Python, free AI models, and clever automation.'},
    {'type':'spacer', 'h':0.1},
]

# Split Ollama content into rough sections
raw_sections = guide_content.split('\n\n')
current_section = ''
for chunk in raw_sections:
    chunk = chunk.strip()
    if not chunk:
        continue
    if chunk.startswith('#') or (len(chunk) < 80 and chunk.endswith(':')):
        if current_section:
            guide_sections.append({'type':'body', 'text': current_section})
            current_section = ''
        guide_sections.append({'type':'h1', 'text': chunk.lstrip('#').strip().rstrip(':')})
    elif chunk.startswith('Step ') or chunk.startswith('**Step'):
        guide_sections.append({'type':'h1', 'text': chunk.lstrip('*').strip()})
    else:
        current_section += chunk + '\n\n'
        
if current_section:
    guide_sections.append({'type':'body', 'text': current_section})

guide_sections.extend([
    {'type':'hr'},
    {'type':'h1', 'text':'Quick Start Commands'},
    {'type':'bullets', 'items':[
        'Install Python 3.12 from python.org',
        'Install Ollama from ollama.com — it runs AI models locally for free',
        'Run: ollama pull mistral (downloads the AI brain)',
        'Run: python AUTONOMOUS_AGENT.py (starts the system)',
        'Open http://localhost:7780 to see everything running',
        'Connect services via the Grand Setup Wizard at http://localhost:7776',
        'Your system now diagnoses itself, fixes problems, and earns revenue 24/7',
    ]},
    {'type':'spacer','h':0.2},
    {'type':'body', 'text':'The complete source code, setup scripts, and templates described in this guide are available at github.com/meekotharaccoon-cell. Every piece is open-source and free to use, modify, and build on.'},
])

build_pdf(OUT/'Gaza_Rose_AI_System_Guide.pdf',
    'How I Built a Fully Autonomous\nAI Agent System',
    'Zero Cloud Cost · Runs 24/7 · Generates Passive Income',
    guide_sections, accent='#00cc66')

# ═══════════════════════════════════════════════════════════
# PDF 2: PROMPT PACK — THE ART BEHIND GAZA ROSE
# ═══════════════════════════════════════════════════════════
print("\nGenerating PDF 2: AI Art Prompt Pack...")

prompt_content = ask("""Write a prompt engineering guide for creating stunning 300 DPI floral digital art using AI image generators (Midjourney, DALL-E, Stable Diffusion, Adobe Firefly).

Include:
1. Introduction: Why prompts are the most valuable skill in AI art
2. The Core Gaza Rose Formula: The exact prompt structure that creates vibrant, print-ready floral art
3. 20 specific example prompts (one per line, each for a different flower/style)
4. How to achieve 300 DPI print quality
5. Color theory prompts: getting vivid, gallery-quality colors
6. Background prompts: transparent vs. textured vs. gradient
7. Style modifiers that work best for floral art
8. How to sell AI art legally and ethically
9. Pricing strategy: why $1 per piece at volume beats $50 per piece at low volume

Write specific, usable prompts. Be technical and practical. Approximately 1200 words.""")

print(f"  Ollama wrote {len(prompt_content.split())} words")

prompt_sections = [
    {'type':'body', 'text':'This pack contains the exact prompt formulas, techniques, and strategies used to create the Gaza Rose Collection — 69 pieces of 300 DPI digital floral art. These prompts work in Midjourney, DALL-E, Adobe Firefly, and Stable Diffusion.'},
    {'type':'spacer','h':0.1},
]

raw2 = prompt_content.split('\n\n')
current2 = ''
for chunk in raw2:
    chunk = chunk.strip()
    if not chunk: continue
    if chunk.startswith('#') or (len(chunk) < 80 and chunk.endswith(':')):
        if current2:
            prompt_sections.append({'type':'body','text':current2})
            current2 = ''
        prompt_sections.append({'type':'h1','text':chunk.lstrip('#').strip().rstrip(':')})
    else:
        current2 += chunk + '\n\n'
if current2:
    prompt_sections.append({'type':'body','text':current2})

prompt_sections.extend([
    {'type':'hr'},
    {'type':'h1','text':'Quick Reference Prompt Templates'},
    {'type':'bullets','items':[
        '"A single [FLOWER], hyper-detailed, 8k, photorealistic, vibrant colors, studio lighting, white background, macro photography"',
        '"[FLOWER] bloom, bioluminescent, glowing petals, dark background, ethereal light, ultra-sharp focus, print quality"',
        '"Abstract [FLOWER], geometric shapes, neon colors, black background, digital art, 300dpi, graphic design"',
        '"Watercolor [FLOWER], loose brushstrokes, pastel palette, natural imperfections, fine art print"',
        '"[FLOWER] field at golden hour, cinematic, bokeh background, warm tones, editorial photography"',
    ]},
])

build_pdf(OUT/'Gaza_Rose_Prompt_Pack.pdf',
    'Gaza Rose AI Art Prompt Pack',
    '69 Prompts · Print-Ready Formulas · Sell Anywhere',
    prompt_sections, accent='#ff3366')

# ═══════════════════════════════════════════════════════════
# PDF 3: PASSIVE INCOME BLUEPRINT
# ═══════════════════════════════════════════════════════════
print("\nGenerating PDF 3: Passive Income Blueprint...")

income_content = ask("""Write a practical passive income blueprint for someone who has: local AI running, 69 pieces of digital art, PayPal connected, Gumroad account, GitHub, and Python automation.

Include:
1. The Passive Income Mindset: Why most people fail (they stop too early)
2. Stream 1: Digital Art Sales (Gumroad, Etsy, Creative Market) — exact setup steps
3. Stream 2: Print-on-Demand (Redbubble, Printify, Merch by Amazon) — upload once, earn forever
4. Stream 3: AI System Guide (sell the knowledge of how you built the system)
5. Stream 4: Prompt Packs (sell the prompts that made the art)
6. Stream 5: GitHub Sponsors and Ko-fi (monetize open-source work)
7. Stream 6: Licensing (license art for commercial use at $5-25/piece)
8. The Automation Stack: How to post, promote, and sell without lifting a finger
9. PCRF Integration: How the charity angle actually increases conversions
10. Month 1 Action Plan: Exact steps, in order, to get first sale within 7 days

Be specific, practical, and direct. No fluff. Approximately 1400 words.""")

print(f"  Ollama wrote {len(income_content.split())} words")

income_sections = [
    {'type':'body','text':'This blueprint maps exactly how to turn AI tools, digital art, and automation into multiple streams of passive income — starting today, with what you already have.'},
    {'type':'spacer','h':0.1},
]
raw3 = income_content.split('\n\n')
current3 = ''
for chunk in raw3:
    chunk = chunk.strip()
    if not chunk: continue
    if chunk.startswith('#') or (len(chunk) < 80 and chunk.endswith(':')):
        if current3:
            income_sections.append({'type':'body','text':current3})
            current3 = ''
        income_sections.append({'type':'h1','text':chunk.lstrip('#').strip().rstrip(':')})
    else:
        current3 += chunk + '\n\n'
if current3:
    income_sections.append({'type':'body','text':current3})

income_sections.extend([
    {'type':'hr'},
    {'type':'h1','text':'7-Day Quick Start'},
    {'type':'bullets','items':[
        'Day 1: Upload all art to Redbubble (free account, they print & ship)',
        'Day 2: Create Etsy shop, list 10 digital download art pieces at $2.99',
        'Day 3: List AI System Guide PDF on Gumroad at $9.99',
        'Day 4: Set up Ko-fi tip page, link it everywhere',
        'Day 5: Enable GitHub Sponsors on your profile',
        'Day 6: Post 3 art pieces to Reddit r/DigitalArt with gallery link',
        'Day 7: Set up automated weekly posting — system runs itself from here',
    ]},
])

build_pdf(OUT/'Gaza_Rose_Passive_Income_Blueprint.pdf',
    'Passive Income Blueprint',
    'AI Art · Digital Products · Automated Revenue',
    income_sections, accent='#ffc800')

print(f"""
{'='*55}
3 SELLABLE PDFs CREATED IN:
  {OUT}

  1. Gaza_Rose_AI_System_Guide.pdf
  2. Gaza_Rose_Prompt_Pack.pdf  
  3. Gaza_Rose_Passive_Income_Blueprint.pdf

NEXT: Upload these to Gumroad manually:
  gumroad.com/new-product
  - AI System Guide: $9.99
  - Prompt Pack: $4.99
  - Income Blueprint: $7.99
{'='*55}
""")
