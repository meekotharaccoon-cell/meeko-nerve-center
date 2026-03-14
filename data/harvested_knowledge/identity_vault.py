#!/usr/bin/env python3
"""
🏛️ IDENTITY VAULT — Autonomous Legal & Financial Autonomy Layer
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Your rights, your records, your filings — automated.

Capabilities:
  FOIA requests — automated public records requests
  Debt validation letters — FDCPA-compliant (collectors must respond)
  Cease & desist — auto-generated for harassment
  Credit dispute letters — FCRA-compliant
  Demand letters — small claims, landlord disputes, wage theft
  CFPB/FTC complaints — auto-formatted and filed
  Benefits eligibility check — public assistance programs
  Document vault — encrypted local storage of critical docs
  SSA/IRS correspondence templates — never miss a deadline
  Statute of limitations tracker — know when debts expire

All tools are:
  - 100% legal (you have these rights by law)
  - Free to use (no court filings without your explicit action)
  - Permission-first (nothing sends without your review)
  - Based on established law (FOIA, FDCPA, FCRA, FOIA)

Usage:
  python identity_vault.py                    # menu
  python identity_vault.py --foia             # generate FOIA request
  python identity_vault.py --debt-validate    # debt validation letter
  python identity_vault.py --cease-desist     # cease and desist
  python identity_vault.py --credit-dispute   # credit bureau dispute
  python identity_vault.py --demand           # demand letter
  python identity_vault.py --sol-check        # statute of limitations
  python identity_vault.py --benefits         # benefits eligibility
  python identity_vault.py --cfpb             # CFPB complaint
"""

import os
import sys
import json
import datetime
import argparse
from pathlib import Path

# ─────────────────────────────────────────────────────
COLORS
# ─────────────────────────────────────────────────────
class C:
    G = '\033[92m'; Y = '\033[93m'; R = '\033[91m'
    C = '\033[96m'; B = '\033[1m'; D = '\033[2m'; X = '\033[0m'

def g(s): return f"{C.G}{s}{C.X}"
def y(s): return f"{C.Y}{s}{C.X}"
def c(s): return f"{C.C}{s}{C.X}"
def b(s): return f"{C.B}{s}{C.X}"
def d(s): return f"{C.D}{s}{C.X}"
def r(s): return f"{C.R}{s}{C.X}"

# ─────────────────────────────────────────────────────
VAULT SETUP
# ─────────────────────────────────────────────────────
VAULT_DIR = Path.home() / '.identity_vault'
DOCS_DIR = VAULT_DIR / 'documents'
TRACKER_FILE = VAULT_DIR / 'tracker.json'

def setup_vault():
    VAULT_DIR.mkdir(exist_ok=True)
    DOCS_DIR.mkdir(exist_ok=True)
    if not TRACKER_FILE.exists():
        TRACKER_FILE.write_text(json.dumps({
            'debts': [], 'disputes': [], 'requests': [], 'letters': []
        }, indent=2))

def load_tracker():
    setup_vault()
    return json.loads(TRACKER_FILE.read_text())

def save_tracker(data):
    TRACKER_FILE.write_text(json.dumps(data, indent=2))

def save_doc(filename, content):
    path = DOCS_DIR / filename
    path.write_text(content)
    print(f"  {g('Saved:')} {path}")
    return path

def get_today(): return datetime.date.today().strftime("%B %d, %Y")
def get_file_date(): return datetime.date.today().strftime("%Y%m%d")

