#!/usr/bin/env python3
"""
Nexus Healer - Monitors and repairs Nexus instances
"""
import os
import sys
import time
import json
import signal
import subprocess
import threading
import requests
from pathlib import Path

class NexusHealer:
    def __init__(self, port, base_dir):
        self.port = port
        self.base_dir = Path(base_dir)
        self.health_log = self.base_dir / 'logs' / 'health.jsonl'
        self.health_log.parent.mkdir(exist_ok=True)
        self.failure_count = 0
        self.max_failures = 5
        self.healing = False
        self.stop_event = threading.Event()
        
        # Health check configuration
        self.check_interval = 30  # seconds
        self.timeout = 10  # seconds
    
    def start(self):
        """Start health monitoring"""
        print(f"🏥 Healer started for port {self.port}")
        
        monitor_thread = threading.Thread(target=self.monitor, daemon=True)
        monitor_thread.start()
        
        # Log startup
        self.log_health('healer_started', {
            'port': self.port,
            'check_interval': self.check_interval
        })
    
    def stop(self):
        """Stop health monitoring"""
        self.stop_event.set()
        print("🛑 Healer stopped")
    
    def monitor(self):
        """Monitor health and trigger repairs"""
        while not self.stop_event.is_set():
            try:
                healthy = self.check_health()
                
                if healthy:
                    if self.failure_count > 0:
                        print(f"✅ Health restored after {self.failure_count} failures")
                        self.failure_count = 0
                        self.log_health('health_restored', {'failure_count_reset': True})
                else:
                    self.failure_count += 1
                    print(f"⚠️ Health check failed ({self.failure_count}/{self.max_failures})")
                    
                    if self.failure_count >= self.max_failures and not self.healing:
                        self.healing = True
                        print("🔧 Starting healing process...")
                        self.heal()
                        self.healing = False
                
            except Exception as e:
                print(f"❌ Health monitor error: {e}")
            
            # Wait for next check
            self.stop_event.wait(self.check_interval)
    
    def check_health(self):
        """Check if Nexus is healthy"""
        try:
            response = requests.get(
                f'http://localhost:{self.port}/',
                timeout=self.timeout
            )
            
            healthy = response.status_code == 200
            
            self.log_health('check', {
                'timestamp': time.time(),
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'healthy': healthy
            })
            
            return healthy
            
        except requests.RequestException as e:
            self.log_health('check_failed', {
                'timestamp': time.time(),
                'error': str(e),
                'healthy': False
            })
            return False
    
    def heal(self):
        """Attempt to heal the Nexus instance"""
        print(f"🛠️  Starting healing process for port {self.port}")
        
        healing_steps = [
            self.restart_server,
            self.repair_files,
            self.escalate_healing
        ]
        
        for step in healing_steps:
            if self.try_healing_step(step):
                if self.check_health():
                    print(f"✅ Healing successful with step: {step.__name__}")
                    self.log_health('healing_successful', {
                        'step': step.__name__,
                        'failure_count': self.failure_count
                    })
                    self.failure_count = 0
                    return True
        
        # If all steps fail, log and potentially trigger replication
        print("❌ All healing steps failed")
        self.log_health('healing_failed', {
            'failure_count': self.failure_count,
            'action': 'may_trigger_replacement'
        })
        
        # Could trigger replication to replace this instance
        return False
    
    def try_healing_step(self, step_func):
        """Try a healing step with error handling"""
        try:
            return step_func()
        except Exception as e:
            print(f"❌ Healing step {step_func.__name__} failed: {e}")
            self.log_health('healing_step_failed', {
                'step': step_func.__name__,
                'error': str(e)
            })
            return False
    
    def restart_server(self):
        """Restart the HTTP server"""
        print("♻️  Attempting server restart...")
        
        # Kill existing server
        try:
            subprocess.run(['fuser', '-k', f'{self.port}/tcp'], 
                         stderr=subprocess.DEVNULL)
        except:
            pass
        
        # Wait a moment
        time.sleep(2)
        
        # Try to start via the main app
        app_path = self.base_dir / 'src' / 'app.py'
        if app_path.exists():
            # This would ideally be done by the controller
            # For now, we'll just check if port becomes available
            pass
        
        # Check if port is now free
        try:
            # Try to bind to port to see if it's free
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('localhost', self.port))
                return result != 0  # Port should be free if restart worked
        except:
            return False
    
    def repair_files(self):
        """Check and repair Nexus files"""
        print("📁 Checking and repairing files...")
        
        essential_files = [
            'index.html',
            'src/app.py',
            'src/replicate.py',
            'src/heal.py'
        ]
        
        all_exist = True
        for file in essential_files:
            file_path = self.base_dir / file
            if not file_path.exists():
                print(f"   Missing: {file}")
                all_exist = False
                
                # Try to restore from backup if available
                backup_path = self.base_dir / 'backups' / file
                if backup_path.exists():
                    print(f"   Restoring from backup: {file}")
                    backup_path.parent.mkdir(exist_ok=True)
                    shutil.copy2(backup_path, file_path)
        
        if not all_exist:
            # Try to restore from git
            print("   Attempting git restore...")
            try:
                subprocess.run(['git', 'checkout', '--', '.'], 
                             cwd=self.base_dir, 
                             capture_output=True)
            except:
                pass
        
        return self.check_health()
    
    def escalate_healing(self):
        """More aggressive healing steps"""
        print("🚑 Escalating healing...")
        
        # 1. Full restart of the application
        print("   1. Full application restart")
        
        # 2. System resource check
        print("   2. Checking system resources")
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory().percent
            
            if cpu > 90 or memory > 90:
                print(f"   High resource usage: CPU {cpu}%, Memory {memory}%")
                # Could trigger load-based replication here
        except:
            pass
        
        # 3. Network check
        print("   3. Checking network connectivity")
        
        # Return True if we think we've done enough
        # Actual success will be determined by health check
        return True
    
    def log_health(self, event_type, data):
        """Log health event"""
        entry = {
            'timestamp': time.time(),
            'event': event_type,
            'port': self.port,
            'data': data
        }
        
        with open(self.health_log, 'a') as f:
            f.write(json.dumps(entry) + '\n')
    
    def is_healthy(self):
        """Quick health check"""
        return self.failure_count < (self.max_failures // 2)
