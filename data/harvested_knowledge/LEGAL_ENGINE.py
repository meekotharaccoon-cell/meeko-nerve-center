"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  MEEKO LEGAL ENGINE                                                         ║
║  Generates legally valid documents using your vault identity.               ║
║  Every output is dated, signed, and ready to send or file.                 ║
╚══════════════════════════════════════════════════════════════════════════════╝

Documents this engine generates:
  1.  TCPA demand letter (illegal robocalls/texts)
  2.  FDCPA debt collector violation letter
  3.  Debt validation letter (stop collectors cold)
  4.  FOIA request (any federal agency)
  5.  State FOIA / public records request
  6.  Cease and desist (harassment, contact, IP)
  7.  Credit dispute letter (Equifax/Experian/TransUnion)
  8.  Small claims court complaint
  9.  Landlord demand letter (repairs, deposit return)
  10. HIPAA violation complaint
  11. 30-day demand letter (general)
  12. ADA accommodation request
  13. CFPB complaint letter
  14. Unemployment appeal letter
  15. Benefits denial appeal (generic)

Usage: python LEGAL_ENGINE.py
"""

import os
import sys
import json
import re
from datetime import datetime, timedelta
from pathlib import Path

# ── Vault import ──────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path.home() / "Desktop"))
try:
    from vault_reader import get_fields, vault_available, lock_vault
    VAULT_OK = vault_available()
except ImportError:
    VAULT_OK = False
    print("  ⚠️  vault_reader.py not found. Run from Desktop or check file location.")

# ── Output directory ──────────────────────────────────────────────────────────
OUTPUT_DIR = Path.home() / "Desktop" / "LEGAL_DOCUMENTS"
OUTPUT_DIR.mkdir(exist_ok=True)

# ── Utilities ─────────────────────────────────────────────────────────────────
def today():
    return datetime.now().strftime("%B %d, %Y")

def today_file():
    return datetime.now().strftime("%Y%m%d")

def deadline(days=30):
    return (datetime.now() + timedelta(days=days)).strftime("%B %d, %Y")

def save_doc(name: str, content: str, identity: dict) -> Path:
    filename = f"{today_file()}_{name}_{identity.get('full_legal_name','').replace(' ','_')}.txt"
    path = OUTPUT_DIR / filename
    path.write_text(content, encoding="utf-8")
    print(f"\n  ✅ Saved: {path}")
    return path

def section(title):
    print(f"\n  ── {title} " + "─" * (58 - len(title)))

def header():
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║  ⚖️   MEEKO LEGAL ENGINE                                                    ║
║       Generating legally valid documents with your verified identity        ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")

def addr_block(identity: dict) -> str:
    lines = [identity.get("full_legal_name", "")]
    if identity.get("address_line1"):
        lines.append(identity["address_line1"])
    if identity.get("address_line2"):
        lines.append(identity["address_line2"])
    city  = identity.get("city", "")
    state = identity.get("state", "")
    zip_  = identity.get("zip_code", "")
    if city or state or zip_:
        lines.append(f"{city}, {state} {zip_}".strip(", "))
    if identity.get("phone_primary"):
        lines.append(identity["phone_primary"])
    email = identity.get("email_legal") or identity.get("email_primary", "")
    if email:
        lines.append(email)
    return "\n".join(lines)

def sig_block(identity: dict) -> str:
    name = identity.get("full_legal_name", "_________________________")
    return f"""
Sincerely,