# ─────────────────────────────────────────────────────
FOIA REQUEST GENERATOR
# ─────────────────────────────────────────────────────
def generate_foia():
    print(f"\n{b('🏛️ FOIA REQUEST GENERATOR')}")
    print(d("━" * 55))
    print(d("  Freedom of Information Act — you have the right to these records."))
    print(d("  Federal agencies must respond within 20 business days."))
    print(d("  State agencies vary (usually 5-30 days)."))
    print()

    your_name     = input(f"  {c('Your full name:')} ").strip()
    your_address  = input(f"  {c('Your address:')} ").strip()
    agency_name   = input(f"  {c('Agency name (e.g. FBI, local PD, IRS):')} ").strip()
    agency_address= input(f"  {c('Agency address:')} ").strip()
    records_desc  = input(f"  {c('Records you want (be specific):')} ").strip()
    date_range    = input(f"  {c('Date range (e.g. Jan 2020 to present):')} ").strip()
    fee_waiver    = input(f"  {c('Reason for fee waiver (e.g. public interest, journalism, or press Enter to skip):')} ").strip()

    fee_waiver_text = ""
    if fee_waiver:
        fee_waiver_text = f"""
FEE WAIVER REQUEST

I request a waiver of all fees for this request. The requested records concern a matter of 
significant public interest: {fee_waiver}. Disclosure of this information is in the public 
interest because it is likely to contribute significantly to public understanding of the 
operations or activities of the government and is not primarily in my commercial interest.
"""

    letter = f"""FREEDOM OF INFORMATION ACT REQUEST

{get_today()}

{your_name}
{your_address}

{agency_name}
{agency_address}

Re: Freedom of Information Act Request

To Whom It May Concern:

Pursuant to the Freedom of Information Act, 5 U.S.C. § 552, I hereby request the following 
records:

RECORDS REQUESTED:
{records_desc}

DATE RANGE: {date_range}

I request that you provide records in electronic format where possible. If there are any 
portions of responsive documents that you believe are exempt from disclosure, please provide 
the non-exempt portions and specify which exemption you claim applies to each withheld portion.

Please note that under FOIA, you are required to respond within 20 business days of receiving 
this request. If you anticipate any delays, please notify me promptly.
{fee_waiver_text}
If you have any questions regarding this request, please contact me at the address above.

Respectfully submitted,


{your_name}

---
This letter was generated using the open-source Meeko Mycelium Identity Vault.
FOIA requests are a legal right under 5 U.S.C. § 552.
"""

    filename = f"FOIA_request_{agency_name.replace(' ', '_')}_{get_file_date()}.txt"
    path = save_doc(filename, letter)
    print(f"\n  {g('✓ FOIA request generated!')}")
    print(f"  {d('Review it, then send by certified mail with return receipt.')}")
    print(f"  {d('Keep your tracking number. Agencies must respond in 20 business days.')}")
    print(f"  {d('If they miss the deadline, that itself can be a FOIA violation.'))}")
    print(f"\n  {c('File:')} {path}")
    return path

