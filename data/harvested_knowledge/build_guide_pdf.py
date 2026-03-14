"""
Build the Meeko Mycelium System Guide PDF
Complete beginner guide - assumes zero computer knowledge
"""
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.units import inch
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors
import os

OUTPUT = r'C:\Users\meeko\Desktop\MEEKO_MYCELIUM_SYSTEM_GUIDE.pdf'

doc = SimpleDocTemplate(
    OUTPUT,
    pagesize=letter,
    rightMargin=0.75*inch,
    leftMargin=0.75*inch,
    topMargin=0.75*inch,
    bottomMargin=0.75*inch
)

# Colors
ROSE = HexColor('#C0395A')
DARK = HexColor('#1a1a2e')
GOLD = HexColor('#FFD700')
LIGHT = HexColor('#f8f4f0')
GREEN = HexColor('#2ecc71')

styles = getSampleStyleSheet()

# Custom styles
title_style = ParagraphStyle(
    'CustomTitle',
    parent=styles['Title'],
    fontSize=32,
    textColor=ROSE,
    spaceAfter=20,
    fontName='Helvetica-Bold',
    alignment=1
)

subtitle_style = ParagraphStyle(
    'Subtitle',
    parent=styles['Normal'],
    fontSize=16,
    textColor=DARK,
    spaceAfter=10,
    fontName='Helvetica',
    alignment=1
)

h1_style = ParagraphStyle(
    'H1',
    parent=styles['Heading1'],
    fontSize=22,
    textColor=ROSE,
    spaceBefore=20,
    spaceAfter=10,
    fontName='Helvetica-Bold'
)

h2_style = ParagraphStyle(
    'H2',
    parent=styles['Heading2'],
    fontSize=16,
    textColor=DARK,
    spaceBefore=15,
    spaceAfter=8,
    fontName='Helvetica-Bold'
)

body_style = ParagraphStyle(
    'Body',
    parent=styles['Normal'],
    fontSize=12,
    textColor=DARK,
    spaceAfter=8,
    fontName='Helvetica',
    leading=18
)

step_style = ParagraphStyle(
    'Step',
    parent=styles['Normal'],
    fontSize=13,
    textColor=white,
    spaceAfter=6,
    fontName='Helvetica-Bold',
    backColor=ROSE,
    borderPadding=(8, 8, 8, 8),
    leading=20
)

note_style = ParagraphStyle(
    'Note',
    parent=styles['Normal'],
    fontSize=11,
    textColor=DARK,
    spaceAfter=6,
    fontName='Helvetica-Oblique',
    backColor=LIGHT,
    borderPadding=(6, 6, 6, 6),
    leading=16
)

story = []

# ============ COVER PAGE ============
story.append(Spacer(1, 1*inch))
story.append(Paragraph("THE MEEKO MYCELIUM SYSTEM", title_style))
story.append(Spacer(1, 0.2*inch))
story.append(Paragraph("Complete Build Guide", subtitle_style))
story.append(Spacer(1, 0.1*inch))
story.append(HRFlowable(width="100%", thickness=3, color=ROSE))
story.append(Spacer(1, 0.2*inch))
story.append(Paragraph("How to Build Your Own AI System From Scratch", subtitle_style))
story.append(Spacer(1, 0.2*inch))
story.append(Paragraph("Written for someone who has never touched a computer before", note_style))
story.append(Spacer(1, 0.3*inch))
story.append(Paragraph("By Meeko | Gaza Rose Initiative | 70% of proceeds to PCRF", subtitle_style))
story.append(Spacer(1, 0.5*inch))

# What you will have
story.append(Paragraph("What You Will Have When You Finish This Guide:", h2_style))
items = [
    "Your own AI that runs entirely on YOUR computer — no monthly fees",
    "A system that thinks, learns, remembers, and improves itself",
    "Multiple AI agents working together like a team",
    "Connected to Gumroad, PayPal and Stripe to generate real revenue",
    "A self-healing system that fixes its own errors automatically",
    "Everything legal and ethical from the ground up",
    "A digital mycelium — a living network that grows forever"
]
for item in items:
    story.append(Paragraph(f"   CHECKMARK  {item}", body_style))

story.append(PageBreak())

# ============ CHAPTER 1 ============
story.append(Paragraph("CHAPTER 1: Before You Begin", h1_style))
story.append(HRFlowable(width="100%", thickness=1, color=ROSE))
story.append(Spacer(1, 0.1*inch))