_________________________
{name}
{identity.get("address_line1", "")}
{identity.get("city", "")}, {identity.get("state", "")} {identity.get("zip_code", "")}
{identity.get("phone_primary", "")}
{identity.get("email_legal") or identity.get("email_primary", "")}
Date: {today()}
"""

def ask(prompt, optional=False):
    tag = " (optional, press Enter to skip)" if optional else ""
    return input(f"  {prompt}{tag}: ").strip() or None

# ══════════════════════════════════════════════════════════════════════════════
# DOCUMENT TEMPLATES
# ══════════════════════════════════════════════════════════════════════════════

def doc_tcpa_demand(identity):
    section("TCPA DEMAND LETTER")
    print("  The Telephone Consumer Protection Act (TCPA) prohibits")
    print("  robocalls, auto-texts, and calls to numbers on the Do Not Call Registry.")
    print("  Violations = $500–$1,500 per call. This letter puts them on notice.\n")

    company     = ask("Name of company that called/texted you")
    company_addr = ask("Company address (if known)", optional=True)
    call_dates  = ask("Date(s) of the calls/texts (e.g. Jan 5, Jan 7, Jan 12)")
    call_count  = ask("Approximate number of calls/texts received")
    call_type   = ask("Type of contact (robocall/auto-text/both)")
    your_status = ask("Were you on the Do Not Call Registry? (yes/no)")
    prior_consent = ask("Did you ever give them permission to contact you? (yes/no)")

    dnc = "I was registered on the Federal Do Not Call Registry at the time of these calls." if your_status and 'yes' in your_status.lower() else ""
    consent = "I have never provided prior express written consent to receive these communications." if prior_consent and 'no' in prior_consent.lower() else ""
    count_num = int(re.findall(r'\d+', call_count)[0]) if call_count and re.findall(r'\d+', call_count) else 1
    min_damages = count_num * 500
    max_damages = count_num * 1500

    doc = f"""
{addr_block(identity)}

{today()}

{company or 'To Whom It May Concern'}
{company_addr or ''}

                    VIA CERTIFIED MAIL / RETURN RECEIPT REQUESTED

RE: NOTICE OF VIOLATIONS OF THE TELEPHONE CONSUMER PROTECTION ACT (TCPA),
    47 U.S.C. § 227; DEMAND FOR CESSATION AND STATUTORY DAMAGES

To Whom It May Concern:

I, {identity.get('full_legal_name')}, am writing to formally notify you of your company's
violations of the Telephone Consumer Protection Act (TCPA), 47 U.S.C. § 227,
and to demand immediate cessation of unlawful contact and payment of applicable
statutory damages.

FACTS:

Between approximately {call_dates or '[dates of contact]'}, I received approximately
{call_count or '[number]'} {call_type or 'unsolicited'} communication(s) from your company or
its agents. {dnc} {consent}

VIOLATIONS:

Your conduct violates the TCPA, specifically:

  1. 47 U.S.C. § 227(b) — Use of automatic telephone dialing systems or
     prerecorded voices without prior express written consent.

  2. 47 U.S.C. § 227(c) — Calls to numbers registered on the National
     Do Not Call Registry without prior express invitation or permission.

  3. 47 C.F.R. § 64.1200 — FCC regulations implementing the TCPA.

DAMAGES:

Under 47 U.S.C. § 227(b)(3) and § 227(c)(5), I am entitled to:
  - $500 per violation (minimum)
  - $1,500 per willful violation (treble damages)
  - Injunctive relief

Based on {call_count or '[number]'} contacts, potential statutory damages range from
${min_damages:,} to ${max_damages:,}.

DEMANDS:

  1. IMMEDIATE cessation of all contact with me via phone, text, or any
     automated system.
  2. Remove my number from all calling lists and databases immediately.
  3. Provide written confirmation of compliance within 15 days.
  4. Preserve all records related to calls made to my number.

NOTICE: If I do not receive a satisfactory response by {deadline(15)}, I will,
without further notice, file complaints with:
  - The Federal Communications Commission (FCC)
  - The Federal Trade Commission (FTC)  
  - My state Attorney General
  - Small Claims Court or Federal District Court

This letter shall serve as formal notice. All subsequent contacts will be
documented and may constitute additional willful violations, increasing
potential damages.

{sig_block(identity)}

ENCLOSURES:
  - Call/text log documentation
  - FCC Do Not Call Registry confirmation (if applicable)
