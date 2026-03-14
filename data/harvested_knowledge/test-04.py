import os
from dotenv import load_dotenv
load_dotenv()

matrix_directive = {
    "universal_id": 'matrix',
    "name": "matrix",
    "filesystem": {"folders": [], "files": {}},
    "children": [
        {
            "universal_id": "matrix-https",
            "name": "matrix_https",
            # ... other config
        },
        {
            "universal_id": "websocket-relay",
            "name": "matrix_websocket",
            "config": {
                "port": 8765,
                "factories": {"reflex.health.status_report": {}},
                # This relay handles both alerts and other RPC calls
                "service-manager": [{"role": ["hive.rpc.route", "hive.alert.send_alert_msg"]}]
            }
        },
        {
            "universal_id": "detective-1",
            "name": "forensic_detective",
            "config": {
                # This agent subscribes to the data feed role to receive reports
                "service-manager": [{"role": ["hive.forensics.data_feed"]}]
            }
        },

        {
            "universal_id": "apache_watchdog-1",
            "name": "apache_watchdog",
            "app": "matrix-core",
            "config": {
                "check_interval_sec": 10,
                "service_name": "httpd",  # change to "httpd" for RHEL/CentOS
                "ports": [80, 443],
                "restart_limit": 3,
                "always_alert": 1,
                "alert_cooldown": 300,
                #"alert_to_role": "hive.alert.send_alert_msg",
                # Role for detailed, machine-readable data packets
                "report_to_role": "hive.forensics.data_feed",
                "report_handler": "cmd_ingest_status_report"
            },
            "children": [],
            "filesystem": {},
            "delegated": [],
        },
        {
            "universal_id": "invisible-man",
            "name": "ghost_wire",
            "config": {
                "tick_rate": 5,
                "watch_paths": [
                    "/etc/passwd",
                    "/etc/shadow",
                    "/root/.ssh",
                    "/var/www",
                    "/home"
                ],
                "command_patterns": [
                    "rm -rf",
                    "scp",
                    "curl",
                    "wget",
                    "nano /etc",
                    "vi /etc",
                    "vim /etc",
                    "sudo",
                    "su",
                    "chmod 777",
                    "service stop",
                ],
                #"report_to_role": "hive.forensics.data_feed",
                #"report_handler": "cmd_ingest_status_report"
            }
        },
        {
            "universal_id": "nginx-sentinel",
            "name": "nginx_watchdog",
            "app": "swarm-edge",
            "config": {
                "check_interval_sec": 10,
                "always_alert": 1,
                "restart_limit": 3,
                "service_name": "nginx",
                "ports": [85],
                "alert_cooldown": 300,
                "alert_to_role": "hive.alert.send_alert_msg", #They both send alerts, but report_to_role - a little more
                "report_to_role": "hive.forensics.data_feed"
            }
        },
        {
            "universal_id": "mysql-sentry-1",
            "name": "mysql_watchdog",
            "config": {
                "service_name": "mariadb", # Or "mysql", "mysqld" depending on your system
                "check_interval_sec": 30,
                "restart_limit": 2,
                #"alert_to_role": "hive.alert.send_alert_msg", They both send alerts, but report_to_role - a little more
                "report_to_role": "hive.forensics.data_feed"
            }
        },
        {
            "universal_id": "redis-hammer",
            "name": "redis_watchdog",
            "app": "redis-core",
            "enabled": False, #deactivate - to activate remove enabled element
            "config": {
                "check_interval_sec": 10,
                "restart_limit": 3,
                "redis_port": 6379,
                "always_alert": 1,
                "socket_path": "/var/run/redis/redis-server.sock",
                "service_name": "redis"
            }
            ,
            "children": []
        },
        {
            "universal_id": "gatekeeper",
            "name": "gatekeeper",
            "app": "swarm-core",
            "enabled": False, #deactivate - to activate remove enabled element
            "config": {
                "log_path": "/var/log/auth.log",
                "maxmind_db": "GeoLite2-City.mmdb",
                "geoip_enabled": 1,
                "always_alert": 1,
            }
            ,
            "children": []
        },
        {
            "universal_id": "mysql-red-phone",
            "name": "mysql_watchdog",
            "app": "mysql-demo",
            "enabled": False, #deactivate - to activate remove enabled element
            "config": {
                "mysql_port": 3306,
                "socket_path": "/var/run/mysqld/mysqld.sock",
                "service_name": "mariadb",
                "check_interval_sec": 20,
                "restart_limit": 3,
                "alert_thresholds": {
                    "uptime_pct_min": 90,
                    "slow_restart_sec": 10
                },
                "role": "mysql-alarm",
            }
            ,
            "children": []
        },
        {
            "universal_id": "discord-delta-5",
            "name": "discord_relay",
            "app": "mysql-demo",
            "filesystem": {
                "folders": []
            },
            "config": {
                "bot_token": os.getenv("DISCORD_TOKEN"),
                "channel_id": os.getenv("DISCORD_CHANNEL_ID"),
                "service-manager": [{
                    "role": ["comm", "comm.security", "hive.alert.send_alert_msg", "comm.*"],
                    "scope": ["parent", "any"],     # who it serves
                    "auth": {"sig": True},
                    "priority": 10,                # lower = more preferred
                    "exclusive": False             # can other services respond?
                }]
            }
        },
        {
            # Our new, config-driven system health monitor
            "universal_id": "system-health-1",
            "name": "system_health",
            "config": {
                "check_interval_sec": 60,
                "mem_threshold_percent": 90.0,  # Custom threshold
                "cpu_threshold_percent": 85.0,  # Custom threshold
                "disk_threshold_percent": 95.0,
                # It reports to the same data feed as the other watchdogs
                "report_to_role": "hive.forensics.data_feed",
                "report_handler": "cmd_ingest_status_report"
            }
        },
        {
            "universal_id": "network-health-1",
            "name": "network_health",
            "config": {
                "check_interval_sec": 30,  # Check network status every 30 seconds
                "exclude_interfaces": [],  # List of interfaces to skip (e.g. ["lo"])
                "tx_threshold_mbps": 100,  # Warn if outbound rate exceeds 100 Mbps
                "rx_threshold_mbps": 100,  # Warn if inbound rate exceeds 100 Mbps
                "conn_threshold": 1000,  # Warn if active TCP/UDP conns > 1000
                "top_n_procs": 5,  # Include top 5 process hogs in report
                "report_to_role": "hive.forensics.data_feed",
                "report_handler": "cmd_ingest_status_report"
            }
        },
        {
            "universal_id": "telegram-bot-father-2",
            "name": "telegram_relay",
            "app": "mysql-demo",
            "filesystem": {
                "folders": []
            },
            "config": {
                "bot_token": os.getenv("TELEGRAM_API_KEY"),
                "chat_id": os.getenv("TELEGRAM_CHAT_ID"),
                "service-manager": [{
                    "role": ["comm", "comm.security", "comm.*, hive.alert.send_alert_msg"],
                    "scope": ["parent", "any"],     # who it serves
                    "auth": {"sig": True},
                    "priority": 10,                # lower = more preferred
                    "exclusive": False             # can other services respond?
                }]
            }
        },
    ]
}