story.append(Paragraph("What is this system?", h2_style))
story.append(Paragraph(
    "Think of this system like hiring a team of workers who never sleep, never take breaks, "
    "and get smarter every single day. These workers live inside your computer. They are "
    "called AI agents. Your job is to be the boss — you tell them what to do, they do it, "
    "and they report back to you before touching anything important like your money.",
    body_style))

story.append(Paragraph("What computer do you need?", h2_style))
story.append(Paragraph(
    "You need a Windows computer (Windows 10 or 11). Your computer should have at least "
    "8GB of memory (RAM) and 50GB of free storage space. If you are not sure, ask someone "
    "to check for you — it takes less than one minute.",
    body_style))

story.append(Paragraph("Important Rule Before We Start:", h2_style))
story.append(Paragraph(
    "This system will always ask YOU before it does anything with real money. "
    "YOU are always in charge. The AI works FOR you, not instead of you.",
    note_style))

story.append(PageBreak())

# ============ CHAPTER 2 ============
story.append(Paragraph("CHAPTER 2: Installing Your Tools", h1_style))
story.append(HRFlowable(width="100%", thickness=1, color=ROSE))
story.append(Spacer(1, 0.1*inch))
story.append(Paragraph(
    "Think of this chapter like going to a hardware store before building a house. "
    "We need to get our tools first. Each tool below is completely FREE.",
    body_style))

# Tools table
tool_data = [
    ['Tool Name', 'What It Does', 'Where to Get It'],
    ['Python', 'The language your AI speaks', 'python.org/downloads'],
    ['Git', 'Saves and tracks your work', 'git-scm.com'],
    ['Ollama', 'Runs AI on YOUR computer', 'ollama.com'],
    ['Node.js', 'Runs web tools', 'nodejs.org'],
    ['Docker', 'Keeps tools separated safely', 'docker.com'],
    ['VS Code', 'Where you write instructions', 'code.visualstudio.com'],
]

tool_table = Table(tool_data, colWidths=[1.5*inch, 2.5*inch, 2.5*inch])
tool_table.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), ROSE),
    ('TEXTCOLOR', (0,0), (-1,0), white),
    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
    ('FONTSIZE', (0,0), (-1,-1), 11),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [LIGHT, white]),
    ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ('PADDING', (0,0), (-1,-1), 8),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
]))
story.append(tool_table)
story.append(Spacer(1, 0.3*inch))

story.append(Paragraph("How to install each tool:", h2_style))
story.append(Paragraph(
    "For each tool above, go to the website listed, look for a big button that says "
    "DOWNLOAD, click it, then open the file that downloads and click NEXT until it finishes. "
    "That is all. You do not need to understand what is happening — just click through.",
    body_style))

story.append(PageBreak())

# ============ CHAPTER 3 ============
story.append(Paragraph("CHAPTER 3: Opening PowerShell", h1_style))
story.append(HRFlowable(width="100%", thickness=1, color=ROSE))
story.append(Spacer(1, 0.1*inch))
story.append(Paragraph(
    "PowerShell is like a text message conversation with your computer. "
    "You type instructions, your computer reads them and does them. "
    "Do not be scared — if you make a mistake, nothing bad happens.",
    body_style))

steps_ch3 = [
    ("Step 1", "Press the Windows key on your keyboard (it looks like a little flag in the bottom left of your keyboard)"),
    ("Step 2", "Type the word: PowerShell"),
    ("Step 3", "You will see a result appear. RIGHT-CLICK on it"),
    ("Step 4", "Click 'Run as Administrator'"),
    ("Step 5", "A dark blue window will open. This is PowerShell. Keep it open."),
]
for label, text in steps_ch3:
    story.append(Paragraph(f" {label} ", step_style))
    story.append(Paragraph(text, body_style))
    story.append(Spacer(1, 0.05*inch))

story.append(PageBreak())

# ============ CHAPTER 4 ============
story.append(Paragraph("CHAPTER 4: Getting Your AI Models", h1_style))
story.append(HRFlowable(width="100%", thickness=1, color=ROSE))
story.append(Spacer(1, 0.1*inch))
story.append(Paragraph(
    "Now we download the AI brains. These are called models. Think of them like "
    "hiring different specialists — one for writing, one for coding, one for understanding. "
    "They all live on YOUR computer and work for free forever once downloaded.",
    body_style))

story.append(Paragraph("In your PowerShell window, type each line below and press ENTER:", h2_style))

commands_ch4 = [
    ("ollama pull mistral", "Your main thinking AI — good at everything"),
    ("ollama pull codellama", "Your coding specialist AI"),
    ("ollama pull llama3.2", "Your fast response AI"),
    ("ollama pull nomic-embed-text", "Your memory AI — helps the system remember things"),
]
for cmd, desc in commands_ch4:
    story.append(Paragraph(f"Type exactly: {cmd}", step_style))
    story.append(Paragraph(f"This downloads: {desc}", note_style))
    story.append(Spacer(1, 0.1*inch))