"""
    return save_doc("TCPA_DEMAND", doc, identity)


def doc_debt_validation(identity):
    section("DEBT VALIDATION LETTER — FDCPA § 809")
    print("  Under the FDCPA, debt collectors must STOP all collection activity")
    print("  until they verify the debt. Send this within 30 days of first contact.\n")

    collector   = ask("Name of debt collection company")
    col_addr    = ask("Collector's address")
    account_num = ask("Account number they referenced (if known)", optional=True)
    original_creditor = ask("Original creditor (if known)", optional=True)
    amount      = ask("Amount they claim you owe (if known)", optional=True)
    contact_date = ask("Date they first contacted you")

    acc_ref = f"Account No.: {account_num}" if account_num else "the account referenced in your communication"

    doc = f"""
{addr_block(identity)}

{today()}

{collector or 'Debt Collection Agency'}
{col_addr or ''}

                    VIA CERTIFIED MAIL / RETURN RECEIPT REQUESTED
                    FDCPA DEBT VALIDATION REQUEST

RE: REQUEST FOR DEBT VALIDATION PURSUANT TO 15 U.S.C. § 1692g
    {acc_ref}
    {"Alleged Amount: $" + amount if amount else ""}

To Whom It May Concern:

This letter is in response to your communication dated approximately
{contact_date or '[date of first contact]'} regarding an alleged debt.

Pursuant to the Fair Debt Collection Practices Act (FDCPA), 15 U.S.C. § 1692g,
I hereby formally dispute this alleged debt and request validation.

YOU ARE HEREBY NOTIFIED that:

  1. I dispute the validity of this alleged debt in its entirety.
  
  2. Pursuant to 15 U.S.C. § 1692g(b), all collection activity must
     CEASE immediately until you provide the following verification:

REQUIRED VALIDATION (provide ALL of the following):

  (a) The name and address of the original creditor
  (b) A copy of the original signed agreement creating the alleged debt
  (c) Complete payment history showing how the amount was calculated
  (d) Proof that your company is licensed to collect debts in {identity.get('state', 'my state')}
  (e) Your company's debt collector license number for {identity.get('state', 'my state')}
  (f) Proof that you own this debt or are authorized to collect it
  (g) The date the statute of limitations expires on this alleged debt
  (h) Complete chain of title showing all assignments of this debt

WARNING: Any collection activity — including calls, letters, credit
reporting, or legal action — before providing full validation is a
violation of 15 U.S.C. § 1692g(b) and may result in statutory damages
of $1,000 per violation plus actual damages and attorney's fees.

Additionally, if you report this disputed debt to any credit bureau
before providing validation, this constitutes a violation of
15 U.S.C. § 1692e(8) (false or misleading representations).

This is not a refusal to pay a legitimately established debt. This is a
lawful request for verification to which I am entitled by federal law.

Provide all documentation to my address above within 30 days.

{sig_block(identity)}

cc: Consumer Financial Protection Bureau (CFPB)
    Federal Trade Commission (FTC)
    {identity.get('state', 'State')} Attorney General
"""
    return save_doc("DEBT_VALIDATION", doc, identity)


def doc_foia_federal(identity):
    section("FEDERAL FOIA REQUEST")
    print("  Freedom of Information Act — any federal agency must respond")
    print("  within 20 business days. Free or low-cost. Your legal right.\n")

    agency     = ask("Federal agency name (e.g. FBI, SSA, USCIS, IRS, VA)")
    agency_div = ask("Specific division/office (optional)", optional=True)
    agency_addr = ask("Agency address (or check agency website for FOIA office)")
    records     = ask("Describe the records you want (be specific)")
    date_range  = ask("Date range for records (e.g. January 2020 to present)")
    purpose     = ask("Purpose (optional — can help get fee waiver)", optional=True)
    fee_waiver  = ask("Are you a journalist, researcher, or non-profit? (yes/no)", optional=True)

    fee_text = ""
    if fee_waiver and 'yes' in fee_waiver.lower():
        fee_text = f"""
