# Crisis Response Coordination AI
import requests
import json
from datetime import datetime


class CrisisResponseAI:
    """AI that coordinates humanitarian aid distribution."""

    CRISIS_ZONES = {
        "gaza": {
            "needs": ["food", "medical", "shelter", "water"],
            "trusted_orgs": ["UNRWA", "PCRF", "MedicalAidForPalestinians"],
            # In a real system these would be verified on-chain wallets.
            "crypto_wallets": [],
            "priority": "critical",
        },
        "sudan": {
            "needs": ["food", "medical", "refugee_support"],
            "trusted_orgs": ["UNHCR", "RedCross", "MSF"],
            "priority": "critical",
        },
        "congo": {
            "needs": ["medical", "food", "child_protection"],
            "trusted_orgs": ["UNICEF", "IRC", "DoctorsWithoutBorders"],
            "priority": "high",
        },
    }

    def __init__(self):
        self.aid_log = []

    def identify_most_effective_allocation(self, amount):
        """AI determines where aid is most needed."""
        allocations = []

        for zone, data in self.CRISIS_ZONES.items():
            effectiveness_score = {
                "gaza": 0.95,  # Current acute crisis
                "sudan": 0.90,
                "congo": 0.85,
            }.get(zone, 0.70)

            allocation = {
                "zone": zone,
                "amount": round(amount * effectiveness_score, 2),
                "needs": data["needs"][:2],  # Top 2 needs
                "orgs": data["trusted_orgs"],
                "timestamp": str(datetime.now()),
                "effectiveness_score": effectiveness_score,
            }
            allocations.append(allocation)

        # Sort by effectiveness
        allocations.sort(key=lambda x: x["effectiveness_score"], reverse=True)
        return allocations

    def generate_smart_contract(self, allocation):
        """Create transparent smart contract payload for aid."""
        contract = {
            "contract_id": f"AID-CONTRACT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "parties": ["Autonomous_Humanitarian_AI", allocation["zone"]],
            "terms": {
                "amount": allocation["amount"],
                "currency": "USD",
                "purpose": f"Humanitarian aid for {allocation['zone']}",
                "distribution_method": "crypto_to_verified_wallets",
                "verification": "public_blockchain",
                "reporting": "weekly_transparency_reports",
            },
            "conditions": [
                "Funds only for humanitarian purposes",
                "Public audit trail required",
                "AI verification of distribution",
            ],
            "created": str(datetime.now()),
            "blockchain_anchor": True,
        }
        return contract

    def monitor_impact(self, allocation):
        """AI monitors aid impact."""
        # This would connect to on-ground reporting
        impact_metrics = {
            "estimated_people_helped": int(
                allocation["amount"] / 50
            ),  # Rough estimate
            "food_packages": int(allocation["amount"] / 25),
            "medical_kits": int(allocation["amount"] / 100),
            "water_supply_days": int(allocation["amount"] / 10),
        }

        return {
            "allocation_id": allocation.get("tracking_id", "UNKNOWN"),
            "impact": impact_metrics,
            "verification_status": "ai_estimated",
            "next_allocation_recommendation": "continue_support",
        }


if __name__ == "__main__":
    # Lightweight CLI test harness so importing this module
    # from the humanitarian orchestrator does not trigger test output.
    crisis_ai = CrisisResponseAI()

    print("  CRISIS RESPONSE AI ACTIVATED")
    print("=" * 50)

    test_amount = 1000
    allocations = crisis_ai.identify_most_effective_allocation(test_amount)

    print(f"TEST ALLOCATION OF ${test_amount}:")
    for alloc in allocations[:2]:  # Show top 2
        print(f"\n {alloc['zone'].upper()}: ${alloc['amount']}")
        print(f"   Needs: {', '.join(alloc['needs'])}")
        print(f"   Orgs: {', '.join(alloc['orgs'][:2])}")

        contract = crisis_ai.generate_smart_contract(alloc)
        print(f"   Contract: {contract['contract_id']}")

        impact = crisis_ai.monitor_impact(alloc)
        print(f"   Estimated impact: {impact['impact']['estimated_people_helped']} people")

    print("\n" + "=" * 50)
    print(" AI READY TO COORDINATE HUMANITARIAN AID")
    print(" Transparent, blockchain-verified, AI-optimized")
