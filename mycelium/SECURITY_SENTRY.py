import re

def audit_code(code, context="Scavenged"):
    # High-risk patterns that could compromise the host
    blacklist = [
        r"os\.system\(['\"]rm ", r"shutil\.rmtree", r"os\.remove\(['\"]C:\\Windows", 
        r"format ", r"subprocess\.run\(['\"]powershell", r"registry", r"socket\.bind"
    ]
    
    for pattern in blacklist:
        if re.search(pattern, code, re.IGNORECASE):
            print(f"⚠️ SECURITY ALERT: Blocked {context} code containing pattern: {pattern}")
            return False, pattern
            
    return True, "Safe"

if __name__ == "__main__":
    print("🛡️ Security Sentry: Active and auditing buffers.")