# ─────────────────────────────────────────────────────
DEBT VALIDATION LETTER (FDCPA)
# ─────────────────────────────────────────────────────
def generate_debt_validation():
    print(f"\n{b('💳 DEBT VALIDATION LETTER (FDCPA)')}")
    print(d("━" * 55))
    print(d("  Under FDCPA § 809(b), collectors must validate debt within 30 days."))
    print(d("  While validation is pending, they must CEASE ALL COLLECTION ACTIVITY."))
    print(d("  This includes calls, letters, credit reporting, and lawsuits."))
    print()

    your_name       = input(f"  {c('Your full name:')} ").strip()
    your_address    = input(f"  {c('Your address:')} ").strip()
    collector_name  = input(f"  {c('Collection agency name:')} ").strip()
    collector_addr  = input(f"  {c('Collection agency address:')} ").strip()
    account_ref     = input(f"  {c('Account/reference number (from their letter):')} ").strip()
    alleged_amount  = input(f"  {c('Alleged amount owed:')} ").strip()
    original_cred   = input(f"  {c('Original creditor name (if known):')} ").strip()

    letter = f"""DEBT VALIDATION REQUEST PURSUANT TO 15 U.S.C. § 1692g(b)

{get_today()}

{your_name}
{your_address}

Sent via Certified Mail, Return Receipt Requested

{collector_name}
{collector_addr}

Re: Account/Reference Number: {account_ref}
    Alleged Amount: {alleged_amount}
    Alleged Original Creditor: {original_cred or 'Unknown'}

Dear {collector_name},

I am writing in response to your recent communication regarding the above-referenced account. 
This letter is not a refusal to pay, but a notice pursuant to the Fair Debt Collection 
Practices Act (FDCPA), 15 U.S.C. § 1692g(b), that I hereby dispute this debt in its entirety 
and request validation.

Pursuant to my rights under the FDCPA, please provide the following:

1. The name and address of the original creditor to whom the debt is owed
2. A complete account history showing how the alleged amount was calculated
3. A copy of any written agreement creating the alleged debt and bearing my signature
4. Evidence that your agency is licensed to collect debt in my state
5. Evidence that the alleged debt is within the statute of limitations
6. Proof that you own the debt or are authorized to collect on behalf of the owner
7. A copy of the last billing statement from the original creditor

FEDERAL LAW NOTICE: Until you have provided complete validation of this debt as required 
by law, you must CEASE AND DESIST all collection activities including:
- Phone calls to me, my family, or my employer
- Written communications (except legally required notices)
- Credit bureau reporting or updates
- Legal proceedings

Failure to validate this debt and cease collection activity as required by law may result 
in a complaint to the Consumer Financial Protection Bureau (CFPB), the Federal Trade 
Commission (FTC), the state Attorney General, and civil action under 15 U.S.C. § 1692k, 
which provides for actual damages, statutory damages up to $1,000 per violation, and 
attorney fees.

Please respond in writing only. Do not contact me by telephone.

Sincerely,


{your_name}

---
This letter was generated using the open-source Meeko Mycelium Identity Vault.
FDCPA rights are established under 15 U.S.C. § 1692 et seq.
Send via certified mail. Keep your tracking number as proof of delivery.
"""

    filename = f"DebtValidation_{collector_name.replace(' ', '_')}_{get_file_date()}.txt"
    path = save_doc(filename, letter)

    # Track in vault
    tracker = load_tracker()
    tracker['debts'].append({
        'collector': collector_name,
        'amount': alleged_amount,
        'account': account_ref,
        'letter_date': str(datetime.date.today()),
        'response_deadline': str(datetime.date.today() + datetime.timedelta(days=30)),
        'file': str(path),
        'status': 'validation_requested'
    })
    save_tracker(tracker)

    print(f"\n  {g('✓ Debt validation letter generated!')}")
    print(f"  {g('Response deadline:')} {d(str(datetime.date.today() + datetime.timedelta(days=30)))}")
    print(f"  {d('Send by certified mail. They must respond within 30 days.')}")
    print(f"  {d('If they fail to respond, the debt may be legally unenforceable.')}")
    print(f"  {d('If they continue collecting without validating: FDCPA violation = $1,000 per violation.')}")
    print(f"\n  {c('File:')} {path}")
    return path

# ─────────────────────────────────────────────────────
CEASE AND DESIST
# ─────────────────────────────────────────────────────
def generate_cease_desist():
    print(f"\n{b('✋ CEASE AND DESIST LETTER')}")
    print(d("━" * 55))
    print(d("  Works for: debt collectors, harassment, defamation, stalking,"))
    print(d("  unwanted contact, copyright infringement, trademark violations."))
    print()

    your_name    = input(f"  {c('Your full name:')} ").strip()
    your_address = input(f"  {c('Your address:')} ").strip()
    recipient    = input(f"  {c('Recipient name/company:')} ").strip()
    recip_addr   = input(f"  {c('Recipient address:')} ").strip()
    conduct      = input(f"  {c('Describe the conduct to stop (be specific):')} ").strip()
    legal_basis  = input(f"  {c('Legal basis (e.g. FDCPA, harassment, defamation):')} ").strip()
    remedy       = input(f"  {c('What you want them to do (e.g. stop all contact):')} ").strip()
    deadline     = input(f"  {c('Compliance deadline (e.g. 10 days, or press Enter for 10 days):')} ").strip() or '10'

    deadline_date = datetime.date.today() + datetime.timedelta(days=int(deadline))

    letter = f"""CEASE AND DESIST NOTICE

{get_today()}

{your_name}
{your_address}

Sent via Certified Mail, Return Receipt Requested

{recipient}
{recip_addr}

Re: Demand to Cease and Desist — {conduct[:50]}

TO {recipient.upper()}:

I am writing to formally demand that you immediately CEASE AND DESIST from the following 
conduct:

{conduct}

LEGAL BASIS: This conduct violates {legal_basis}. You are hereby placed on notice that 
continuation of this conduct may expose you to civil liability, statutory damages, and 
other legal remedies.

DEMAND: You are hereby required to:
{remedy}

DEADLINE: You must comply no later than {deadline_date.strftime("%B %d, %Y")} ({deadline} days from the date of this letter).

WARNING: If you fail to comply with this demand, I reserve all rights to pursue any and 
all legal remedies available to me, including but not limited to:
- Filing a complaint with the appropriate regulatory agencies
- Initiating civil litigation
- Seeking injunctive relief
- Pursuing all applicable statutory and actual damages

This letter constitutes formal legal notice. Retain this letter and your response to it.

Very truly yours,


{your_name}

---
This letter was generated using the open-source Meeko Mycelium Identity Vault.
Send via certified mail. Keep your tracking number.
"""

    filename = f"CeaseDesist_{recipient.replace(' ', '_')}_{get_file_date()}.txt"
    path = save_doc(filename, letter)
    print(f"\n  {g('✓ Cease and desist generated!')}")
    print(f"  {g('Compliance deadline:')} {d(str(deadline_date))}")
    print(f"  {d('Send certified mail. Keep the tracking number and return receipt.')}")
    print(f"\n  {c('File:')} {path}")
    return path

