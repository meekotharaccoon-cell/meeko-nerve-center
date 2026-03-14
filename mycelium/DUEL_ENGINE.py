import time
import subprocess
import os

def duel_functions(func_name, version_a, version_b):
    results = {}
    for version, code in [('A', version_a), ('B', version_b)]:
        test_file = f'data/temp_duel_{version}.py'
        # Wrap the scavenged code in a performance timer
        test_wrapper = f"""
import time
{code}
start = time.perf_counter()
try:
    {func_name}()
    print(f"SUCCESS:{{time.perf_counter() - start}}")
except Exception as e:
    print(f"FAILURE:{{e}}")
"""
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_wrapper)
        
        try:
            proc = subprocess.run(['python', test_file], capture_output=True, text=True, timeout=5)
            output = proc.stdout.strip()
            if "SUCCESS" in output:
                results[version] = float(output.split(':')[1])
            else:
                results[version] = float('inf')
        except:
            results[version] = float('inf')
        finally:
            if os.path.exists(test_file): os.remove(test_file)

    winner = 'A' if results.get('A', float('inf')) <= results.get('B', float('inf')) else 'B'
    print(f"🏆 Duel for {func_name}: Version {winner} won ({results[winner]:.6f}s)")
    return version_a if winner == 'A' else version_b

if __name__ == "__main__":
    print("⚖️ Duel Engine: Standing by for arbitration.")
