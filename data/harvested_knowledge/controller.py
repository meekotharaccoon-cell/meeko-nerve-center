"""
SolarPunk System Integration Controller
Coordinates all modules and provides unified interface
"""

import os
import sys
import importlib.util
from datetime import datetime

class SystemController:
    def __init__(self):
        self.modules = {}
        self.system_status = {
            'online': True,
            'start_time': datetime.now(),
            'modules_loaded': 0,
            'last_update': None
        }
        self.load_modules()
    
    def load_modules(self):
        module_dir = 'modules'
        if not os.path.exists(module_dir):
            print(f"❌ Modules directory not found: {module_dir}")
            return
        
        for filename in os.listdir(module_dir):
            if filename.endswith('.py') and filename != '__init__.py':
                module_name = filename[:-3]
                module_path = os.path.join(module_dir, filename)
                
                try:
                    spec = importlib.util.spec_from_file_location(module_name, module_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    self.modules[module_name] = module
                    self.system_status['modules_loaded'] += 1
                    print(f"✅ Loaded module: {module_name}")
                    
                except Exception as e:
                    print(f"❌ Failed to load {module_name}: {e}")
        
        self.system_status['last_update'] = datetime.now()
    
    def get_system_report(self):
        report = f"""
        ╔══════════════════════════════════════════════════════╗
        ║              SOLARPUNK SYSTEM STATUS                 ║
        ╠══════════════════════════════════════════════════════╣
        ║  Status:           {'🟢 ONLINE' if self.system_status['online'] else '🔴 OFFLINE'}
        ║  Uptime:           {(datetime.now() - self.system_status['start_time']).total_seconds():.0f} seconds
        ║  Modules Loaded:   {self.system_status['modules_loaded']}
        ║  Last Updated:     {self.system_status['last_update'].strftime('%Y-%m-%d %H:%M:%S')}
        ╠══════════════════════════════════════════════════════╣
        ║  AVAILABLE MODULES:                                 ║
        """
        
        for module_name in sorted(self.modules.keys()):
            report += f"        ║    • {module_name:30} ║\n"
        
        report += "        ╠══════════════════════════════════════════════════════╣\n"
        report += "        ║  SYSTEM PATHS:                                      ║\n"
        
        paths = [
            ('Root Directory', os.getcwd()),
            ('Modules', 'modules/'),
            ('Data Storage', 'data/'),
            ('Logs', 'logs/'),
            ('Exports', 'exports/')
        ]
        
        for name, path in paths:
            exists = "✅" if os.path.exists(path) else "❌"
            report += f"        ║    {exists} {name:20} {path:25} ║\n"
        
        report += "        ╚══════════════════════════════════════════════════════╝"
        
        return report
    
    def execute_module(self, module_name, function_name='main', *args):
        if module_name not in self.modules:
            print(f"❌ Module not found: {module_name}")
            return False
        
        module = self.modules[module_name]
        
        if hasattr(module, function_name):
            try:
                function = getattr(module, function_name)
                print(f"🚀 Executing {module_name}.{function_name}...")
                result = function(*args) if args else function()
                return result
            except Exception as e:
                print(f"❌ Execution failed: {e}")
                return False
        else:
            print(f"❌ Function {function_name} not found in {module_name}")
            return False
    
    def automated_daily_cycle(self):
        print("\n🔄 INITIATING DAILY OPERATIONAL CYCLE")
        print("="*50)
        
        steps = [
            ('financial_simulator', 'main', 'Run financial simulation'),
            ('asset_manager', 'asset_management_demo', 'Update asset allocations'),
            ('dashboard', 'main', 'Refresh monitoring dashboard')
        ]
        
        for module_name, function_name, description in steps:
            print(f"\n📋 Step: {description}")
            print("-"*30)
            
            success = self.execute_module(module_name, function_name)
            
            if success is not False:
                print(f"✅ {description} completed successfully")
            else:
                print(f"⚠️  {description} encountered issues")
        
        print("\n" + "="*50)
        print("🎯 DAILY CYCLE COMPLETE")
        print("📊 Reports available in exports/ directory")
    
    def interactive_console(self):
        while True:
            print("\n" + "="*60)
            print("SOLARPUNK SYSTEM INTEGRATION CONSOLE")
            print("="*60)
            print(self.get_system_report().split('╠')[0].split('║')[1].strip())
            print("\nOPERATIONS MENU:")
            print("  1. View Complete System Status")
            print("  2. Execute Financial Simulation")
            print("  3. Launch Asset Manager")
            print("  4. Start Monitoring Dashboard")
            print("  5. Run Automated Daily Cycle")
            print("  6. Export System Diagnostics")
            print("  7. Exit Console")
            print("="*60)
            
            choice = input("\nEnter command (1-7): ").strip()
            
            if choice == "1":
                print(self.get_system_report())
            
            elif choice == "2":
                self.execute_module('financial_simulator', 'main')
            
            elif choice == "3":
                self.execute_module('asset_manager', 'asset_management_demo')
            
            elif choice == "4":
                print("1. Run simulation")
                print("2. Live dashboard")
                subchoice = input("Select dashboard mode: ")
                if subchoice == "1":
                    self.execute_module('dashboard', 'simulate_operations', 30)
                else:
                    self.execute_module('dashboard', 'run_live_dashboard')
            
            elif choice == "5":
                self.automated_daily_cycle()
            
            elif choice == "6":
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"exports/system_diagnostics_{timestamp}.txt"
                
                with open(filename, 'w') as f:
                    f.write(self.get_system_report())
                    f.write("\n\nMODULE DETAILS:\n")
                    for name, module in self.modules.items():
                        f.write(f"\n{name}:\n")
                        f.write(f"  Functions: {[x for x in dir(module) if not x.startswith('_')]}\n")
                
                print(f"✅ Diagnostics exported to {filename}")
            
            elif choice == "7":
                print("\n🚀 SolarPunk system shutdown complete")
                print("📁 All data preserved in project directories")
                break
            
            else:
                print("❌ Invalid command")
            
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    controller = SystemController()
    controller.interactive_console()