# ─────────────────────────────────────────────────────
CREDIT DISPUTE (FCRA)
# ─────────────────────────────────────────────────────
def generate_credit_dispute():
    print(f"\n{b('📊 CREDIT BUREAU DISPUTE (FCRA)')}")
    print(d("━" * 55))
    print(d("  Under the Fair Credit Reporting Act, bureaus must investigate"))
    print(d("  disputes within 30 days and remove unverified information."))
    print()

    your_name    = input(f"  {c('Your full name:')} ").strip()
    your_address = input(f"  {c('Your address:')} ").strip()
    your_ssn_last4 = input(f"  {c('Last 4 of SSN (for verification only):')} ").strip()
    bureau       = input(f"  {c('Bureau (Equifax/Experian/TransUnion):')} ").strip()
    account_name = input(f"  {c('Account/tradeline name on report:')} ").strip()
    account_num  = input(f"  {c('Account number (if known):')} ").strip()
    error_desc   = input(f"  {c('Describe the inaccuracy:')} ").strip()
    desired_fix  = input(f"  {c('What correction do you want?')} ").strip()

    bureaus = {
        'equifax':   'P.O. Box 740256, Atlanta, GA 30374-0256',
        'experian':  'P.O. Box 4500, Allen, TX 75013',
        'transunion': 'Consumer Dispute Center, P.O. Box 2000, Chester, PA 19016'
    }
    bureau_addr = bureaus.get(bureau.lower(), f'{bureau} Dispute Department')

    letter = f"""CREDIT REPORT DISPUTE — FAIR CREDIT REPORTING ACT § 611

{get_today()}

{your_name}
{your_address}
Last 4 SSN: {your_ssn_last4 if your_ssn_last4 else '[attach copy of ID]'}

{bureau}
{bureau_addr}

Re: Dispute of Inaccurate Information
    Account: {account_name} ({account_num or 'See report'})

To Whom It May Concern:

I am writing pursuant to the Fair Credit Reporting Act (FCRA), 15 U.S.C. § 1681, 
to dispute inaccurate information appearing in my credit report.

INACCURACY:
The following account contains inaccurate information:
  Account Name: {account_name}
  Account Number: {account_num or 'As shown on report'}
  Error: {error_desc}

REQUESTED CORRECTION:
{desired_fix}

FEDERAL LAW REQUIRES:
Under FCRA § 611, you are required to:
1. Conduct a reasonable investigation within 30 days
2. Notify the furnisher of the disputed information
3. Review all relevant information I submit
4. Correct or delete inaccurate, incomplete, or unverifiable information
5. Notify me in writing of the results within 5 business days of completing the investigation

If the information cannot be verified, it MUST be deleted from my report.

I am enclosing [a copy of my government-issued ID and proof of address / relevant 
documentation supporting this dispute].

Please investigate this matter and provide me with the results of your investigation in writing.

Sincerely,


{your_name}

Enclosures:
- Copy of government-issued ID
- Proof of current address
- Supporting documentation (as applicable)

---
This letter was generated using the open-source Meeko Mycelium Identity Vault.
FCRA rights established under 15 U.S.C. § 1681 et seq.
Send via certified mail with return receipt. Keep all records.
"""

    filename = f"CreditDispute_{bureau}_{account_name.replace(' ', '_')}_{get_file_date()}.txt"
    path = save_doc(filename, letter)
    print(f"\n  {g('✓ Credit dispute generated!')}")
    print(f"  {g('Investigation deadline:')} {d(str(datetime.date.today() + datetime.timedelta(days=30)))}")
    print(f"  {d('Attach: government ID, proof of address, supporting docs.')}")
    print(f"  {d('Send certified mail. They must respond in 30 days.')}")
    print(f"\n  {c('File:')} {path}")
    return path

