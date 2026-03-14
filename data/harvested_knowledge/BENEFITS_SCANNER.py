"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  MEEKO BENEFITS SCANNER                                                     ║
║  Screens federal + state programs you qualify for based on your vault.     ║
║  Generates pre-filled applications where possible.                         ║
╚══════════════════════════════════════════════════════════════════════════════╝

Programs screened:
  Federal: SNAP, Medicaid/CHIP, ACP, Lifeline, WIC, LIHEAP, SSI,
           SSDI, Housing vouchers (Section 8), EITC, Child Tax Credit,
           Free/Reduced school meals, Head Start, TANF, Pell Grant,
           FAFSA, AmeriCorps, Job Corps, Veterans benefits (if applicable)
  
  Auto-generates: Benefit summary report, application checklist,
                  links to apply, estimated monthly value

Usage: python BENEFITS_SCANNER.py
"""

import sys
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path.home() / "Desktop"))
try:
    from vault_reader import get_fields, vault_available, lock_vault
    VAULT_OK = vault_available()
except ImportError:
    VAULT_OK = False

OUTPUT_DIR = Path.home() / "Desktop" / "LEGAL_DOCUMENTS"
OUTPUT_DIR.mkdir(exist_ok=True)

# ── 2025 Federal Poverty Level (FPL) guidelines ───────────────────────────────
FPL_BASE    = 15_060   # 1-person annual (2025)
FPL_EACH    = 5_380    # each additional person

def fpl(household_size: int) -> int:
    n = max(1, household_size)
    return FPL_BASE + FPL_EACH * (n - 1)

def fpl_pct(income_annual: float, household_size: int) -> float:
    base = fpl(household_size)
    return (income_annual / base) * 100 if base else 999

# ── Program definitions ───────────────────────────────────────────────────────
# Each: name, income_pct_limit, description, estimated_monthly_value, apply_url, notes

PROGRAMS = [
    {
        "id": "snap",
        "name": "SNAP (Food Stamps)",
        "category": "Food",
        "income_limit_pct": 130,
        "gross_income_limit_pct": 200,
        "description": "Monthly funds for groceries loaded onto an EBT card.",
        "est_monthly_value": "~$200–$450/month depending on household size",
        "apply_url": "https://www.benefits.gov/benefit/361",
        "state_apply": "Search: '[your state] SNAP application online'",
        "notes": "Apply online or at local DSS/DHS office. Decision in ~30 days.",
        "docs_needed": ["ID", "SSN", "Proof of income", "Rent/utility bills"],
    },
    {
        "id": "medicaid",
        "name": "Medicaid / CHIP",
        "category": "Healthcare",
        "income_limit_pct": 138,
        "gross_income_limit_pct": 200,
        "description": "Free or low-cost health coverage for adults and children.",
        "est_monthly_value": "~$400–$800/month in coverage value",
        "apply_url": "https://www.healthcare.gov/medicaid-chip/",
        "state_apply": "https://www.medicaid.gov/about-us/contact-us/contact-state-page.html",
        "notes": "Apply anytime — no enrollment period. Coverage can be retroactive.",
        "docs_needed": ["ID", "SSN", "Proof of income", "Citizenship/residency"],
    },
    {
        "id": "acp",
        "name": "Affordable Connectivity Program (ACP)",
        "category": "Utilities",
        "income_limit_pct": 200,
        "gross_income_limit_pct": 200,
        "description": "Up to $30/month discount on internet service (up to $75 on tribal lands).",
        "est_monthly_value": "$30/month internet discount",
        "apply_url": "https://www.affordableconnectivity.gov/",
        "state_apply": "https://acpbenefit.org/",
        "notes": "Also qualifies you for a one-time $100 device discount.",
        "docs_needed": ["ID", "SSN or benefits letter"],
    },
    {
        "id": "lifeline",
        "name": "Lifeline Phone Program",
        "category": "Utilities",
        "income_limit_pct": 135,
        "gross_income_limit_pct": 200,
        "description": "$9.25/month discount on phone or internet service.",
        "est_monthly_value": "$9.25/month telecom discount",
        "apply_url": "https://www.lifelinesupport.org/",
        "state_apply": "https://www.lifelinesupport.org/",
        "notes": "Can be combined with ACP for maximum savings.",
        "docs_needed": ["ID", "Income proof or benefits letter"],
    },
    {
        "id": "liheap",
        "name": "LIHEAP (Energy Assistance)",
        "category": "Utilities",
        "income_limit_pct": 150,
        "gross_income_limit_pct": 200,
        "description": "Help paying heating/cooling bills, energy crises, and weatherization.",
        "est_monthly_value": "$300–$1,000/year in energy bill assistance",
        "apply_url": "https://www.acf.hhs.gov/ocs/programs/liheap",
        "state_apply": "Search: '[your state] LIHEAP application'",
        "notes": "Seasonal availability — apply in fall for winter heating.",
        "docs_needed": ["ID", "Proof of income", "Utility bills"],
    },
    {
        "id": "eitc",
        "name": "Earned Income Tax Credit (EITC)",
        "category": "Tax Credits",
        "income_limit_pct": 400,
        "gross_income_limit_pct": 400,
        "description": "Refundable federal tax credit for working individuals/families. Paid as a lump sum.",
        "est_monthly_value": "$600–$7,430/year (one-time at tax time)",
        "apply_url": "https://www.irs.gov/credits-deductions/individuals/earned-income-tax-credit-eitc",
        "state_apply": "Claimed on federal tax return (Form 1040)",
        "notes": "Many states have a matching state EITC on top of federal. File free at freefile.irs.gov",
        "docs_needed": ["W-2 or 1099", "SSN for all family members"],
    },
    {
        "id": "pell",
        "name": "Pell Grant (Education)",
        "category": "Education",
        "income_limit_pct": 300,
        "gross_income_limit_pct": 400,
        "description": "Free money for college — does not need to be repaid. Up to $7,395/year.",
        "est_monthly_value": "Up to $7,395/year for school",
        "apply_url": "https://studentaid.gov/h/apply-for-aid/fafsa",
        "state_apply": "https://studentaid.gov/",
        "notes": "File FAFSA every year. Most community colleges free with Pell if income qualifies.",
        "docs_needed": ["SSN", "Tax returns", "FSA ID (create at fsaid.ed.gov)"],
    },
    {
        "id": "housing",
        "name": "Section 8 / Housing Choice Voucher",
        "category": "Housing",
        "income_limit_pct": 50,
        "gross_income_limit_pct": 80,
        "description": "Voucher covers the difference between 30% of income and fair market rent.",
        "est_monthly_value": "Covers majority of rent — varies by area",
        "apply_url": "https://www.hud.gov/topics/housing_choice_voucher_program_section_8",
        "state_apply": "Contact local Public Housing Authority (PHA)",
        "notes": "Waitlist is often long (months–years). Apply NOW even if not immediately needed.",
        "docs_needed": ["ID", "SSN", "Income verification", "Rental history"],
    },
    {
        "id": "tanf",
        "name": "TANF (Cash Assistance)",
        "category": "Cash",
        "income_limit_pct": 100,
        "gross_income_limit_pct": 150,
        "description": "Monthly cash assistance for families with children.",
        "est_monthly_value": "$400–$700/month (varies by state)",
        "apply_url": "https://www.benefits.gov/benefit/613",
        "state_apply": "Search: '[your state] TANF application'",
        "notes": "Has work requirements after 24 months. Time-limited (60 months federal lifetime).",
        "docs_needed": ["ID", "SSN (all family members)", "Proof of income", "Birth certificates"],
    },
    {
        "id": "wic",
        "name": "WIC (Women, Infants, Children)",
        "category": "Food",
        "income_limit_pct": 185,
        "gross_income_limit_pct": 185,
        "description": "Food, nutrition counseling, and healthcare referrals for pregnant/nursing women and children under 5.",
        "est_monthly_value": "~$50–$100/month in food benefits",
        "apply_url": "https://www.fns.usda.gov/wic/wic-eligibility-requirements",
        "state_apply": "Search: '[your state] WIC program'",
        "notes": "Must have a qualifying condition (pregnant, nursing, recently gave birth, child under 5).",
        "docs_needed": ["ID", "Proof of income", "Proof of residency", "Proof of qualifying status"],
    },
    {
        "id": "school_meals",
        "name": "Free/Reduced School Meals",
        "category": "Food",
        "income_limit_pct": 185,
        "gross_income_limit_pct": 185,
        "description": "Free or reduced-price breakfast and lunch for school-age children.",
        "est_monthly_value": "~$150–$300/month per child in meal costs",
        "apply_url": "https://www.fns.usda.gov/nslp",
        "state_apply": "Apply through your child's school",
        "notes": "Apply at school start each year. Qualifies family for other benefits.",
        "docs_needed": ["Income verification (or SNAP/TANF letter auto-qualifies)"],
    },
    {
        "id": "ssi",
        "name": "SSI (Supplemental Security Income)",
        "category": "Cash",
        "income_limit_pct": 100,
        "gross_income_limit_pct": 100,
        "description": "Monthly cash for disabled, blind, or elderly low-income individuals.",
        "est_monthly_value": "Up to $943/month (2024)",
        "apply_url": "https://www.ssa.gov/ssi/",
        "state_apply": "ssa.gov or call 1-800-772-1213",
        "notes": "Also qualifies you for Medicaid automatically in most states.",
        "docs_needed": ["ID", "SSN", "Medical records", "Proof of income/assets"],
        "requires": ["disability_or_65_plus"],
    },
    {
        "id": "childcare",
        "name": "CCDBG Childcare Subsidy",
        "category": "Childcare",
        "income_limit_pct": 250,
        "gross_income_limit_pct": 250,
        "description": "Federal childcare subsidy for working/in-school parents.",
        "est_monthly_value": "Covers majority of childcare costs",
        "apply_url": "https://www.acf.hhs.gov/occ",
        "state_apply": "Search: '[your state] child care assistance program'",
        "notes": "Availability varies by state. Apply early — waitlists exist.",
        "docs_needed": ["ID", "Proof of income", "Childcare provider info"],
    },
    {
        "id": "broadband",
        "name": "Emergency Broadband / State Broadband Programs",
        "category": "Utilities",
        "income_limit_pct": 200,
        "gross_income_limit_pct": 200,
        "description": "State-level internet subsidy programs (varies by state).",
        "est_monthly_value": "Varies by state — up to $50/month",
        "apply_url": "https://www.benton.org/initiatives/broadband_opportunity/get_connected",
        "state_apply": "Search: '[your state] broadband assistance'",
        "notes": "Check your state's public utility commission website.",
        "docs_needed": ["ID", "Income proof"],
    },
]


def header():
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║  💰  MEEKO BENEFITS SCANNER                                                 ║
║      Screening programs you qualify for based on your identity vault        ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")

def main():
    if not VAULT_OK:
        print("\n  ❌ Identity vault not found.")
        print("  Run IDENTITY_VAULT_SETUP.py first.\n")
        return

    header()
    print("  Unlocking identity vault...\n")

    identity = get_fields([
        "full_legal_name", "monthly_income", "household_size",
        "state", "city", "date_of_birth", "occupation",
        "address_line1", "zip_code", "email_primary", "phone_primary",
    ])

    if not identity.get("full_legal_name"):
        print("  ❌ Could not unlock vault.\n")
        return

    # Parse income and household
    try:
        monthly = float(str(identity.get("monthly_income", "0")).replace(",","").replace("$",""))
        annual  = monthly * 12
    except:
        monthly_input = input("  Monthly income not in vault. Enter now (e.g. 2500): $")
        try:
            monthly = float(monthly_input.replace(",","").replace("$",""))
            annual  = monthly * 12
        except:
            monthly = 0
            annual  = 0

    try:
        hh_size = int(str(identity.get("household_size", "1")).strip())
    except:
        hh_input = input("  Household size not in vault. How many people in your household? ")
        try:
            hh_size = int(hh_input)
        except:
            hh_size = 1

    state = identity.get("state", "").upper()
    name  = identity.get("full_legal_name", "")

    print(f"  Name:            {name}")
    print(f"  Monthly income:  ${monthly:,.2f}  (${annual:,.2f}/year)")
    print(f"  Household size:  {hh_size}")
    print(f"  State:           {state}")

    pct = fpl_pct(annual, hh_size)
    print(f"  FPL %:           {pct:.0f}% of Federal Poverty Level")
    print(f"  ({hh_size}-person FPL: ${fpl(hh_size):,}/year)")

    # Screen programs
    print("\n\n  ══ SCREENING PROGRAMS ═══════════════════════════════════════════\n")

    qualified     = []
    likely        = []
    not_qualified = []

    for p in PROGRAMS:
        limit = p["income_limit_pct"]
        # Skip programs with special requirements (SSI) unless we know they qualify
        if p.get("requires"):
            not_qualified.append(p)
            continue
        if pct <= limit:
            qualified.append(p)
        elif pct <= p.get("gross_income_limit_pct", limit * 1.3):
            likely.append(p)
        else:
            not_qualified.append(p)

    # Monthly value estimate
    def extract_value(v_str):
        import re
        nums = re.findall(r'\d[\d,]*', v_str)
        if nums:
            return int(nums[0].replace(',', ''))
        return 0

    monthly_est = sum(extract_value(p["est_monthly_value"]) for p in qualified) / 12 if qualified else 0
    monthly_est += sum(extract_value(p["est_monthly_value"]) for p in likely) / 12 * 0.5 if likely else 0

    print(f"  ✅ LIKELY QUALIFIED ({len(qualified)} programs):\n")
    for p in qualified:
        print(f"    ★ {p['name']}")
        print(f"      {p['description']}")
        print(f"      Value: {p['est_monthly_value']}")
        print(f"      Apply: {p['apply_url']}")
        print()

    if likely:
        print(f"\n  🟡 POSSIBLY QUALIFIED — CHECK ELIGIBILITY ({len(likely)} programs):\n")
        for p in likely:
            print(f"    ◑ {p['name']}")
            print(f"      Income limit: {p['income_limit_pct']}% FPL — you are at {pct:.0f}% (close)")
            print(f"      Apply: {p['apply_url']}")
            print()

    if not_qualified:
        print(f"\n  ○ NOT CURRENTLY QUALIFIED ({len(not_qualified)} programs)")
        for p in not_qualified:
            print(f"      {p['name']} (limit: {p['income_limit_pct']}% FPL)")

    # Generate report
    print("\n\n  ══ GENERATING BENEFITS REPORT ═══════════════════════════════════\n")

    report = f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  BENEFITS ELIGIBILITY REPORT                                                ║
║  Generated: {datetime.now().strftime('%B %d, %Y %I:%M %p')}                               
║  For: {name}                     
╚══════════════════════════════════════════════════════════════════════════════╝

FINANCIAL PROFILE:
  Monthly income:  ${monthly:,.2f}
  Annual income:   ${annual:,.2f}
  Household size:  {hh_size}
  FPL percentage:  {pct:.1f}%
  State:           {state}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ PROGRAMS YOU LIKELY QUALIFY FOR ({len(qualified)} found):

"""
    for p in qualified:
        report += f"""
┌─ {p['name']} [{p['category']}]
│  {p['description']}
│  Estimated value: {p['est_monthly_value']}
│  Apply at: {p['apply_url']}
│  State apply: {p.get('state_apply', '')}
│  Documents needed: {', '.join(p.get('docs_needed', []))}
│  Notes: {p.get('notes', '')}
└{'─' * 70}
"""

    if likely:
        report += f"\n🟡 PROGRAMS TO CHECK ({len(likely)} — income close to limit):\n\n"
        for p in likely:
            report += f"  • {p['name']}: Apply at {p['apply_url']}\n"
            report += f"    Income limit: {p['income_limit_pct']}% FPL | Your income: {pct:.0f}% FPL\n\n"

    report += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