story.append(Paragraph(
    "Each download may take 5 to 20 minutes depending on your internet speed. "
    "That is normal. Just wait until you see the cursor blinking again before typing the next one.",
    note_style))

story.append(PageBreak())

# ============ CHAPTER 5 ============
story.append(Paragraph("CHAPTER 5: Installing Your AI Framework", h1_style))
story.append(HRFlowable(width="100%", thickness=1, color=ROSE))
story.append(Spacer(1, 0.1*inch))
story.append(Paragraph(
    "Now we install the tools that let your AI agents talk to each other and to the world. "
    "Copy each line below into PowerShell exactly as written and press ENTER.",
    body_style))

pip_commands = [
    "python -m venv mycelium_env",
    "mycelium_env\\Scripts\\activate",
    "pip install crewai langchain langchain-community",
    "pip install chromadb ollama fastapi",
    "pip install litellm reportlab Pillow",
]
for cmd in pip_commands:
    story.append(Paragraph(f"  {cmd}", step_style))
    story.append(Spacer(1, 0.05*inch))

story.append(Spacer(1, 0.2*inch))
story.append(Paragraph(
    "Wait for each command to finish before typing the next one. "
    "You will know it is done when you see the blinking cursor again.",
    note_style))

story.append(PageBreak())

# ============ CHAPTER 6 ============
story.append(Paragraph("CHAPTER 6: Building Your First Agent", h1_style))
story.append(HRFlowable(width="100%", thickness=1, color=ROSE))
story.append(Spacer(1, 0.1*inch))
story.append(Paragraph(
    "Now the exciting part. We are going to create your first AI agent. "
    "An agent is like an employee with a specific job. "
    "We will create two agents who work as a team.",
    body_style))

story.append(Paragraph(
    "Open Notepad (press Windows key, type Notepad, press Enter). "
    "Copy the entire block of text below into Notepad exactly as written. "
    "Then save it on your Desktop and name it: agent.py",
    body_style))

code_style = ParagraphStyle(
    'Code',
    parent=styles['Normal'],
    fontSize=9,
    fontName='Courier',
    backColor=DARK,
    textColor=GOLD,
    borderPadding=(10, 10, 10, 10),
    leading=14,
    spaceAfter=10
)

story.append(Paragraph(
    "from crewai import Agent, Task, Crew, LLM\n\n"
    "llm = LLM(model='ollama/mistral',\n"
    "          base_url='http://localhost:11434')\n\n"
    "researcher = Agent(\n"
    "    role='Researcher',\n"
    "    goal='Find the best information on any topic',\n"
    "    backstory='Expert researcher with vast knowledge',\n"
    "    llm=llm, verbose=True)\n\n"
    "builder = Agent(\n"
    "    role='Builder',\n"
    "    goal='Turn research into action steps',\n"
    "    backstory='Expert at making things happen',\n"
    "    llm=llm, verbose=True)\n\n"
    "task1 = Task(\n"
    "    description='Research how to make money online ethically',\n"
    "    agent=researcher,\n"
    "    expected_output='Top 5 methods with details')\n\n"
    "task2 = Task(\n"
    "    description='Create an action plan from the research',\n"
    "    agent=builder,\n"
    "    expected_output='Step by step action plan')\n\n"
    "crew = Crew(agents=[researcher, builder],\n"
    "            tasks=[task1, task2], verbose=True)\n\n"
    "result = crew.kickoff()\n"
    "print(result)",
    code_style))

story.append(Paragraph(
    "To run it, go to PowerShell and type:\n"
    "python Desktop\\agent.py\n"
    "Then press ENTER and watch your AI agents work.",
    note_style))

story.append(PageBreak())

# ============ CHAPTER 7 ============
story.append(Paragraph("CHAPTER 7: Connecting Your Revenue Accounts", h1_style))
story.append(HRFlowable(width="100%", thickness=1, color=ROSE))
story.append(Spacer(1, 0.1*inch))
story.append(Paragraph(
    "This is where your system starts making real money. "
    "We connect it to Gumroad so you can sell digital products automatically. "
    "Your API keys are NEVER saved to your computer — you enter them fresh each time for safety.",
    body_style))