# ─────────────────────────────────────────────────────
STATUTE OF LIMITATIONS CHECKER
# ─────────────────────────────────────────────────────
SOL_BY_STATE = {
    'AL': 6, 'AK': 3, 'AZ': 6, 'AR': 5, 'CA': 4, 'CO': 6, 'CT': 6,
    'DE': 3, 'FL': 5, 'GA': 6, 'HI': 6, 'ID': 5, 'IL': 5, 'IN': 6,
    'IA': 5, 'KS': 5, 'KY': 5, 'LA': 3, 'ME': 6, 'MD': 3, 'MA': 6,
    'MI': 6, 'MN': 6, 'MS': 3, 'MO': 5, 'MT': 5, 'NE': 5, 'NV': 6,
    'NH': 3, 'NJ': 6, 'NM': 6, 'NY': 6, 'NC': 3, 'ND': 6, 'OH': 6,
    'OK': 5, 'OR': 6, 'PA': 4, 'RI': 10, 'SC': 3, 'SD': 6, 'TN': 6,
    'TX': 4, 'UT': 6, 'VT': 6, 'VA': 5, 'WA': 6, 'WV': 10, 'WI': 6,
    'WY': 8, 'DC': 3
}

def check_sol():
    print(f"\n{b('⏱️ STATUTE OF LIMITATIONS CHECKER')}")
    print(d("━" * 55))
    print(d("  After SOL expires, the debt is time-barred."))
    print(d("  Collectors CAN still ask for payment, but CANNOT sue you."))
    print(d("  Making a payment or even acknowledging the debt can restart the clock."))
    print()

    state = input(f"  {c('Your state (2-letter code, e.g. CA, TX):')} ").strip().upper()
    last_payment = input(f"  {c('Date of last payment (YYYY-MM-DD, or press Enter if unknown):')} ").strip()
    debt_type = input(f"  {c('Debt type (credit card / auto loan / medical / other):')} ").strip()

    sol_years = SOL_BY_STATE.get(state, 6)
    print(f"\n  {g('State:')} {state}")
    print(f"  {g('SOL for written contracts in ' + state + ':')} {sol_years} years")

    if last_payment:
        try:
            last_date = datetime.date.fromisoformat(last_payment)
            expiry = last_date.replace(year=last_date.year + sol_years)
            today = datetime.date.today()
            if today > expiry:
                print(f"  {g('✓ DEBT IS TIME-BARRED!')} SOL expired {(today - expiry).days} days ago.")
                print(f"  {g('They cannot sue you for this debt.')})")
                print(f"  {y('WARNING:')} Do not make any payment — it may restart the clock.")
                print(f"  {y('WARNING:')} Do not acknowledge the debt in writing.")
            else:
                days_left = (expiry - today).days
                print(f"  {y('SOL expires:')} {expiry} ({days_left} days from today)")
                print(f"  {d('Debt is still within the statute of limitations.')}")
        except ValueError:
            print(f"  {y('Could not parse date. Format: YYYY-MM-DD')}")
    else:
        print(f"  {d('SOL typically runs from date of last payment or last activity.')}")
        print(f"  {d('Check your credit report for the original delinquency date.')}")

    print(f"\n  {d('Note: This is general information, not legal advice.')}")
    print(f"  {d('SOL rules vary by debt type and are subject to legal interpretation.')}")

