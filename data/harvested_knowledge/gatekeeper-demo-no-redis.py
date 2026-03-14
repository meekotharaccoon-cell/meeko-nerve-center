import os
from dotenv import load_dotenv

load_dotenv()

# MATRIX CORE DEPLOYMENT
matrix_directive = {
    "universal_id": 'matrix',
    "name": "matrix",
    "filesystem": {
        "folders": [],
        "files": {}
    },

    "children": [

        # MATRIX PROTECTION LAYER 4 SENTINELS
        # 4th SENTINEL WATCHES MATRIX, REST WATCH SENTINEL IN FRONT
        # ONLY WAY TO KILL MATRIX WOULD BE TO KILL THEM ALL, TAKING ANY COMBO OF 4 OUT DOES NOTHING
        {
            "universal_id": "guardian-1",
            "name": "sentinel",
            "app": "matrix-core",
            "filesystem": {},
            "config": {"matrix_secure_verified": 1},
            "children": [
                {
                    "universal_id": "guardian-2",
                    "name": "sentinel",
                    "app": "matrix-core",
                    "filesystem": {},
                    "config": {"matrix_secure_verified": 1},
                    "children": [
                        {
                            "universal_id": "guardian-3",
                            "name": "sentinel",
                            "app": "matrix-core",
                            "filesystem": {},
                            "config": {"matrix_secure_verified": 1},
                            "children": [
                                {
                                    "universal_id": "guardian-4",
                                    "name": "sentinel",
                                    "app": "matrix-core",
                                    "filesystem": {},
                                    "config": {
                                        "matrix_secure_verified": 1,
                                        "watching": "the Queen",
                                        "universal_id_under_watch": "matrix"
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        },
        {
            "universal_id": "matrix-https",
            "name": "matrix_https",
            "delegated": [],
            "app": "matrix-core",
            "filesystem": {
                "folders": [],
                "files": {}
            },
            "allowlist_ips": [
                  #allowed list of ips to access server
            ],

        },
        {
            "universal_id": "agent_doctor-1",
            "name": "agent_doctor",
            "config": {
                "scan_interval_sec": 20,
                "max_allowed_beacon_age": 10,
                "threads_to_check": ["worker", "cmd_listener"]
            }
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
                    "chmod 777"
                ]
            }
        },
        {
            "universal_id": "scavenger-strike",
            "name": "scavenger",
            "app": "matrix-core",
            "filesystem": {
                "folders": []
            },
            "config": {}
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
                "alert_cooldown": 300
            },
            "children": [],
            "filesystem": {},
            "delegated": [],
        }
        ,
        {
            "universal_id": "commander-1",
            "name": "commander",
            "app": "matrix-core",
            "children": []
        },
        {
            "universal_id": "gatekeeper",
            "name": "gatekeeper",
            "app": "swarm-core",
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
            "universal_id": "websocket-relay",
            "name": "matrix_websocket",
            "config": {
                "port": 8765,
                "factories": {
                    "reflex.health.status_report": {}
                },
                "service-manager": [{
                    "role": ["hive.alert.send_alert_msg, hive.rpc.route"],
                    "scope": ["parent", "any"],     # who it serves
                    "auth": {"sig": True},
                    "priority": 10,                # lower = more preferred
                    "exclusive": False             # can other services respond?
                }],
                "allowlist_ips": [
                  #allowed list of ips to access server
                ],

            },

            "filesystem": {},
            "delegated": []
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
        {
            "universal_id": "storm-crow",
            "name": "storm_crow",
            "delegated": [],
            "description": "Watches for server weather alerts for your area.",
            "config": {
                "zip-code": os.getenv("WEATHER_ZIPCODE"),
                "service-manager": [{
                    "alert-handler": ["hive.alert.send_alert_msg"], #setup discord, telegram, websocket to use this role to receive alerts from storm-crow,
                }]
            }

        },

    ]
}
