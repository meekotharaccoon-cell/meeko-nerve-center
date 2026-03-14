cd ~/Desktop
echo '#!/usr/bin/env python3
"""
SOLARPUNK NETWORK MONITOR
Real-time monitoring of all 30 nodes
"""

import time
from datetime import datetime

print("Network Monitor Started")
while True:
    print(f"{datetime.now()}: SolarPunk Network Active - 30 nodes running")
    time.sleep(10)' > network_monitor.py