rev_steps = [
    ("Gumroad", "Go to gumroad.com/oauth/applications", "Create an app, name it anything, use http://localhost as redirect URI, generate your access token"),
    ("Stripe", "Go to dashboard.stripe.com/apikeys", "Click Reveal on your Secret Key (starts with sk_live_)"),
    ("PayPal", "Go to developer.paypal.com/dashboard/applications/live", "Create an app and copy your Client ID and Secret"),
]

for platform, where, howto in rev_steps:
    story.append(Paragraph(f" {platform} ", step_style))
    story.append(Paragraph(f"Where to go: {where}", body_style))
    story.append(Paragraph(f"What to do: {howto}", note_style))
    story.append(Spacer(1, 0.1*inch))

story.append(PageBreak())

# ============ CHAPTER 8 ============
story.append(Paragraph("CHAPTER 8: The Gaza Rose System", h1_style))
story.append(HRFlowable(width="100%", thickness=1, color=ROSE))
story.append(Spacer(1, 0.1*inch))
story.append(Paragraph(
    "The Gaza Rose system is the heart of everything. It is an ethical autonomous loop — "
    "meaning it runs by itself, makes money, and automatically directs a percentage of every "
    "sale to help people in crisis. This is built into the code itself. It cannot be removed.",
    body_style))

story.append(Paragraph("The Ethical Split:", h2_style))

split_data = [
    ['Where the money goes', 'Percentage'],
    ['Crisis Aid (PCRF and others)', '50%'],
    ['System Reinvestment (upgrades itself)', '20%'],
    ['YOUR personal account', '30%'],
]
split_table = Table(split_data, colWidths=[3.5*inch, 2.5*inch])
split_table.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), ROSE),
    ('TEXTCOLOR', (0,0), (-1,0), white),
    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
    ('FONTSIZE', (0,0), (-1,-1), 12),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [LIGHT, white]),
    ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ('PADDING', (0,0), (-1,-1), 10),
    ('ALIGN', (1,0), (1,-1), 'CENTER'),
]))
story.append(split_table)
story.append(Spacer(1, 0.3*inch))
story.append(Paragraph(
    "The system will ALWAYS ask you before moving any real money. "
    "You approve every transaction. The AI suggests, you decide.",
    note_style))

story.append(PageBreak())

# ============ CHAPTER 9 ============
story.append(Paragraph("CHAPTER 9: Making Your System Grow", h1_style))
story.append(HRFlowable(width="100%", thickness=1, color=ROSE))
story.append(Spacer(1, 0.1*inch))
story.append(Paragraph(
    "Your system is now alive. Every day it runs, it gets smarter. "
    "Here is how to keep it growing:",
    body_style))

growth_steps = [
    ("Run the Evolution Cycle", "Type in PowerShell: python UltimateAI_Master\\ultimate_ai_master_v15.py --evolve\nDo this once a day. Your system will upgrade itself."),
    ("Run the Crew", "Type: python UltimateAI_Master\\connect_crew.py\nYour AI agents will research what to improve and save their findings automatically."),
    ("Check Your Revenue", "Type: python UltimateAI_Master\\subsystems\\predictive_analytics.py\nSee a report of everything your system has learned and earned."),
    ("Add New Products", "Put any digital file in your Gumroad account and your system will help you describe and price it."),
]

for title, desc in growth_steps:
    story.append(Paragraph(f" {title} ", step_style))
    story.append(Paragraph(desc, body_style))
    story.append(Spacer(1, 0.1*inch))

story.append(PageBreak())

# ============ FINAL PAGE ============
story.append(Spacer(1, 0.5*inch))
story.append(Paragraph("You Did It.", title_style))
story.append(Spacer(1, 0.2*inch))
story.append(HRFlowable(width="100%", thickness=3, color=ROSE))
story.append(Spacer(1, 0.3*inch))
story.append(Paragraph(
    "You now have a living, self-improving AI system running on your own computer. "
    "It costs you nothing to run. It gets smarter every day. "
    "It makes money while you sleep. And every time it does, "
    "people in crisis get help automatically.",
    body_style))
story.append(Spacer(1, 0.3*inch))
story.append(Paragraph(
    "This is not just a system. This is proof that technology built with good intentions "
    "from the code up can change the world one transaction at a time.",
    body_style))
story.append(Spacer(1, 0.5*inch))
story.append(Paragraph("Gaza Rose Initiative", h1_style))
story.append(Paragraph("Built by Meeko | For everyone | Forever", subtitle_style))
story.append(Spacer(1, 0.3*inch))
story.append(Paragraph(
    "PCRF Wallet: "https://give.pcrf.net/campaign/739651/donate"",
    note_style))

# Build PDF
doc.build(story)
print(f"PDF created: {OUTPUT}")