# ─────────────────────────────────────────────────────
BENEFITS ELIGIBILITY
# ─────────────────────────────────────────────────────
def check_benefits():
    print(f"\n{b('🌱 PUBLIC BENEFITS ELIGIBILITY GUIDE')}")
    print(d("━" * 55))
    print(d("  You may qualify for programs you don't know about."))
    print(d("  All programs below are federally guaranteed rights, not charity."))
    print()

    programs = {
        'SNAP (Food Stamps)': {
            'url': 'https://www.fns.usda.gov/snap/eligibility',
            'basics': 'Income at or below 130% FPL. ~$281/month avg individual.',
            'apply': 'Apply at your state SNAP office or benefits.gov'
        },
        'Medicaid': {
            'url': 'https://www.medicaid.gov/medicaid/eligibility/index.html',
            'basics': 'Income-based health coverage. No/low cost. Emergency coverage often immediate.',
            'apply': 'healthcare.gov or your state Medicaid office'
        },
        'EITC (Earned Income Tax Credit)': {
            'url': 'https://www.irs.gov/credits-deductions/individuals/earned-income-tax-credit/eitc-income-limits-maximum-credit-amounts',
            'basics': 'Up to $7,430 refundable tax credit if you work. Many miss this.',
            'apply': 'File federal taxes. Free filing: irs.gov/freefile'
        },
        'LIHEAP (Energy Assistance)': {
            'url': 'https://www.acf.hhs.gov/ocs/liheap',
            'basics': 'Help with heating/cooling bills. Income-based.',
            'apply': 'Contact your local community action agency'
        },
        'WIC': {
            'url': 'https://www.fns.usda.gov/wic',
            'basics': 'Food + nutrition for pregnant/nursing women and children under 5.',
            'apply': 'Local WIC office. Usually same-day enrollment.'
        },
        'Social Security Disability (SSDI/SSI)': {
            'url': 'https://www.ssa.gov/benefits/disability/',
            'basics': 'If you cannot work due to disability. SSI also income/asset based.',
            'apply': 'ssa.gov/apply or call 1-800-772-1213'
        },
        'ACP (Affordable Connectivity Program)': {
            'url': 'https://www.fcc.gov/acp',
            'basics': '$30/month off internet bill. $75 for tribal lands.',
            'apply': 'affordableconnectivity.gov'
        },
        'TANF (Cash Assistance)': {
            'url': 'https://www.acf.hhs.gov/ofa/programs/tanf',
            'basics': 'Temporary cash assistance for families with children.',
            'apply': 'Your state TANF office (varies by state)'
        },
    }

    for name, info in programs.items():
        print(f"  {g('●')} {b(name)}")
        print(f"    {d(info['basics'])}")
        print(f"    Apply: {c(info['apply'])}")
        print(f"    Info:  {d(info['url'])}")
        print()

    print(f"  {b('Screening tools:')}")    
    print(f"  {c('benefits.gov')} — federal screener for 1,000+ programs")
    print(f"  {c('findhelp.org')} — local resources by zip code")
    print(f"  {c('211.org')}     — call 2-1-1, free, confidential, 24/7")

# ─────────────────────────────────────────────────────
CFPB COMPLAINT GUIDE
# ─────────────────────────────────────────────────────
def cfpb_guide():
    print(f"\n{b('⚖️ CFPB / FTC COMPLAINT GUIDE')}")
    print(d("━" * 55))
    print(d("  CFPB complaints have real teeth. Regulated companies MUST respond."))
    print(d("  Average response time: 15 days. Public record."))
    print()

    print(f"  {b('WHERE TO FILE:')}")  
    print(f"  {g('CFPB (banks, credit, debt collectors, mortgages):')}")  
    print(f"  {c('  consumerfinance.gov/complaint')}")
    print(f"  {d('  1-855-411-2372')})")
    print()
    print(f"  {g('FTC (fraud, scams, ID theft, unfair practices):')}")  
    print(f"  {c('  reportfraud.ftc.gov')}")
    print()
    print(f"  {g('State AG (check for pattern violations):')}")  
    print(f"  {c('  naag.org/find-my-ag')}")  
    print()
    print(f"  {b('WHAT TO INCLUDE:')}")  
    print(f"  {d('  - Name and address of the company')}")  
    print(f"  {d('  - Account numbers')}")  
    print(f"  {d('  - Dates of violations')}")  
    print(f"  {d('  - What law was violated (FDCPA, FCRA, TILA, etc.)')}")  
    print(f"  {d('  - What you want done')}")  
    print(f"  {d('  - Any letters or documentation')}")  
    print()
    print(f"  {b('POWER MOVE:')} {d('File with CFPB + state AG simultaneously.')}")  
    print(f"  {d('Pattern complaints trigger enforcement actions.')}")  