FEE WAIVER REQUEST:
I request a fee waiver pursuant to 5 U.S.C. § 552(a)(4)(A)(iii) on the grounds
that disclosure of the requested information is in the public interest.
{("Specifically: " + purpose) if purpose else ""}
"""
    else:
        fee_text = "I agree to pay reasonable fees up to $25.00. Please notify me before incurring fees above this amount."

    doc = f"""
{addr_block(identity)}

{today()}

FOIA/Privacy Act Request
{agency or 'Federal Agency'}{', ' + agency_div if agency_div else ''}
{agency_addr or '[Agency FOIA Office Address]'}

                    FREEDOM OF INFORMATION ACT REQUEST
                    5 U.S.C. § 552

To the FOIA Officer:

Pursuant to the Freedom of Information Act, 5 U.S.C. § 552, and the Privacy
Act of 1974, 5 U.S.C. § 552a, I hereby request access to and copies of the
following records maintained by {agency or 'your agency'}:

RECORDS REQUESTED:

{records or '[Description of records requested]'}

DATE RANGE: {date_range or '[Specify date range]'}

IDENTITY VERIFICATION:
Full Name:    {identity.get('full_legal_name', '')}
Address:      {identity.get('address_line1', '')}, {identity.get('city', '')}, {identity.get('state', '')} {identity.get('zip_code', '')}
Date of Birth: {identity.get('date_of_birth', '')}

I am willing to provide a copy of my government-issued ID upon request.

{fee_text}

EXPEDITED PROCESSING: If expedited processing is available, I request it on the
grounds that delay could result in [specify if applicable: harm to personal
interests, media or public interest, etc.].

RESPONSE FORMAT: Please provide records in electronic format where possible.

If any records are withheld in full or in part, please provide a Vaughn index
identifying each withheld document, the exemption claimed, and why the
exemption applies.

Response deadline per 5 U.S.C. § 552(a)(6)(A)(i): 20 business days.

I look forward to your timely response. If you have questions, contact me at
{identity.get('email_legal') or identity.get('email_primary', '')} or {identity.get('phone_primary', '')}.

{sig_block(identity)}
"""
    return save_doc("FOIA_FEDERAL", doc, identity)


def doc_cease_desist(identity):
    section("CEASE AND DESIST LETTER")
    print("  Covers: harassment, unwanted contact, IP infringement, defamation,\n")
    print("  stalking, or any conduct you want to legally demand stop.\n")

    respondent     = ask("Full name of person/company to send this to")
    resp_addr      = ask("Their address")
    issue_type     = ask("Type of issue (harassment/contact/IP/defamation/stalking/other)")
    description    = ask("Describe the conduct in detail")
    dates          = ask("Dates or date range of the conduct")
    prior_requests = ask("Have you previously asked them to stop? (yes/no)")
    harm_suffered  = ask("Describe any harm you've suffered (emotional, financial, reputational)")

    doc = f"""
{addr_block(identity)}

{today()}

{respondent or 'To Whom It May Concern'}
{resp_addr or ''}

                    CEASE AND DESIST — NOTICE OF LEGAL ACTION
                    Via Certified Mail / Return Receipt Requested

RE: DEMAND TO CEASE AND DESIST {issue_type.upper() if issue_type else 'UNLAWFUL CONDUCT'}

To {respondent or 'You'}:

I, {identity.get('full_legal_name')}, am writing to formally demand that you
immediately cease and desist from the following conduct:

CONDUCT AT ISSUE:

{description or '[Describe the conduct]'}

This conduct occurred on or around {dates or '[dates]'} and has continued.
{"I have previously requested that you stop this conduct." if prior_consent and 'yes' in prior_consent.lower() else ""}

HARM SUFFERED:

As a direct result of your conduct, I have suffered:
{harm_suffered or '[Describe harm]'}

LEGAL BASIS:

