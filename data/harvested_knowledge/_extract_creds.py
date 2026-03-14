import subprocess, json, os, ctypes, sys
from pathlib import Path

# Pull Kraken key pair IDs from Windows Credential Manager
# These are stored as key_pair_es384.kraken and key_pair_es384_id.kraken
print('=== WINDOWS CREDENTIAL MANAGER EXTRACT ===')

try:
    import ctypes.wintypes
    # Use PowerShell to read the actual credential values
    ps_script = """
Add-Type -AssemblyName System.Security
function Get-Cred($target) {
    $sig = @'
[DllImport("Advapi32.dll", EntryPoint = "CredReadW", CharSet = CharSet.Unicode, SetLastError = true)]
public static extern bool CredRead(string target, int type, int flags, out IntPtr credential);
[DllImport("Advapi32.dll", EntryPoint = "CredFree", SetLastError = true)]
public static extern void CredFree(IntPtr buffer);
'@
    $Advapi32 = Add-Type -MemberDefinition $sig -Name 'Advapi32' -Namespace 'PsUtils' -PassThru -ErrorAction SilentlyContinue
    $pCredential = [IntPtr]::Zero
    $result = [PsUtils.Advapi32]::CredRead($target, 1, 0, [ref]$pCredential)
    if ($result) {
        try {
            $credential = [System.Runtime.InteropServices.Marshal]::PtrToStructure($pCredential, [type][System.Management.Automation.PSObject])
        } finally {
            [PsUtils.Advapi32]::CredFree($pCredential)
        }
    }
}

$targets = @('session.kraken','key_pair_es384.kraken','key_pair_es384_id.kraken','device.kraken')
foreach ($t in $targets) {
    try {
        $cred = Get-StoredCredential -Target $t 2>$null
        if ($cred) {
            $pwd = [Runtime.InteropServices.Marshal]::PtrToStringBSTR([Runtime.InteropServices.Marshal]::SecureStringToBSTR($cred.Password))
            Write-Output "${t}|||${pwd}"
        }
    } catch {}
}
"""
    r = subprocess.run(['powershell', '-Command', ps_script], capture_output=True, text=True, timeout=10)
    if r.stdout.strip():
        for line in r.stdout.strip().splitlines():
            if '|||' in line:
                name, val = line.split('|||', 1)
                print(f'  FOUND: {name} = {val[:20]}...')
    else:
        print('  PowerShell credential read returned empty (normal - needs CredentialManager module)')
except Exception as e:
    print(f'  Note: {e}')

# Try the simpler cmdkey approach
print()
print('=== CMDKEY DETAILS ===')
try:
    r = subprocess.run(['cmdkey', '/list'], capture_output=True, text=True, timeout=5)
    for line in r.stdout.splitlines():
        if 'kraken' in line.lower() or 'github' in line.lower():
            print('  ' + line.strip())
except: pass

print()
print('Key finding: Kraken has session/keypair in credential manager.')
print('These are SESSION tokens, not API keys.')
print('For API keys: kraken.com -> Security -> API -> Add Key')