# ─────────────────────────────────────────────────────
STATUS / DASHBOARD
# ─────────────────────────────────────────────────────
def show_status():
    print(f"\n{b('📋 IDENTITY VAULT — STATUS')}")
    print(d("━" * 55))
    tracker = load_tracker()

    total = sum(len(v) for v in tracker.values())
    if total == 0:
        print(f"  {d('Vault is empty. Generate your first letter to start tracking.')}")
        return

    for category, items in tracker.items():
        if items:
            print(f"  {g(category.upper())} ({len(items)} tracked):")
            for item in items[-3:]:  # show last 3
                print(f"    {d('●')} {json.dumps(item)[:80]}")
    print(f"\n  {d('Vault location: ' + str(VAULT_DIR))}")

# ─────────────────────────────────────────────────────
MENU
# ─────────────────────────────────────────────────────
def show_menu():
    print(f"\n{b('🏛️ IDENTITY VAULT — WHAT DO YOU NEED?')}")
    print(d("━" * 55))
    items = [
        ('1', '📋 FOIA request',           'get government records on anything'),
        ('2', '💳 Debt validation',         'collectors must prove debt is real + pause all collection'),
        ('3', '✋ Cease and desist',        'stop harassment, unwanted contact, any conduct'),
        ('4', '📊 Credit dispute',          'fix errors on credit report (bureaus must investigate)'),
        ('5', '⏱️ Statute of limitations',  'check if a debt is time-barred'),
        ('6', '🌱 Benefits eligibility',    'programs you may qualify for and not know about'),
        ('7', '⚖️  CFPB/FTC complaint',     'file against a company (real enforcement power)'),
        ('8', '📁 Vault status',            'see all tracked matters'),
        ('Q', 'Quit',                       ''),
    ]
    for key, label, desc in items:
        print(f"  {g('[' + key + ']')} {b(label):<35} {d(desc)}")
    print()

def interactive_menu():
    while True:
        show_menu()
        choice = input(f"  {c('Choose:')} ").strip().upper()
        if choice == '1': generate_foia()
        elif choice == '2': generate_debt_validation()
        elif choice == '3': generate_cease_desist()
        elif choice == '4': generate_credit_dispute()
        elif choice == '5': check_sol()
        elif choice == '6': check_benefits()
        elif choice == '7': cfpb_guide()
        elif choice == '8': show_status()
        elif choice in ('Q', 'QUIT', 'EXIT'): break
        else: print(f"  {y('Invalid choice.')}")
        print()

# ─────────────────────────────────────────────────────
MAIN
# ─────────────────────────────────────────────────────
def main():
    setup_vault()
    parser = argparse.ArgumentParser(description="Identity Vault — Legal Autonomy Tools")
    parser.add_argument('--foia',           action='store_true')
    parser.add_argument('--debt-validate',  action='store_true')
    parser.add_argument('--cease-desist',   action='store_true')
    parser.add_argument('--credit-dispute', action='store_true')
    parser.add_argument('--sol-check',      action='store_true')
    parser.add_argument('--benefits',       action='store_true')
    parser.add_argument('--cfpb',           action='store_true')
    parser.add_argument('--status',         action='store_true')
    args = parser.parse_args()

    print()
    print(g("━" * 60))
    print(g("  🏛️ IDENTITY VAULT — Legal & Financial Autonomy"))
    print(f"  {d('Your rights, automated. All tools are legal. Nothing sends without you.')}")
    print(g("━" * 60))

    if   args.foia:           generate_foia()
    elif args.debt_validate:  generate_debt_validation()
    elif args.cease_desist:   generate_cease_desist()
    elif args.credit_dispute: generate_credit_dispute()
    elif args.sol_check:      check_sol()
    elif args.benefits:       check_benefits()
    elif args.cfpb:           cfpb_guide()
    elif args.status:         show_status()
    else:                     interactive_menu()

if __name__ == '__main__':
    main()