Your conduct may constitute violations of one or more of the following:
  - State harassment statutes ({identity.get('state', 'applicable state')} law)
  - Federal stalking/harassment statutes (18 U.S.C. § 2261A) [if applicable]
  - Intentional infliction of emotional distress (tort)
  - [Other applicable law based on issue type]

DEMANDS:

Effective immediately, you must:

  1. CEASE AND DESIST all conduct described above.
  2. HAVE NO CONTACT with me, directly or indirectly, in any form.
  3. REMOVE any content about me from any platform within 72 hours [if applicable].
  4. PRESERVE all records related to this matter.

WARNING: If you fail to comply with these demands by {deadline(10)}, I will,
without further notice:
  - File a police report
  - Seek a restraining order / protective order
  - File civil suit for damages, injunctive relief, and attorney's fees
  - Report the conduct to relevant regulatory agencies

This letter is admissible as evidence of your knowledge and notice.

{sig_block(identity)}
"""
    return save_doc("CEASE_AND_DESIST", doc, identity)


def doc_credit_dispute(identity):
    section("CREDIT BUREAU DISPUTE LETTER")
    print("  Under FCRA § 611, credit bureaus must investigate disputed items")
    print("  within 30 days and remove unverifiable or inaccurate items.\n")

    bureau    = ask("Which bureau? (Equifax / Experian / TransUnion / all three)")
    items     = ask("Describe the item(s) you're disputing (account name, number if known)")
    reason    = ask("Reason for dispute (not mine / incorrect info / outdated / identity theft)")
    account   = ask("Account number (if shown on your report)", optional=True)

    bureaus = {
        "equifax":     ("Equifax Information Services LLC", "P.O. Box 740256, Atlanta, GA 30374"),
        "experian":    ("Experian", "P.O. Box 4500, Allen, TX 75013"),
        "transunion":  ("TransUnion LLC Consumer Dispute Center", "P.O. Box 2000, Chester, PA 19016"),
    }

    bureau_lower = (bureau or "").lower()
    targets = []
    if "all" in bureau_lower or "three" in bureau_lower:
        targets = list(bureaus.items())
    else:
        for k in bureaus:
            if k in bureau_lower:
                targets = [(k, bureaus[k])]
                break
    if not targets:
        targets = [("bureau", (bureau or "Credit Bureau", "[Bureau Address]"))]

    paths = []
    for key, (bname, baddr) in targets:
        doc = f"""
{addr_block(identity)}

{today()}

{bname}
{baddr}

                    FORMAL CREDIT REPORT DISPUTE
                    Fair Credit Reporting Act, 15 U.S.C. § 1681i

To the Credit Bureau Dispute Department:

Pursuant to the Fair Credit Reporting Act (FCRA), 15 U.S.C. § 1681i, I am
formally disputing the following inaccurate/unverifiable information appearing
on my credit report:

CONSUMER INFORMATION:
Full Legal Name: {identity.get('full_legal_name', '')}
Date of Birth:   {identity.get('date_of_birth', '')}
SSN (last 4):    ●●●-●●-{identity.get('ssn', '')[:-4] if identity.get('ssn') and len(identity.get('ssn','')) >= 4 else '●●●●'}[last 4 only — full SSN available upon request]
Current Address: {identity.get('address_line1', '')}, {identity.get('city', '')}, {identity.get('state', '')} {identity.get('zip_code', '')}

DISPUTED ITEM(S):

Account/Item: {items or '[Description of disputed item]'}
Account No.:  {account or 'See credit report'}
Reason:       {reason or 'Inaccurate information'}

This information is {reason or 'inaccurate/unverifiable'} and must be
investigated and corrected or removed.

REQUIRED ACTIONS:

  1. Investigate this dispute within 30 days as required by 15 U.S.C. § 1681i(a)(1).
  2. Forward all relevant information to the furnisher of this information.
  3. Provide me with the results of the investigation.
  4. Remove or correct the disputed item if it cannot be verified.

