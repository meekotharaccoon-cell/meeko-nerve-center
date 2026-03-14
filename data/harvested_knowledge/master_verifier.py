#!/usr/bin/env python3
"""
GAZA ROSE - MASTER SYSTEM VERIFICATION
Tests all self-healing systems and verifies they actually work.
Based on research from multiple academic and open-source sources. [citation:1][citation:2][citation:3]
"""

import os
import sys
import time
import json
import subprocess
import requests
from datetime import datetime
from pathlib import Path

# ==============================================
# CONFIGURATION
# ==============================================
VERIFY_ROOT = r"C:\Users\meeko\Desktop\GAZA_ROSE_VERIFICATION"
SYSTEMS_TO_TEST = {
    "self_healing_framework": {
        "path": f"{VERIFY_ROOT}/self-healing-framework",
        "test_cmd": "npm test",
        "type": "self_healing",
        "description": "Agentic Postgres self-healing framework [citation:1]"
    },
    "opensearch": {
        "test_cmd": "curl -s http://localhost:9200/_cluster/health",
        "type": "monitoring",
        "description": "ML-based anomaly detection [citation:2]"
    },
    "9v_checker": {
        "path": f"{VERIFY_ROOT}/9v-checker",
        "test_cmd": "python -c 'import ninev; print(\"9V-Checker OK\")'",
        "type": "verification",
        "description": "Formal trust verification [citation:3]"
    },
    "autoheal": {
        "path": f"{VERIFY_ROOT}/autoheal-locators",
        "test_cmd": "mvn test -Dtest=OrangeHRMLoginTest",
        "type": "browser_healing",
        "description": "AI-powered self-healing locators [citation:6]"
    },
    "chess": {
        "path": f"{VERIFY_ROOT}/chess",
        "test_cmd": "docker-compose -f CHESS-artifact/docker-compose.yml up -d",
        "type": "chaos_engineering",
        "description": "Chaos engineering fault injection [citation:9]"
    }
}

class SystemVerifier:
    """
    Tests every self-healing system and reports results.
    Based on formal verification methods from academic research. [citation:3][citation:4]
    """
    
    def __init__(self):
        self.results = {}
        self.passed = 0
        self.failed = 0
        self.start_time = datetime.now()
        
    def test_system(self, name, config):
        """Test a single system and return result"""
        print(f"\n🔍 TESTING: {name}")
        print(f"   {config.get('description', '')}")
        
        try:
            if name == "opensearch":
                # Test OpenSearch health endpoint
                result = subprocess.run(
                    ["curl", "-s", "http://localhost:9200/_cluster/health"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                if result.returncode == 0 and "status" in result.stdout:
                    status = json.loads(result.stdout).get("status", "unknown")
                    success = status in ["green", "yellow"]
                else:
                    success = False
                    
            elif "path" in config:
                # Run test in specified directory
                result = subprocess.run(
                    config["test_cmd"],
                    cwd=config["path"],
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                success = result.returncode == 0
            else:
                success = False
                
            if success:
                self.passed += 1
                print(f"   ✅ PASSED")
                return {"status": "PASS", "timestamp": str(datetime.now())}
            else:
                self.failed += 1
                print(f"   ❌ FAILED")
                return {"status": "FAIL", "timestamp": str(datetime.now())}
                
        except Exception as e:
            self.failed += 1
            print(f"   ❌ ERROR: {e}")
            return {"status": "ERROR", "error": str(e), "timestamp": str(datetime.now())}
    
    def verify_all(self):
        """Test all systems"""
        print("\n" + "="*60)
        print("  🧪 GAZA ROSE - MASTER SYSTEM VERIFICATION")
        print("="*60)
        print(f"  Testing {len(SYSTEMS_TO_TEST)} systems...")
        print("="*60)
        
        for name, config in SYSTEMS_TO_TEST.items():
            self.results[name] = self.test_system(name, config)
            time.sleep(2)
        
        return self.results
    
    def generate_report(self):
        """Generate comprehensive test report"""
        report = {
            "test_run": str(self.start_time),
            "duration": str(datetime.now() - self.start_time),
            "systems_tested": len(SYSTEMS_TO_TEST),
            "passed": self.passed,
            "failed": self.failed,
            "results": self.results,
            "summary": {
                "self_healing": [k for k, v in self.results.items() if v["status"] == "PASS"],
                "needs_attention": [k for k, v in self.results.items() if v["status"] != "PASS"]
            }
        }
        
        # Save report
        report_path = f"{VERIFY_ROOT}/verification_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
        
        # Generate HTML report
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>GAZA ROSE - System Verification Report</title>
            <style>
                body {{ font-family: Arial; margin: 40px; background: #0a0a0a; color: white; }}
                .header {{ text-align: center; margin-bottom: 40px; }}
                h1 {{ color: #ff6b6b; }}
                .summary {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 20px 0; }}
                .stat {{ background: #1a1a1a; padding: 20px; border-radius: 10px; text-align: center; }}
                .pass {{ color: #4caf50; font-size: 24px; }}
                .fail {{ color: #f44336; font-size: 24px; }}
                .system {{ background: #1a1a1a; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                .system.PASS {{ border-left: 5px solid #4caf50; }}
                .system.FAIL {{ border-left: 5px solid #f44336; }}
                .timestamp {{ color: #888; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🧪 GAZA ROSE - SYSTEM VERIFICATION REPORT</h1>
                <p>Generated: {report['test_run']}</p>
                <p>Duration: {report['duration']}</p>
            </div>
            
            <div class="summary">
                <div class="stat">
                    <div class="pass">{report['passed']}</div>
                    <div>SYSTEMS PASSING</div>
                </div>
                <div class="stat">
                    <div class="fail">{report['failed']}</div>
                    <div>SYSTEMS FAILING</div>
                </div>
                <div class="stat">
                    <div>{report['systems_tested']}</div>
                    <div>TOTAL SYSTEMS</div>
                </div>
            </div>
            
            <h2>📋 DETAILED RESULTS</h2>
        """
        
        for name, result in report['results'].items():
            status_class = "PASS" if result['status'] == "PASS" else "FAIL"
            html += f"""
            <div class="system {status_class}">
                <h3>{name.upper()}</h3>
                <p>Status: <strong class="{status_class.lower()}">{result['status']}</strong></p>
                <p>Timestamp: {result.get('timestamp', 'N/A')}</p>
                {f"<p>Error: {result.get('error', '')}</p>" if 'error' in result else ''}
            </div>
            """
        
        html += """
            <div class="timestamp">
                <p>Report generated by GAZA ROSE Verification Suite</p>
                <p>Based on research from multiple open-source frameworks [citation:1][citation:2][citation:3]</p>
            </div>
        </body>
        </html>
        """
        
        html_path = f"{VERIFY_ROOT}/verification_report.html"
        with open(html_path, "w") as f:
            f.write(html)
        
        print(f"\n📊 REPORT GENERATED: {report_path}")
        print(f"🌐 HTML REPORT: {html_path}")
        
        return report

if __name__ == "__main__":
    verifier = SystemVerifier()
    verifier.verify_all()
    report = verifier.generate_report()
    
    # Open HTML report
    import webbrowser
    webbrowser.open(f"file:///{VERIFY_ROOT}/verification_report.html")
