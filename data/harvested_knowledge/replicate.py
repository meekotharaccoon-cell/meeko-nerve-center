#!/usr/bin/env python3
"""
Nexus Replicator - Creates new Nexus instances
"""
import os
import sys
import json
import time
import shutil
import hashlib
import subprocess
from pathlib import Path
import random

class NexusReplicator:
    def __init__(self, base_dir, parent_id):
        self.base_dir = Path(base_dir)
        self.parent_id = parent_id
        self.children = []
        self.replication_log = self.base_dir / 'logs' / 'replications.jsonl'
        self.replication_log.parent.mkdir(exist_ok=True)
        
        # Load configuration
        self.config = self.load_config()
    
    def load_config(self):
        """Load replication configuration"""
        config_path = self.base_dir / 'config' / 'replication.json'
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        
        # Default configuration
        return {
            "min_uptime_before_replication": 300,  # 5 minutes
            "min_free_disk_gb": 1,
            "max_instances_per_host": 3,
            "replication_cooldown": 3600,  # 1 hour
            "target_ports": [5000, 5001, 5002, 5003, 5004]
        }
    
    def should_replicate(self):
        """Determine if conditions are right for replication"""
        # Check uptime
        uptime_file = self.base_dir / 'logs' / 'startup_time.txt'
        if uptime_file.exists():
            with open(uptime_file, 'r') as f:
                start_time = float(f.read().strip())
                uptime = time.time() - start_time
                if uptime < self.config['min_uptime_before_replication']:
                    return False
        
        # Check disk space
        try:
            import psutil
            free_gb = psutil.disk_usage(self.base_dir).free / (1024**3)
            if free_gb < self.config['min_free_disk_gb']:
                return False
        except:
            pass  # If psutil not available, skip check
        
        # Check if we've reached max instances
        if len(self.get_existing_instances()) >= self.config['max_instances_per_host']:
            return False
        
        # Check cooldown
        last_replication = self.get_last_replication_time()
        if time.time() - last_replication < self.config['replication_cooldown']:
            return False
        
        return True
    
    def get_existing_instances(self):
        """Get list of existing Nexus instances on this host"""
        instances = []
        parent_dir = self.base_dir.parent
        
        for item in parent_dir.iterdir():
            if item.is_dir() and item.name.startswith('nexus_'):
                # Check if it's a Nexus instance
                if (item / 'src' / 'app.py').exists():
                    instances.append(item.name)
        
        return instances
    
    def get_last_replication_time(self):
        """Get timestamp of last replication"""
        if not self.replication_log.exists():
            return 0
        
        last_time = 0
        with open(self.replication_log, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    last_time = max(last_time, entry.get('timestamp', 0))
                except:
                    continue
        
        return last_time
    
    def replicate(self):
        """Create a new Nexus instance"""
        # Find available port
        used_ports = self.get_used_ports()
        available_ports = [p for p in self.config['target_ports'] if p not in used_ports]
        
        if not available_ports:
            print("❌ No available ports for replication")
            return None
        
        new_port = random.choice(available_ports)
        new_instance_id = self.generate_child_id()
        
        # Create new instance directory
        new_dir = self.base_dir.parent / f"nexus_{new_instance_id}"
        
        try:
            print(f"🌀 Creating new Nexus instance at {new_dir.name} on port {new_port}")
            
            # Copy essential files (exclude logs and data)
            exclude = {'logs', 'data', '__pycache__', '.git', '*.log', '*.db'}
            
            def ignore_patterns(path, names):
                ignored = set()
                for name in names:
                    # Check if this should be excluded
                    for pattern in exclude:
                        if pattern.startswith('*.') and name.endswith(pattern[1:]):
                            ignored.add(name)
                        elif name == pattern:
                            ignored.add(name)
                        elif (path / name).is_dir() and name in exclude:
                            ignored.add(name)
                return ignored
            
            shutil.copytree(self.base_dir, new_dir, ignore=ignore_patterns, dirs_exist_ok=True)
            
            # Generate new config for child
            child_config = {
                'parent_id': self.parent_id,
                'instance_id': new_instance_id,
                'created_at': time.time(),
                'port': new_port,
                'ethics_hash': hashlib.sha256(json.dumps(self.load_ethics()).encode()).hexdigest()[:16]
            }
            
            config_file = new_dir / 'config' / 'instance.json'
            config_file.parent.mkdir(exist_ok=True)
            with open(config_file, 'w') as f:
                json.dump(child_config, f, indent=2)
            
            # Create startup script for child
            startup_script = new_dir / 'start_child.sh'
            with open(startup_script, 'w') as f:
                f.write(f"""#!/bin/bash
cd "{new_dir}"
python3 src/app.py --port {new_port} --instance-id {new_instance_id}
""")
            
            os.chmod(startup_script, 0o755)
            
            # Start child instance
            child_process = subprocess.Popen(
                ['python3', 'src/app.py', '--port', str(new_port), '--instance-id', new_instance_id],
                cwd=new_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Log replication
            self.log_replication(new_instance_id, new_port, child_process.pid)
            
            # Add to children list
            self.children.append({
                'id': new_instance_id,
                'port': new_port,
                'pid': child_process.pid,
                'start_time': time.time()
            })
            
            print(f"✅ Created child instance {new_instance_id} (PID: {child_process.pid})")
            return new_instance_id
            
        except Exception as e:
            print(f"❌ Replication failed: {e}")
            # Clean up on failure
            if new_dir.exists():
                shutil.rmtree(new_dir, ignore_errors=True)
            return None
    
    def generate_child_id(self):
        """Generate unique child ID"""
        seed = f"{self.parent_id}{time.time()}{os.urandom(8).hex()}"
        return hashlib.sha256(seed.encode()).hexdigest()[:8]
    
    def get_used_ports(self):
        """Get list of ports currently in use by Nexus instances"""
        used_ports = []
        
        # Check existing instances
        for instance_dir in self.base_dir.parent.iterdir():
            if instance_dir.is_dir() and instance_dir.name.startswith('nexus_'):
                config_file = instance_dir / 'config' / 'instance.json'
                if config_file.exists():
                    try:
                        with open(config_file, 'r') as f:
                            config = json.load(f)
                            used_ports.append(config.get('port'))
                    except:
                        pass
        
        return used_ports
    
    def load_ethics(self):
        """Load ethics configuration"""
        ethics_path = self.base_dir / 'src' / 'ethics.json'
        if ethics_path.exists():
            with open(ethics_path, 'r') as f:
                return json.load(f)
        return {}
    
    def log_replication(self, child_id, child_port, child_pid):
        """Log replication event"""
        entry = {
            'timestamp': time.time(),
            'parent_id': self.parent_id,
            'child_id': child_id,
            'child_port': child_port,
            'child_pid': child_pid,
            'event': 'replication'
        }
        
        with open(self.replication_log, 'a') as f:
            f.write(json.dumps(entry) + '\n')