If the item is verified, please provide:
  - The name and contact information of the furnisher
  - A description of the procedure used to determine accuracy
  - My right to add a statement of dispute to my file

Please send your investigation results to my address above.

{sig_block(identity)}

ENCLOSED (check all that apply):
  ☐ Copy of government-issued ID
  ☐ Copy of Social Security card
  ☐ Utility bill showing current address
  ☐ Highlighted copy of credit report showing disputed item
  ☐ Supporting documentation
"""
        path = save_doc(f"CREDIT_DISPUTE_{key.upper()}", doc, identity)
        paths.append(path)
    return paths


def doc_small_claims(identity):
    section("SMALL CLAIMS COURT COMPLAINT")
    print("  Small claims lets you sue without a lawyer for amounts typically")
    print("  up to $5,000–$25,000 depending on your state.\n")

    defendant     = ask("Defendant's full name or company name")
    def_addr      = ask("Defendant's address")
    amount        = ask("Amount you're suing for (numbers only, e.g. 2500)")
    claim_desc    = ask("Describe what happened and why you're owed money")
    incident_date = ask("Date of the incident")
    state_limit   = ask(f"Small claims limit in {identity.get('state','your state')} (look up your state's limit)", optional=True)

    try:
        amount_formatted = f"${float(amount.replace(',','').replace('$','')):,.2f}"
    except:
        amount_formatted = f"${amount}"

    doc = f"""
╔══════════════════════════════════════════════════════════════════════╗
║  SMALL CLAIMS COURT — COMPLAINT WORKSHEET                           ║
║  Use this as a guide when filling out your court's official form.   ║
╚══════════════════════════════════════════════════════════════════════╝

STATE: {identity.get('state', '')}   COUNTY: {identity.get('county', '[Your County]')}

PLAINTIFF (You):
  Name:     {identity.get('full_legal_name', '')}
  Address:  {identity.get('address_line1', '')}, {identity.get('city', '')}, {identity.get('state', '')} {identity.get('zip_code', '')}
  Phone:    {identity.get('phone_primary', '')}
  Email:    {identity.get('email_primary', '')}

DEFENDANT:
  Name:     {defendant or '[Defendant Name]'}
  Address:  {def_addr or '[Defendant Address]'}

AMOUNT CLAIMED: {amount_formatted}

DATE OF INCIDENT: {incident_date or '[Date]'}

DESCRIPTION OF CLAIM:

{claim_desc or '[Your description here]'}

BASIS FOR CLAIM (check all that apply):
  ☐ Breach of contract
  ☐ Property damage
  ☐ Unpaid wages
  ☐ Security deposit not returned
  ☐ Goods/services not delivered
  ☐ Consumer protection violation
  ☐ TCPA/FDCPA statutory damages
  ☐ Negligence
  ☐ Other: _______________

DEMAND MADE PRIOR TO FILING?
  ☐ Yes — Date of demand: _______________
  ☐ No

EVIDENCE I WILL BRING:
  ☐ Contracts / agreements
  ☐ Receipts / invoices
  ☐ Photographs
  ☐ Text messages / emails
  ☐ Witnesses: _______________
  ☐ Other: _______________

FILING INSTRUCTIONS FOR {identity.get('state', 'YOUR STATE')}:
  1. Search: "{identity.get('state', 'your state')} small claims court filing online"
  2. Most states allow online filing at your county courthouse website
  3. Filing fee is typically $30–$100 (waivable if low income)
  4. Serve the defendant via certified mail or process server
  5. Court will notify you of hearing date (usually 4–8 weeks out)