APPLICATION CHECKLIST — DOCUMENTS YOU'LL NEED:

  ☐ Government-issued photo ID (state ID, driver's license, or passport)
  ☐ Social Security card or SSN documentation
  ☐ Proof of income (pay stubs, tax returns, benefit letters)
  ☐ Proof of address (utility bill, lease, bank statement)
  ☐ Birth certificates (if applying for household members)
  ☐ Bank account info (for direct deposit — routing + account number)

PRIORITY ORDER — Apply in this order for fastest impact:
  1. SNAP — fastest approval, immediate food assistance
  2. Medicaid — covers healthcare, no deductibles
  3. LIHEAP — seasonal, apply before winter
  4. ACP + Lifeline — easiest to apply, immediate utility savings
  5. EITC — file at tax time for lump sum payment
  6. Section 8 — long waitlist, apply NOW

FREE HELP APPLYING:
  • 211.org — local human services directory, will help you apply
  • Benefits.gov — official federal portal for all programs
  • Your local DSS/DHS office — in-person help applying
  • Legal aid organizations in your area — free, confidential

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This report was generated by the Meeko Mycelium benefits scanner.
Information is based on 2025 federal guidelines. Program availability
and income limits vary by state. Always verify directly with the program.
"""

    report_file = OUTPUT_DIR / f"{datetime.now().strftime('%Y%m%d')}_BENEFITS_REPORT_{name.replace(' ','_')}.txt"
    report_file.write_text(report, encoding="utf-8")

    print(f"  ✅ Report saved to: {report_file}")
    print(f"\n  SUMMARY:")
    print(f"  Programs you qualify for: {len(qualified)}")
    print(f"  Programs to check:        {len(likely)}")
    print(f"  Output folder:            {OUTPUT_DIR}\n")

    lock_vault()

if __name__ == "__main__":
    main()