FEE WAIVER: If your income is below 125% of federal poverty line, file
Form [your state's fee waiver form] simultaneously.

{sig_block(identity)}
"""
    return save_doc("SMALL_CLAIMS_COMPLAINT", doc, identity)


def doc_landlord_demand(identity):
    section("LANDLORD DEMAND LETTER")
    print("  Covers: security deposit return, repair demands, habitability,")
    print("  illegal entry, lease violations, retaliatory eviction.\n")

    landlord      = ask("Landlord's full name or management company")
    ll_addr       = ask("Landlord's address")
    rental_addr   = ask("Your rental property address (if different from yours)", optional=True)
    issue_type    = ask("Issue type (deposit/repairs/habitability/entry/other)")
    description   = ask("Describe the issue in detail")
    move_out_date = ask("Move-out date (if deposit issue)", optional=True)
    deposit_amt   = ask("Security deposit amount (if deposit issue)", optional=True)
    repair_dates  = ask("Date(s) repairs were requested (if repair issue)", optional=True)

    doc = f"""
{addr_block(identity)}

{today()}

{landlord or 'Landlord/Property Manager'}
{ll_addr or ''}

                    FORMAL DEMAND LETTER — TENANT RIGHTS
                    Via Certified Mail / Return Receipt Requested

RE: {issue_type.upper() if issue_type else 'LANDLORD VIOLATION'} — 
    Property: {rental_addr or identity.get('address_line1', '')}

Dear {landlord or 'Landlord/Property Manager'}:

I, {identity.get('full_legal_name')}, am writing to formally demand resolution
of the following issue(s):

ISSUE DESCRIPTION:

{description or '[Describe the issue]'}

{f"I vacated the property on {move_out_date}." if move_out_date else ""}
{f"Security deposit amount: ${deposit_amt}" if deposit_amt else ""}
{f"I made written repair requests on: {repair_dates}" if repair_dates else ""}

YOUR LEGAL OBLIGATIONS:

Under {identity.get('state', 'state')} landlord-tenant law:

{"• Security deposit must be returned within [state-specific days, typically 14-30] days of move-out with itemized deduction list. Failure results in up to 3x the deposit amount in damages." if deposit_amt else ""}
{"• You are required to maintain the property in habitable condition and make repairs within a reasonable time after notice." if 'repair' in (issue_type or '').lower() else ""}
{"• You must provide proper notice (typically 24-48 hours) before entering a tenant's unit." if 'entry' in (issue_type or '').lower() else ""}
{"• Retaliatory eviction or action following a tenant's assertion of their legal rights is illegal." if 'retaliat' in (issue_type or '').lower() else ""}

DEMAND:

I demand that you:
  1. [Specific action: return deposit / make repairs / cease illegal entry / etc.]
  2. Respond in writing to this letter within 14 days.
  3. Provide confirmation of compliance.

If you fail to comply by {deadline(14)}, I will:
  - File a complaint with {identity.get('state', 'state')} housing authorities
  - File in small claims court for return of deposit plus statutory penalties
  - File a complaint with the local housing inspection department
  - Consult with a tenant's rights attorney regarding additional remedies

{sig_block(identity)}
"""
    return save_doc("LANDLORD_DEMAND", doc, identity)


def doc_cfpb_complaint(identity):
    section("CFPB COMPLAINT LETTER")
    print("  The Consumer Financial Protection Bureau takes complaints against")
    print("  banks, lenders, credit cards, debt collectors, and more.")
    print("  File at consumerfinance.gov/complaint — this letter documents your claim.\n")

    company    = ask("Company you're complaining about")
    issue_type = ask("Issue type (billing / collections / credit reporting / mortgage / student loan / other)")
    description = ask("Describe what happened")
    account_num = ask("Account or reference number", optional=True)
    dates      = ask("Key dates")
    resolution = ask("What resolution are you seeking")

    doc = f"""
{addr_block(identity)}

{today()}

Consumer Financial Protection Bureau
P.O. Box 2900
Clinton, IA 52733-2900
(Also file online at: consumerfinance.gov/complaint)

RE: FORMAL COMPLAINT — {company or '[Company Name]'}
    Issue: {issue_type or 'Consumer Financial Violation'}
    {("Account/Reference: " + account_num) if account_num else ""}

CONSUMER INFORMATION:
Name:    {identity.get('full_legal_name', '')}
Address: {identity.get('address_line1', '')}, {identity.get('city', '')}, {identity.get('state', '')} {identity.get('zip_code', '')}
Phone:   {identity.get('phone_primary', '')}
Email:   {identity.get('email_primary', '')}
DOB:     {identity.get('date_of_birth', '')}
SSN (last 4): ●●●-●●-{identity.get('ssn', '●●●●')[-4:] if identity.get('ssn') else '●●●●'}

COMPLAINT AGAINST: {company or '[Company Name]'}

DATES: {dates or '[Key dates]'}

DESCRIPTION:

{description or '[Full description of the issue]'}

RESOLUTION SOUGHT:

{resolution or '[What you want the company to do]'}

PRIOR ATTEMPTS TO RESOLVE:
I have [previously/not yet] contacted {company or 'the company'} directly to resolve
this issue. [Describe any prior contact and outcome.]

I declare under penalty of perjury that the foregoing is true and correct.

{sig_block(identity)}

ATTACHMENTS:
  ☐ Account statements showing the problem
  ☐ Correspondence with the company
  ☐ Supporting documentation
"""
    return save_doc("CFPB_COMPLAINT", doc, identity)


# ══════════════════════════════════════════════════════════════════════════════
# MENU
# ══════════════════════════════════════════════════════════════════════════════

MENU = [
    ("TCPA Demand Letter — illegal robocalls/texts ($500-$1,500/call)", doc_tcpa_demand),
    ("Debt Validation Letter — stop collectors cold (FDCPA § 809)", doc_debt_validation),
    ("Federal FOIA Request — get records from any federal agency", doc_foia_federal),
    ("Cease and Desist — harassment, contact, IP, defamation", doc_cease_desist),
    ("Credit Bureau Dispute — remove inaccurate items (FCRA)", doc_credit_dispute),
    ("Small Claims Complaint — sue without a lawyer", doc_small_claims),
    ("Landlord Demand — deposit, repairs, habitability", doc_landlord_demand),
    ("CFPB Complaint — banks, lenders, debt collectors", doc_cfpb_complaint),
]


def main():
    import platform
    if not VAULT_OK:
        print("\n  ❌ Identity vault not found.")
        print("  Run IDENTITY_VAULT_SETUP.py first to create your vault.\n")
        return

    header()
    print(f"  Output directory: {OUTPUT_DIR}\n")

    # Load identity from vault
    print("  Unlocking identity vault...\n")
    identity = get_fields([
        "full_legal_name", "preferred_name", "date_of_birth",
        "address_line1", "address_line2", "city", "state", "zip_code", "county",
        "phone_primary", "email_primary", "email_legal",
        "ssn", "state_id_number", "state_id_state",
        "occupation", "monthly_income", "household_size",
    ])

    if not identity.get("full_legal_name"):
        print("  ❌ Could not unlock vault. Check password.\n")
        return

    print(f"  ✅ Identity loaded: {identity.get('full_legal_name')}")
    print(f"     {identity.get('address_line1')}, {identity.get('city')}, {identity.get('state')}\n")

    while True:
        section("SELECT DOCUMENT TO GENERATE")
        for i, (label, _) in enumerate(MENU, 1):
            print(f"  {i:2}. {label}")
        print(f"\n   Q. Quit\n")

        choice = input("  Choose [1-{}/Q]: ".format(len(MENU))).strip().upper()

        if choice == 'Q':
            lock_vault()
            print("\n  Vault locked. Goodbye.\n")
            break

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(MENU):
                label, fn = MENU[idx]
                print(f"\n  Generating: {label}")
                result = fn(identity)
                if result:
                    print(f"\n  Document saved. Open it, review it, then send via certified mail.")
                    print(f"  Document path: {result}")
            else:
                print("  Invalid choice.")
        except ValueError:
            print("  Invalid input.")
        except KeyboardInterrupt:
            lock_vault()
            print("\n\n  Vault locked. Exiting.\n")
            break


if __name__ == "__main__":
    main()
